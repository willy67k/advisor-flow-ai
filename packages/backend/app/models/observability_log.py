"""Persisted structured observability events — Phase 8.2 (canonical ORM module under ``app.models``)."""

from django.db import models


class ObservabilityLog(models.Model):
    """Append-only JSON events mirroring stderr structlog (AI calls + failures)."""

    class Category(models.TextChoices):
        AI_COMPLETION = "ai_completion", "AI completion"
        HTTP_EXCEPTION = "http_exception", "HTTP exception"
        CELERY_FAILURE = "celery_failure", "Celery failure"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    category = models.CharField(max_length=32, choices=Category.choices, db_index=True)
    severity = models.CharField(max_length=16, choices=Severity.choices, db_index=True)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "observability"
        db_table = "observability_observabilitylog"
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.category}:{self.severity}:{self.pk}"
