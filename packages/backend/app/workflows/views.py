"""Workflow status API — checklist Step 3.4."""

from celery.result import AsyncResult
from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.meetings.tasks import run_meeting_summary_task
from app.models.meeting import Meeting
from app.models.workflow import Workflow
from app.worker import celery_app
from app.workflows.serializers import (
    WorkflowSerializer,
    WorkflowStartedResponseSerializer,
    WorkflowStartSerializer,
)


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
