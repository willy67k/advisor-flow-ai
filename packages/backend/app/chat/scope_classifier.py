"""LLM-backed scope gate for workspace chat — small model binary classification."""

from __future__ import annotations

import logging
import re
from typing import Final

from app.chat.chat_scope import user_message_covers_workspace_scope
from app.chat.gateway_providers import resolve_primary_and_fallback_providers
from app.config.env import get_env
from app.services.ai.gateway import ChatMessage, LLMGatewayError, LLMProvider, complete_chat

logger = logging.getLogger(__name__)

_SCOPE_CLASSIFIER_SYSTEM: Final[str] = (
    "You are a strict binary classifier for Advisor Flow AI workspace support chat.\n"
    "Reply with exactly one token after optional whitespace: IN_SCOPE or OFF_TOPIC.\n\n"
    "IN_SCOPE: anything plausibly about this product or advisor operations — meetings, transcripts, summaries, "
    "clients/onboarding/KYC/portfolio/advisory contexts, uploads (PDF/doc), documents, embeddings/RAG/search in-app, "
    "workflows, approvals, audits, regulatory/compliance workflows, IPS, CRM in wealth context, how to use the app.\n\n"
    "OFF_TOPIC: general trivia, unrelated coding puzzles, hobbies, gossip, unrelated science/homework, medical/legal "
    "advice unrelated to compliance gates, unrelated math riddles, or small talk clearly not tied to advisory work "
    "(e.g. “write a poem”, “solve this LeetCode problem”). If it is ambiguous but could be framed as work, "
    "choose IN_SCOPE."
)

_SCOPE_TOKEN_RE = re.compile(r"\b(IN_SCOPE|OFF_TOPIC)\b", re.IGNORECASE)
_MAX_CHARS_FOR_CLASSIFIER = 6_000


def _resolution_model(primary: LLMProvider) -> str:
    env = get_env()
    manual = env.ai_chat_scope_model.strip()
    if manual:
        return manual
    if primary == LLMProvider.OPENAI:
        return "gpt-4o-mini"
    if primary == LLMProvider.ANTHROPIC:
        return env.ai_anthropic_default_model
    return env.ai_gemini_default_model


def _parse_classifier_output(raw: str) -> bool | None:
    if not isinstance(raw, str):
        return None
    m = _SCOPE_TOKEN_RE.search(raw)
    if not m:
        return None
    token = m.group(1).upper()
    if token == "IN_SCOPE":
        return True
    if token == "OFF_TOPIC":
        return False
    return None


def is_workspace_message_in_scope(payload: str) -> bool:
    """
    Prefer a cheap LLM classify; fallback to deterministic keywords on failure or missing keys.

    Returns True iff the assistant should proceed to full chat completion.
    """
    if not isinstance(payload, str):
        return False
    trimmed = payload.strip()
    condensed = "".join(trimmed.split())
    if len(condensed) < 4:
        return False

    try:
        primary, fb = resolve_primary_and_fallback_providers()
    except LLMGatewayError:
        return user_message_covers_workspace_scope(trimmed)

    clipped = trimmed[:_MAX_CHARS_FOR_CLASSIFIER]

    msgs = (
        ChatMessage(role="system", content=_SCOPE_CLASSIFIER_SYSTEM),
        ChatMessage(role="user", content=clipped),
    )

    model = _resolution_model(primary)
    try:
        result = complete_chat(
            msgs,
            provider=primary,
            model=model,
            temperature=0.0,
            fallback_provider=fb,
        )
        parsed = _parse_classifier_output(result.content)
        if parsed is None:
            logger.debug(
                "chat scope classifier ambiguous output=%r — using keyword fallback",
                result.content[:200],
            )
            return user_message_covers_workspace_scope(trimmed)
        return parsed
    except LLMGatewayError as exc:
        logger.warning("chat scope classifier failed: %s — keyword fallback", exc)
        return user_message_covers_workspace_scope(trimmed)
