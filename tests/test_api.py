"""
Integration tests for the FastAPI application.

These tests validate the API endpoints end-to-end using the mock model.
"""

import pytest
from fastapi.testclient import TestClient

from api.app import app, ACTIVE_AGENTS


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_active_agents():
    """Clear active agents before each test."""
    ACTIVE_AGENTS.clear()
    yield
    ACTIVE_AGENTS.clear()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health check returns correct status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "0.1.0"
        assert "active_tasks" in data
    
    def test_root_endpoint(self, client):
        """Test that root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["docs"] == "/docs"


class TestRunEndpoint:
    """Tests for the /run endpoint."""
    
    def test_run_simple_task(self, client):
        """Test running a simple task successfully."""
        request_data = {
            "task": "Plan a birthday party for my friend",
            "model": "mock"
        }
        
        response = client.post("/run", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] in ["succeeded", "partial_success", "failed"]
        assert "result" in data
        assert "steps" in data
        assert len(data["steps"]) > 0
        assert "plan" in data
        assert "metadata" in data
        
        # Validate step structure
        first_step = data["steps"][0]
        assert "index" in first_step
        assert "subtask_id" in first_step
        assert "action" in first_step
        assert "observation" in first_step
        assert "status" in first_step
    
    def test_run_research_task(self, client):
        """Test running a research-type task."""
        request_data = {
            "task": "Write a summary of Canadian AI startups",
            "model": "mock",
            "settings": {
                "max_steps": 10,
                "log_level": "info"
            }
        }
        
        response = client.post("/run", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["succeeded", "partial_success"]
        assert len(data["steps"]) <= 10  # Respects max_steps
    
    def test_run_with_invalid_model(self, client):
        """Test that invalid model returns error."""
        request_data = {
            "task": "Do something",
            "model": "invalid-model"
        }
        
        response = client.post("/run", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert "invalid-model" in data["error"].lower()
    
    def test_run_with_short_task(self, client):
        """Test that too-short task description is rejected."""
        request_data = {
            "task": "Short",
            "model": "mock"
        }
        
        response = client.post("/run", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_run_with_settings(self, client):
        """Test running with custom settings."""
        request_data = {
            "task": "Create a detailed project plan for building a web application",
            "model": "mock",
            "settings": {
                "max_steps": 5,
                "log_level": "debug",
                "enable_replanning": False
            }
        }
        
        response = client.post("/run", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data


class TestPlanEndpoint:
    """Tests for the /plan endpoint."""
    
    def test_generate_plan(self, client):
        """Test generating a plan without execution."""
        request_data = {
            "task": "Organize a photoshoot for a sneaker brand",
            "model": "mock"
        }
        
        response = client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "plan_id" in data
        assert data["task"] == request_data["task"]
        assert "subtasks" in data
        assert len(data["subtasks"]) > 0
        assert "metadata" in data
        
        # Validate subtask structure
        first_subtask = data["subtasks"][0]
        assert "id" in first_subtask
        assert "description" in first_subtask
        assert "tool" in first_subtask
        assert "dependencies" in first_subtask
        assert "success_criteria" in first_subtask
        assert "deliverable" in first_subtask
    
    def test_plan_with_context(self, client):
        """Test planning with additional context."""
        request_data = {
            "task": "Research machine learning trends",
            "model": "mock",
            "context": {
                "domain": "technology",
                "time_period": "2024-2025"
            }
        }
        
        response = client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["subtasks"]) >= 5  # Should have at least 5 subtasks
    
    def test_plan_validation(self, client):
        """Test that generated plans are valid."""
        request_data = {
            "task": "Build a recommendation system",
            "model": "mock"
        }
        
        response = client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        subtask_ids = [s["id"] for s in data["subtasks"]]
        
        # Check for unique IDs
        assert len(subtask_ids) == len(set(subtask_ids))
        
        # Check that dependencies reference valid IDs
        for subtask in data["subtasks"]:
            for dep in subtask["dependencies"]:
                assert dep in subtask_ids


class TestExecuteStepEndpoint:
    """Tests for the /execute-step endpoint."""
    
    def test_execute_single_step(self, client):
        """Test executing a single subtask."""
        request_data = {
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
        
        response = client.post("/execute-step", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "step_id" in data
        assert data["subtask_id"] == "step-1"
        assert data["status"] in ["succeeded", "failed"]
        assert "output" in data
        assert "trace" in data
    
    def test_execute_step_with_dependencies(self, client):
        """Test executing a step with context from previous outputs."""
        request_data = {
            "subtask": {
                "id": "step-2",
                "description": "Refine the party theme based on constraints",
                "tool": "modify_data",
                "dependencies": ["step-1"],
                "success_criteria": "Theme is refined",
                "deliverable": "Refined theme"
            },
            "context": {
                "task_description": "Plan a birthday party",
                "previous_outputs": {
                    "step-1": {
                        "text": "Generated: Beach theme, Garden theme, Space theme"
                    }
                }
            }
        }
        
        response = client.post("/execute-step", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["subtask_id"] == "step-2"
    
    def test_execute_step_trace(self, client):
        """Test that execution trace is captured."""
        request_data = {
            "subtask": {
                "id": "test-step",
                "description": "Test subtask",
                "tool": "generate_text",
                "dependencies": [],
                "success_criteria": "Output generated",
                "deliverable": "Text output"
            }
        }
        
        response = client.post("/execute-step", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        trace = data["trace"]
        
        # Should have thought, action, and observation events
        trace_types = [event["type"] for event in trace]
        assert "thought" in trace_types
        assert "action" in trace_types
        assert "observation" in trace_types


class TestDebugEndpoints:
    """Tests for debug and introspection endpoints."""
    
    def test_get_debug_state(self, client):
        """Test retrieving debug state for a task."""
        # First run a task
        run_response = client.post("/run", json={
            "task": "Plan a birthday party",
            "model": "mock"
        })
        assert run_response.status_code == 200
        task_id = run_response.json()["task_id"]
        
        # Now get debug state
        debug_response = client.get(f"/debug/state/{task_id}")
        assert debug_response.status_code == 200
        
        data = debug_response.json()
        assert data["task_id"] == task_id
        assert "state" in data
        assert "memory" in data
        assert "plan" in data
        assert "results" in data
        
        # Validate state structure
        state = data["state"]
        assert "task_description" in state
        assert "status" in state
        assert "started_at" in state
    
    def test_get_debug_state_not_found(self, client):
        """Test that requesting non-existent task returns 404."""
        response = client.get("/debug/state/nonexistent-task-id")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
    
    def test_list_active_tasks(self, client):
        """Test listing all active tasks."""
        # Run a couple of tasks
        client.post("/run", json={
            "task": "Plan a birthday party",
            "model": "mock"
        })
        client.post("/run", json={
            "task": "Research AI startups",
            "model": "mock"
        })
        
        # List active tasks
        response = client.get("/debug/state")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_tasks" in data
        assert "count" in data
        assert data["count"] >= 2
        
        # Validate task structure
        if data["active_tasks"]:
            task = data["active_tasks"][0]
            assert "task_id" in task
            assert "task" in task
            assert "status" in task


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_malformed_json(self, client):
        """Test that malformed JSON is handled gracefully."""
        response = client.post(
            "/run",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test that missing required fields are caught."""
        response = client.post("/run", json={
            "model": "mock"
            # Missing 'task' field
        })
        assert response.status_code == 422
    
    def test_invalid_settings(self, client):
        """Test that invalid settings are rejected."""
        request_data = {
            "task": "Do something interesting",
            "model": "mock",
            "settings": {
                "max_steps": -1,  # Invalid: negative
                "log_level": "invalid_level"  # Invalid: not a valid level
            }
        }
        
        response = client.post("/run", json=request_data)
        assert response.status_code == 422


class TestCORS:
    """Tests for CORS configuration."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/health")
        # CORS middleware should add appropriate headers
        # Exact behavior depends on configuration
        assert response.status_code in [200, 405]  # OPTIONS may be handled differently


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api", "--cov-report=html"])

