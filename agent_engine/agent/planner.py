"""
LLM-based (simulated) planner.

For now this uses a deterministic, rule-based "fake LLM" so that the system
is fully testable without external dependencies. The public interface is
designed so that you can later swap in a real LLM call with minimal changes.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .schemas import Subtask, TaskPlan, ToolName, validate_task_plan
from .state import TaskState
from .memory import Memory
from . import utils


class Planner:
    """
    Produce a structured multi-step plan for a natural language task.

    Public API:
        Planner.create_plan(task: str) -> TaskPlan

    The `plan` method is kept as a thin alias for backwards compatibility
    with earlier code in this project.
    """

    def create_plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        Create a TaskPlan for the given high-level task description.

        In a production system this would:
        - Prompt an LLM with the task and a JSON schema
        - Parse the JSON into Subtask objects
        - Validate with `validate_task_plan`

        Here we emulate that behaviour deterministically.
        """
        utils.logger().info("Planner: creating plan", extra={"task": task})

        candidates = self._generate_candidate_plans(task, context=context, n=3)
        plan = self._select_best_plan(candidates, context=context)

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

    # ------------------------------------------------------------------
    # Tree/Graph-of-Thought helpers
    # ------------------------------------------------------------------

    def _generate_candidate_plans(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        n: int = 3,
    ) -> List[TaskPlan]:
        """
        Generate N candidate TaskPlans for the given task.

        For now, this tweaks the base fake plan slightly to simulate branching.
        """
        base_subtasks = self._fake_llm_plan(task)
        candidates: List[TaskPlan] = []

        for i in range(1, n + 1):
            # Create a shallow copy of subtasks with small descriptive variations.
            variant: List[Subtask] = []
            for s in base_subtasks:
                suffix = "" if i == 1 else f" (variant {i})"
                variant.append(
                    Subtask(
                        id=s.id,
                        description=s.description + suffix,
                        tool=s.tool,
                        dependencies=list(s.dependencies),
                        success_criteria=s.success_criteria,
                        deliverable=s.deliverable,
                    )
                )
            candidates.append(TaskPlan(task=task, subtasks=variant))
        return candidates

    def _score_plan(
        self,
        plan: TaskPlan,
        context: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Deterministic scoring function for candidate plans.

        Heuristics:
        - prefer plans that include both SEARCH_IN_FILES and SAVE_OUTPUT
        - mildly prefer more subtasks (up to 10)
        """
        tools = {s.tool for s in plan.subtasks}
        score = 0
        if ToolName.SEARCH_IN_FILES in tools:
            score += 2
        if ToolName.SAVE_OUTPUT in tools:
            score += 2
        score += min(len(plan.subtasks), 10)
        return score

    def _select_best_plan(
        self,
        candidates: List[TaskPlan],
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskPlan:
        """Pick the highest-scoring candidate plan."""
        if not candidates:
            raise ValueError("No candidate plans generated.")
        scored = [(self._score_plan(p, context=context), p) for p in candidates]
        best_score, best_plan = max(scored, key=lambda x: x[0])
        utils.logger().debug("Planner selected best plan", extra={"score": best_score})
        return best_plan

    # ------------------------------------------------------------------
    # Dynamic replanning
    # ------------------------------------------------------------------

    def replan(self, state: TaskState, memory: Memory) -> Optional[TaskPlan]:
        """
        Produce a small recovery plan when the current trajectory is failing.

        This is a deterministic "fake" replan that can later be backed by an LLM.
        """
        if not state.task_description:
            return None

        task = f"Recovery for: {state.task_description}"
        subtasks: List[Subtask] = [
            Subtask(
                id="replan-1",
                description="Analyse previous failures and missing information.",
                tool=ToolName.GENERATE_TEXT,
                dependencies=[],
                success_criteria="Summarises what went wrong and what is missing.",
                deliverable="Short diagnostic note.",
            ),
            Subtask(
                id="replan-2",
                description="Save updated recommendations to storage.",
                tool=ToolName.SAVE_OUTPUT,
                dependencies=["replan-1"],
                success_criteria="Recommendations are stored and referenced by a key.",
                deliverable="Storage key for updated recommendations.",
            ),
        ]
        recovery_plan = TaskPlan(task=task, subtasks=subtasks)
        return recovery_plan


__all__ = ["Planner"]


