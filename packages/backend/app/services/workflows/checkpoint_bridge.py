"""Map LangGraph interrupt payloads to Django ``Workflow`` / ``ApprovalRequest`` rows — Step 7.1."""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from app.models.approval import ApprovalRequest
from app.models.workflow import Workflow
from app.services.workflows.meeting_summary import graph_first_interrupt_value

logger = logging.getLogger(__name__)

_COMPLIANCE_STAGE = "compliance_review"
_ADVISOR_STAGE = "advisor_approval"


class WorkflowInterruptSyncResult(TypedDict, total=False):
    awaiting_compliance: bool
    awaiting_approval: bool
    approval_request_id: int


def normalize_advisor_draft_payload(intr: dict[str, Any]) -> dict[str, Any]:
    """Shape stored on ``ApprovalRequest.ai_draft_json`` (frontend expects summary + action_items)."""
    stage = intr.get("stage")
    if stage == _ADVISOR_STAGE:
        return {
            "summary": str(intr.get("summary") or ""),
            "action_items": list(intr.get("action_items") or []),
            "compliance": intr.get("compliance"),
        }
    if "summary" in intr and "action_items" in intr:
        return dict(intr)
    return {
        "summary": str(intr.get("summary") or ""),
        "action_items": list(intr.get("action_items") or []),
        "compliance": intr.get("compliance"),
    }


def sync_workflow_from_graph_state(
    wf_row: Workflow, state: dict[str, Any]
) -> WorkflowInterruptSyncResult:
    """After ``invoke`` / ``resume``, persist workflow state when still interrupted or terminal."""
    intr = graph_first_interrupt_value(state)
    wf_qs = Workflow.objects.filter(pk=wf_row.pk)

    if not isinstance(intr, dict):
        return {}

    stage = intr.get("stage")
    if stage == _COMPLIANCE_STAGE:
        wf_qs.update(status=Workflow.Status.WAITING_COMPLIANCE, result_json=intr)
        logger.warning(
            "compliance_hold workflow_id=%s meeting_id=%s risk=%s",
            wf_row.pk,
            wf_row.meeting_id,
            (intr.get("compliance") or {}).get("risk_level"),
        )
        return {"awaiting_compliance": True}

    ar = ApprovalRequest.objects.create(
        workflow=wf_row,
        status=ApprovalRequest.Status.PENDING,
        reviewer=None,
        ai_draft_json=normalize_advisor_draft_payload(intr),
    )
    wf_qs.update(status=Workflow.Status.WAITING_APPROVAL, result_json=None)
    return {"awaiting_approval": True, "approval_request_id": int(ar.pk)}


__all__ = [
    "normalize_advisor_draft_payload",
    "sync_workflow_from_graph_state",
]
