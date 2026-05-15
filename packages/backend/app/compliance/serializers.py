"""Compliance API serializers — Step 7.1."""

from rest_framework import serializers


class ComplianceNoteSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="")


class CompliancePendingSerializer(serializers.Serializer):
    workflow_id = serializers.IntegerField()
    meeting_id = serializers.IntegerField()
    meeting_title = serializers.CharField()
    compliance_review = serializers.DictField()
