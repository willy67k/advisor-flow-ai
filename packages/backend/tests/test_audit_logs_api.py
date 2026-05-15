"""Audit log list API — managers only (Step 7.2)."""

import pytest

from app.accounts.models import User
from app.models.audit_log import AuditLog


@pytest.mark.django_db
def test_audit_logs_forbidden_for_advisor(api_client):
    User.objects.create_user(username="alog_adv", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "alog_adv", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    resp = api_client.get("/api/audit-logs/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_audit_logs_ok_for_manager(api_client):
    User.objects.create_user(username="alog_mgr", password="pw", role=User.Role.MANAGER)
    AuditLog.objects.create(
        action="workflow.processing",
        resource_type="workflow",
        resource_id="99",
        before_json={"status": "pending"},
        after_json={"status": "processing"},
    )

    login = api_client.post(
        "/api/auth/login/",
        {"username": "alog_mgr", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    resp = api_client.get("/api/audit-logs/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    assert any(r["resource_id"] == "99" for r in body["results"])


@pytest.mark.django_db
def test_audit_logs_resource_type_substring_match(api_client):
    User.objects.create_user(username="alog_mgr2", password="pw", role=User.Role.MANAGER)
    AuditLog.objects.create(
        action="workflow.processing",
        resource_type="workflow",
        resource_id="1",
        before_json=None,
        after_json=None,
    )

    login = api_client.post(
        "/api/auth/login/",
        {"username": "alog_mgr2", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")

    resp = api_client.get("/api/audit-logs/", {"resource_type": "workflo"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["resource_type"] == "workflow"
