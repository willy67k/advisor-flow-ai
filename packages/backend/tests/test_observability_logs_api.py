"""Observability log list API — managers only."""

import pytest

from app.accounts.models import User
from app.models.observability_log import ObservabilityLog


@pytest.mark.django_db
def test_observability_logs_forbidden_for_advisor(api_client):
    User.objects.create_user(username="obs_adv", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/", {"username": "obs_adv", "password": "pw"}, format="json"
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    assert api_client.get("/api/observability-logs/").status_code == 403


@pytest.mark.django_db
def test_observability_logs_ok_for_manager(api_client):
    User.objects.create_user(username="obs_mgr", password="pw", role=User.Role.MANAGER)
    ObservabilityLog.objects.create(
        category=ObservabilityLog.Category.AI_COMPLETION,
        severity=ObservabilityLog.Severity.INFO,
        payload={"event": "ai.completion", "outcome": "ok"},
    )
    login = api_client.post(
        "/api/auth/login/", {"username": "obs_mgr", "password": "pw"}, format="json"
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    resp = api_client.get("/api/observability-logs/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    row = next(r for r in body["results"] if r["payload"].get("event") == "ai.completion")
    assert row["category"] == ObservabilityLog.Category.AI_COMPLETION


@pytest.mark.django_db
def test_observability_logs_filter_category(api_client):
    User.objects.create_user(username="obs_mgr2", password="pw", role=User.Role.MANAGER)
    ObservabilityLog.objects.create(
        category=ObservabilityLog.Category.CELERY_FAILURE,
        severity=ObservabilityLog.Severity.WARNING,
        payload={"event": "celery.task_failure"},
    )
    ObservabilityLog.objects.create(
        category=ObservabilityLog.Category.AI_COMPLETION,
        severity=ObservabilityLog.Severity.INFO,
        payload={"event": "ai.completion"},
    )
    login = api_client.post(
        "/api/auth/login/", {"username": "obs_mgr2", "password": "pw"}, format="json"
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    resp = api_client.get(
        "/api/observability-logs/", {"category": ObservabilityLog.Category.CELERY_FAILURE}
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    assert resp.json()["results"][0]["category"] == ObservabilityLog.Category.CELERY_FAILURE
