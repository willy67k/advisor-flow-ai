"""Celery document pipeline writes ``DocumentChunk`` rows + embeddings (Step 5.2)."""

import numpy as np
import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from app.accounts.models import User
from app.documents.tasks import process_document_task
from app.models.client import Client
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.meeting import Meeting


@pytest.fixture
def extracted_body() -> str:
    return "\n\n".join(f"SECTION_{i}\n" + ("phrase " * 400) for i in range(5))


@pytest.mark.django_db
def test_process_document_creates_chunks(extracted_body, monkeypatch, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(username="chunk_u", password="pw", role=User.Role.ADVISOR)
    client = Client.objects.create(name="Corp", email="c@test", advisor=user)
    meeting = Meeting.objects.create(
        title="M",
        date="2026-06-01",
        notes="",
        client=client,
        advisor=user,
    )

    monkeypatch.setattr(
        "app.documents.tasks.extract_document_text",
        lambda path, name: extracted_body,
    )
    monkeypatch.setattr(
        "app.documents.tasks.embed_texts_batch",
        lambda texts: [[0.025] * 1536 for _ in texts],
    )

    rel_path = f"documents/meetings/{meeting.pk}/mock.pdf"
    default_storage.save(rel_path, ContentFile(b"%PDF-1.x\n"))

    doc = Document.objects.create(
        file_name="notes.pdf",
        file_path=rel_path,
        status=Document.Status.UPLOADED,
        meeting=meeting,
    )

    process_document_task.apply(args=[doc.pk])

    doc.refresh_from_db()
    assert doc.status == Document.Status.READY

    qs = DocumentChunk.objects.filter(document=doc).order_by("position")
    assert qs.count() >= 1
    sample = qs.first()
    assert sample is not None
    vec = np.asarray(sample.embedding)
    assert vec.shape == (1536,)
