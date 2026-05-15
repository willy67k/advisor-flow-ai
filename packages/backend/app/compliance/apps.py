"""Django app label for compliance HTTP surface (Step 7.1 — no ORM models)."""

from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.compliance"
    label = "compliance"
