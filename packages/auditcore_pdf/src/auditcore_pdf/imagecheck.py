"""Erkennung von Seiten, deren Bildinhalt ohne OCR nicht prüfbar ist.

Text in Bildern (Scans, eingefügte Bildausschnitte) wird weder geschwärzt noch von
der Nachprüfung erkannt. Statt solche Seiten still als geprüft zu behandeln, werden
sie mit Grund gemeldet. Eine OCR findet bewusst nicht statt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from auditcore_pdf.engine import make_rect

if TYPE_CHECKING:
    from pymupdf import Document, Page, Rect


def _check_threshold(threshold: float) -> None:
    if not 0.0 < threshold <= 1.0:
        raise ValueError("Der Schwellenwert für den Bildanteil muss in (0, 1] liegen.")


def _image_rects(page: Page) -> list[Rect]:
    """Sichtbare Bildflächen der Seite, auf den Seitenbereich beschnitten."""
    rects: list[Rect] = []
    for info in page.get_image_info():
        rect = make_rect(*info["bbox"]) & page.rect
        if not rect.is_empty:
            rects.append(rect)
    return rects


def _text_rects(page: Page) -> list[Rect]:
    """Flächen der Textblöcke (Blocktyp 0) der Seite."""
    return [make_rect(*block[:4]) for block in page.get_text("blocks") if block[6] == 0]


def page_image_reason(page: Page, threshold: float) -> str | None:
    """Grund, warum der Bildinhalt der Seite nicht prüfbar ist, sonst ``None``.

    Gemeldet werden Seiten ohne Textebene mit Bild, Seiten, deren Bilder zusammen
    mindestens ``threshold`` der Seitenfläche bedecken (Überlappungen zählen mehrfach,
    also eher zu viel als zu wenig), und Seiten, auf denen ein Bild einen Textblock
    überdeckt oder hinterlegt.
    """
    images = _image_rects(page)
    if not images:
        return None
    texts = _text_rects(page)
    if not texts:
        return "keine Textebene, Bildinhalt ohne OCR nicht prüfbar"
    share = sum(rect.get_area() for rect in images) / page.rect.get_area()
    if share >= threshold:
        return f"Bildanteil {share:.0%} ab Schwelle {threshold:.0%}, Bildinhalt nicht prüfbar"
    if any(image.intersects(text) for image in images for text in texts):
        return "Bild überdeckt Textbereich, Bildinhalt nicht prüfbar"
    return None


def find_unverifiable_pages(doc: Document, threshold: float) -> dict[int, str]:
    """1-basierte Seitennummern mit Grund für alle Seiten mit nicht prüfbarem Bildinhalt."""
    _check_threshold(threshold)
    reasons: dict[int, str] = {}
    for index in range(doc.page_count):
        reason = page_image_reason(doc[index], threshold)
        if reason is not None:
            reasons[index + 1] = reason
    return reasons
