"""Immutable audit trail rows — checklist Step 7.2."""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Records workflow-related mutations for compliance review."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=64, db_index=True)
    resource_type = models.CharField(max_length=64, db_index=True)
    resource_id = models.CharField(max_length=64, db_index=True)
    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)
    token_usage = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "workflows"
        db_table = "workflows_auditlog"
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.action}:{self.resource_type}:{self.resource_id}"
