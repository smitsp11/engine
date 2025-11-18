"""
Utility helpers for logging, JSON handling, and timestamps.

These are intentionally lightweight so that the rest of the system can rely
on them without pulling in heavy external dependencies.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict


_LOGGER_NAME = "agent_engine"
_logger: logging.Logger | None = None


def logger() -> logging.Logger:
    """
    Get a module‑level logger configured with a simple, readable format.
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger(_LOGGER_NAME)
    if not _logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
    return _logger


def utc_now_iso() -> str:
    """Return current UTC time as an ISO‑8601 string."""
    return datetime.now(timezone.utc).isoformat()


def to_json(data: Any, *, indent: int = 2) -> str:
    """Serialise data to a JSON string."""
    return json.dumps(data, indent=indent, default=str)


def from_json(text: str) -> Any:
    """Parse a JSON string into Python data structures."""
    return json.loads(text)


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Small helper to access dict keys with a default."""
    return d.get(key, default)


__all__ = ["logger", "utc_now_iso", "to_json", "from_json", "safe_get"]


