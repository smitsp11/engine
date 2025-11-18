"""
Prompt rewriting engine for subtasks.

This module transforms raw subtask descriptions into optimized, context-rich
prompts that maximize the likelihood of successful execution.

For each subtask, the rewriter injects:
- Previous outputs (context continuity from earlier steps)
- Success criteria (explicit constraints and goals)
- Examples (few-shot scaffolding when available)
- Think-step-by-step instructions (Chain-of-Thought)
- Tool-specific best practices

This is the "meta-prompting" layer that sits between planning and execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import Subtask, ToolName
from .memory import Memory
from .state import TaskState
from . import utils


class PromptRewriter:
    """
    Transform raw subtask descriptions into optimized prompts.
    
    The rewriter is deterministic by default (for testing), but designed
    so that you can later swap in LLM-based rewriting with minimal changes.
    """

    def __init__(self) -> None:
        # Tool-specific templates for best practices
        self._tool_templates = self._initialize_tool_templates()

    def rewrite(
        self,
        subtask: Subtask,
        tool: ToolName,
        memory: Memory,
        state: TaskState,
    ) -> str:
        """
        Rewrite a subtask description into an optimized prompt.

        Parameters
        ----------
        subtask:
            The subtask to rewrite a prompt for.
        tool:
            The tool that will execute this subtask.
        memory:
            Current agent memory with previous outputs and context.
        state:
            Current task state with high-level task info.

        Returns
        -------
        str
            An optimized, context-rich prompt ready for the tool.
        """
        utils.logger().info(
            "PromptRewriter: rewriting subtask prompt",
            extra={"subtask_id": subtask.id, "tool": tool.value},
        )

        # 1. Start with base description
        base = subtask.description

        # 2. Add high-level context
        context_block = self._build_context_block(subtask, state, memory)

        # 3. Add previous outputs summary (continuity)
        previous_outputs_block = self._build_previous_outputs_block(subtask, memory)

        # 4. Add success criteria (explicit constraints)
        criteria_block = self._build_criteria_block(subtask)

        # 5. Add tool-specific scaffolding
        tool_scaffolding = self._build_tool_scaffolding(tool, subtask)

        # 6. Add think-step-by-step instruction
        cot_instruction = self._build_cot_instruction(tool)

        # Assemble the final optimized prompt
        sections = [
            "=== OPTIMIZED PROMPT ===",
            "",
            "## Context",
            context_block,
            "",
            "## Your Task",
            base,
            "",
        ]

        if previous_outputs_block:
            sections.extend([
                "## Previous Work",
                previous_outputs_block,
                "",
            ])

        if criteria_block:
            sections.extend([
                "## Success Criteria",
                criteria_block,
                "",
            ])

        if tool_scaffolding:
            sections.extend([
                "## Tool Guidance",
                tool_scaffolding,
                "",
            ])

        sections.extend([
            "## Instructions",
            cot_instruction,
            "",
            "Now proceed with the task above.",
        ])

        rewritten_prompt = "\n".join(sections)

        utils.logger().debug(
            "PromptRewriter: prompt rewritten",
            extra={
                "subtask_id": subtask.id,
                "original_length": len(base),
                "rewritten_length": len(rewritten_prompt),
            },
        )

        return rewritten_prompt

    # ------------------------------------------------------------------
    # Context builders
    # ------------------------------------------------------------------

    def _build_context_block(
        self,
        subtask: Subtask,
        state: TaskState,
        memory: Memory,
    ) -> str:
        """Build a high-level context summary."""
        parts = []
        
        if state.task_description:
            parts.append(f"Overall Goal: {state.task_description}")
        
        parts.append(f"Current Step: {subtask.id}")
        
        if subtask.dependencies:
            deps_str = ", ".join(subtask.dependencies)
            parts.append(f"Depends On: {deps_str}")
        
        if state.plan and state.plan.subtasks:
            total_steps = len(state.plan.subtasks)
            completed_steps = len(state.subtask_results)
            parts.append(f"Progress: {completed_steps}/{total_steps} steps completed")
        
        return "\n".join(parts)

    def _build_previous_outputs_block(
        self,
        subtask: Subtask,
        memory: Memory,
    ) -> str:
        """Summarize relevant previous outputs for context continuity."""
        if not subtask.dependencies:
            return ""
        
        parts = []
        for dep_id in subtask.dependencies:
            if dep_id in memory.tool_outputs:
                output = memory.tool_outputs[dep_id]
                # Extract key info from the output
                summary = self._summarize_output(dep_id, output)
                parts.append(f"- From {dep_id}: {summary}")
        
        if not parts:
            return ""
        
        return "\n".join(parts)

    def _summarize_output(self, subtask_id: str, output: Dict[str, Any]) -> str:
        """Create a concise summary of a subtask's output."""
        # Extract the most relevant piece of information
        if "text" in output:
            text = str(output["text"])
            # Truncate long outputs
            if len(text) > 150:
                text = text[:150] + "..."
            return text
        elif "results" in output:
            results = output.get("results", [])
            return f"{len(results)} results found"
        elif "summary" in output:
            return str(output["summary"])
        elif "key" in output:
            return f"stored as {output['key']}"
        else:
            return "completed successfully"

    def _build_criteria_block(self, subtask: Subtask) -> str:
        """Format success criteria as explicit constraints."""
        parts = []
        
        if subtask.success_criteria:
            parts.append(f"✓ {subtask.success_criteria}")
        
        if subtask.deliverable:
            parts.append(f"📦 Deliverable: {subtask.deliverable}")
        
        return "\n".join(parts) if parts else ""

    def _build_tool_scaffolding(self, tool: ToolName, subtask: Subtask) -> str:
        """Add tool-specific best practices and guidance."""
        template = self._tool_templates.get(tool, "")
        return template

    def _build_cot_instruction(self, tool: ToolName) -> str:
        """Build a Chain-of-Thought instruction tailored to the tool."""
        base = "Think step-by-step:"
        
        if tool == ToolName.GENERATE_TEXT:
            steps = [
                "1. Understand what information is being requested",
                "2. Consider any constraints or requirements",
                "3. Organize your thoughts logically",
                "4. Generate clear, concise text",
                "5. Verify it meets the success criteria",
            ]
        elif tool == ToolName.SEARCH_IN_FILES:
            steps = [
                "1. Identify the key search terms",
                "2. Consider what types of files might contain this info",
                "3. Execute the search systematically",
                "4. Review results for relevance",
                "5. Extract the most pertinent findings",
            ]
        elif tool == ToolName.MODIFY_DATA:
            steps = [
                "1. Understand the current data structure",
                "2. Identify what transformations are needed",
                "3. Apply modifications systematically",
                "4. Validate the modified data",
                "5. Summarize the changes made",
            ]
        elif tool == ToolName.SAVE_OUTPUT:
            steps = [
                "1. Gather all relevant outputs from previous steps",
                "2. Organize the information logically",
                "3. Format it for storage",
                "4. Save with a clear reference key",
                "5. Confirm successful storage",
            ]
        else:
            steps = [
                "1. Understand the task requirements",
                "2. Break it into smaller steps",
                "3. Execute each step carefully",
                "4. Validate the result",
                "5. Confirm success",
            ]
        
        return base + "\n" + "\n".join(steps)

    # ------------------------------------------------------------------
    # Template initialization
    # ------------------------------------------------------------------

    def _initialize_tool_templates(self) -> Dict[ToolName, str]:
        """Initialize tool-specific templates with best practices."""
        return {
            ToolName.GENERATE_TEXT: (
                "Best practices for text generation:\n"
                "- Be specific and concrete\n"
                "- Use clear structure (bullets, numbered lists, paragraphs)\n"
                "- Include all requested information\n"
                "- Provide clear, well-structured output"
            ),
            ToolName.SEARCH_IN_FILES: (
                "Best practices for searching:\n"
                "- Use relevant keywords\n"
                "- Be prepared for no results (that's valid too)\n"
                "- Focus on extracting the most relevant findings\n"
                "- Consider fallback strategies if nothing is found"
            ),
            ToolName.MODIFY_DATA: (
                "Best practices for data modification:\n"
                "- Preserve important structure from previous outputs\n"
                "- Make transformations explicit and traceable\n"
                "- Include a summary of what changed\n"
                "- Validate the modified data makes sense"
            ),
            ToolName.SAVE_OUTPUT: (
                "Best practices for saving:\n"
                "- Collect all relevant information from prior steps\n"
                "- Use descriptive keys that indicate content\n"
                "- Ensure the saved content is complete\n"
                "- Confirm storage was successful"
            ),
        }


__all__ = ["PromptRewriter"]

