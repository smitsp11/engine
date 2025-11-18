"""
LLM-based (simulated) planner.

For now this uses a deterministic, rule-based "fake LLM" so that the system
is fully testable without external dependencies. The public interface is
designed so that you can later swap in a real LLM call with minimal changes.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import List

from .schemas import Subtask, TaskPlan, ToolName, validate_task_plan
from . import utils


class Planner:
    """
    Produce a structured multi-step plan for a natural language task.

    Public API:
        Planner.create_plan(task: str) -> TaskPlan

    The `plan` method is kept as a thin alias for backwards compatibility
    with earlier code in this project.
    """

    def create_plan(self, task: str) -> TaskPlan:
        """
        Create a TaskPlan for the given high-level task description.

        In a production system this would:
        - Prompt an LLM with the task and a JSON schema
        - Parse the JSON into Subtask objects
        - Validate with `validate_task_plan`

        Here we emulate that behaviour deterministically.
        """
        utils.logger().info("Planner: creating plan", extra={"task": task})

        subtasks: List[Subtask] = self._fake_llm_plan(task)
        plan = TaskPlan(task=task, subtasks=subtasks)

        # Validate structure and constraints (5–15 subtasks, unique IDs, etc.)
        validate_task_plan(plan)
        return plan

    # Alias used by existing core loop
    def plan(self, task: str) -> TaskPlan:  # pragma: no cover - trivial wrapper
        return self.create_plan(task)

    # ------------------------------------------------------------------
    # Internal "fake LLM" implementation
    # ------------------------------------------------------------------

    def _fake_llm_plan(self, task: str) -> List[Subtask]:
        """
        Deterministically construct 5–7 subtasks tailored to the task string.

        This simulates the output of an LLM while keeping behaviour predictable.
        """
        lower = task.lower()

        # Choose a general pattern based on keywords
        if "birthday" in lower or "party" in lower:
            base = "birthday_party"
        elif "research" in lower or "study" in lower:
            base = "research"
        else:
            base = "generic"

        if base == "birthday_party":
            subtasks = [
                Subtask(
                    id="step-1",
                    description="Clarify constraints: budget, date, and number of guests.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=[],
                    success_criteria="Constraints are listed clearly (budget, date, guest count).",
                    deliverable="Short paragraph outlining constraints.",
                ),
                Subtask(
                    id="step-2",
                    description="Brainstorm 3–5 party themes and locations.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=["step-1"],
                    success_criteria="At least three distinct theme ideas with possible locations.",
                    deliverable="Bulleted list of themes and venues.",
                ),
                Subtask(
                    id="step-3",
                    description="Draft an agenda with rough timeline for the party.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=["step-2"],
                    success_criteria="Timeline covers arrival, main activities, food, and wrap-up.",
                    deliverable="Timeline with time blocks and activities.",
                ),
                Subtask(
                    id="step-4",
                    description="Refine logistics: food, decorations, and supplies checklist.",
                    tool=ToolName.MODIFY_DATA,
                    dependencies=["step-2"],
                    success_criteria="Checklist includes items for food, decor, and supplies.",
                    deliverable="Structured checklist of logistics items.",
                ),
                Subtask(
                    id="step-5",
                    description="Save final birthday party plan to storage.",
                    tool=ToolName.SAVE_OUTPUT,
                    dependencies=["step-3", "step-4"],
                    success_criteria="Plan summary is stored and can be retrieved.",
                    deliverable="Reference key or ID for the saved plan.",
                ),
            ]
        elif base == "research":
            subtasks = [
                Subtask(
                    id="step-1",
                    description="Clarify research question and scope.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=[],
                    success_criteria="Clear, single-sentence research question with scope.",
                    deliverable="Research question statement.",
                ),
                Subtask(
                    id="step-2",
                    description="Identify 3–5 key topics or sub-questions to investigate.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=["step-1"],
                    success_criteria="List of sub-questions covering main aspects of the topic.",
                    deliverable="Bulleted list of sub-questions.",
                ),
                Subtask(
                    id="step-3",
                    description="Search for relevant sources (simulated).",
                    tool=ToolName.SEARCH_IN_FILES,
                    dependencies=["step-2"],
                    success_criteria="At least a few mock sources or an explicit 'no sources found' note.",
                    deliverable="List of mock source references.",
                ),
                Subtask(
                    id="step-4",
                    description="Synthesize findings into a concise summary.",
                    tool=ToolName.MODIFY_DATA,
                    dependencies=["step-3"],
                    success_criteria="Summary references the research question and key findings.",
                    deliverable="1–3 paragraphs summary.",
                ),
                Subtask(
                    id="step-5",
                    description="Save final research summary to storage.",
                    tool=ToolName.SAVE_OUTPUT,
                    dependencies=["step-4"],
                    success_criteria="Summary is stored and can be retrieved.",
                    deliverable="Reference key or ID for the saved summary.",
                ),
            ]
        else:
            # Generic 5‑step plan applicable to arbitrary tasks
            subtasks = [
                Subtask(
                    id="step-1",
                    description=f"Understand the task requirements: '{task}'.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=[],
                    success_criteria="Key constraints and goals are listed.",
                    deliverable="Short paragraph summarizing requirements.",
                ),
                Subtask(
                    id="step-2",
                    description="Break the task into smaller actionable steps.",
                    tool=ToolName.GENERATE_TEXT,
                    dependencies=["step-1"],
                    success_criteria="List of 3–7 actionable steps.",
                    deliverable="Bulleted list of steps.",
                ),
                Subtask(
                    id="step-3",
                    description="Simulate searching for any existing relevant information.",
                    tool=ToolName.SEARCH_IN_FILES,
                    dependencies=["step-2"],
                    success_criteria="Either mock search results or a clear note that nothing was found.",
                    deliverable="Mock search results object.",
                ),
                Subtask(
                    id="step-4",
                    description="Transform steps and findings into a concrete plan.",
                    tool=ToolName.MODIFY_DATA,
                    dependencies=["step-2", "step-3"],
                    success_criteria="Plan includes sequence, responsibilities (if any), and expected outcome.",
                    deliverable="Structured plan description.",
                ),
                Subtask(
                    id="step-5",
                    description="Save the final plan to storage for later use.",
                    tool=ToolName.SAVE_OUTPUT,
                    dependencies=["step-4"],
                    success_criteria="Plan summary is stored and referenced by a key or ID.",
                    deliverable="Reference key or ID for the saved plan.",
                ),
            ]

        # Log a pseudo "JSON" version to mimic what we would send to / receive from an LLM.
        utils.logger().debug(
            "Planner fake LLM output",
            extra={"subtasks": [asdict(s) for s in subtasks]},
        )
        return subtasks


__all__ = ["Planner"]


