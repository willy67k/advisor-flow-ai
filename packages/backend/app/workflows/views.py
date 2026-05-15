"""Workflow status API — checklist Step 3.4."""

from celery.result import AsyncResult
from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.meetings.tasks import run_meeting_summary_task
from app.models.audit_log import AuditLog
from app.models.meeting import Meeting
from app.models.workflow import Workflow
from app.services.audit.log import workflow_audit_snapshot, write_audit_log
from app.worker import celery_app
from app.workflows.permissions import IsManager
from app.workflows.serializers import (
    AuditLogSerializer,
    WorkflowListItemSerializer,
    WorkflowSerializer,
    WorkflowStartedResponseSerializer,
    WorkflowStartSerializer,
)


class WorkflowPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 50


class WorkflowListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = WorkflowListItemSerializer
    pagination_class = WorkflowPagination

    def get_queryset(self):
        return Workflow.objects.filter(meeting__advisor=self.request.user).select_related("meeting")


def _celery_state_for_workflow(wf: Workflow) -> str | None:
    if not wf.celery_task_id:
        return None
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return {
            Workflow.Status.COMPLETED: "SUCCESS",
            Workflow.Status.FAILED: "FAILURE",
            Workflow.Status.REJECTED: "SUCCESS",
            Workflow.Status.PROCESSING: "STARTED",
            Workflow.Status.PENDING: "PENDING",
            Workflow.Status.WAITING_COMPLIANCE: "SUCCESS",
            Workflow.Status.WAITING_APPROVAL: "SUCCESS",
        }.get(wf.status, "PENDING")

    return AsyncResult(wf.celery_task_id, app=celery_app).state


class WorkflowStartView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=WorkflowStartSerializer,
        responses={201: WorkflowStartedResponseSerializer},
        examples=[
            OpenApiExample(name="payload", value={"meeting_id": 42}, request_only=True),
        ],
    )
    def post(self, request):
        ser = WorkflowStartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        meeting_id = int(ser.validated_data["meeting_id"])

        meeting = get_object_or_404(
            Meeting.objects.filter(advisor=request.user),
            pk=meeting_id,
        )

        wf = Workflow.objects.create(meeting=meeting)
        async_res = run_meeting_summary_task.delay(meeting_id, wf.pk)
        Workflow.objects.filter(pk=wf.pk).update(celery_task_id=async_res.id)
        wf.refresh_from_db(fields=["status", "meeting_id", "celery_task_id", "result_json"])
        write_audit_log(
            actor=request.user,
            action="workflow.run_enqueued",
            resource_type="workflow",
            resource_id=str(wf.pk),
            before_json=None,
            after_json=workflow_audit_snapshot(wf),
            token_usage=None,
        )

        return Response({"workflow_id": wf.pk}, status=status.HTTP_201_CREATED)


class WorkflowDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: WorkflowSerializer})
    def get(self, request, pk: int):
        wf = get_object_or_404(
            Workflow.objects.select_related("meeting"),
            pk=pk,
            meeting__advisor=request.user,
        )

        payload = WorkflowSerializer(wf).data
        celery_state = _celery_state_for_workflow(wf)
        return Response({"celery_state": celery_state, **payload})


class AuditLogPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 50


class AuditLogListView(ListAPIView):
    """Paginated audit trail — managers only (optional ``resource_type`` / ``resource_id`` filters)."""

    permission_classes = (IsAuthenticated, IsManager)
    serializer_class = AuditLogSerializer
    pagination_class = AuditLogPagination

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor").all()

        resource_type = self.request.query_params.get("resource_type")
        resource_id = self.request.query_params.get("resource_id")
        if resource_type is not None and str(resource_type).strip():
            qs = qs.filter(resource_type__icontains=str(resource_type).strip())
        if resource_id:
            qs = qs.filter(resource_id=str(resource_id))

        return qs.order_by("-id")
