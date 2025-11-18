"""
Fake text generation tool.

Deterministic behaviour:
    input:  {"prompt": "...", ...}
    output: {"text": "Generated: <prompt>"}
"""

from __future__ import annotations

from typing import Any, Dict


def generate_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        prompt = "No prompt provided."
    return {"text": f"Generated: {prompt}"}


__all__ = ["generate_text"]


