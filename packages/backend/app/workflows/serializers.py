"""Workflow API serializers — checklist Step 3.4."""

from rest_framework import serializers

from app.models.workflow import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    meeting_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workflow
        fields = ("id", "status", "meeting_id", "celery_task_id", "result_json")


class WorkflowStartSerializer(serializers.Serializer):
    meeting_id = serializers.IntegerField(min_value=1)


class WorkflowStartedResponseSerializer(serializers.Serializer):
    workflow_id = serializers.IntegerField()
