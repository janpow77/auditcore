"""Schwärzen im Dokument: versteckte Ablagen, Seitenbereiche, Formulardaten."""

from __future__ import annotations

from typing import TYPE_CHECKING

from auditcore_pdf.engine import fitz
from auditcore_pdf.redaction.layers import _expose_full_page, _restore_layers, _ViewTransform
from auditcore_pdf.redaction.plan import Candidate
from auditcore_pdf.redaction.scrub import _remove_hidden
from auditcore_pdf.redaction.selection import Area

if TYPE_CHECKING:
    from pymupdf import Document, Page, Rect


def _remove_hidden_candidates(doc: Document, hidden: list[Candidate]) -> None:
    """Versteckte Inhalte zuerst — danach ändern sich Kennungen der Seitenobjekte."""
    by_ref: dict[str, list[Candidate]] = {}
    for cand in hidden:
        by_ref.setdefault(repr(sorted(cand.ref.items())), []).append(cand)
    for cands in by_ref.values():
        _remove_hidden(doc, cands)


def _page_boxes(
    chosen: list[Candidate], areas: tuple[Area, ...], transforms: list[_ViewTransform]
) -> dict[int, list[Rect]]:
    """Schwärzungsrechtecke je Seite: erst Fundstellen, dann eigene Bereiche."""
    boxes: dict[int, list[Rect]] = {}
    for cand in chosen:
        if cand.kind == "text" and cand.page:
            boxes.setdefault(cand.page - 1, []).extend(fitz.Rect(r) for r in cand.rects)
    area_boxes: dict[int, list[Rect]] = {}
    for area in areas:
        area_boxes.setdefault(area.page - 1, []).append(
            transforms[area.page - 1].from_view(list(area.box))
        )
    return {
        pno: boxes.get(pno, []) + area_boxes.get(pno, [])
        for pno in sorted(set(boxes) | set(area_boxes))
    }


def _remove_overlays(page: Page, rects: list[Rect]) -> int:
    """Formularfelder und Kommentare bringen eigene Darstellungen mit,
    die apply_redactions nicht ändert. Liegen sie unter einer
    Schwärzung, werden sie entfernt."""
    removed = 0
    for widget in list(page.widgets() or []):
        if any(widget.rect.intersects(r) for r in rects):
            page.delete_widget(widget)
            removed += 1
    for annot in list(page.annots() or []):
        if any(annot.rect.intersects(r) for r in rects):
            page.delete_annot(annot)
            removed += 1
    return removed


def _redact_pages(doc: Document, page_boxes: dict[int, list[Rect]]) -> int:
    """Rechtecke schwärzen; Rückgabe: Zahl entfernter Felder und Kommentare."""
    removed = 0
    for pno, rects in page_boxes.items():
        page = doc[pno]
        # Den gespeicherten Wert sichern: Eine CropBox, die über die MediaBox
        # hinausragt, ist zulässig, lässt sich mit set_cropbox aber nicht
        # zurückschreiben.
        saved_crop = [(page.xref, "CropBox", *doc.xref_get_key(page.xref, "CropBox"))]
        original_crop = _expose_full_page(page)
        removed += _remove_overlays(page, rects)
        for rect in rects:
            page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS)
        if original_crop is not None:
            _restore_layers(doc, saved_crop)
    return removed


def _drop_xfa(doc: Document) -> int:
    """XFA-Formulardaten sind eine zweite, unabhängige Kopie der Feldinhalte.
    Wie Acrobat beim Schwärzen: immer entfernen, es bleibt das AcroForm."""
    cat = doc.pdf_catalog()
    if doc.xref_get_key(cat, "AcroForm/XFA")[0] != "null":
        doc.xref_set_key(cat, "AcroForm/XFA", "null")
        return 1
    return 0
