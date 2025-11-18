"""
Top-level package for the modular agent engine.

This package exposes a simple `run_agent` helper while keeping the
planner / executor / tools modular for future extension.
"""

from .agent.core import run_agent  # noqa: F401


