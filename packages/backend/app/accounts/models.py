"""User model (project checklist: equivalently surfaced as accounts models)."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Financial-advisor workspace user with a fixed RBAC role."""

    class Role(models.TextChoices):
        ADVISOR = "advisor", "Advisor"
        MANAGER = "manager", "Manager"
        COMPLIANCE_OFFICER = "compliance_officer", "Compliance Officer"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.ADVISOR,
        db_index=True,
    )

    class Meta:
        db_table = "accounts_user"
