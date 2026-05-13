"""Celery meeting summary task (Step 3.3)."""

from datetime import date
from unittest.mock import patch

import pytest
from django_celery_results.models import TaskResult

from app.accounts.models import User
from app.meetings.tasks import run_meeting_summary_task
from app.models.client import Client
from app.models.meeting import Meeting
from app.services.workflows.meeting_summary import MeetingActionItem, MeetingSummaryOutput


@pytest.fixture
def advisor_user():
    return User.objects.create_user(username="cel_adv", password="pw", role=User.Role.ADVISOR)


@pytest.fixture
def sample_meeting(advisor_user):
    c = Client.objects.create(
        name="ACME",
        email="a@test",
        phone="",
        advisor=advisor_user,
    )
    return Meeting.objects.create(
        title="Q1",
        date=date.today(),
        notes="Agreed to rebalance equities. Send proposal by Tuesday.",
        client=c,
        advisor=advisor_user,
    )


@pytest.mark.django_db
def test_run_meeting_summary_task_delay_eager_writes_to_django_results(sample_meeting):
    fake = MeetingSummaryOutput(
        summary="S",
        action_items=[
            MeetingActionItem(task="Send proposal", owner="Advisor", due="Tuesday"),
        ],
    )

    with patch(
        "app.meetings.tasks.run_meeting_summary_workflow",
        return_value=fake,
    ):
        async_result = run_meeting_summary_task.delay(sample_meeting.pk)

    assert async_result.successful()
    assert async_result.get() == fake.model_dump()

    row = TaskResult.objects.get(task_id=async_result.id)
    assert row.status == "SUCCESS"


@pytest.mark.django_db
def test_run_meeting_summary_task_raises_when_meeting_missing():
    with pytest.raises(Meeting.DoesNotExist):
        run_meeting_summary_task.delay(987_654_321)
