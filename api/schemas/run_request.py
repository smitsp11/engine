"""
Request schemas for Task Manager API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TaskSettings(BaseModel):
    """Optional settings for task execution."""
    
    max_steps: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum number of subtasks to execute"
    )
    log_level: str = Field(
        default="info",
        description="Logging level: debug, info, warning, error"
    )
    timeout_seconds: Optional[int] = Field(
        default=None,
        ge=1,
        description="Optional timeout for task execution"
    )
    enable_replanning: bool = Field(
        default=True,
        description="Whether to enable dynamic replanning on failures"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = {"debug", "info", "warning", "error"}
        if v.lower() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.lower()


class RunRequest(BaseModel):
    """Request to run a complete task through the agent."""
    
    task: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the task to accomplish",
        examples=["Plan a birthday party for my friend", "Research AI startups in Canada"]
    )
    model: str = Field(
        default="mock",
        description="Model to use for reasoning (currently only 'mock' is supported)",
        examples=["mock"]
    )
    settings: Optional[TaskSettings] = Field(
        default=None,
        description="Optional execution settings"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": "Write a summary of Canadian AI startups",
                "model": "mock",
                "settings": {
                    "max_steps": 10,
                    "log_level": "info"
                }
            }
        }


class PlanRequest(BaseModel):
    """Request to generate a plan without executing it."""
    
    task: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the task to plan"
    )
    model: str = Field(
        default="mock",
        description="Model to use for planning",
        examples=["mock"]
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional context for planning"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": "Organize a photoshoot for a sneaker brand",
                "model": "mock"
            }
        }


class ExecuteStepRequest(BaseModel):
    """Request to execute a single subtask manually."""
    
    subtask: Dict[str, Any] = Field(
        ...,
        description="Subtask definition including id, description, tool, etc."
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context including task description and previous outputs"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "subtask": {
                    "id": "step-1",
                    "description": "Generate a list of party themes",
                    "tool": "generate_text",
                    "dependencies": [],
                    "success_criteria": "At least 3 themes listed",
                    "deliverable": "List of party themes"
                },
                "context": {
                    "task_description": "Plan a birthday party",
                    "previous_outputs": {}
                }
            }
        }

