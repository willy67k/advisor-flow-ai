"""Django app for human approval APIs (Step 4.1)."""

from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.approvals"
    label = "approvals"
    verbose_name = "Approvals"
