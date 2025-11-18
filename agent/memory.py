"""
Short‑term memory and scratchpad for the agent.

The memory module tracks:
- current subtask ID
- per‑subtask tool outputs
- scratchpad / reflections
- a lightweight history of decisions
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from . import utils
from .schemas import SubtaskResult


@dataclass
class Memory:
    """Simple in‑memory scratchpad for a single agent run."""

    current_subtask_id: Optional[str] = None
    tool_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scratchpad: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def add_note(self, text: str) -> None:
        """Append a free‑form reflection to the scratchpad."""
        entry = f"[{utils.utc_now_iso()}] {text}"
        self.scratchpad.append(entry)

    def record_result(self, subtask_id: str, result: SubtaskResult) -> None:
        """Store tool output and a minimal history event for a subtask."""
        self.tool_outputs[subtask_id] = result.output
        self.history.append(
            {
                "timestamp": utils.utc_now_iso(),
                "subtask_id": subtask_id,
                "status": result.status.value,
                "error": result.error,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable view of the memory."""
        return {
            "current_subtask_id": self.current_subtask_id,
            "tool_outputs": self.tool_outputs,
            "scratchpad": list(self.scratchpad),
            "history": list(self.history),
        }


__all__ = ["Memory"]


