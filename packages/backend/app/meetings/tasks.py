"""Async tasks for meetings domain (Step 3.3 meeting summary Celery runner)."""

from __future__ import annotations

from django.db.models import QuerySet

from app.models.meeting import Meeting
from app.models.workflow import Workflow
from app.services.workflows.meeting_summary import (
    MeetingSummaryOutput,
    run_meeting_summary_workflow,
)
from app.worker import celery_app


@celery_app.task(bind=True, store_eager_result=True)
def run_meeting_summary_task(
    self,
    meeting_id: int,
    workflow_id: int | None = None,
) -> dict[str, object]:
    """Fetch meeting notes, run LangGraph workflow, optionally update ``Workflow`` row."""
    wf_qs: QuerySet[Workflow] | None = (
        Workflow.objects.filter(pk=int(workflow_id)) if workflow_id is not None else None
    )
    try:
        if wf_qs is not None:
            wf_row = wf_qs.select_related("meeting").get()
            if wf_row.meeting_id != int(meeting_id):
                msg = "meeting_id does not match workflow.meeting."
                raise ValueError(msg)
            wf_qs.update(status=Workflow.Status.PROCESSING)

        m = Meeting.objects.get(pk=int(meeting_id))
        notes = str(m.notes or "")
        out: MeetingSummaryOutput = run_meeting_summary_workflow(notes)
        payload = out.model_dump()

        if wf_qs is not None:
            wf_qs.update(status=Workflow.Status.COMPLETED, result_json=payload)

        return payload
    except Exception as exc:
        if wf_qs is not None:
            wf_qs.update(status=Workflow.Status.FAILED, result_json={"error": str(exc)})
        raise
