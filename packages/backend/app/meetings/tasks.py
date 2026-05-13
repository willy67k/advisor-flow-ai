"""Async tasks for meetings domain (Step 3.3 meeting summary Celery runner)."""

from __future__ import annotations

from app.models.meeting import Meeting
from app.services.workflows.meeting_summary import (
    MeetingSummaryOutput,
    run_meeting_summary_workflow,
)
from app.worker import celery_app


@celery_app.task(bind=True, store_eager_result=True)
def run_meeting_summary_task(self, meeting_id: int) -> dict[str, object]:
    """Fetch meeting notes, run LangGraph workflow, return structured summary JSON."""
    m = Meeting.objects.get(pk=int(meeting_id))
    notes = str(m.notes or "")
    out: MeetingSummaryOutput = run_meeting_summary_workflow(notes)
    return out.model_dump()
