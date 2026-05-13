"""Client entity — checklist Step 2.4 (`advisor` FK → ``AUTH_USER_MODEL``)."""

from django.conf import settings
from django.db import models


class Client(models.Model):
    """A client record owned by exactly one advisor user."""

    name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=64, blank=True, default="")
    advisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
        db_index=True,
    )

    class Meta:
        app_label = "clients"
        db_table = "clients_client"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name
