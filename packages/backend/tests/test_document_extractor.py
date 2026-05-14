"""Unit tests for ``extract_document_text`` (Step 5.1)."""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfWriter

from app.services.documents.extractor import extract_document_text


def test_extract_pdf_prefers_pdfplumber_or_pypdf(tmp_path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    path = tmp_path / "blank.pdf"
    path.write_bytes(buf.getvalue())
    # Blank page → typically no text; must not raise
    assert extract_document_text(path, "blank.pdf") == ""


def test_extract_docx_from_minimal_ooxml(tmp_path: Path) -> None:
    import zipfile

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Hello DOCX</w:t></w:r></w:p></w:body></w:document>"
    )
    path = tmp_path / "sample.docx"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
        zf.writestr("[Content_Types].xml", b"dummy")
    assert "Hello DOCX" in extract_document_text(path, "sample.docx")
