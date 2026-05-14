"""Document processing (extractors, RAG prep)."""

from app.services.documents.chunking import chunk_text_semantic
from app.services.documents.embeddings import embed_texts_batch
from app.services.documents.extractor import extract_document_text

__all__ = ["chunk_text_semantic", "embed_texts_batch", "extract_document_text"]
