"""Approval API — Step 4.1."""

from __future__ import annotations

from typing import Any, cast

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.approvals.serializers import ApprovalDecisionSerializer, ApprovalPendingSerializer
from app.models.approval import ApprovalRequest
from app.models.workflow import Workflow
from app.services.audit.log import workflow_audit_snapshot, write_audit_log
from app.services.workflows.meeting_summary import (
    graph_first_interrupt_value,
    meeting_state_to_summary_output,
    resume_meeting_summary_graph,
)

_APPROVAL_ACTION_APPROVE = "approve"
_APPROVAL_ACTION_REJECT = "reject"
_APPROVAL_RESULT_APPROVED = "approved"
_APPROVAL_RESULT_REJECTED = "rejected"


def _approval_queryset_for(user):
    return ApprovalRequest.objects.select_related("workflow", "workflow__meeting").filter(
        workflow__meeting__advisor=user,
    )


class ApprovalPendingListView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: ApprovalPendingSerializer(many=True)})
    def get(self, request):
        qs = (
            _approval_queryset_for(request.user)
            .filter(status=ApprovalRequest.Status.PENDING)
            .order_by("-id")
        )
        return Response(ApprovalPendingSerializer(qs, many=True).data)


class ApprovalApproveView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=ApprovalDecisionSerializer, responses={200: None})
    @transaction.atomic
    def post(self, request, pk: int):
        ar = get_object_or_404(
            _approval_queryset_for(request.user).select_for_update(),
            pk=int(pk),
        )
        if ar.status != ApprovalRequest.Status.PENDING:
            return Response({"detail": "approval is not pending."}, status=status.HTTP_409_CONFLICT)

        ser = ApprovalDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = str(ser.validated_data.get("note") or "")

        checkpoint_path = settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH
        state = resume_meeting_summary_graph(
            workflow_id=int(ar.workflow_id),
            resume_payload={"action": _APPROVAL_ACTION_APPROVE, "note": note},
            checkpoint_path=checkpoint_path,
        )
        if graph_first_interrupt_value(cast(dict[str, Any], state)) is not None:
            return Response(
                {"detail": "graph is still interrupted after approve."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        decision = str(state.get("approval_status") or "")
        if decision != _APPROVAL_RESULT_APPROVED:
            return Response(
                {"detail": f"unexpected graph state: {decision!r}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        out = meeting_state_to_summary_output(state)
        payload = out.model_dump()
        payload["approval_status"] = _APPROVAL_RESULT_APPROVED
        payload["approval_decision_note"] = str(state.get("approval_decision_note") or "")

        ar.status = ApprovalRequest.Status.APPROVED
        ar.reviewer = request.user
        ar.decision_note = note
        ar.save(update_fields=["status", "reviewer", "decision_note"])

        wf_row = Workflow.objects.get(pk=ar.workflow_id)
        before = workflow_audit_snapshot(wf_row)
        Workflow.objects.filter(pk=ar.workflow_id).update(
            status=Workflow.Status.COMPLETED,
            result_json=payload,
        )
        wf_row.refresh_from_db(fields=["status", "meeting_id", "celery_task_id", "result_json"])
        write_audit_log(
            actor=request.user,
            action="workflow.completed",
            resource_type="workflow",
            resource_id=str(ar.workflow_id),
            before_json=before,
            after_json=workflow_audit_snapshot(wf_row),
            token_usage=None,
        )

        return Response({"workflow_id": int(ar.workflow_id), "result_json": payload})


class ApprovalRejectView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=ApprovalDecisionSerializer, responses={200: None})
    @transaction.atomic
    def post(self, request, pk: int):
        ar = get_object_or_404(
            _approval_queryset_for(request.user).select_for_update(),
            pk=int(pk),
        )
        if ar.status != ApprovalRequest.Status.PENDING:
            return Response({"detail": "approval is not pending."}, status=status.HTTP_409_CONFLICT)

        ser = ApprovalDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = str(ser.validated_data.get("note") or "")

        checkpoint_path = settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH
        state = resume_meeting_summary_graph(
            workflow_id=int(ar.workflow_id),
            resume_payload={"action": _APPROVAL_ACTION_REJECT, "note": note},
            checkpoint_path=checkpoint_path,
        )
        if graph_first_interrupt_value(cast(dict[str, Any], state)) is not None:
            return Response(
                {"detail": "graph is still interrupted after reject."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        decision = str(state.get("approval_status") or "")
        if decision != _APPROVAL_RESULT_REJECTED:
            return Response(
                {"detail": f"unexpected graph state: {decision!r}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        result_json = {
            "approval_status": _APPROVAL_RESULT_REJECTED,
            "approval_decision_note": str(state.get("approval_decision_note") or ""),
            "draft": ar.ai_draft_json,
        }

        ar.status = ApprovalRequest.Status.REJECTED
        ar.reviewer = request.user
        ar.decision_note = note
        ar.save(update_fields=["status", "reviewer", "decision_note"])

        wf_row = Workflow.objects.get(pk=ar.workflow_id)
        before = workflow_audit_snapshot(wf_row)
        Workflow.objects.filter(pk=ar.workflow_id).update(
            status=Workflow.Status.REJECTED,
            result_json=result_json,
        )
        wf_row.refresh_from_db(fields=["status", "meeting_id", "celery_task_id", "result_json"])
        write_audit_log(
            actor=request.user,
            action="workflow.advisor_rejected",
            resource_type="workflow",
            resource_id=str(ar.workflow_id),
            before_json=before,
            after_json=workflow_audit_snapshot(wf_row),
            token_usage=None,
        )

        return Response({"workflow_id": int(ar.workflow_id), "result_json": result_json})
