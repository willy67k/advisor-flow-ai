"""DRF serializers — observability logs."""

from rest_framework import serializers

from app.models.observability_log import ObservabilityLog


class ObservabilityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservabilityLog
        fields = ("id", "category", "severity", "payload", "created_at")
