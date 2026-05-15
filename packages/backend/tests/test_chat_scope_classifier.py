"""Chat relevance classifier helpers."""

from __future__ import annotations

import pytest

from app.chat.chat_scope import user_message_covers_workspace_scope as keyword_scope
from app.chat.scope_classifier import _parse_classifier_output, is_workspace_message_in_scope
from app.services.ai.gateway import LLMProvider, LLMResult


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("IN_SCOPE", True),
        ("OFF_TOPIC", False),
        ("IN_SCOPE.", True),
        ("The label is OFF_TOPIC here.", False),
        ("**IN_SCOPE**", True),
        ("", None),
        ("okay", None),
    ],
)
def test_parse_classifier_output(raw, expected):
    assert _parse_classifier_output(raw) == expected


def test_classifier_falls_back_to_keywords_on_ambiguous_llm_output(monkeypatch):
    monkeypatch.setattr(
        "app.chat.scope_classifier.complete_chat",
        lambda *_a, **_k: LLMResult(
            content="maybe",
            provider=LLMProvider.OPENAI,
            model="m",
            prompt_tokens=1,
            completion_tokens=1,
        ),
    )
    assert is_workspace_message_in_scope("請幫我整理會議摘要的重點") is keyword_scope(
        "請幫我整理會議摘要的重點"
    )


@pytest.mark.parametrize("content", ["OFF_TOPIC", "off_topic "])
def test_classifier_respects_negative_label(monkeypatch, content):
    monkeypatch.setattr(
        "app.chat.scope_classifier.complete_chat",
        lambda *_a, **_k: LLMResult(
            content=content,
            provider=LLMProvider.OPENAI,
            model="m",
            prompt_tokens=1,
            completion_tokens=1,
        ),
    )
    assert is_workspace_message_in_scope("Write a standalone haiku") is False
