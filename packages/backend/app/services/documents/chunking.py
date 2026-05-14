"""Split document text into overlapping chunks suitable for embeddings (Step 5.2)."""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

# ~250-350 tokens typical; overlaps preserve sentence boundaries via separators.
_CHUNK_SIZE = 1200
_CHUNK_OVERLAP = 200


def chunk_text_semantic(text: str) -> list[str]:
    """Paragraph-aware recursive split (structure-first, no extra embedding calls)."""
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )
    parts = splitter.split_text(cleaned)
    return [p.strip() for p in parts if p.strip()]
