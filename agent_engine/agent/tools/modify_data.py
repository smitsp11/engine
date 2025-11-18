"""
Fake data modification tool.

This tool performs a simple, deterministic transformation:
    - echoes the input under `original`
    - adds a `summary` describing what was "changed"
"""

from __future__ import annotations

from typing import Any, Dict


def modify_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Work on a shallow copy so we don't mutate caller data.
    data = dict(payload)
    # Remove non-data fields if present.
    data.pop("metadata", None)

    summary = f"Modified data with {len(data)} top-level keys."
    return {
        "original": data,
        "summary": summary,
    }


__all__ = ["modify_data"]


