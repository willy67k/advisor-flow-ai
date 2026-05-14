"""Plain-text extraction for uploaded documents (Step 5.1) — ``pdfplumber`` + ``pypdf`` for PDF."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path


def _extract_pdf_text(path: Path) -> str:
    """Prefer ``pdfplumber`` (layout-aware); fall back to ``pypdf`` if empty or unreadable."""
    chunks: list[str] = []

    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    chunks.append(t)
    except Exception:
        chunks.clear()

    joined = "\n".join(chunks).strip()
    if joined:
        return joined

    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                chunks.append(t)
    except Exception:
        return ""

    return "\n".join(chunks).strip()


def _extract_docx_text(path: Path) -> str:
    """Lightweight .docx body text via OOXML zip (no extra deps)."""
    try:
        with zipfile.ZipFile(path) as zf:
            data = zf.read("word/document.xml").decode("utf-8", errors="replace")
    except (KeyError, OSError, zipfile.BadZipFile, ValueError):
        return ""
    text = re.sub(r"<[^>]+>", " ", data)
    return re.sub(r"\s+", " ", text).strip()


def extract_document_text(path: Path, file_name: str) -> str:
    """Dispatch by suffix; unsupported legacy ``.doc`` returns empty string."""
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix == ".docx":
        return _extract_docx_text(path)
    return ""
