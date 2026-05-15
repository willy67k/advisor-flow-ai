"""Compliance review API — Step 7.1 (high-risk pause + notify via workflow status)."""

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

from app.compliance.permissions import IsComplianceOfficer
from app.compliance.serializers import ComplianceNoteSerializer, CompliancePendingSerializer
from app.models.workflow import Workflow
from app.services.audit.log import workflow_audit_snapshot, write_audit_log
from app.services.workflows.checkpoint_bridge import sync_workflow_from_graph_state
from app.services.workflows.meeting_summary import (
    graph_first_interrupt_value,
    resume_meeting_summary_graph,
)


class CompliancePendingListView(APIView):
    permission_classes = (IsAuthenticated, IsComplianceOfficer)

    @extend_schema(responses={200: CompliancePendingSerializer(many=True)})
    def get(self, request):
        rows = (
            Workflow.objects.filter(status=Workflow.Status.WAITING_COMPLIANCE)
            .select_related("meeting")
            .order_by("-id")
        )
        out = []
        for wf in rows:
            payload = wf.result_json if isinstance(wf.result_json, dict) else {}
            out.append(
                {
                    "workflow_id": int(wf.pk),
                    "meeting_id": int(wf.meeting_id),
                    "meeting_title": str(wf.meeting.title),
                    "compliance_review": payload,
                }
            )
        return Response(out)


class ComplianceWorkflowClearView(APIView):
    permission_classes = (IsAuthenticated, IsComplianceOfficer)

    @extend_schema(request=ComplianceNoteSerializer, responses={200: None})
    @transaction.atomic
    def post(self, request, pk: int):
        wf = get_object_or_404(
            Workflow.objects.select_for_update(),
            pk=int(pk),
            status=Workflow.Status.WAITING_COMPLIANCE,
        )
        ser = ComplianceNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = str(ser.validated_data.get("note") or "")

        state = resume_meeting_summary_graph(
            workflow_id=int(wf.pk),
            resume_payload={"action": "clear", "note": note},
            checkpoint_path=settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH,
        )
        if graph_first_interrupt_value(cast(dict[str, Any], state)) is None:
            return Response(
                {"detail": "expected advisor interrupt after compliance clear."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        sync_workflow_from_graph_state(wf, state, actor=request.user)
        wf.refresh_from_db()
        return Response(
            {
                "workflow_id": int(wf.pk),
                "status": wf.status,
            },
            status=status.HTTP_200_OK,
        )


class ComplianceWorkflowRejectView(APIView):
    permission_classes = (IsAuthenticated, IsComplianceOfficer)

    @extend_schema(request=ComplianceNoteSerializer, responses={200: None})
    @transaction.atomic
    def post(self, request, pk: int):
        wf = get_object_or_404(
            Workflow.objects.select_for_update(),
            pk=int(pk),
            status=Workflow.Status.WAITING_COMPLIANCE,
        )
        ser = ComplianceNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = str(ser.validated_data.get("note") or "")

        state = resume_meeting_summary_graph(
            workflow_id=int(wf.pk),
            resume_payload={"action": "reject", "note": note},
            checkpoint_path=settings.LANGGRAPH_CHECKPOINT_SQLITE_PATH,
        )
        if graph_first_interrupt_value(cast(dict[str, Any], state)) is not None:
            return Response(
                {"detail": "graph still interrupted after compliance reject."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if str(state.get("compliance_decision") or "") != "rejected":
            return Response(
                {"detail": "unexpected graph state after compliance reject."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        stored = wf.result_json if isinstance(wf.result_json, dict) else {}
        wf.refresh_from_db(fields=["status", "meeting_id", "celery_task_id", "result_json"])
        before = workflow_audit_snapshot(wf)
        Workflow.objects.filter(pk=wf.pk).update(
            status=Workflow.Status.REJECTED,
            result_json={
                "compliance_rejected": True,
                "compliance_decision_note": str(state.get("compliance_decision_note") or ""),
                "draft": {
                    "summary": stored.get("summary", state.get("summary", "")),
                    "action_items": stored.get("action_items", state.get("action_items") or []),
                },
            },
        )
        wf.refresh_from_db(fields=["status", "meeting_id", "celery_task_id", "result_json"])
        write_audit_log(
            actor=request.user,
            action="workflow.compliance_rejected",
            resource_type="workflow",
            resource_id=str(wf.pk),
            before_json=before,
            after_json=workflow_audit_snapshot(wf),
            token_usage=None,
        )
        return Response({"workflow_id": int(wf.pk), "status": Workflow.Status.REJECTED})
