"""Meeting summary workflow tracker — checklist Step 3.4."""

from django.db import models

from app.models.meeting import Meeting


class Workflow(models.Model):
    """Async meeting-summary run linked to Celery (`run_meeting_summary_task`)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="workflows",
        db_index=True,
    )
    celery_task_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    result_json = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "workflows"
        db_table = "workflows_workflow"
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.pk}:{self.status}"
