"""Workspace chat streaming API."""

from __future__ import annotations

import pytest

from app.accounts.models import User
from app.services.ai.gateway import LLMProvider, LLMResult

pytestmark = pytest.mark.django_db


@pytest.fixture
def advisor_logged_in(api_client):
    user = User.objects.create_user(
        username="chat_adv",
        password="pw",
        role=User.Role.ADVISOR,
    )
    login = api_client.post(
        "/api/auth/login/",
        {"username": "chat_adv", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    return user


def test_chat_stream_requires_auth(api_client):
    res = api_client.post(
        "/api/chat/stream",
        {"message": "How do I upload a document?"},
        format="json",
    )
    assert res.status_code == 401


def test_chat_stream_off_topic_skips_llm(api_client, advisor_logged_in, monkeypatch):
    def classify_then_maybe_main(*_, **__) -> LLMResult:
        raise AssertionError("main complete_chat must not run for off-topic")

    monkeypatch.setattr(
        "app.chat.scope_classifier.complete_chat",
        lambda *_a, **_k: LLMResult(
            content="OFF_TOPIC",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            prompt_tokens=2,
            completion_tokens=2,
        ),
    )
    monkeypatch.setattr("app.chat.views.complete_chat", classify_then_maybe_main)

    res = api_client.post(
        "/api/chat/stream",
        {"message": "Write a Python quicksort implementation"},
        format="json",
    )
    assert res.status_code == 200
    body = b"".join(res.streaming_content).decode()
    assert "Advisor Flow" in body
    assert "節約" in body or "資源" in body


def test_chat_stream_sse_accept_header_not_406(api_client, advisor_logged_in, monkeypatch):
    """DRF negotiates Accept before the handler; SSE clients must not get NotAcceptable."""
    monkeypatch.setattr(
        "app.chat.views.is_workspace_message_in_scope",
        lambda _msg: False,
    )

    res = api_client.post(
        "/api/chat/stream",
        {"message": "tell me about cats"},
        format="json",
        HTTP_ACCEPT="text/event-stream",
    )
    assert res.status_code != 406


def test_chat_stream_on_topic_streams_llm(
    api_client,
    advisor_logged_in,
    monkeypatch,
):
    def fake_complete(messages, **_kwargs):
        sys0 = messages[0].content if messages else ""
        if isinstance(sys0, str) and "binary classifier" in sys0.lower():
            return LLMResult(
                content="IN_SCOPE",
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                prompt_tokens=2,
                completion_tokens=2,
            )
        return LLMResult(
            content="Discuss goals with your client before the portfolio review.",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr("app.chat.scope_classifier.complete_chat", fake_complete)
    monkeypatch.setattr("app.chat.views.complete_chat", fake_complete)

    res = api_client.post(
        "/api/chat/stream",
        {"message": "How do I prepare for a client portfolio review meeting?"},
        format="json",
    )
    assert res.status_code == 200
    body = b"".join(res.streaming_content).decode()
    assert "portfo" in body and "lio review" in body and '"type": "done"' in body


def test_chat_stream_allows_compliance_officer(api_client, monkeypatch):
    User.objects.create_user(
        username="chat_comp",
        password="pw",
        role=User.Role.COMPLIANCE_OFFICER,
    )
    login = api_client.post(
        "/api/auth/login/",
        {"username": "chat_comp", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    def fake_complete(messages, **_kwargs):
        sys0 = messages[0].content if messages else ""
        if isinstance(sys0, str) and "binary classifier" in sys0.lower():
            return LLMResult(
                content="IN_SCOPE",
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                prompt_tokens=2,
                completion_tokens=2,
            )
        return LLMResult(
            content="Use the Compliance reviews queue for high-risk summaries.",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr("app.chat.scope_classifier.complete_chat", fake_complete)
    monkeypatch.setattr("app.chat.views.complete_chat", fake_complete)

    res = api_client.post(
        "/api/chat/stream",
        {"message": "How does the compliance workflow interact with approvals?"},
        format="json",
    )
    assert res.status_code == 200
    body = b"".join(res.streaming_content).decode()
    assert "Compliance" in body or "compliance" in body.lower()
