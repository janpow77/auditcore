"""Einheitlicher Einstieg zum Lesen von DOCX/DOCM/PDF in Vergleichseinheiten."""

from __future__ import annotations

from pathlib import Path

from auditcore_documents.errors import ParseError
from auditcore_documents.limits import DEFAULT_LIMITS, ReadLimits
from auditcore_documents.model import CompareItem
from auditcore_documents.ooxml import (
    accept_revisions,
    checklist_items,
    detect_docx_mode,
    docx_paragraphs,
    read_ooxml,
)
from auditcore_documents.pdftext import (
    OcrCallback,
    PageSource,
    pdf_paragraphs,
    text_items_from_paragraphs,
)

ALLOWED_EXTENSIONS = frozenset({".docx", ".docm", ".pdf"})
MODES = frozenset({"checklist", "text"})


def detect_mode(path: Path, *, limits: ReadLimits = DEFAULT_LIMITS) -> str:
    """PDF ist immer Fließtext; DOCX nach Tabellenzeilen- und Absatzzahl."""
    if path.suffix.casefold() == ".pdf":
        return "text"
    return detect_docx_mode(read_ooxml(path, limits))


def _check_input(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ParseError(f"Nicht unterstütztes Format: {path.suffix or 'unbekannt'}")
    if not path.is_file():
        raise ParseError(f"Datei nicht gefunden: {path.name}")
    return suffix


def read_text_paragraphs(
    path: Path,
    *,
    ocr_callback: OcrCallback | None = None,
    page_source: PageSource | None = None,
    limits: ReadLimits = DEFAULT_LIMITS,
) -> list[tuple[str, bool]]:
    """Alle sichtbaren Absätze mit Überschriftenkennzeichen (Fließtextsicht)."""
    suffix = _check_input(path)
    if suffix == ".pdf":
        return pdf_paragraphs(
            path, page_source=page_source, ocr_callback=ocr_callback, limits=limits
        )
    root = read_ooxml(path, limits)
    accept_revisions(root)
    return docx_paragraphs(root)


def read_document(
    path: Path,
    mode: str = "auto",
    *,
    ocr_callback: OcrCallback | None = None,
    page_source: PageSource | None = None,
    limits: ReadLimits = DEFAULT_LIMITS,
) -> tuple[str, list[CompareItem]]:
    """Dokument lesen; liefert erkannte Dokumentart und Vergleichseinheiten.

    Entspricht ``read_document`` des Originals einschließlich Fehlertexten.
    PDF ist stets Fließtext; ``mode`` wird dort nicht ausgewertet.
    """
    suffix = _check_input(path)
    if suffix == ".pdf":
        items = text_items_from_paragraphs(
            pdf_paragraphs(path, page_source=page_source, ocr_callback=ocr_callback, limits=limits)
        )
        if not items:
            raise ParseError(f"In {path.name} wurden keine vergleichbaren Textstellen gefunden.")
        return "text", items
    resolved_mode = detect_mode(path, limits=limits) if mode == "auto" else mode
    if resolved_mode not in MODES:
        raise ParseError(f"Unbekannte Dokumentart: {resolved_mode}")
    root = read_ooxml(path, limits)
    accept_revisions(root)
    items = (
        checklist_items(root)
        if resolved_mode == "checklist"
        else text_items_from_paragraphs(docx_paragraphs(root))
    )
    if not items:
        raise ParseError(
            f"In {path.name} wurden keine vergleichbaren "
            f"{'Prüffragen' if resolved_mode == 'checklist' else 'Textstellen'} gefunden."
        )
    return resolved_mode, items
