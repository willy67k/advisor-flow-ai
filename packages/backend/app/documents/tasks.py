"""Async document processing — Step 5.1 text extraction."""

from __future__ import annotations

from pathlib import Path

from django.core.files.storage import default_storage

from app.models.document import Document
from app.services.documents.extractor import extract_document_text
from app.worker import celery_app


@celery_app.task(bind=True, store_eager_result=True)
def process_document_task(self, document_id: int) -> dict[str, object]:
    """Read stored file, extract plain text, mark document ``ready``."""
    doc = Document.objects.filter(pk=int(document_id)).first()
    if doc is None:
        return {"ok": False, "error": "document_not_found"}

    Document.objects.filter(pk=doc.pk).update(status=Document.Status.PROCESSING)
    path = Path(default_storage.path(doc.file_path))
    text = extract_document_text(path, doc.file_name)
    Document.objects.filter(pk=doc.pk).update(
        extracted_text=text,
        status=Document.Status.READY,
    )
    return {"ok": True, "document_id": int(doc.pk), "chars": len(text)}
