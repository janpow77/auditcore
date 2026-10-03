"""Sicherer Zugriffspunkt auf das PDF-Backend."""

from __future__ import annotations

import types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # mypy sieht nur die maßgebliche Engine; die Laufzeit-Rückfälle unten bleiben
    # damit frei von ``type: ignore`` – mit und ohne installiertes PyMuPDF.
    import pymupdf as fitz
    from pymupdf import Document, Matrix, Rect

    PYMUPDF_AVAILABLE: bool
else:
    try:
        import pymupdf as fitz
        from pymupdf import Document

        PYMUPDF_AVAILABLE = True
    except ImportError:
        try:
            import fitz
            from fitz import Document

            PYMUPDF_AVAILABLE = True
        except ImportError:
            fitz = types.ModuleType("fitz")
            Document = object
            PYMUPDF_AVAILABLE = False


#: Maximale Seitenzahl zur Verhinderung von Ressourcen-Überlastung
MAX_PAGES = 5000


def is_pymupdf_available() -> bool:
    """Gibt zurück, ob PyMuPDF auf dem System zur Verfügung steht."""
    return PYMUPDF_AVAILABLE


def _require_engine() -> None:
    """Bricht mit einem klaren Hinweis ab, wenn PyMuPDF fehlt."""
    if not PYMUPDF_AVAILABLE:
        msg = "PyMuPDF ist nicht verfügbar. Bitte auditcore_pdf[pymupdf] installieren."
        raise RuntimeError(msg)


def new_pdf() -> Document:
    """Legt ein leeres PDF-Dokument an (Zusammenführen und Aufteilen)."""
    _require_engine()
    return fitz.open()


def make_rect(x0: float, y0: float, x1: float, y1: float) -> Rect:
    """Erzeugt ein Rechteck der PDF-Engine aus Seitenkoordinaten."""
    _require_engine()
    return fitz.Rect(x0, y0, x1, y1)


def make_matrix(zoom_x: float, zoom_y: float) -> Matrix:
    """Erzeugt eine Skalierungsmatrix der PDF-Engine."""
    _require_engine()
    return fitz.Matrix(zoom_x, zoom_y)


def open_pdf(content: bytes) -> Document:
    """Öffnet ein PDF-Dokument sicher aus einem Byte-Puffer im Arbeitsspeicher."""
    _require_engine()
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
