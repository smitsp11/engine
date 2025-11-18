"""
Main FastAPI application for the Task Manager Agent Engine.

This provides a RESTful API to run tasks, generate plans, and debug
the agent's internal state.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from agent_engine.agent.core import AgentCore
from agent_engine.agent.planner import Planner
from agent_engine.agent.executor import Executor
from agent_engine.agent.memory import Memory
from agent_engine.agent.state import TaskState

from .schemas.run_request import RunRequest, PlanRequest, ExecuteStepRequest
from .schemas.run_response import (
    RunResponse,
    PlanResponse,
    ExecuteStepResponse,
    HealthResponse,
    DebugStateResponse,
    ErrorResponse,
)
from .models.mock_model import MockReasoningModel

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


# Global state store for active agents (in-memory for now)
ACTIVE_AGENTS: Dict[str, AgentCore] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    logger.info("startup", message="Task Manager API starting up")
    yield
    logger.info("shutdown", message="Task Manager API shutting down")
    ACTIVE_AGENTS.clear()


# Initialize FastAPI app
app = FastAPI(
    title="Task Manager Agent Engine API",
    description="A reasoning improvement engine for LLMs that turns messy tasks into structured, executable plans.",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    logger.error(
        "http_error",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail or "An error occurred",
            status_code=exc.status_code,
            timestamp=datetime.utcnow().isoformat(),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception("unexpected_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc),
            status_code=500,
            timestamp=datetime.utcnow().isoformat(),
        ).model_dump(),
    )


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns basic system information and status.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
        active_tasks=len(ACTIVE_AGENTS),
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Task Manager Agent Engine API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Core Agent Endpoints
# ============================================================================


@app.post("/run", response_model=RunResponse, tags=["Agent"], status_code=status.HTTP_200_OK)
async def run_task(request: RunRequest):
    """
    Execute a complete task through the agent engine.
    
    This endpoint:
    1. Creates a new agent instance
    2. Plans the task into subtasks
    3. Executes each subtask
    4. Returns the complete results with all steps
    
    **Parameters:**
    - `task`: Natural language description of the task
    - `model`: Model to use (currently only "mock" is supported)
    - `settings`: Optional execution settings (max_steps, log_level, etc.)
    
    **Returns:**
    - Complete execution results including task_id, status, steps, and final output
    """
    task_id = str(uuid.uuid4())
    
    logger.info(
        "run_task_start",
        task_id=task_id,
        task=request.task,
        model=request.model,
        settings=request.settings.model_dump() if request.settings else {},
    )
    
    try:
        # Create agent with appropriate model
        if request.model == "mock":
            planner = Planner()
            agent = AgentCore(planner=planner)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported model: {request.model}. Currently only 'mock' is supported.",
            )
        
        # Store agent for potential debugging
        ACTIVE_AGENTS[task_id] = agent
        
        # Run the task
        result = agent.run_task(request.task)
        
        logger.info(
            "run_task_complete",
            task_id=task_id,
            status=result["status"],
            num_steps=len(result["results"]),
        )
        
        # Transform internal result to API response format
        steps = []
        for idx, subtask_result in enumerate(result["results"], 1):
            steps.append({
                "index": idx,
                "subtask_id": subtask_result["subtask_id"],
                "action": f"Execute: {subtask_result['subtask_id']}",
                "observation": subtask_result.get("output", {}),
                "status": subtask_result["status"],
                "error": subtask_result.get("error"),
            })
        
        response = RunResponse(
            task_id=task_id,
            status=result["status"],
            result=_generate_final_summary(result),
            steps=steps,
            plan=result.get("plan", []),
            metadata={
                "started_at": agent.state.started_at,
                "finished_at": agent.state.finished_at,
                "model": request.model,
            },
        )
        
        # Clean up agent from active store (keep for 5 minutes in production)
        # For now we keep it for debugging via /debug/state
        
        return response
        
    except Exception as exc:
        logger.exception("run_task_error", task_id=task_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(exc)}",
        )


@app.post("/plan", response_model=PlanResponse, tags=["Agent"])
async def plan_task(request: PlanRequest):
    """
    Generate a plan for a task without executing it.
    
    This endpoint only runs the planning phase, returning a structured
    breakdown of subtasks that would be executed.
    
    **Parameters:**
    - `task`: Natural language description of the task
    - `model`: Model to use for planning (currently only "mock")
    
    **Returns:**
    - Task plan with subtasks, dependencies, and success criteria
    """
    plan_id = str(uuid.uuid4())
    
    logger.info("plan_task_start", plan_id=plan_id, task=request.task, model=request.model)
    
    try:
        # Create planner
        planner = Planner()
        
        # Generate plan
        plan = planner.create_plan(request.task)
        
        logger.info("plan_task_complete", plan_id=plan_id, num_subtasks=len(plan.subtasks))
        
        return PlanResponse(
            plan_id=plan_id,
            task=request.task,
            subtasks=[
                {
                    "id": subtask.id,
                    "description": subtask.description,
                    "tool": subtask.tool.value,
                    "dependencies": subtask.dependencies,
                    "success_criteria": subtask.success_criteria,
                    "deliverable": subtask.deliverable,
                }
                for subtask in plan.subtasks
            ],
            metadata={"model": request.model, "timestamp": datetime.utcnow().isoformat()},
        )
        
    except Exception as exc:
        logger.exception("plan_task_error", plan_id=plan_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Planning failed: {str(exc)}",
        )


@app.post("/execute-step", response_model=ExecuteStepResponse, tags=["Agent"])
async def execute_step(request: ExecuteStepRequest):
    """
    Execute a single subtask manually.
    
    This is useful for step-by-step execution or debugging individual
    subtasks without running the full task.
    
    **Parameters:**
    - `subtask`: Subtask definition including id, description, tool, etc.
    - `context`: Optional context including task description and previous results
    
    **Returns:**
    - Execution result for the single subtask
    """
    step_id = str(uuid.uuid4())
    
    logger.info(
        "execute_step_start",
        step_id=step_id,
        subtask_id=request.subtask.get("id"),
        tool=request.subtask.get("tool"),
    )
    
    try:
        # Import Subtask schema
        from agent_engine.agent.schemas import Subtask, ToolName
        
        # Create minimal state and memory for execution
        state = TaskState()
        memory = Memory()
        
        if request.context:
            state.task_description = request.context.get("task_description", "Manual step execution")
            # Populate memory with previous outputs if provided
            if "previous_outputs" in request.context:
                memory.tool_outputs = request.context["previous_outputs"]
        else:
            state.task_description = "Manual step execution"
        
        # Create executor
        executor = Executor(memory=memory, state=state)
        
        # Parse subtask
        subtask = Subtask(
            id=request.subtask["id"],
            description=request.subtask["description"],
            tool=ToolName(request.subtask["tool"]),
            dependencies=request.subtask.get("dependencies", []),
            success_criteria=request.subtask.get("success_criteria", ""),
            deliverable=request.subtask.get("deliverable", ""),
        )
        
        # Execute
        result = executor.execute_subtask(subtask)
        
        logger.info(
            "execute_step_complete",
            step_id=step_id,
            subtask_id=subtask.id,
            status=result.status.value,
        )
        
        return ExecuteStepResponse(
            step_id=step_id,
            subtask_id=result.subtask_id,
            status=result.status.value,
            output=result.output,
            error=result.error,
            trace=memory.traces.get(subtask.id, []),
        )
        
    except Exception as exc:
        logger.exception("execute_step_error", step_id=step_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Step execution failed: {str(exc)}",
        )


# ============================================================================
# Debug & Introspection Endpoints
# ============================================================================


@app.get("/debug/state/{task_id}", response_model=DebugStateResponse, tags=["Debug"])
async def get_debug_state(task_id: str):
    """
    Get the internal state of a running or completed task.
    
    This is useful for debugging and understanding what the agent
    is doing at each step.
    
    **Parameters:**
    - `task_id`: The task ID returned from /run
    
    **Returns:**
    - Complete internal state including memory, traces, and metadata
    """
    if task_id not in ACTIVE_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found. It may have expired or never existed.",
        )
    
    agent = ACTIVE_AGENTS[task_id]
    
    return DebugStateResponse(
        task_id=task_id,
        state={
            "task_description": agent.state.task_description,
            "status": agent.state.status.value,
            "started_at": agent.state.started_at,
            "finished_at": agent.state.finished_at,
            "metadata": agent.state.metadata,
        },
        memory=agent.memory.to_dict(),
        plan=[
            {
                "id": s.id,
                "description": s.description,
                "tool": s.tool.value,
                "dependencies": s.dependencies,
            }
            for s in (agent.state.plan.subtasks if agent.state.plan else [])
        ],
        results=[
            {
                "subtask_id": r.subtask_id,
                "status": r.status.value,
                "output": r.output,
                "error": r.error,
            }
            for r in agent.state.subtask_results
        ],
    )


@app.get("/debug/state", tags=["Debug"])
async def list_active_tasks():
    """
    List all active task IDs currently in memory.
    
    **Returns:**
    - List of active task IDs with basic info
    """
    tasks = []
    for task_id, agent in ACTIVE_AGENTS.items():
        tasks.append({
            "task_id": task_id,
            "task": agent.state.task_description,
            "status": agent.state.status.value,
            "started_at": agent.state.started_at,
        })
    
    return {"active_tasks": tasks, "count": len(tasks)}


# ============================================================================
# Helper Functions
# ============================================================================


def _generate_final_summary(result: Dict[str, Any]) -> str:
    """Generate a human-readable summary from the task result."""
    task = result.get("task", "Unknown task")
    status = result.get("status", "unknown")
    num_steps = len(result.get("results", []))
    
    summary_parts = [f"Task: {task}", f"Status: {status}", f"Completed {num_steps} steps"]
    
    # Add key outputs
    if result.get("results"):
        last_result = result["results"][-1]
        if last_result.get("output"):
            summary_parts.append(f"Final output available with keys: {list(last_result['output'].keys())}")
    
    return " | ".join(summary_parts)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

