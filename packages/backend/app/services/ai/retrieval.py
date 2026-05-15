"""Vector similarity search + retrieved-context assembly — Step 5.3."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from django.db.models import QuerySet
from pgvector.django import CosineDistance

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.documents.embeddings import embed_texts_batch

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 8
DEFAULT_MAX_CHARS = 12_000
_QUERY_CHAR_CAP = 8_192


def _truncate(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    return t[:max_chars]


def fallback_query_text_for_meeting_documents(meeting_id: int) -> str:
    """Embedding query when the advisor left meeting notes blank but uploaded PDFs are READY."""
    doc = (
        Document.objects.filter(meeting_id=int(meeting_id), status=Document.Status.READY)
        .exclude(extracted_text__exact="")
        .order_by("id")
        .first()
    )
    if doc is not None:
        return _truncate(str(doc.extracted_text), _QUERY_CHAR_CAP)
    chunk = (
        DocumentChunk.objects.filter(
            document__meeting_id=int(meeting_id),
            document__status=Document.Status.READY,
        )
        .order_by("id")
        .first()
    )
    if chunk is not None:
        return _truncate(chunk.content, _QUERY_CHAR_CAP)
    return ""


def assemble_retrieved_context(
    chunks: Iterable[DocumentChunk],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Format ranked chunks into a single block for prompting (truncated by ``max_chars``)."""
    parts: list[str] = []
    used = 0
    for idx, chunk in enumerate(chunks, start=1):
        doc_label = getattr(chunk.document, "file_name", None) or "document"
        header = f"--- Source file: {doc_label} (excerpt {idx}) ---"
        body = chunk.content.strip()
        segment = f"{header}\n{body}"
        if used + len(segment) + 2 > max_chars:
            if not parts:
                remain = max(0, max_chars - len(header) - 1)
                if remain > 0:
                    parts.append(f"{header}\n{body[:remain]}")
            break
        parts.append(segment)
        used += len(segment) + 2
    return "\n\n".join(parts)


def search_similar_chunks(
    *,
    meeting_id: int,
    query_embedding: list[float],
    top_k: int = DEFAULT_TOP_K,
) -> list[DocumentChunk]:
    """Cosine nearest neighbors among ``READY`` document chunks attached to ``meeting_id``."""
    qs: QuerySet[DocumentChunk] = (
        DocumentChunk.objects.filter(
            document__meeting_id=int(meeting_id),
            document__status=Document.Status.READY,
        )
        .select_related("document")
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[: int(top_k)]
    )
    return list(qs)


def retrieve_context_for_meeting_notes(
    *,
    meeting_id: int,
    query_text: str,
    top_k: int = DEFAULT_TOP_K,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Embed ``query_text`` as the query vector when non-empty; if notes are blank but the meeting has
    READY documents, derive query text from ``extracted_text`` or the first chunk so upload-only
    workflows still retrieve context.

    Returns empty string when there is nothing indexed, no embedding key, or on recoverable DB errors.
    """
    query = _truncate(query_text, _QUERY_CHAR_CAP).strip()
    if not query:
        query = _truncate(
            fallback_query_text_for_meeting_documents(meeting_id), _QUERY_CHAR_CAP
        ).strip()
    if not query:
        return ""

    if not DocumentChunk.objects.filter(
        document__meeting_id=int(meeting_id),
        document__status=Document.Status.READY,
    ).exists():
        logger.debug(
            "RAG retrieval skipped — no READY chunks for meeting_id=%s",
            meeting_id,
        )
        return ""

    try:
        vectors = embed_texts_batch([query])
        if not vectors:
            return ""
        rows = search_similar_chunks(
            meeting_id=int(meeting_id),
            query_embedding=vectors[0],
            top_k=top_k,
        )
        if not rows:
            return ""
        return assemble_retrieved_context(rows, max_chars=max_chars)
    except Exception:
        logger.exception("RAG retrieval failed for meeting_id=%s", meeting_id)
        return ""


__all__ = [
    "assemble_retrieved_context",
    "fallback_query_text_for_meeting_documents",
    "retrieve_context_for_meeting_notes",
    "search_similar_chunks",
]
