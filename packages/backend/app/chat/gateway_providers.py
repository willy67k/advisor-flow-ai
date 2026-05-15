"""Shared LLM provider selection for chat-related calls."""

from __future__ import annotations

from app.config.env import get_env
from app.services.ai.gateway import LLMGatewayError, LLMProvider


def resolve_primary_and_fallback_providers() -> tuple[LLMProvider, LLMProvider | None]:
    env = get_env()
    if env.openai_api_key:
        fb: LLMProvider | None = None
        if env.anthropic_api_key:
            fb = LLMProvider.ANTHROPIC
        elif env.google_api_key:
            fb = LLMProvider.GEMINI
        return LLMProvider.OPENAI, fb
    if env.anthropic_api_key:
        fb = LLMProvider.GEMINI if env.google_api_key else None
        return LLMProvider.ANTHROPIC, fb
    if env.google_api_key:
        return LLMProvider.GEMINI, None
    msg = "No LLM API key configured (OpenAI, Anthropic, or Google/Gemini)."
    raise LLMGatewayError(msg)
