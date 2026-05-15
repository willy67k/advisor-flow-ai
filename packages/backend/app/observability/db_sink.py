"""Best-effort persistence of observability events — Step 8.2."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def persist_observability_event(*, category: str, severity: str, payload: dict[str, Any]) -> None:
    """Insert one row when ``settings.OBSERVABILITY_LOG_TO_DB`` is true; never raises."""
    if not getattr(settings, "OBSERVABILITY_LOG_TO_DB", False):
        return
    try:
        from app.models.observability_log import ObservabilityLog

        ObservabilityLog.objects.create(category=category, severity=severity, payload=payload)
    except Exception:
        logger.exception("observability_db_persist_failed")


__all__ = ["persist_observability_event"]
