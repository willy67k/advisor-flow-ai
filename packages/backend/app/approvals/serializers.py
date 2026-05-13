"""Serializers for approval decisions — Step 4.1 + pending list (Step 4.2)."""

from rest_framework import serializers

from app.models.approval import ApprovalRequest


class ApprovalDecisionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ApprovalPendingSerializer(serializers.ModelSerializer):
    workflow_id = serializers.IntegerField(read_only=True)
    meeting_id = serializers.IntegerField(source="workflow.meeting_id", read_only=True)
    meeting_title = serializers.CharField(source="workflow.meeting.title", read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = ("id", "workflow_id", "meeting_id", "meeting_title", "ai_draft_json")
