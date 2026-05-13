"""Workflow start + detail API — checklist Step 3.4."""

from datetime import date
from unittest.mock import patch

import pytest

from app.accounts.models import User
from app.models.client import Client
from app.models.meeting import Meeting
from app.models.workflow import Workflow
from app.services.workflows.meeting_summary import MeetingActionItem, MeetingSummaryOutput


@pytest.fixture
def advisor_ws(api_client):
    user = User.objects.create_user(username="ws_adv", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "ws_adv", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    token = login.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return user


@pytest.fixture
def client_ws(advisor_ws):
    return Client.objects.create(
        name="WS Corp",
        email="ws@test",
        phone="",
        advisor=advisor_ws,
    )


@pytest.fixture
def meeting_ws(advisor_ws, client_ws):
    return Meeting.objects.create(
        title="Planning",
        date=date.today(),
        notes="Discuss fees and goals.",
        client=client_ws,
        advisor=advisor_ws,
    )


@pytest.fixture
def other_meeting():
    u = User.objects.create_user(username="ws_other", password="pw", role=User.Role.ADVISOR)
    c = Client.objects.create(name="X", email="x@test", phone="", advisor=u)
    return Meeting.objects.create(
        title="Other",
        date=date.today(),
        notes="secret",
        client=c,
        advisor=u,
    )


@pytest.mark.django_db
def test_workflow_start_returns_id_and_tracks_status(api_client, advisor_ws, meeting_ws):
    fake = MeetingSummaryOutput(
        summary="Done",
        action_items=[MeetingActionItem(task="Follow up", owner="Advisor", due="next week")],
    )

    with patch(
        "app.meetings.tasks.run_meeting_summary_workflow",
        return_value=fake,
    ):
        started = api_client.post(
            "/api/workflows/start",
            {"meeting_id": meeting_ws.pk},
            format="json",
        )

    assert started.status_code == 201
    body = started.json()
    assert body["workflow_id"] >= 1
    wid = body["workflow_id"]
    wf = Workflow.objects.get(pk=wid, meeting=meeting_ws)
    assert wf.status == Workflow.Status.COMPLETED
    assert wf.result_json == fake.model_dump()
    assert wf.celery_task_id

    detail = api_client.get(f"/api/workflows/{wid}")
    assert detail.status_code == 200
    got = detail.json()
    assert got["id"] == wid
    assert got["status"] == Workflow.Status.COMPLETED
    assert got["meeting_id"] == meeting_ws.pk
    assert got["result_json"] == fake.model_dump()
    assert got["celery_state"] == "SUCCESS"


@pytest.mark.django_db
def test_workflow_start_404_for_other_advisor_meeting(api_client, advisor_ws, other_meeting):
    with patch(
        "app.meetings.tasks.run_meeting_summary_workflow",
        return_value=MeetingSummaryOutput(summary="x"),
    ):
        resp = api_client.post(
            "/api/workflows/start",
            {"meeting_id": other_meeting.pk},
            format="json",
        )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_workflow_detail_404_for_other_advisor(api_client, advisor_ws, other_meeting):
    foreign = Workflow.objects.create(meeting=other_meeting)

    detail = api_client.get(f"/api/workflows/{foreign.pk}")
    assert detail.status_code == 404
