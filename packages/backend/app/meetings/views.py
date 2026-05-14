from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.meetings.serializers import MeetingSerializer
from app.models.approval import ApprovalRequest
from app.models.meeting import Meeting
from app.models.workflow import Workflow


class MeetingPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MeetingViewSet(viewsets.ModelViewSet):
    """CRUD for meetings owned by the authenticated advisor (via ``client``)."""

    serializer_class = MeetingSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = MeetingPagination
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return Meeting.objects.filter(advisor=self.request.user).select_related("client")

    def perform_create(self, serializer):
        serializer.save(advisor=self.request.user)

    @action(detail=True, methods=["get"], url_path="ai-summary")
    def ai_summary(self, request, pk=None):
        """Latest meeting-summary workflow snapshot (read-only) for the UI detail page."""
        meeting = self.get_object()
        wf = Workflow.objects.filter(meeting=meeting).order_by("-id").first()

        if wf is None:
            return Response(
                {
                    "meeting_id": meeting.pk,
                    "workflow_id": None,
                    "workflow_status": None,
                    "pending_approval_id": None,
                    "has_approved_summary": False,
                    "summary": None,
                    "action_items": [],
                    "approval_decision_note": None,
                }
            )

        pending_ar = (
            ApprovalRequest.objects.filter(workflow=wf, status=ApprovalRequest.Status.PENDING)
            .order_by("-id")
            .first()
        )
        pending_approval_id = int(pending_ar.pk) if pending_ar is not None else None

        approved = wf.status == Workflow.Status.COMPLETED and bool(wf.result_json)
        payload = wf.result_json if isinstance(wf.result_json, dict) else {}

        return Response(
            {
                "meeting_id": meeting.pk,
                "workflow_id": wf.pk,
                "workflow_status": wf.status,
                "pending_approval_id": pending_approval_id,
                "has_approved_summary": approved,
                "summary": payload.get("summary") if approved else None,
                "action_items": (payload.get("action_items") or []) if approved else [],
                "approval_decision_note": (
                    payload.get("approval_decision_note") if approved else None
                ),
            }
        )
