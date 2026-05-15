"""Compliance officer API — Step 7.1."""

from datetime import date
from unittest.mock import patch

import pytest

from app.accounts.models import User
from app.models.approval import ApprovalRequest
from app.models.client import Client
from app.models.meeting import Meeting
from app.models.workflow import Workflow
from app.services.workflows.meeting_summary import MeetingActionItem


@pytest.fixture
def advisor_co(api_client):
    user = User.objects.create_user(username="co_adv", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "co_adv", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    return user


@pytest.fixture
def compliance_officer_user():
    return User.objects.create_user(
        username="co_off",
        password="pw",
        role=User.Role.COMPLIANCE_OFFICER,
    )


@pytest.fixture
def high_risk_meeting(advisor_co):
    c = Client.objects.create(name="Co", email="co@test", phone="", advisor=advisor_co)
    return Meeting.objects.create(
        title="Risky",
        date=date.today(),
        notes="Discussed marketing language.",
        client=c,
        advisor=advisor_co,
    )


def _start_high_risk_workflow(api_client, *, meeting_id: int, tmp_path, settings):
    settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH = tmp_path / "lg-co.sqlite"
    patched_items = [MeetingActionItem(task="Fix wording", owner="Advisor", due="ASAP")]
    with (
        patch(
            "app.services.workflows.meeting_summary._llm_summarize_notes",
            return_value="This product is completely risk-free for investors.",
        ),
        patch(
            "app.services.workflows.meeting_summary._llm_extract_action_items",
            return_value=patched_items,
        ),
    ):
        return api_client.post("/api/workflows/start", {"meeting_id": meeting_id}, format="json")


@pytest.mark.django_db
def test_high_risk_workflow_waits_compliance_then_officer_can_clear(
    api_client, advisor_co, compliance_officer_user, high_risk_meeting, tmp_path, settings
):
    login_a = api_client.post(
        "/api/auth/login/",
        {"username": "co_adv", "password": "pw"},
        format="json",
    )
    assert login_a.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_a.json()['access']}")

    started = _start_high_risk_workflow(
        api_client, meeting_id=high_risk_meeting.pk, tmp_path=tmp_path, settings=settings
    )
    assert started.status_code == 201
    wid = started.json()["workflow_id"]

    wf = Workflow.objects.get(pk=wid)
    assert wf.status == Workflow.Status.WAITING_COMPLIANCE
    assert wf.result_json is not None
    assert wf.result_json.get("stage") == "compliance_review"

    api_client.credentials()  # logout advisor
    login_o = api_client.post(
        "/api/auth/login/",
        {"username": "co_off", "password": "pw"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_o.json()['access']}")

    pending = api_client.get("/api/compliance/pending")
    assert pending.status_code == 200
    body = pending.json()
    assert len(body) == 1
    assert body[0]["workflow_id"] == wid
    assert body[0]["compliance_review"].get("compliance", {}).get("risk_level") == "high"

    cleared = api_client.post(
        f"/api/compliance/workflows/{wid}/clear", {"note": "exception logged"}, format="json"
    )
    assert cleared.status_code == 200
    wf.refresh_from_db()
    assert wf.status == Workflow.Status.WAITING_APPROVAL
    assert ApprovalRequest.objects.filter(
        workflow=wf, status=ApprovalRequest.Status.PENDING
    ).exists()


@pytest.mark.django_db
def test_compliance_officer_can_reject_hold(
    api_client, advisor_co, compliance_officer_user, high_risk_meeting, tmp_path, settings
):
    login_a = api_client.post(
        "/api/auth/login/",
        {"username": "co_adv", "password": "pw"},
        format="json",
    )
    assert login_a.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_a.json()['access']}")

    _start_high_risk_workflow(
        api_client, meeting_id=high_risk_meeting.pk, tmp_path=tmp_path, settings=settings
    )
    wid = Workflow.objects.get(meeting=high_risk_meeting).pk

    login_o = api_client.post(
        "/api/auth/login/",
        {"username": "co_off", "password": "pw"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_o.json()['access']}")

    resp = api_client.post(
        f"/api/compliance/workflows/{wid}/reject", {"note": "cannot publish"}, format="json"
    )
    assert resp.status_code == 200
    wf = Workflow.objects.get(pk=wid)
    assert wf.status == Workflow.Status.REJECTED
    assert wf.result_json.get("compliance_rejected") is True
