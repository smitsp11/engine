"""
Registry of simple deterministic tools used by the agent.

Each tool:
    - accepts a JSON-like `dict` as input
    - returns a `dict` as output

These are intentionally minimal so the agent can be exercised safely and
predictably in tests and examples.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from .generate_text import generate_text
from .search_in_files import search_in_files
from .modify_data import modify_data
from .save_output import save_output, get_storage_snapshot
from ..schemas import ToolName


ToolFunc = Callable[[Dict[str, Any]], Dict[str, Any]]


TOOL_REGISTRY: Dict[ToolName, ToolFunc] = {
    ToolName.GENERATE_TEXT: generate_text,
    ToolName.SEARCH_IN_FILES: search_in_files,
    ToolName.MODIFY_DATA: modify_data,
    ToolName.SAVE_OUTPUT: save_output,
}


__all__ = [
    "ToolFunc",
    "TOOL_REGISTRY",
    "generate_text",
    "search_in_files",
    "modify_data",
    "save_output",
    "get_storage_snapshot",
]


