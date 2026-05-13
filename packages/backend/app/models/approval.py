"""Human-in-the-loop approval for meeting summary workflows — checklist Step 4.1."""

from django.conf import settings
from django.db import models

from app.models.workflow import Workflow


class ApprovalRequest(models.Model):
    """Gate after AI draft; workflow pauses until approve or reject."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="approval_requests",
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_reviews",
    )
    ai_draft_json = models.JSONField()
    decision_note = models.TextField(blank=True, default="")

    class Meta:
        app_label = "approvals"
        db_table = "approvals_approvalrequest"
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.pk}:{self.status}"
