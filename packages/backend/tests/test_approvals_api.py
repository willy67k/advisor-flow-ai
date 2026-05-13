"""Human approval endpoints — checklist Step 4.1."""

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
def advisor_ap(api_client):
    user = User.objects.create_user(username="ap_adv", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "ap_adv", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    token = login.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return user


@pytest.fixture
def setup_meeting(advisor_ap):
    c = Client.objects.create(name="C", email="c@test", phone="", advisor=advisor_ap)
    m = Meeting.objects.create(
        title="M",
        date=date.today(),
        notes="notes",
        client=c,
        advisor=advisor_ap,
    )
    return m


def _start_pending_workflow(api_client, *, meeting_id: int, tmp_path, settings):
    settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH = tmp_path / "lg.sqlite"
    patched_items = [MeetingActionItem(task="Follow up")]
    with (
        patch(
            "app.services.workflows.meeting_summary._llm_summarize_notes",
            return_value="Draft summary",
        ),
        patch(
            "app.services.workflows.meeting_summary._llm_extract_action_items",
            return_value=patched_items,
        ),
    ):
        started = api_client.post("/api/workflows/start", {"meeting_id": meeting_id}, format="json")
    assert started.status_code == 201
    return int(started.json()["workflow_id"])


@pytest.mark.django_db
def test_reject_terminates_workflow(api_client, advisor_ap, setup_meeting, tmp_path, settings):
    wid = _start_pending_workflow(
        api_client,
        meeting_id=setup_meeting.pk,
        tmp_path=tmp_path,
        settings=settings,
    )
    wf = Workflow.objects.get(pk=wid)
    ar = ApprovalRequest.objects.filter(workflow=wf, status=ApprovalRequest.Status.PENDING).get()

    resp = api_client.post(f"/api/approvals/{ar.pk}/reject", {"note": "redo"}, format="json")
    assert resp.status_code == 200

    wf.refresh_from_db()
    ar.refresh_from_db()
    assert wf.status == Workflow.Status.REJECTED
    assert wf.result_json is not None
    assert wf.result_json["approval_status"] == "rejected"
    assert wf.result_json["draft"]["summary"] == "Draft summary"
    assert ar.status == ApprovalRequest.Status.REJECTED


@pytest.mark.django_db
def test_duplicate_approve_conflict(api_client, advisor_ap, setup_meeting, tmp_path, settings):
    wid = _start_pending_workflow(
        api_client,
        meeting_id=setup_meeting.pk,
        tmp_path=tmp_path,
        settings=settings,
    )
    wf = Workflow.objects.get(pk=wid)
    ar = ApprovalRequest.objects.filter(workflow=wf, status=ApprovalRequest.Status.PENDING).get()

    first = api_client.post(f"/api/approvals/{ar.pk}/approve", {}, format="json")
    assert first.status_code == 200

    second = api_client.post(f"/api/approvals/{ar.pk}/approve", {}, format="json")
    assert second.status_code == 409


@pytest.mark.django_db
def test_pending_list_requires_auth(api_client):
    resp = api_client.get("/api/approvals/pending")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_pending_list_empty_then_populated(
    api_client, advisor_ap, setup_meeting, tmp_path, settings
):
    empty = api_client.get("/api/approvals/pending")
    assert empty.status_code == 200
    assert empty.json() == []

    _start_pending_workflow(
        api_client,
        meeting_id=setup_meeting.pk,
        tmp_path=tmp_path,
        settings=settings,
    )
    populated = api_client.get("/api/approvals/pending")
    assert populated.status_code == 200
    body = populated.json()
    assert len(body) == 1
    assert body[0]["meeting_title"] == "M"
    assert body[0]["workflow_id"] >= 1
    assert body[0]["meeting_id"] == setup_meeting.pk
    assert isinstance(body[0]["ai_draft_json"], dict)
