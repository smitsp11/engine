"""
Real text generation tool using LLM.

This tool uses an LLM to generate text based on the provided prompt.
"""

from __future__ import annotations

from typing import Any, Dict

from ..llm import get_llm_client


def generate_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate text using an LLM based on the provided prompt.
    
    Parameters
    ----------
    payload: Dict[str, Any]
        Must contain:
        - "prompt": The text generation prompt (required)
        - Other fields are ignored but may be present for context
    
    Returns
    -------
    Dict[str, Any]
        Contains:
        - "text": The generated text
    """
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {"text": "No prompt provided."}
    
    try:
        # Get LLM client and generate text
        llm = get_llm_client()
        
        # Build system prompt from context if available
        system_prompt = None
        task = payload.get("task", "")
        if task:
            system_prompt = f"You are helping to complete this task: {task}. Generate high-quality, relevant text that contributes to accomplishing this goal."
        
        generated_text = llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )
        
        return {"text": generated_text}
    except Exception as e:
        # Fallback to simple response if LLM fails
        return {
            "text": f"Error generating text: {str(e)}. Original prompt: {prompt[:100]}",
        }


__all__ = ["generate_text"]


