"""Streaming chat endpoint for the workspace copilot (SSE)."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.chat.chat_scope import OFF_TOPIC_NOTICE
from app.chat.gateway_providers import resolve_primary_and_fallback_providers
from app.chat.privacy import compose_chat_system_prompt
from app.chat.renderers import TextEventStreamRenderer
from app.chat.scope_classifier import is_workspace_message_in_scope
from app.services.ai.gateway import ChatMessage, LLMGatewayError, complete_chat

logger = logging.getLogger(__name__)

MAX_MESSAGE_CHARS = 12_000


def _sse(data: dict) -> bytes:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


def _chunk_text(text: str, *, size: int = 48) -> Iterator[str]:
    if not text:
        return
    yield from (text[i : i + size] for i in range(0, len(text), size))


class ChatStreamView(APIView):
    """JSONRenderer second so tools with ``Accept: application/json`` still work for errors."""

    renderer_classes = (TextEventStreamRenderer, JSONRenderer)
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request):
        payload = request.data if isinstance(request.data, dict) else {}
        raw = payload.get("message")
        if not isinstance(raw, str):
            return Response(
                {"message": ["A string `message` field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        text = raw.strip()
        if not text:
            return Response(
                {"message": ["Message must not be empty."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(text) > MAX_MESSAGE_CHARS:
            return Response(
                {"message": [f"Message exceeds {MAX_MESSAGE_CHARS} characters."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def events() -> Iterator[bytes]:
            if not is_workspace_message_in_scope(text):
                for piece in _chunk_text(OFF_TOPIC_NOTICE):
                    yield _sse({"type": "token", "content": piece})
                yield _sse({"type": "done"})
                return

            try:
                primary, fb = resolve_primary_and_fallback_providers()
            except LLMGatewayError as exc:
                yield _sse({"type": "error", "message": str(exc)})
                yield _sse({"type": "done"})
                return

            messages = (
                ChatMessage(role="system", content=compose_chat_system_prompt(request.user)),
                ChatMessage(role="user", content=text),
            )
            try:
                result = complete_chat(
                    messages,
                    provider=primary,
                    temperature=0.3,
                    fallback_provider=fb,
                )
            except LLMGatewayError as exc:
                logger.warning("chat stream LLM failure: %s", exc)
                yield _sse(
                    {
                        "type": "error",
                        "message": "The AI service is temporarily unavailable. Please try again shortly.",
                    }
                )
                yield _sse({"type": "done"})
                return

            for piece in _chunk_text(result.content):
                yield _sse({"type": "token", "content": piece})
            yield _sse({"type": "done"})

        resp = StreamingHttpResponse(events(), content_type="text/event-stream; charset=utf-8")
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"
        return resp
