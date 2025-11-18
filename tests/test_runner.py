"""
Test runner for Agent Engine evaluation framework.

Handles execution of tests against the running API.
"""

import json
import time
from typing import Dict, Any, Optional
import requests


class AgentTestRunner:
    """Runs tests against the Agent Engine API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the test runner.
        
        Parameters
        ----------
        base_url: str
            Base URL of the running API server
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> bool:
        """Check if the API server is running."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def run_test(self, test_json: Dict[str, Any], model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """
        Run a single test case.
        
        Parameters
        ----------
        test_json: Dict[str, Any]
            Test case definition
        model: str
            Model to use for execution
        
        Returns
        -------
        Dict[str, Any]
            Test execution result
        """
        task = test_json["task"]
        test_id = test_json.get("id", "unknown")
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/run",
                json={"task": task, "model": model},
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            result = response.json()
            
            execution_time = time.time() - start_time
            
            return {
                "test_id": test_id,
                "status": "success",
                "execution_time": execution_time,
                "result": result,
                "error": None,
            }
        except requests.exceptions.Timeout:
            return {
                "test_id": test_id,
                "status": "timeout",
                "execution_time": time.time() - start_time,
                "result": None,
                "error": "Request timed out after 5 minutes",
            }
        except requests.exceptions.RequestException as e:
            return {
                "test_id": test_id,
                "status": "error",
                "execution_time": time.time() - start_time,
                "result": None,
                "error": str(e),
            }

    def run_plan_only(self, test_json: Dict[str, Any], model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """
        Run planning phase only (no execution).
        
        Parameters
        ----------
        test_json: Dict[str, Any]
            Test case definition
        model: str
            Model to use for planning
        
        Returns
        -------
        Dict[str, Any]
            Planning result
        """
        task = test_json["task"]
        test_id = test_json.get("id", "unknown")
        
        try:
            response = self.session.post(
                f"{self.base_url}/plan",
                json={"task": task, "model": model},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "test_id": test_id,
                "error": str(e),
            }


__all__ = ["AgentTestRunner"]

