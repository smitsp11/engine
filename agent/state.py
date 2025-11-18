"""
Global task state for the agent.

This module tracks the high‑level lifecycle of a task:
- when it started / finished
- the current status
- the active plan
- per‑subtask results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from . import utils
from .schemas import TaskPlan, Subtask, SubtaskResult, SubtaskStatus


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


@dataclass
class TaskState:
    """Mutable task state, intended for a single agent run."""

    task_description: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    plan: Optional[TaskPlan] = None
    subtask_results: List[SubtaskResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start_task(self, task_description: str) -> None:
        self.task_description = task_description
        self.status = TaskStatus.RUNNING
        self.started_at = utils.utc_now_iso()

    def set_plan(self, plan: TaskPlan) -> None:
        self.plan = plan

    def start_subtask(self, subtask: Subtask) -> None:
        # Could add per‑subtask timing here if desired.
        self.metadata.setdefault("started_subtasks", []).append(
            {"id": subtask.id, "timestamp": utils.utc_now_iso()}
        )

    def finish_subtask(self, subtask_id: str, result: SubtaskResult) -> None:
        self.subtask_results.append(result)

    def finish_task(self) -> None:
        """Determine final task status and close out the run."""
        self.finished_at = utils.utc_now_iso()
        if not self.subtask_results:
            self.status = TaskStatus.FAILED
            return

        any_failed = any(r.status == SubtaskStatus.FAILED for r in self.subtask_results)
        if any_failed:
            # If at least one succeeded we count this as partial success.
            any_succeeded = any(r.status == SubtaskStatus.SUCCEEDED for r in self.subtask_results)
            self.status = TaskStatus.PARTIAL_SUCCESS if any_succeeded else TaskStatus.FAILED
        else:
            self.status = TaskStatus.SUCCEEDED


__all__ = ["TaskState", "TaskStatus"]


