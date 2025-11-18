"""
Unit tests for the mock reasoning model.
"""

import pytest
from api.models.mock_model import MockReasoningModel, get_mock_model


class TestMockReasoningModel:
    """Tests for MockReasoningModel class."""
    
    def test_initialization(self):
        """Test that model initializes correctly."""
        model = MockReasoningModel(model_name="test-model")
        
        assert model.model_name == "test-model"
        assert model.call_count == 0
        assert len(model.call_history) == 0
    
    def test_generate_basic(self):
        """Test basic text generation."""
        model = MockReasoningModel()
        
        response = model.generate("Generate a plan for a party")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert model.call_count == 1
        assert len(model.call_history) == 1
    
    def test_generate_with_context(self):
        """Test generation with system prompt."""
        model = MockReasoningModel()
        
        response = model.generate(
            prompt="What are the steps?",
            system_prompt="You are a helpful assistant.",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert isinstance(response, str)
        assert model.call_history[0]["system_prompt"] == "You are a helpful assistant."
        assert model.call_history[0]["temperature"] == 0.5
    
    def test_generate_plan_response(self):
        """Test that planning prompts return structured plans."""
        model = MockReasoningModel()
        
        response = model.generate("Break down this task into a plan")
        
        assert "Step" in response
        assert "plan" in response.lower()
    
    def test_generate_clarification_response(self):
        """Test clarification prompts."""
        model = MockReasoningModel()
        
        response = model.generate("Clarify the constraints for this task")
        
        assert "Constraints" in response or "Requirements" in response
    
    def test_generate_brainstorm_response(self):
        """Test brainstorming prompts."""
        model = MockReasoningModel()
        
        response = model.generate("Brainstorm some creative themes")
        
        assert "Option" in response or "theme" in response.lower()
    
    def test_generate_json(self):
        """Test JSON generation with schema."""
        model = MockReasoningModel()
        
        schema = {
            "properties": {
                "subtasks": {
                    "type": "array"
                }
            }
        }
        
        response = model.generate_json(
            prompt="Generate a plan",
            schema=schema
        )
        
        assert isinstance(response, dict)
        assert "subtasks" in response
        assert isinstance(response["subtasks"], list)
        assert len(response["subtasks"]) > 0
        assert model.call_count == 1
    
    def test_check_completion_success(self):
        """Test completion checking with successful output."""
        model = MockReasoningModel()
        
        result = model.check_completion(
            task="Generate text",
            output={"text": "Generated: Hello world"},
            criteria="Output should contain text"
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "reasoning" in result
        assert result["success"] is True
    
    def test_check_completion_empty(self):
        """Test completion checking with empty output."""
        model = MockReasoningModel()
        
        result = model.check_completion(
            task="Generate text",
            output={},
            criteria="Output should contain text"
        )
        
        assert result["success"] is False
    
    def test_call_history_tracking(self):
        """Test that call history is tracked correctly."""
        model = MockReasoningModel()
        
        model.generate("First call")
        model.generate("Second call")
        model.generate_json("Third call", schema={})
        
        assert model.call_count == 3
        assert len(model.call_history) == 3
        assert model.call_history[0]["prompt"] == "First call"
        assert model.call_history[2]["response_type"] == "json"
    
    def test_reset_history(self):
        """Test resetting call history."""
        model = MockReasoningModel()
        
        model.generate("Test")
        model.generate("Test 2")
        assert model.call_count == 2
        
        model.reset_history()
        
        assert model.call_count == 0
        assert len(model.call_history) == 0
    
    def test_get_stats(self):
        """Test getting model statistics."""
        model = MockReasoningModel(model_name="stats-test")
        
        model.generate("Test 1")
        model.generate("Test 2")
        
        stats = model.get_stats()
        
        assert stats["model_name"] == "stats-test"
        assert stats["total_calls"] == 2
        assert stats["history_length"] == 2
    
    def test_convenience_function(self):
        """Test the get_mock_model convenience function."""
        model = get_mock_model("convenience-test")
        
        assert isinstance(model, MockReasoningModel)
        assert model.model_name == "convenience-test"
    
    def test_deterministic_responses(self):
        """Test that responses are deterministic."""
        model1 = MockReasoningModel()
        model2 = MockReasoningModel()
        
        prompt = "Generate a plan for organizing an event"
        
        response1 = model1.generate(prompt)
        response2 = model2.generate(prompt)
        
        # Same prompt should produce same response
        assert response1 == response2
    
    def test_response_types_coverage(self):
        """Test different response type triggers."""
        model = MockReasoningModel()
        
        # Plan response
        plan_resp = model.generate("break down the task into a plan")
        assert "Step" in plan_resp
        
        # Search response
        search_resp = model.generate("search for relevant information")
        assert "Search Results" in search_resp or "Document" in search_resp
        
        # Modification response
        modify_resp = model.generate("modify this data structure")
        assert "Modified" in modify_resp or "Modifications" in modify_resp
        
        # Generic response
        generic_resp = model.generate("do something unspecified")
        assert "Generated" in generic_resp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

