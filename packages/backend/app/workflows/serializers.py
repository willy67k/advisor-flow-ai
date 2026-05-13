"""Workflow API serializers — checklist Step 3.4."""

from rest_framework import serializers

from app.models.approval import ApprovalRequest
from app.models.workflow import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    meeting_id = serializers.IntegerField(read_only=True)
    pending_approval_id = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = (
            "id",
            "status",
            "meeting_id",
            "celery_task_id",
            "result_json",
            "pending_approval_id",
        )

    def get_pending_approval_id(self, obj: Workflow) -> int | None:
        ar = (
            ApprovalRequest.objects.filter(
                workflow=obj,
                status=ApprovalRequest.Status.PENDING,
            )
            .order_by("-id")
            .first()
        )
        return int(ar.pk) if ar is not None else None


class WorkflowStartSerializer(serializers.Serializer):
    meeting_id = serializers.IntegerField(min_value=1)


class WorkflowStartedResponseSerializer(serializers.Serializer):
    workflow_id = serializers.IntegerField()
