"""
Task simplification and specification builder.

This module turns a messy natural language request into a more structured
specification that can be consumed by the planner and executor.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from .intent_canonicalizer import IntentCanonicalizer, intents_to_dict


@dataclass
class SimplifiedTask:
    original_task: str
    normalized_task: str
    intents: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    missing_info: List[str]
    is_valid: bool
    notes: str


class TaskSimplifier:
    """Deterministic pre-planner that cleans and structures a raw task."""

    def __init__(self) -> None:
        self._canonicalizer = IntentCanonicalizer()

    def simplify(self, raw_task: str) -> Dict[str, Any]:
        text = (raw_task or "").strip()
        if not text:
            simplified = SimplifiedTask(
                original_task=raw_task,
                normalized_task="",
                intents=[],
                constraints={},
                missing_info=["task_description"],
                is_valid=False,
                notes="Empty task description.",
            )
            return asdict(simplified)

        intents = self._canonicalizer.canonicalize(text)
        intents_dicts = intents_to_dict(intents)

        # Simple constraint extraction: look for budget-like markers.
        constraints: Dict[str, Any] = {}
        if "$" in text or "budget" in text.lower():
            constraints["has_budget_reference"] = True

        # Normalised task is a concise combination of canonical intents.
        normalized = "; ".join(i.description for i in intents) if intents else text

        simplified = SimplifiedTask(
            original_task=text,
            normalized_task=normalized,
            intents=intents_dicts,
            constraints=constraints,
            missing_info=[],
            is_valid=True,
            notes="Heuristically simplified task.",
        )
        return asdict(simplified)


__all__ = ["SimplifiedTask", "TaskSimplifier"]


