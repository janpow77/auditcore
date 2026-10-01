"""Sicherer Zugriffspunkt auf das PDF-Backend."""

from __future__ import annotations

import types

try:
    import pymupdf as fitz
    from pymupdf import Document

    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz  # type: ignore[no-redef]
        from fitz import Document  # type: ignore[no-redef]

        PYMUPDF_AVAILABLE = True
    except ImportError:
        fitz = types.ModuleType("fitz")
        Document = object  # type: ignore[assignment,misc]
        PYMUPDF_AVAILABLE = False


#: Maximale Seitenzahl zur Verhinderung von Ressourcen-Überlastung
MAX_PAGES = 5000


def is_pymupdf_available() -> bool:
    """Gibt zurück, ob PyMuPDF auf dem System zur Verfügung steht."""
    return PYMUPDF_AVAILABLE


def open_pdf(content: bytes) -> Document:
    """Öffnet ein PDF-Dokument sicher aus einem Byte-Puffer im Arbeitsspeicher."""
    if not PYMUPDF_AVAILABLE:
        msg = "PyMuPDF ist nicht verfügbar. Bitte auditcore_pdf[pymupdf] installieren."
        raise RuntimeError(msg)
    if not content:
        raise ValueError("PDF-Inhalt darf nicht leer sein.")
    doc = fitz.open(stream=content, filetype="pdf")
    if doc.page_count > MAX_PAGES:
        count = doc.page_count
        doc.close()
        raise ValueError(
            f"Dokument hat {count} Seiten – zulässig sind höchstens {MAX_PAGES} Seiten."
        )
    return doc
