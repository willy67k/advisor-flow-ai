"""Uploaded document metadata — checklist Step 2.6."""

from django.db import models

from app.models.meeting import Meeting


class Document(models.Model):
    """File tied to a meeting (ownership enforced via ``meeting.advisor`` in views)."""

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"

    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="documents",
        db_index=True,
    )
    extracted_text = models.TextField(blank=True, default="")

    class Meta:
        app_label = "documents"
        db_table = "documents_document"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.file_name
