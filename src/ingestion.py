from __future__ import annotations

from pathlib import Path


def read_text(path: str | Path) -> str:
    """Read a supported customer or knowledge-base document into plain text."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix in {".md", ".txt"}:
        return source.read_text(encoding="utf-8")
    if suffix == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(source).paragraphs)
    if suffix == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(source).pages)
    raise ValueError(f"Unsupported file type: {suffix}. Use md, txt, docx, or pdf.")
