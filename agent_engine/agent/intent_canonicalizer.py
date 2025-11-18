"""
Intent canonicalization for messy, multi-intent user requests.

This module provides a deterministic, rule-based implementation that can later
be replaced with an LLM-driven classifier.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class CanonicalIntent:
    """Lightweight representation of a single intent extracted from a query."""

    id: str
    description: str
    index: int


class IntentCanonicalizer:
    """
    Split a raw user request into one or more canonical intents.

    Heuristics are intentionally simple and deterministic:
    - split on " and " when it appears to separate actions
    - otherwise treat the whole string as a single intent
    """

    def canonicalize(self, raw: str) -> List[CanonicalIntent]:
        text = (raw or "").strip()
        if not text:
            return []

        # Very lightweight multi-intent detection: split by " and ".
        parts = [p.strip() for p in text.split(" and ") if p.strip()]
        if len(parts) == 1:
            parts = [text]

        intents: List[CanonicalIntent] = []
        for idx, fragment in enumerate(parts, start=1):
            intents.append(
                CanonicalIntent(
                    id=f"intent-{idx}",
                    description=fragment,
                    index=idx,
                )
            )
        return intents


def intents_to_dict(intents: List[CanonicalIntent]) -> List[Dict[str, Any]]:
    """Serialise a list of CanonicalIntent objects into plain dicts."""
    return [asdict(i) for i in intents]


__all__ = ["CanonicalIntent", "IntentCanonicalizer", "intents_to_dict"]


