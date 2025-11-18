"""
Evaluator for Agent Engine test results.

Validates planning, tool selection, execution, and output quality.
"""

import re
from typing import Dict, Any, List, Optional


class Evaluator:
    """Validates test results against expected criteria."""

    def validate_plan(self, plan: List[Dict[str, Any]], expected: Dict[str, Any]) -> List[str]:
        """
        Validate that a plan meets expected criteria.
        
        Parameters
        ----------
        plan: List[Dict[str, Any]]
            Generated plan (list of subtasks)
        expected: Dict[str, Any]
            Expected plan criteria
        
        Returns
        -------
        List[str]
            List of validation errors (empty if valid)
        """
        errors = []

        # Step count validation
        num_steps = len(plan)
        min_steps = expected.get("min_steps", 0)
        max_steps = expected.get("max_steps", 100)
        
        if not (min_steps <= num_steps <= max_steps):
            errors.append(
                f"Step count {num_steps} outside expected range [{min_steps}, {max_steps}]"
            )

        # Required tools validation
        tools_used = [step.get("tool", "") for step in plan]
        required_tools = expected.get("required_tools", [])
        
        for tool in required_tools:
            if tool not in tools_used:
                errors.append(f"Missing required tool: {tool}")

        # Disallowed tools validation
        disallowed_tools = expected.get("disallowed_tools", [])
        for tool in disallowed_tools:
            if tool in tools_used:
                errors.append(f"Used disallowed tool: {tool}")

        # Dependency validation
        step_ids = {step.get("id", "") for step in plan}
        for step in plan:
            deps = step.get("dependencies", [])
            for dep in deps:
                if dep not in step_ids:
                    errors.append(
                        f"Step {step.get('id')} references non-existent dependency: {dep}"
                    )

        # Check for circular dependencies (simple check)
        for step in plan:
            step_id = step.get("id", "")
            deps = step.get("dependencies", [])
            if step_id in deps:
                errors.append(f"Step {step_id} depends on itself (circular dependency)")

        return errors

    def validate_tool_selection(
        self, 
        plan: List[Dict[str, Any]], 
        expected: Dict[str, Any]
    ) -> List[str]:
        """
        Validate tool selection accuracy.
        
        Parameters
        ----------
        plan: List[Dict[str, Any]]
            Generated plan
        expected: Dict[str, Any]
            Expected tool selection criteria
        
        Returns
        -------
        List[str]
            List of validation errors
        """
        errors = []
        tools_used = [step.get("tool", "") for step in plan]

        # Required tools
        required_tools = expected.get("required_tools", [])
        for tool in required_tools:
            if tool not in tools_used:
                errors.append(f"Missing required tool: {tool}")

        # Disallowed tools
        disallowed_tools = expected.get("disallowed_tools", [])
        for tool in disallowed_tools:
            if tool in tools_used:
                errors.append(f"Used disallowed tool: {tool}")

        # Tool appropriateness (basic heuristic)
        task_lower = expected.get("task", "").lower()
        for step in plan:
            tool = step.get("tool", "")
            desc = step.get("description", "").lower()
            
            # Basic sanity checks
            if "search" in desc and tool != "search_in_files":
                # Not an error, just a warning - could be valid
                pass
            if "save" in desc and tool != "save_output":
                # Not an error, just a warning
                pass

        return errors

    def validate_execution(
        self, 
        execution_result: Dict[str, Any], 
        expected: Dict[str, Any]
    ) -> List[str]:
        """
        Validate execution correctness.
        
        Parameters
        ----------
        execution_result: Dict[str, Any]
            Execution result from API
        expected: Dict[str, Any]
            Expected execution criteria
        
        Returns
        -------
        List[str]
            List of validation errors
        """
        errors = []

        # Check execution status
        status = execution_result.get("status", "unknown")
        if status not in ["succeeded", "partial_success"]:
            errors.append(f"Execution status is {status}, expected success")

        # Check that all steps completed
        steps = execution_result.get("steps", [])
        failed_steps = [s for s in steps if s.get("status") == "failed"]
        if failed_steps:
            errors.append(f"{len(failed_steps)} step(s) failed during execution")

        # Check for required outputs
        required_outputs = expected.get("required_outputs", [])
        for output_key in required_outputs:
            found = False
            for step in steps:
                if output_key in str(step.get("observation", {})):
                    found = True
                    break
            if not found:
                errors.append(f"Required output '{output_key}' not found")

        return errors

    def score_output(
        self, 
        output: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Score output quality against criteria.
        
        Parameters
        ----------
        output: Dict[str, Any]
            Final output from execution
        criteria: Dict[str, Any]
            Scoring criteria
        
        Returns
        -------
        Dict[str, float]
            Scores for each criterion (0-5 scale)
        """
        scores = {}
        
        # Extract text content from output
        text_content = self._extract_text(output)
        text_lower = text_content.lower()

        # Relevance score (simple heuristic - can be enhanced with LLM)
        relevance_target = criteria.get("relevance", ">=3")
        relevance_score = self._heuristic_score(text_content, "relevance")
        scores["relevance"] = relevance_score

        # Correctness score
        correctness_target = criteria.get("correctness", ">=3")
        correctness_score = self._heuristic_score(text_content, "correctness")
        scores["correctness"] = correctness_score

        # Completeness score
        completeness_target = criteria.get("completeness", ">=3")
        completeness_score = self._heuristic_score(text_content, "completeness")
        scores["completeness"] = completeness_score

        # Check if scores meet targets
        for criterion, target in criteria.items():
            if isinstance(target, str) and ">=" in target:
                min_score = float(target.replace(">=", "").strip())
                actual_score = scores.get(criterion, 0)
                if actual_score < min_score:
                    scores[f"{criterion}_met"] = False
                else:
                    scores[f"{criterion}_met"] = True

        return scores

    def _extract_text(self, output: Dict[str, Any]) -> str:
        """Extract all text content from output."""
        text_parts = []
        
        # Extract from steps
        steps = output.get("steps", [])
        for step in steps:
            observation = step.get("observation", {})
            if isinstance(observation, dict):
                text = observation.get("text", "")
                if text:
                    text_parts.append(text)
            elif isinstance(observation, str):
                text_parts.append(observation)
        
        # Extract from result
        result = output.get("result", "")
        if result:
            text_parts.append(result)
        
        return " ".join(text_parts)

    def _heuristic_score(self, text: str, criterion: str) -> float:
        """
        Simple heuristic scoring (0-5 scale).
        
        This is a placeholder - can be enhanced with LLM-as-judge.
        """
        if not text:
            return 0.0
        
        score = 2.0  # Base score
        
        # Length heuristic
        if len(text) > 100:
            score += 0.5
        if len(text) > 500:
            score += 0.5
        
        # Structure heuristic
        if "\n" in text or "-" in text or "•" in text:
            score += 0.5  # Has some structure
        
        # Content heuristic (very basic)
        if len(text.split()) > 20:
            score += 0.5
        
        # Cap at 5.0
        return min(score, 5.0)


__all__ = ["Evaluator"]

