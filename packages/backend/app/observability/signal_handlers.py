"""Global failure hooks — Step 8.2."""

from __future__ import annotations

import sys
import traceback

import structlog
from celery.signals import task_failure
from django.core.signals import got_request_exception
from django.dispatch import receiver

from app.models.observability_log import ObservabilityLog
from app.observability.db_sink import persist_observability_event


def _elog():
    return structlog.get_logger("advisorflow.errors")


@receiver(got_request_exception)
def log_uncaught_request_exception(sender, request, **kwargs) -> None:
    """Emit structured context when an exception propagates during request handling."""
    exc = sys.exc_info()[1]
    payload = {
        "event": "request.exception",
        "path": getattr(request, "path", ""),
        "method": getattr(request, "method", ""),
        "user_id": getattr(getattr(request, "user", None), "pk", None),
        "exc_type": type(exc).__name__ if exc else None,
        "exc": str(exc)[:2000] if exc else None,
    }
    _elog().warning(**payload)
    persist_observability_event(
        category=ObservabilityLog.Category.HTTP_EXCEPTION,
        severity=ObservabilityLog.Severity.WARNING,
        payload=payload,
    )


@task_failure.connect
def log_celery_task_failure(sender=None, task_id=None, exception=None, einfo=None, **kw) -> None:
    tail = _tb_tail(einfo)
    payload = {
        "event": "celery.task_failure",
        "task": str(getattr(sender, "name", sender)),
        "task_id": str(task_id) if task_id else None,
        "exc_type": type(exception).__name__ if exception else None,
        "exc": str(exception)[:2000] if exception else None,
        "traceback_tail": tail,
    }
    _elog().warning(**payload)
    persist_observability_event(
        category=ObservabilityLog.Category.CELERY_FAILURE,
        severity=ObservabilityLog.Severity.WARNING,
        payload=payload,
    )


def _tb_tail(tb_obj: object | None, *, limit: int = 12) -> str | None:
    if tb_obj is None:
        return None
    raw = getattr(tb_obj, "traceback", None)
    if isinstance(raw, str) and raw.strip():
        lines = raw.strip().splitlines()
    else:
        fmt = getattr(tb_obj, "format", None)
        if callable(fmt):
            try:
                lines = "".join(fmt()).strip().splitlines()
            except Exception:
                lines = traceback.format_exc().splitlines()
        else:
            lines = traceback.format_exc().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


__all__: list[str] = []
