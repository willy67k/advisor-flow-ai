"""Chunks + embeddings for RAG — checklist Step 5.2."""

from django.db import models
from pgvector.django import VectorField

from app.models.document import Document

# OpenAI ``text-embedding-3-small`` default output size.
EMBEDDING_DIMENSIONS = 1536


class DocumentChunk(models.Model):
    """A slice of extracted document text with a dense embedding."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
        db_index=True,
    )
    content = models.TextField()
    position = models.PositiveSmallIntegerField(
        db_index=True,
        help_text="Chunk order within the document (0-based).",
    )
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)

    class Meta:
        app_label = "documents"
        db_table = "documents_documentchunk"
        ordering = ("document_id", "position")

    def __str__(self) -> str:
        return f"chunk {self.document_id}:{self.position}"
