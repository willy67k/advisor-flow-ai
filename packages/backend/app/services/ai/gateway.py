"""Unified LLM gateway — checklist Step 3.1 (OpenAI / Anthropic / Gemini, retry, fallback, tokens)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

import tiktoken
from anthropic import APIConnectionError as AnthropicAPIConnectionError
from anthropic import RateLimitError as AnthropicRateLimitError
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from openai import APIConnectionError as OpenAIAPIConnectionError
from openai import APITimeoutError as OpenAIAPITimeoutError
from openai import InternalServerError as OpenAIInternalServerError
from openai import RateLimitError as OpenAIRateLimitError
from tenacity import (
    retry,
    retry_any,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.env import get_env

logger = logging.getLogger(__name__)


class LLMProvider(StrEnum):
    """Use vendor IDs (not model brands): ``openai``, ``anthropic``, ``gemini``."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


@dataclass(frozen=True)
class LLMResult:
    content: str
    provider: LLMProvider
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None


class LLMGatewayError(RuntimeError):
    """Raised when all retries (and optional fallback) fail to produce a response."""


_RETRY_OPENAI_ANTHROPIC = (
    OpenAIRateLimitError,
    OpenAIAPIConnectionError,
    OpenAIAPITimeoutError,
    OpenAIInternalServerError,
    AnthropicRateLimitError,
    AnthropicAPIConnectionError,
)


def _retryable_google(exc: BaseException) -> bool:
    """Retry Gemini 5xx and 429-style quota / rate limits."""
    from google.genai.errors import ClientError, ServerError

    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, ClientError):
        code = getattr(exc, "code", None)
        try:
            return int(code) == 429
        except (TypeError, ValueError):
            return False
    return False


def estimate_messages_tokens(
    messages: Sequence[ChatMessage], *, model_hint: str = "gpt-4o-mini"
) -> int:
    """Approximate input tokens with tiktoken (encoding falls back to ``cl100k_base``)."""
    try:
        encoding = tiktoken.encoding_for_model(model_hint)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    total = 0
    for msg in messages:
        total += 4 + len(encoding.encode(msg.content))
    return total


def _default_model(provider: LLMProvider) -> str:
    env = get_env()
    if provider == LLMProvider.OPENAI:
        return env.ai_openai_default_model
    if provider == LLMProvider.ANTHROPIC:
        return env.ai_anthropic_default_model
    return env.ai_gemini_default_model


def _require_api_key(provider: LLMProvider) -> str:
    env = get_env()
    if provider == LLMProvider.OPENAI:
        key = env.openai_api_key
        label = "OPENAI_API_KEY"
    elif provider == LLMProvider.ANTHROPIC:
        key = env.anthropic_api_key
        label = "ANTHROPIC_API_KEY"
    else:
        key = env.google_api_key
        label = "GOOGLE_API_KEY or GEMINI_API_KEY"
    if not key:
        msg = f"Missing {label} for provider '{provider.value}'."
        raise LLMGatewayError(msg)
    return key


def _to_lc_messages(messages: Sequence[ChatMessage]) -> list[BaseMessage]:
    out: list[BaseMessage] = []
    for m in messages:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content))
        else:
            out.append(AIMessage(content=m.content))
    return out


def _extract_text(ai_msg: AIMessage) -> str:
    raw = ai_msg.content
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts: list[str] = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(raw)


def _extract_usage(ai_msg: AIMessage) -> tuple[int | None, int | None]:
    meta = getattr(ai_msg, "response_metadata", None) or {}
    usage = meta.get("token_usage")
    if isinstance(usage, dict):
        prompt = usage.get("prompt_tokens") or usage.get("input_tokens")
        completion = usage.get("completion_tokens") or usage.get("output_tokens")
        return (
            int(prompt) if prompt is not None else None,
            int(completion) if completion is not None else None,
        )
    usage_meta = getattr(ai_msg, "usage_metadata", None)
    if isinstance(usage_meta, dict):
        prompt = usage_meta.get("input_tokens")
        completion = usage_meta.get("output_tokens")
        return (
            int(prompt) if prompt is not None else None,
            int(completion) if completion is not None else None,
        )
    return None, None


def _build_chat_model(
    provider: LLMProvider,
    *,
    model: str,
    temperature: float,
    api_key: str,
) -> BaseChatModel:
    if provider == LLMProvider.OPENAI:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )
    if provider == LLMProvider.ANTHROPIC:
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    retry=retry_any(
        retry_if_exception_type(_RETRY_OPENAI_ANTHROPIC),
        retry_if_exception(_retryable_google),
    ),
    reraise=True,
)
def _invoke(llm: BaseChatModel, lc_messages: list[BaseMessage]) -> BaseMessage:
    return llm.invoke(lc_messages)


def _complete_single_provider(
    messages: Sequence[ChatMessage],
    *,
    provider: LLMProvider,
    model: str,
    temperature: float,
) -> LLMResult:
    if not messages:
        msg = "messages must be non-empty."
        raise ValueError(msg)

    api_key = _require_api_key(provider)
    lc_messages = _to_lc_messages(messages)
    llm = _build_chat_model(provider, model=model, temperature=temperature, api_key=api_key)

    try:
        ai_msg = _invoke(llm, lc_messages)
    except Exception as exc:
        if isinstance(exc, _RETRY_OPENAI_ANTHROPIC) or _retryable_google(exc):
            logger.warning("LLM provider %s failed after retries: %s", provider.value, exc)
            raise LLMGatewayError(f"{provider.value} request failed after retries.") from exc
        logger.exception("LLM provider %s raised unexpected error", provider.value)
        raise LLMGatewayError(f"{provider.value} request failed.") from exc

    if not isinstance(ai_msg, AIMessage):
        msg = "Expected AIMessage from chat model."
        raise LLMGatewayError(msg)

    content = _extract_text(ai_msg)
    prompt_toks, completion_toks = _extract_usage(ai_msg)

    if prompt_toks is None:
        prompt_toks = estimate_messages_tokens(messages, model_hint=model)
    if completion_toks is None:
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        completion_toks = len(enc.encode(content))

    return LLMResult(
        content=content,
        provider=provider,
        model=model,
        prompt_tokens=prompt_toks,
        completion_tokens=completion_toks,
    )


def _parse_provider(raw: LLMProvider | str) -> LLMProvider:
    if isinstance(raw, LLMProvider):
        return raw
    return LLMProvider(str(raw).strip().lower())


def complete_chat(
    messages: Sequence[ChatMessage],
    *,
    provider: LLMProvider | str,
    model: str | None = None,
    temperature: float = 0.2,
    fallback_provider: LLMProvider | str | None = None,
) -> LLMResult:
    """Invoke an LLM with retries; optional ``fallback_provider`` if the primary still fails.

    Token counts prefer provider-reported usage; otherwise tiktoken estimates.
    """
    prov = _parse_provider(provider)
    chosen_model = model or _default_model(prov)

    try:
        return _complete_single_provider(
            messages,
            provider=prov,
            model=chosen_model,
            temperature=temperature,
        )
    except LLMGatewayError:
        if fallback_provider is None:
            raise
        fb = _parse_provider(fallback_provider)
        if fb == prov:
            raise
        fb_model = _default_model(fb)
        logger.warning("Falling back from %s to %s", prov.value, fb.value)
        return _complete_single_provider(
            messages,
            provider=fb,
            model=fb_model,
            temperature=temperature,
        )
