"""
Mock reasoning models for testing only.

This module provides a MockReasoningModel that simulates LLM behavior
for development and testing purposes. 

NOTE: The production system uses real LLM integration via agent_engine.agent.llm.
This mock model is kept only for backward compatibility in tests.
"""

from .mock_model import MockReasoningModel

__all__ = ["MockReasoningModel"]

