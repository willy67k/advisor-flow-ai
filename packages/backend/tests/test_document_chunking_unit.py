"""Semantic chunk splitter — Step 5.2."""

from types import SimpleNamespace

import pytest

from app.services.documents.chunking import chunk_text_semantic
from app.services.documents.embeddings import embed_texts_batch


def test_chunk_text_empty():
    assert chunk_text_semantic("") == []
    assert chunk_text_semantic("   ") == []


def test_chunk_splits_long_sections():
    text = "\n\n".join(f"SECTION_{i}\n" + ("word " * 400) for i in range(4))
    chunks = chunk_text_semantic(text)
    assert len(chunks) >= 2
    assert any("SECTION_0" in c for c in chunks)


def test_embed_batch_requires_openai_key(monkeypatch):
    monkeypatch.setattr(
        "app.services.documents.embeddings.get_env",
        lambda: SimpleNamespace(
            openai_api_key=None,
            openai_embedding_model="text-embedding-3-small",
        ),
    )
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        embed_texts_batch(["hello"])
