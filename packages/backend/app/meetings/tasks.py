"""Async tasks for meetings domain (Step 3.3 meeting summary Celery runner)."""

from __future__ import annotations

from django.conf import settings
from django.db.models import QuerySet

from app.models.meeting import Meeting
from app.models.workflow import Workflow
from app.services.workflows.checkpoint_bridge import sync_workflow_from_graph_state
from app.services.workflows.meeting_summary import (
    graph_first_interrupt_value,
    invoke_meeting_summary_graph,
    meeting_state_to_summary_output,
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
    checkpoint_path = settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH
    try:
        if wf_qs is not None:
            wf_row = wf_qs.select_related("meeting").get()
            if wf_row.meeting_id != int(meeting_id):
                msg = "meeting_id does not match workflow.meeting."
                raise ValueError(msg)
            wf_qs.update(status=Workflow.Status.PROCESSING)

        m = Meeting.objects.get(pk=int(meeting_id))
        notes = str(m.notes or "")

        if wf_qs is None:
            # Backwards-compatible direct invocation (no approvals / no DB row).
            from app.services.workflows.meeting_summary import run_meeting_summary_workflow

            out = run_meeting_summary_workflow(notes)
            return out.model_dump()

        state = invoke_meeting_summary_graph(
            notes=notes,
            meeting_id=int(meeting_id),
            workflow_id=int(wf_row.pk),
            checkpoint_path=checkpoint_path,
        )
        intr = graph_first_interrupt_value(state)

        if intr is not None:
            sync = sync_workflow_from_graph_state(wf_row, state)
            if sync.get("awaiting_compliance"):
                return {"awaiting_compliance": True}
            apid = sync.get("approval_request_id")
            if apid is None:
                msg = "interrupt present but workflow sync returned no approval id"
                raise RuntimeError(msg)
            return {
                "awaiting_approval": True,
                "approval_request_id": int(apid),
            }

        structured = meeting_state_to_summary_output(state)
        payload = structured.model_dump()

        wf_qs.update(status=Workflow.Status.COMPLETED, result_json=payload)
        return payload
    except Exception as exc:
        if wf_qs is not None:
            wf_qs.update(status=Workflow.Status.FAILED, result_json={"error": str(exc)})
        raise
