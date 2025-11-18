"""
Mock reasoning model for testing and development ONLY.

This simulates LLM behavior with deterministic, predictable outputs,
allowing you to validate the entire agent loop without external API calls.

WARNING: This is for testing only. The production system uses real LLM
integration via agent_engine.agent.llm.LLMClient.
"""

from typing import Any, Dict, List, Optional
import json


class MockReasoningModel:
    """
    Mock LLM that returns predictable, deterministic responses.
    
    This is useful for:
    - Testing the agent loop end-to-end
    - Validating state transitions
    - Debugging without API costs
    - CI/CD pipelines
    
    Later, you can swap this with OpenAIReasoningModel or similar.
    """
    
    def __init__(self, model_name: str = "mock-gpt-4"):
        """
        Initialize the mock model.
        
        Args:
            model_name: Identifier for this mock model
        """
        self.model_name = model_name
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate a mock completion.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature (ignored in mock)
            max_tokens: Max tokens to generate (ignored in mock)
        
        Returns:
            Deterministic mock response based on prompt content
        """
        self.call_count += 1
        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        
        # Generate response based on prompt content
        prompt_lower = prompt.lower()
        
        if "plan" in prompt_lower or "break down" in prompt_lower:
            return self._generate_plan_response(prompt)
        elif "clarify" in prompt_lower or "constraints" in prompt_lower:
            return self._generate_clarification_response(prompt)
        elif "brainstorm" in prompt_lower or "themes" in prompt_lower:
            return self._generate_brainstorm_response(prompt)
        elif "search" in prompt_lower or "lookup" in prompt_lower:
            return self._generate_search_response(prompt)
        elif "modify" in prompt_lower or "transform" in prompt_lower:
            return self._generate_modification_response(prompt)
        else:
            return self._generate_generic_response(prompt)
    
    def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response conforming to a schema.
        
        Args:
            prompt: User prompt
            schema: JSON schema to conform to
            system_prompt: Optional system instruction
        
        Returns:
            Mock JSON response
        """
        self.call_count += 1
        self.call_history.append({
            "prompt": prompt,
            "schema": schema,
            "system_prompt": system_prompt,
            "response_type": "json",
        })
        
        # Return a mock plan structure
        if "subtask" in schema.get("properties", {}) or "subtasks" in str(schema):
            return {
                "subtasks": [
                    {
                        "id": "step-1",
                        "description": "Clarify requirements and constraints",
                        "tool": "generate_text",
                        "dependencies": [],
                        "success_criteria": "Requirements are clearly documented",
                        "deliverable": "Requirements document"
                    },
                    {
                        "id": "step-2",
                        "description": "Generate initial draft",
                        "tool": "generate_text",
                        "dependencies": ["step-1"],
                        "success_criteria": "Draft contains all key sections",
                        "deliverable": "Initial draft"
                    },
                    {
                        "id": "step-3",
                        "description": "Review and refine output",
                        "tool": "modify_data",
                        "dependencies": ["step-2"],
                        "success_criteria": "Output meets quality standards",
                        "deliverable": "Final refined output"
                    },
                    {
                        "id": "step-4",
                        "description": "Save final output",
                        "tool": "save_output",
                        "dependencies": ["step-3"],
                        "success_criteria": "Output is stored and retrievable",
                        "deliverable": "Storage confirmation"
                    },
                    {
                        "id": "step-5",
                        "description": "Generate summary report",
                        "tool": "generate_text",
                        "dependencies": ["step-4"],
                        "success_criteria": "Summary captures key points",
                        "deliverable": "Summary report"
                    }
                ]
            }
        
        return {"result": "Mock JSON response"}
    
    def check_completion(
        self,
        task: str,
        output: Dict[str, Any],
        criteria: str,
    ) -> Dict[str, Any]:
        """
        Mock self-check for task completion.
        
        Args:
            task: Task description
            output: Tool output to check
            criteria: Success criteria
        
        Returns:
            Mock evaluation result
        """
        self.call_count += 1
        self.call_history.append({
            "type": "check_completion",
            "task": task,
            "output": output,
            "criteria": criteria,
        })
        
        # Simple heuristic: if output has content, it's probably successful
        has_content = bool(output) and any(
            bool(v) for v in output.values() if v is not None
        )
        
        return {
            "success": has_content,
            "reasoning": "Output contains content" if has_content else "Output is empty",
            "confidence": 0.85 if has_content else 0.3,
        }
    
    def _generate_plan_response(self, prompt: str) -> str:
        """Generate a mock planning response."""
        return """Here's a structured plan to accomplish this task:

Step 1: Clarify requirements and constraints
- Understand the scope and goals
- Identify key constraints (time, budget, resources)

Step 2: Break down into subtasks
- Decompose the main task into manageable steps
- Identify dependencies between steps

Step 3: Execute each subtask
- Follow the plan sequentially
- Validate outputs at each step

Step 4: Review and refine
- Check that all requirements are met
- Make necessary adjustments

Step 5: Complete and document
- Finalize all deliverables
- Save results for future reference"""
    
    def _generate_clarification_response(self, prompt: str) -> str:
        """Generate a mock clarification response."""
        return """Generated: Requirements and Constraints

Key Requirements:
- Clear objective definition
- Realistic timeline expectations
- Available resources and tools
- Success metrics

Constraints:
- Time: Flexible but reasonable timeline
- Budget: Work within provided resources
- Quality: High-quality deliverables expected
- Scope: Well-defined boundaries"""
    
    def _generate_brainstorm_response(self, prompt: str) -> str:
        """Generate a mock brainstorming response."""
        return """Generated: Creative Ideas and Themes

Option 1: Classic and Elegant
- Formal setting with sophisticated decorations
- Traditional approach with proven success

Option 2: Modern and Innovative
- Contemporary design with cutting-edge elements
- Fresh perspective on the challenge

Option 3: Fun and Casual
- Relaxed atmosphere with playful elements
- Easy-going approach for maximum enjoyment

Each option has unique strengths depending on your specific needs and preferences."""
    
    def _generate_search_response(self, prompt: str) -> str:
        """Generate a mock search response."""
        return """Generated: Search Results

Found 3 relevant items:

1. Document A: Contains background information
   - Relevant to: initial research phase
   - Key insights: foundational concepts

2. Document B: Practical implementation guide
   - Relevant to: execution phase
   - Key insights: step-by-step procedures

3. Document C: Best practices and tips
   - Relevant to: optimization phase
   - Key insights: proven strategies"""
    
    def _generate_modification_response(self, prompt: str) -> str:
        """Generate a mock modification response."""
        return """Generated: Modified Data Summary

Modifications Applied:
- Refined structure for better clarity
- Enhanced content with additional details
- Optimized format for target audience
- Validated against requirements

Result: Data has been successfully transformed and improved."""
    
    def _generate_generic_response(self, prompt: str) -> str:
        """Generate a generic mock response."""
        return f"""Generated: Response to Task

Based on the prompt, here's a comprehensive response:

{prompt[:100]}...

The task has been analyzed and processed according to standard procedures.
Output generated successfully with high confidence.

Next steps would involve validation and refinement as needed."""
    
    def reset_history(self) -> None:
        """Clear call history and reset counter."""
        self.call_count = 0
        self.call_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this model."""
        return {
            "model_name": self.model_name,
            "total_calls": self.call_count,
            "history_length": len(self.call_history),
        }


# Convenience function for quick instantiation
def get_mock_model(model_name: str = "mock-gpt-4") -> MockReasoningModel:
    """
    Get a mock reasoning model instance.
    
    Args:
        model_name: Model identifier
    
    Returns:
        MockReasoningModel instance
    """
    return MockReasoningModel(model_name=model_name)

