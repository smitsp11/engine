"""
LLM integration module for real language model interactions.

This module provides a unified interface for calling Google Gemini 2.5 Flash
for various agent operations including planning, text generation, and self-checking.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from . import utils

# Load environment variables from .env file if available
# Look for .env in the project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class LLMClient:
    """
    Client for interacting with Google Gemini 2.5 Flash.
    
    This provides methods for:
    - Text generation
    - JSON-structured generation (for planning)
    - Self-checking/evaluation
    """
    
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Initialize the LLM client.
        
        Parameters
        ----------
        model: str
            Model name to use (defaults to "gemini-2.5-flash")
        api_key: Optional[str]
            Google API key. If not provided, reads from GOOGLE_API_KEY env var.
        temperature: float
            Sampling temperature (0.0-2.0)
        max_tokens: int
            Maximum tokens to generate
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "Google Generative AI package not installed. Install with: pip install google-generativeai"
            )
        
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Gemini client
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key not provided. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        utils.logger().info("LLMClient initialized", extra={"model": model})
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text from a prompt.
        
        Parameters
        ----------
        prompt: str
            User prompt
        system_prompt: Optional[str]
            System instruction (combined with prompt for Gemini)
        temperature: Optional[float]
            Override default temperature
        max_tokens: Optional[float]
            Override default max_tokens
        
        Returns
        -------
        str
            Generated text
        """
        # Combine system prompt and user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        generation_config = {
            "temperature": temperature or self.temperature,
            "max_output_tokens": max_tokens or self.max_tokens,
        }
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            return response.text or ""
        except Exception as e:
            utils.logger().error("LLM generation failed", extra={"error": str(e)})
            raise
    
    def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response conforming to a schema.
        
        Parameters
        ----------
        prompt: str
            User prompt
        schema: Dict[str, Any]
            JSON schema to conform to
        system_prompt: Optional[str]
            System instruction
        
        Returns
        -------
        Dict[str, Any]
            Parsed JSON response
        """
        # Build a prompt that requests JSON output
        json_prompt = f"""{prompt}

Please respond with valid JSON that conforms to this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text or markdown formatting."""
        
        # Combine with system prompt if provided
        full_prompt = json_prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{json_prompt}"
        
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            content = response.text or "{}"
            
            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                return json.loads(content)
        except Exception as e:
            utils.logger().error("LLM JSON generation failed", extra={"error": str(e)})
            raise
    
    def check_completion(
        self,
        task: str,
        output: Dict[str, Any],
        criteria: str,
    ) -> Dict[str, Any]:
        """
        Check if a task output meets success criteria using LLM evaluation.
        
        Parameters
        ----------
        task: str
            Task description
        output: Dict[str, Any]
            Tool output to evaluate
        criteria: str
            Success criteria
        
        Returns
        -------
        Dict[str, Any]
            Evaluation result with 'success', 'reasoning', and 'confidence' fields
        """
        evaluation_prompt = f"""Evaluate whether the following task output meets the success criteria.

Task: {task}
Success Criteria: {criteria}

Output:
{json.dumps(output, indent=2)}

Please evaluate:
1. Does the output meet the success criteria? (yes/no)
2. Provide brief reasoning
3. Rate your confidence (0.0 to 1.0)

Respond in JSON format:
{{
    "success": true/false,
    "reasoning": "your reasoning here",
    "confidence": 0.0-1.0
}}"""
        
        system_prompt = "You are an expert evaluator. Analyze task outputs objectively and provide clear reasoning."
        
        generation_config = {
            "temperature": 0.3,  # Lower temperature for more consistent evaluation
            "max_output_tokens": 500,
        }
        
        try:
            full_prompt = f"{system_prompt}\n\n{evaluation_prompt}"
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            content = response.text or "{}"
            
            # Try to parse JSON from response
            try:
                # Extract JSON if wrapped in markdown
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                result = json.loads(content)
                return {
                    "success": bool(result.get("success", False)),
                    "reasoning": str(result.get("reasoning", "No reasoning provided")),
                    "confidence": float(result.get("confidence", 0.5)),
                }
            except (json.JSONDecodeError, KeyError, ValueError):
                # Fallback: simple heuristic if JSON parsing fails
                content_lower = content.lower()
                success = any(word in content_lower for word in ["yes", "meets", "success", "satisfies"])
                return {
                    "success": success,
                    "reasoning": content[:200],  # First 200 chars
                    "confidence": 0.6 if success else 0.4,
                }
        except Exception as e:
            utils.logger().error("LLM completion check failed", extra={"error": str(e)})
            # Fallback to simple heuristic
            has_content = bool(output) and any(
                bool(v) for v in output.values() if v is not None
            )
            return {
                "success": has_content,
                "reasoning": f"Evaluation failed: {str(e)}",
                "confidence": 0.5,
            }


def get_llm_client(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMClient:
    """
    Convenience function to get an LLM client instance.
    
    Parameters
    ----------
    model: Optional[str]
        Model name (defaults to gemini-2.5-flash)
    api_key: Optional[str]
        API key (defaults to GOOGLE_API_KEY env var)
    
    Returns
    -------
    LLMClient
        Initialized LLM client
    """
    return LLMClient(model=model or "gemini-2.5-flash", api_key=api_key)


__all__ = ["LLMClient", "get_llm_client", "GEMINI_AVAILABLE"]
