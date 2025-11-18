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
from . import utils


@dataclass
class CheckResult:
    """Outcome of the self-check step for a subtask result."""

    success: bool
    retry: bool
    reasoning: str


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
    ) -> None:
        self.memory = memory
        self.state = state
        self.tool_registry: Dict[ToolName, ToolFunc] = tool_registry or TOOL_REGISTRY

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
        utils.logger().info(
            "Executor: executing subtask",
            extra={"subtask_id": subtask.id, "tool": subtask.tool.value},
        )

        tool = self.tool_registry.get(subtask.tool)
        if tool is None:
            reasoning = f"No tool registered for {subtask.tool.value!r}."
            self.memory.add_note(reasoning)
            result = SubtaskResult(
                subtask_id=subtask.id,
                status=SubtaskStatus.FAILED,
                output={},
                error=reasoning,
            )
            self._update_after_execution(subtask, result, None)
            return result

        payload = self._build_payload(subtask)

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
            if allow_retry and check.retry:
                # Single retry with allow_retry=False to avoid infinite loops.
                utils.logger().info(
                    "Executor: retrying subtask after failed self-check",
                    extra={"subtask_id": subtask.id},
                )
                return self.execute_subtask(subtask, allow_retry=False)

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

    def _build_payload(self, subtask: Subtask) -> Dict[str, Any]:
        """
        Construct a JSON-like payload for the target tool based on the subtask.
        """
        base: Dict[str, Any] = {
            "task": self.state.task_description,
            "subtask_id": subtask.id,
            "description": subtask.description,
            "previous_outputs": dict(self.memory.tool_outputs),
        }

        if subtask.tool == ToolName.GENERATE_TEXT:
            base["prompt"] = subtask.description
        elif subtask.tool == ToolName.SEARCH_IN_FILES:
            base["query"] = subtask.description
        elif subtask.tool == ToolName.MODIFY_DATA:
            base["data"] = {
                "description": subtask.description,
                "previous_outputs": dict(self.memory.tool_outputs),
            }
        elif subtask.tool == ToolName.SAVE_OUTPUT:
            base["label"] = subtask.id
            base["content"] = {
                "task": self.state.task_description,
                "subtask_id": subtask.id,
                "plan_summary": [s.id for s in (self.state.plan.subtasks if self.state.plan else [])],
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



