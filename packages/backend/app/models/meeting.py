"""Meeting entity — checklist Step 2.5."""

from django.conf import settings
from django.db import models

from app.models.client import Client


class Meeting(models.Model):
    """Meeting tied to a client and advisor (advisor matches ``client.advisor``)."""

    title = models.CharField(max_length=255)
    date = models.DateField(db_index=True)
    notes = models.TextField(blank=True, default="")
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="meetings",
        db_index=True,
    )
    advisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meetings",
        db_index=True,
    )

    class Meta:
        app_label = "meetings"
        db_table = "meetings_meeting"
        ordering = ("-date", "id")

    def save(self, *args, **kwargs) -> None:
        if self.client_id:
            advisor_id = (
                Client.objects.filter(pk=self.client_id)
                .values_list(
                    "advisor_id",
                    flat=True,
                )
                .first()
            )
            if advisor_id is not None:
                self.advisor_id = advisor_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
