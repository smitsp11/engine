"""
Response schemas for Task Manager API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepInfo(BaseModel):
    """Information about a single execution step."""
    
    index: int = Field(..., description="Step number in the execution sequence")
    subtask_id: str = Field(..., description="ID of the subtask")
    action: str = Field(..., description="Description of the action taken")
    observation: Dict[str, Any] = Field(..., description="Output from the tool")
    status: str = Field(..., description="Status: succeeded, failed, etc.")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class RunResponse(BaseModel):
    """Response from running a complete task."""
    
    task_id: str = Field(..., description="Unique identifier for this task execution")
    status: str = Field(..., description="Final status: succeeded, failed, partial_success")
    result: str = Field(..., description="Human-readable summary of results")
    steps: List[StepInfo] = Field(..., description="List of execution steps with details")
    plan: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Original plan that was executed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about execution"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123",
                "status": "succeeded",
                "result": "Task: Plan a birthday party | Status: succeeded | Completed 5 steps",
                "steps": [
                    {
                        "index": 1,
                        "subtask_id": "step-1",
                        "action": "Execute: step-1",
                        "observation": {"text": "Generated party plan..."},
                        "status": "succeeded",
                        "error": None
                    }
                ],
                "plan": [],
                "metadata": {
                    "started_at": "2025-01-01T12:00:00Z",
                    "finished_at": "2025-01-01T12:05:00Z",
                    "model": "mock"
                }
            }
        }


class SubtaskInfo(BaseModel):
    """Information about a planned subtask."""
    
    id: str = Field(..., description="Subtask identifier")
    description: str = Field(..., description="Natural language description")
    tool: str = Field(..., description="Tool to use for this subtask")
    dependencies: List[str] = Field(default_factory=list, description="IDs of prerequisite subtasks")
    success_criteria: str = Field(..., description="How to verify success")
    deliverable: str = Field(..., description="Expected output")


class PlanResponse(BaseModel):
    """Response from generating a task plan."""
    
    plan_id: str = Field(..., description="Unique identifier for this plan")
    task: str = Field(..., description="Original task description")
    subtasks: List[Dict[str, Any]] = Field(..., description="List of planned subtasks")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional planning metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan-xyz",
                "task": "Research AI startups",
                "subtasks": [
                    {
                        "id": "step-1",
                        "description": "Clarify research question and scope",
                        "tool": "generate_text",
                        "dependencies": [],
                        "success_criteria": "Clear research question",
                        "deliverable": "Research question statement"
                    }
                ],
                "metadata": {
                    "model": "mock",
                    "timestamp": "2025-01-01T12:00:00Z"
                }
            }
        }


class ExecuteStepResponse(BaseModel):
    """Response from executing a single step."""
    
    step_id: str = Field(..., description="Unique identifier for this execution")
    subtask_id: str = Field(..., description="ID of the subtask that was executed")
    status: str = Field(..., description="Execution status")
    output: Dict[str, Any] = Field(..., description="Tool output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    trace: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="ReAct-style trace (thought, action, observation, critique)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_id": "exec-123",
                "subtask_id": "step-1",
                "status": "succeeded",
                "output": {"text": "Generated: Party themes..."},
                "error": None,
                "trace": [
                    {
                        "type": "thought",
                        "content": "Decide which tool to use...",
                        "timestamp": "2025-01-01T12:00:00Z"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    timestamp: str = Field(..., description="Current server time")
    version: str = Field(..., description="API version")
    active_tasks: int = Field(..., description="Number of currently active tasks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-01T12:00:00Z",
                "version": "0.1.0",
                "active_tasks": 3
            }
        }


class DebugStateResponse(BaseModel):
    """Debug state response with internal agent details."""
    
    task_id: str = Field(..., description="Task identifier")
    state: Dict[str, Any] = Field(..., description="Current task state")
    memory: Dict[str, Any] = Field(..., description="Agent memory snapshot")
    plan: List[Dict[str, Any]] = Field(default_factory=list, description="Task plan")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Subtask results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123",
                "state": {
                    "task_description": "Plan a party",
                    "status": "succeeded",
                    "started_at": "2025-01-01T12:00:00Z",
                    "finished_at": "2025-01-01T12:05:00Z"
                },
                "memory": {
                    "scratchpad": ["Note 1", "Note 2"],
                    "tool_outputs": {}
                },
                "plan": [],
                "results": []
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Task execution failed",
                "details": "Invalid tool name: unknown_tool",
                "status_code": 500,
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }

