"""Observability DB sink — Step 8.2."""

import pytest
from django.test.utils import override_settings

from app.models.observability_log import ObservabilityLog
from app.observability.db_sink import persist_observability_event


@pytest.mark.django_db
@override_settings(OBSERVABILITY_LOG_TO_DB=False)
def test_persist_observability_when_disabled_no_row():
    persist_observability_event(
        category=ObservabilityLog.Category.AI_COMPLETION,
        severity=ObservabilityLog.Severity.INFO,
        payload={"event": "ai.completion", "outcome": "ok"},
    )
    assert ObservabilityLog.objects.count() == 0


@pytest.mark.django_db
@override_settings(OBSERVABILITY_LOG_TO_DB=True)
def test_persist_observability_creates_row():
    persist_observability_event(
        category=ObservabilityLog.Category.AI_COMPLETION,
        severity=ObservabilityLog.Severity.INFO,
        payload={"event": "ai.completion", "outcome": "ok"},
    )
    row = ObservabilityLog.objects.get()
    assert row.category == ObservabilityLog.Category.AI_COMPLETION
    assert row.payload["outcome"] == "ok"
