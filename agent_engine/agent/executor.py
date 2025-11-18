"""
Subtask executor and simple self-check logic.

The executor is responsible for:
- mapping a `Subtask` to a concrete tool function
- building the tool input payload
- running the tool
- evaluating the result with a lightweight self-check
- updating memory and task state
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .memory import Memory
from .state import TaskState
from .schemas import Subtask, SubtaskResult, SubtaskStatus, ToolName
from .tools import TOOL_REGISTRY, ToolFunc
from .prompt_rewriter import PromptRewriter
from . import utils


@dataclass
class CheckResult:
    """Outcome of the self-check step for a subtask result."""

    success: bool
    retry: bool
    reasoning: str


class ToolRouter:
    """Simple, rule-based tool router for choosing tools and fallbacks."""

    def __init__(self, tool_registry: Dict[ToolName, ToolFunc]) -> None:
        self.tool_registry = tool_registry

    def choose_tool(self, subtask: Subtask, memory: Memory, state: TaskState) -> ToolName:
        # Prefer explicit tool if registered.
        if subtask.tool in self.tool_registry:
            return subtask.tool

        desc = subtask.description.lower()
        if "search" in desc or "lookup" in desc:
            return ToolName.SEARCH_IN_FILES
        if "save" in desc or "store" in desc:
            return ToolName.SAVE_OUTPUT
        if "modify" in desc or "transform" in desc or "refine" in desc:
            return ToolName.MODIFY_DATA

        return ToolName.GENERATE_TEXT

    def choose_fallback(
        self,
        original_tool: ToolName,
        subtask: Subtask,
        memory: Memory,
        state: TaskState,
    ) -> Optional[ToolName]:
        # Very simple fallback: if search yields nothing useful, fall back to text generation.
        if original_tool == ToolName.SEARCH_IN_FILES:
            return ToolName.GENERATE_TEXT
        return None


class Executor:
    """
    Execute individual subtasks by routing them to the appropriate tool.

    The executor owns the *action* and *observation* parts of the loop:
    it calls tools, collects outputs, performs a simple self-check, and
    records results into memory and state.
    """

    def __init__(
        self,
        memory: Memory,
        state: TaskState,
        tool_registry: Optional[Dict[ToolName, ToolFunc]] = None,
        prompt_rewriter: Optional[PromptRewriter] = None,
    ) -> None:
        self.memory = memory
        self.state = state
        self.tool_registry: Dict[ToolName, ToolFunc] = tool_registry or TOOL_REGISTRY
        self.router = ToolRouter(self.tool_registry)
        self.prompt_rewriter = prompt_rewriter or PromptRewriter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_subtask(self, subtask: Subtask, *, allow_retry: bool = True) -> SubtaskResult:
        """
        Run the tool associated with `subtask` and return a `SubtaskResult`.

        This method:
        - builds a tool payload from the subtask and current memory/state
        - calls the tool
        - runs a simple self-check on the tool output
        - may perform a single retry if the self-check suggests it
        - records the final result into memory and task state
        """
        tool_name = self.router.choose_tool(subtask, self.memory, self.state)
        utils.logger().info(
            "Executor: executing subtask",
            extra={"subtask_id": subtask.id, "tool": tool_name.value},
        )

        # --- ReAct: THOUGHT ---
        thought = (
            f"Decide which tool to use for subtask {subtask.id}: {subtask.description}"
        )
        self.memory.record_trace(
            subtask.id,
            {
                "timestamp": utils.utc_now_iso(),
                "type": "thought",
                "content": thought,
            },
        )

        tool = self.tool_registry.get(tool_name)
        if tool is None:
            reasoning = f"No tool registered for {tool_name.value!r}."
            self.memory.add_note(reasoning)
            result = SubtaskResult(
                subtask_id=subtask.id,
                status=SubtaskStatus.FAILED,
                output={},
                error=reasoning,
            )
            self._update_after_execution(subtask, result, None)
            return result

        # PROMPT REWRITING: Transform subtask into optimized, context-rich prompt
        rewritten_prompt = self.prompt_rewriter.rewrite(
            subtask=subtask,
            tool=tool_name,
            memory=self.memory,
            state=self.state,
        )
        self.memory.add_note(f"Rewritten prompt for {subtask.id} ({len(rewritten_prompt)} chars)")

        payload = self._build_payload(subtask, tool_name, rewritten_prompt=rewritten_prompt)

        # --- ReAct: ACTION ---
        self.memory.record_trace(
            subtask.id,
            {
                "timestamp": utils.utc_now_iso(),
                "type": "action",
                "tool": tool_name.value,
                "payload_preview": {k: v for k, v in payload.items() if k in {"prompt", "query", "label"}},
            },
        )

        try:
            output = tool(payload)
        except Exception as exc:  # pragma: no cover - defensive
            error_msg = f"Tool {subtask.tool.value} raised error: {exc}"
            utils.logger().error(error_msg)
            self.memory.add_note(error_msg)
            result = SubtaskResult(
                subtask_id=subtask.id,
                status=SubtaskStatus.FAILED,
                output={},
                error=str(exc),
            )
            self._update_after_execution(subtask, result, None)
            return result

        # --- ReAct: OBSERVATION ---
        self.memory.record_trace(
            subtask.id,
            {
                "timestamp": utils.utc_now_iso(),
                "type": "observation",
                "tool": tool_name.value,
                "output_preview": list(output.keys()),
            },
        )

        # Provisional success: we still run self-check before finalising.
        provisional = SubtaskResult(
            subtask_id=subtask.id,
            status=SubtaskStatus.SUCCEEDED,
            output=output,
            error=None,
        )

        check = self.self_check(subtask, output)

        if not check.success:
            self.memory.add_note(
                f"Self-check failed for {subtask.id}: {check.reasoning} "
                f"(retry={check.retry})"
            )
            # --- ReAct: CRITIQUE ---
            self.memory.record_trace(
                subtask.id,
                {
                    "timestamp": utils.utc_now_iso(),
                    "type": "critique",
                    "content": check.reasoning,
                    "success": check.success,
                    "retry": check.retry,
                },
            )
            if allow_retry and check.retry:
                # Single retry with allow_retry=False to avoid infinite loops.
                utils.logger().info(
                    "Executor: retrying subtask after failed self-check",
                    extra={"subtask_id": subtask.id},
                )
                return self.execute_subtask(subtask, allow_retry=False)

            # If no retry is suggested, try a simple fallback tool once.
            fallback_tool = self.router.choose_fallback(tool_name, subtask, self.memory, self.state)
            if allow_retry and fallback_tool is not None and fallback_tool in self.tool_registry:
                self.memory.add_note(
                    f"Routing to fallback tool {fallback_tool.value} for subtask {subtask.id}."
                )
                fallback_payload = self._build_payload(subtask, fallback_tool)
                fallback_fn = self.tool_registry[fallback_tool]
                try:
                    fb_output = fallback_fn(fallback_payload)
                except Exception as exc:  # pragma: no cover - defensive
                    provisional.status = SubtaskStatus.FAILED
                    provisional.error = f"Fallback tool error: {exc}"
                else:
                    # Treat fallback output as final observation.
                    self.memory.record_trace(
                        subtask.id,
                        {
                            "timestamp": utils.utc_now_iso(),
                            "type": "observation",
                            "tool": fallback_tool.value,
                            "output_preview": list(fb_output.keys()),
                        },
                    )
                    provisional.output = fb_output
                    # Re-run self-check using same criteria; this might still fail,
                    # but gives the agent a second chance with a different tool.
                    fb_check = self.self_check(
                        Subtask(
                            id=subtask.id,
                            description=subtask.description,
                            tool=fallback_tool,
                            dependencies=subtask.dependencies,
                            success_criteria=subtask.success_criteria,
                            deliverable=subtask.deliverable,
                        ),
                        fb_output,
                    )
                    if fb_check.success:
                        provisional.status = SubtaskStatus.SUCCEEDED
                        provisional.error = None
                        check = fb_check

            provisional.status = SubtaskStatus.FAILED
            provisional.error = f"Self-check failed: {check.reasoning}"

        self._update_after_execution(subtask, provisional, check)
        return provisional

    # Backwards-compatible alias used by earlier code.
    def run_subtask(self, subtask: Subtask) -> SubtaskResult:  # pragma: no cover - simple wrapper
        return self.execute_subtask(subtask)

    # ------------------------------------------------------------------
    # Self-check logic
    # ------------------------------------------------------------------

    def self_check(self, subtask: Subtask, tool_output: Dict[str, Any]) -> CheckResult:
        """
        Fake LLM-based self-check that assesses whether a subtask succeeded.

        Heuristics (deterministic):
        - GENERATE_TEXT: success if "Generated:" present and text is non-empty.
        - SEARCH_IN_FILES: success if results list is non-empty.
        - MODIFY_DATA: success if `summary` present in output.
        - SAVE_OUTPUT: success if `stored` flag is True.
        """
        tool_name = subtask.tool
        reasoning_parts = []
        success = False
        retry = False

        if tool_name == ToolName.GENERATE_TEXT:
            text = str(tool_output.get("text", ""))
            success = bool(text) and "Generated:" in text
            reasoning_parts.append(
                "Output contains generated text." if success else "Missing or empty generated text."
            )
        elif tool_name == ToolName.SEARCH_IN_FILES:
            results = tool_output.get("results") or []
            success = len(results) > 0
            reasoning_parts.append(
                "Found mock search results." if success else "No search results were returned."
            )
            # If no results, we might suggest a retry once.
            retry = not success
        elif tool_name == ToolName.MODIFY_DATA:
            summary = tool_output.get("summary")
            success = isinstance(summary, str) and "Modified data" in summary
            reasoning_parts.append(
                "Summary of modified data present."
                if success
                else "Summary of modifications missing."
            )
        elif tool_name == ToolName.SAVE_OUTPUT:
            stored = bool(tool_output.get("stored"))
            success = stored and "key" in tool_output
            reasoning_parts.append(
                "Output stored with a key." if success else "Output was not confirmed as stored."
            )
        else:  # pragma: no cover - future tools
            reasoning_parts.append("Unknown tool type; assuming failure.")
            success = False

        reasoning = " ".join(reasoning_parts) or "No specific reasoning."
        return CheckResult(success=success, retry=retry, reasoning=reasoning)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        subtask: Subtask,
        tool_name: ToolName,
        rewritten_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Construct a JSON-like payload for the target tool based on the subtask.
        
        If a rewritten_prompt is provided, it will be used instead of the raw
        subtask description for prompt/query fields.
        """
        # Use rewritten prompt if available, otherwise fall back to original description
        effective_prompt = rewritten_prompt if rewritten_prompt else subtask.description
        
        base: Dict[str, Any] = {
            "task": self.state.task_description,
            "subtask_id": subtask.id,
            "description": subtask.description,  # Keep original for reference
            "previous_outputs": dict(self.memory.tool_outputs),
        }

        if tool_name == ToolName.GENERATE_TEXT:
            base["prompt"] = effective_prompt  # Use optimized prompt
        elif tool_name == ToolName.SEARCH_IN_FILES:
            base["query"] = effective_prompt  # Use optimized prompt
        elif tool_name == ToolName.MODIFY_DATA:
            base["data"] = {
                "description": effective_prompt,  # Use optimized prompt
                "previous_outputs": dict(self.memory.tool_outputs),
            }
        elif tool_name == ToolName.SAVE_OUTPUT:
            base["label"] = subtask.id
            base["content"] = {
                "task": self.state.task_description,
                "subtask_id": subtask.id,
                "plan_summary": [s.id for s in (self.state.plan.subtasks if self.state.plan else [])],
                "optimized_description": effective_prompt,  # Include optimized version
            }

        return base

    def _update_after_execution(
        self,
        subtask: Subtask,
        result: SubtaskResult,
        check: Optional[CheckResult],
    ) -> None:
        """Persist the result to state and memory and log basic info."""
        self.state.finish_subtask(subtask.id, result)
        self.memory.record_result(subtask.id, result)

        if check is not None:
            self.memory.add_note(
                f"Self-check for {subtask.id}: "
                f"success={check.success}, retry={check.retry}. "
                f"Reasoning: {check.reasoning}"
            )


__all__ = ["Executor", "CheckResult"]


