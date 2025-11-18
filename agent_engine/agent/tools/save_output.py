"""
Fake persistence tool.

This simulates saving output to a storage backend by keeping data in an
in-memory dictionary keyed by a deterministic string.
"""

from __future__ import annotations

from typing import Any, Dict


_STORAGE: Dict[str, Dict[str, Any]] = {}


def save_output(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save the payload under a deterministic key and return a reference.

    The key is derived from the `label` field if present, otherwise from a
    running counter.
    """
    label = str(payload.get("label") or "output").strip() or "output"
    # Ensure uniqueness by appending a counter if the label already exists.
    existing_indices = [
        int(k.split("#")[-1])
        for k in _STORAGE.keys()
        if k.startswith(label + "#")
        if k.split("#")[-1].isdigit()
    ]
    next_index = (max(existing_indices) + 1) if existing_indices else 1
    key = f"{label}#{next_index}"

    _STORAGE[key] = dict(payload)
    return {"key": key, "stored": True}


def get_storage_snapshot() -> Dict[str, Dict[str, Any]]:
    """Return a shallow copy of the in-memory storage for inspection/testing."""
    return dict(_STORAGE)


__all__ = ["save_output", "get_storage_snapshot"]


