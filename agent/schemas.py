"""
Structured data models and lightweight validation helpers for the agent.

The project is intentionally dependency‑light, so we avoid heavy frameworks
like Pydantic and instead provide simple dataclasses plus validation
functions that operate on plain Python / JSON data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolName(str, Enum):
    GENERATE_TEXT = "generate_text"
    SEARCH_IN_FILES = "search_in_files"
    MODIFY_DATA = "modify_data"
    SAVE_OUTPUT = "save_output"


@dataclass
class Subtask:
    """
    A single planned step in the overall task.

    Attributes
    ----------
    id:
        Stable identifier for the subtask (e.g. "step-1").
    description:
        Natural language description of what this step should accomplish.
    tool:
        Name of the tool the executor *should* use for this step.
    dependencies:
        List of other subtask IDs that should be completed before this one.
    success_criteria:
        A short sentence describing how to know if this step succeeded.
    deliverable:
        Description of the expected output / artifact from this step.
    """

    id: str
    description: str
    tool: ToolName
    dependencies: List[str] = field(default_factory=list)
    success_criteria: str = ""
    deliverable: str = ""


@dataclass
class TaskPlan:
    """A full plan for a task consisting of multiple subtasks."""

    task: str
    subtasks: List[Subtask]


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class SubtaskResult:
    """Result of running a subtask via a tool."""

    subtask_id: str
    status: SubtaskStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def validate_task_plan(plan: TaskPlan) -> None:
    """
    Validate that a `TaskPlan` is structurally sound.

    Rules:
    - 5–15 subtasks
    - unique subtask IDs
    - dependencies refer only to known IDs (no forward‑ref requirement enforced)
    """
    num = len(plan.subtasks)
    if not (5 <= num <= 15):
        raise ValueError(f"TaskPlan must have between 5 and 15 subtasks, got {num}.")

    ids = [s.id for s in plan.subtasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Subtask IDs must be unique.")

    known_ids = set(ids)
    for s in plan.subtasks:
        unknown = [d for d in s.dependencies if d not in known_ids]
        if unknown:
            raise ValueError(
                f"Subtask {s.id!r} has unknown dependencies: {', '.join(unknown)}"
            )


