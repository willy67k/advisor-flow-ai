"""Versioned prompt templates (`.py` modules + registry)."""

from app.prompts.registry import PromptKey, PromptSpec, get_prompt_spec, prompt_template

__all__ = [
    "PromptKey",
    "PromptSpec",
    "get_prompt_spec",
    "prompt_template",
]
