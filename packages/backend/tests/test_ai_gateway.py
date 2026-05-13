"""AI gateway (Step 3.1) — mocked HTTP / LangChain boundaries."""

from unittest.mock import patch

import httpx
import pytest
from langchain_core.messages import AIMessage
from openai import RateLimitError as OpenAIRateLimitError

from app.services.ai.gateway import (
    ChatMessage,
    LLMGatewayError,
    LLMProvider,
    LLMResult,
    complete_chat,
    estimate_messages_tokens,
)


def test_estimate_messages_tokens_counts_prompt():
    msgs = [
        ChatMessage(role="system", content="You are helpful."),
        ChatMessage(role="user", content="Hello world."),
    ]
    n = estimate_messages_tokens(msgs, model_hint="gpt-4o-mini")
    assert n > 10


@pytest.mark.django_db
def test_complete_chat_gemini_uses_invoke_response(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
    from app.config import env as env_mod

    env_mod.get_env.cache_clear()

    ai_msg = AIMessage(
        content="Gemini says hi.",
        response_metadata={"token_usage": {"prompt_tokens": 4, "completion_tokens": 2}},
    )

    with patch("app.services.ai.gateway._invoke", return_value=ai_msg):
        string_provider = complete_chat(
            [ChatMessage(role="user", content="hello")],
            provider="gemini",
            model="gemini-2.0-flash",
        )
        enum_provider = complete_chat(
            [ChatMessage(role="user", content="hello")],
            provider=LLMProvider.GEMINI,
            model="gemini-2.0-flash",
        )

    assert string_provider.provider == LLMProvider.GEMINI
    assert enum_provider.provider == LLMProvider.GEMINI
    assert string_provider.content == "Gemini says hi."
    assert string_provider.prompt_tokens == 4
    assert string_provider.completion_tokens == 2

    env_mod.get_env.cache_clear()


@pytest.mark.django_db  # Django configures settings when pytest-django loads tests that touch app.*
def test_complete_chat_openai_uses_invoke_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    # Reload cached env so gateway picks up key
    from app.config import env as env_mod

    env_mod.get_env.cache_clear()

    ai_msg = AIMessage(
        content="Summary: ok.",
        response_metadata={"token_usage": {"prompt_tokens": 12, "completion_tokens": 3}},
    )

    with patch("app.services.ai.gateway._invoke", return_value=ai_msg):
        out = complete_chat(
            [ChatMessage(role="user", content="notes")],
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
        )

    assert isinstance(out, LLMResult)
    assert out.content == "Summary: ok."
    assert out.provider == LLMProvider.OPENAI
    assert out.prompt_tokens == 12
    assert out.completion_tokens == 3

    env_mod.get_env.cache_clear()


@pytest.mark.django_db
def test_complete_chat_fallback_when_primary_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    from app.config import env as env_mod

    env_mod.get_env.cache_clear()

    ok = LLMResult(
        content="from anthropic",
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-5-haiku-20241022",
        prompt_tokens=5,
        completion_tokens=2,
    )

    with patch(
        "app.services.ai.gateway._complete_single_provider",
        side_effect=[LLMGatewayError("primary down"), ok],
    ) as mocked:
        out = complete_chat(
            [ChatMessage(role="user", content="hello")],
            provider=LLMProvider.OPENAI,
            fallback_provider=LLMProvider.ANTHROPIC,
        )

    assert out.content == "from anthropic"
    assert mocked.call_count == 2

    env_mod.get_env.cache_clear()


@pytest.mark.django_db
def test_invoke_retries_then_raises_llm_gateway_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from app.config import env as env_mod

    env_mod.get_env.cache_clear()

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(429, request=req)
    rate_exc = OpenAIRateLimitError("rate limited", response=resp, body=None)

    with patch("app.services.ai.gateway._invoke", side_effect=rate_exc):
        with pytest.raises(LLMGatewayError):
            complete_chat(
                [ChatMessage(role="user", content="x")],
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
            )

    env_mod.get_env.cache_clear()
