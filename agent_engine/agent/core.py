"""
Core agent loop.

This module wires together:
- Planner → produces a structured plan of subtasks for a high‑level task.
- Executor → runs each subtask via tools and performs simple self‑checks.
- Memory & State → track progress, intermediate results, and reflections.

The initial implementation focuses on a *minimal* but complete loop:

    thought → action → observation → critique → next_thought

The loop is implemented in a way that makes it easy to plug in a real LLM,
more sophisticated planning, and more capable tools later.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .memory import Memory
from .planner import Planner
from .executor import Executor
from .schemas import TaskPlan, SubtaskResult, SubtaskStatus
from .state import TaskState, TaskStatus
from .task_simplifier import TaskSimplifier
from . import utils


class AgentCore:
    """
    The main agent "brainstem".

    High‑level flow for a single task:
      1. **Plan**   – Use `Planner` to break the task into subtasks.
      2. **Loop**   – For each subtask:
           a. Thought   – decide what to do next (here: follow the plan order).
           b. Action    – run the associated tool via `Executor`.
           c. Observation – capture results and update memory/state.
           d. Critique  – run a simple self‑check, maybe retry / mark failed.
      3. **Summarise** – Produce a final report from memory + state.
    """

    def __init__(self, planner: Optional[Planner] = None, executor: Optional[Executor] = None):
        self.planner = planner or Planner()
        self.memory = Memory()
        self.state = TaskState()
        # Executor depends on memory/state so we construct it after them.
        self.executor = executor or Executor(memory=self.memory, state=self.state)
        self.simplifier = TaskSimplifier()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_task(self, task_description: str) -> Dict[str, Any]:
        """
        Run a full multi‑step task using the simple thought→action→observation→critique loop.

        Parameters
        ----------
        task_description:
            High‑level natural language description of the task to accomplish.

        Returns
        -------
        dict
            A structured summary containing:
            - `task`: original task string
            - `status`: final TaskStatus value
            - `plan`: list of subtasks (as dicts)
            - `results`: list of subtask results (as dicts)
            - `memory`: final memory snapshot (as dict)
        """
        utils.logger().info("Starting agent task", extra={"task": task_description})

        # 1) TASK SIMPLIFICATION + PLAN
        self.state.start_task(task_description)

        simplified = self.simplifier.simplify(task_description)
        self.state.metadata["simplified_task"] = simplified

        planning_task = simplified.get("normalized_task") or task_description

        plan: TaskPlan = self.planner.create_plan(planning_task, context=simplified)
        self.state.set_plan(plan)
        self.memory.add_note(f"Plan created with {len(plan.subtasks)} subtasks.")

        # 2) EXECUTE SUBTASKS (WITH OPTIONAL DYNAMIC REPLANNING)
        i = 0
        replans_done = 0
        while i < len(plan.subtasks):
            subtask = plan.subtasks[i]
            utils.logger().info(
                "Starting subtask",
                extra={"subtask_id": subtask.id, "description": subtask.description},
            )
            self.state.start_subtask(subtask)
            self.memory.current_subtask_id = subtask.id

            # a) Thought: (here it's simply "execute the next planned subtask")
            self.memory.add_note(f"Planning to execute subtask: {subtask.description}")

            # b) Action + c) Observation + d) Critique are handled by Executor,
            # including basic self-check with a possible single retry.
            result: SubtaskResult = self.executor.execute_subtask(subtask)

            # If a subtask fails and we have not replanned yet, trigger a simple
            # dynamic replanning step to add recovery subtasks.
            if result.status == SubtaskStatus.FAILED and replans_done == 0:
                recovery_plan = self.planner.replan(self.state, self.memory)
                if recovery_plan is not None and recovery_plan.subtasks:
                    self.state.metadata.setdefault("replans", []).append(
                        {
                            "reason": result.error or "subtask_failed",
                            "recovery_subtasks": [s.id for s in recovery_plan.subtasks],
                        }
                    )
                    plan.subtasks.extend(recovery_plan.subtasks)
                    replans_done += 1

            i += 1

        # 3) FINAL SUMMARY
        self.state.finish_task()
        summary = self._summarise()
        utils.logger().info("Task completed", extra={"status": summary["status"]})
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _summarise(self) -> Dict[str, Any]:
        """Construct a lightweight, serialisable summary of the run."""
        results: List[Dict[str, Any]] = [
            asdict(r) for r in self.state.subtask_results
        ]

        return {
            "task": self.state.task_description,
            "status": self.state.status.value,
            "plan": [asdict(s) for s in self.state.plan.subtasks] if self.state.plan else [],
            "results": results,
            "memory": self.memory.to_dict(),
            "metadata": self.state.metadata,
        }


def run_agent(task_description: str) -> Dict[str, Any]:
    """
    Convenience function to run a one‑off task through the agent.

    Parameters
    ----------
    task_description:
        High‑level natural language description of the task to perform.
    """
    agent = AgentCore()
    return agent.run_task(task_description)


__all__ = ["AgentCore", "run_agent"]


