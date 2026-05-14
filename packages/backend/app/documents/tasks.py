"""Async document processing — Step 5.1 extraction + Step 5.2 chunking / embeddings."""

from __future__ import annotations

from pathlib import Path

from django.core.files.storage import default_storage
from django.db import transaction

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.documents.chunking import chunk_text_semantic
from app.services.documents.embeddings import embed_texts_batch
from app.services.documents.extractor import extract_document_text
from app.worker import celery_app


def _persist_chunks_and_embeddings(doc: Document, text: str) -> int:
    """Replace existing chunks with fresh splits + embeddings. Returns chunk count."""
    DocumentChunk.objects.filter(document_id=doc.pk).delete()
    pieces = chunk_text_semantic(text)
    if not pieces:
        return 0
    vectors = embed_texts_batch(pieces)
    if len(vectors) != len(pieces):
        msg = "Embedding count mismatch for document chunks"
        raise RuntimeError(msg)
    bulk = [
        DocumentChunk(document_id=int(doc.pk), content=c, position=i, embedding=v)
        for i, (c, v) in enumerate(zip(pieces, vectors, strict=True))
    ]
    DocumentChunk.objects.bulk_create(bulk)
    return len(bulk)


@celery_app.task(bind=True, store_eager_result=True)
def process_document_task(self, document_id: int) -> dict[str, object]:
    """Extract text, write chunks + pgvector embeddings, mark document ``ready``."""
    doc = Document.objects.filter(pk=int(document_id)).first()
    if doc is None:
        return {"ok": False, "error": "document_not_found"}

    Document.objects.filter(pk=doc.pk).update(status=Document.Status.PROCESSING)
    path = Path(default_storage.path(doc.file_path))
    text = extract_document_text(path, doc.file_name)
    chunk_count = 0
    with transaction.atomic():
        Document.objects.filter(pk=doc.pk).update(extracted_text=text)
        chunk_count = _persist_chunks_and_embeddings(doc, text)
        Document.objects.filter(pk=doc.pk).update(status=Document.Status.READY)
    return {
        "ok": True,
        "document_id": int(doc.pk),
        "chars": len(text),
        "chunks": chunk_count,
    }
