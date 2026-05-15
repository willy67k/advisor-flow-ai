"""Structured AI / latency logs — Step 8.2."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config.env import get_env
from app.observability.db_sink import persist_observability_event

_structlog_configured = False


def configure_structlog() -> None:
    """JSON stderr logging for ``structlog`` (safe default for Django + Celery)."""
    global _structlog_configured
    if _structlog_configured:
        return
    _structlog_configured = True
    env = get_env()
    level = getattr(logging, str(env.log_level).upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def log_ai_completion(
    *,
    prompt_key: str | None,
    prompt_version: str | None,
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    latency_ms: float,
    outcome: str,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": "ai.completion",
        "prompt_key": prompt_key,
        "prompt_version": prompt_version,
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": round(latency_ms, 3),
        "outcome": outcome,
    }
    if error:
        payload["error"] = error[:2000]
    if extra:
        payload.update(extra)
    log = structlog.get_logger("advisorflow.ai")
    if outcome == "error":
        log.warning(**payload)
    else:
        log.info(**payload)

    from app.models.observability_log import ObservabilityLog

    persist_observability_event(
        category=ObservabilityLog.Category.AI_COMPLETION,
        severity=ObservabilityLog.Severity.WARNING
        if outcome == "error"
        else ObservabilityLog.Severity.INFO,
        payload=payload,
    )


__all__ = ["configure_structlog", "log_ai_completion"]
