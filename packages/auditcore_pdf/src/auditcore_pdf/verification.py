"""Unabhängige Nachprüfung und Verifikation von Schwärzungsergebnissen."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from auditcore_pdf.engine import glyph_text_flags
from auditcore_pdf.imagecheck import find_unverifiable_pages
from auditcore_pdf.layers import open_with_all_layers
from auditcore_pdf.matching import PatternSpec, TextMatcher
from auditcore_pdf.models import DEFAULT_IMAGE_COVERAGE_THRESHOLD, VerificationResult
from auditcore_pdf.sanitize import find_unverifiable_attachments
from auditcore_pdf.structure import collect_structure_texts

if TYPE_CHECKING:
    from pymupdf import Document, Page

#: Geprüfte Bereiche in ``VerificationResult.details``
CHECKED_AREAS = (
    "metadata_checked",
    "attachments_checked",
    "annotations_checked",
    "outline_checked",
    "form_fields_checked",
    "links_checked",
    "named_destinations_checked",
    "page_labels_checked",
    "optional_content_checked",
    "alt_texts_checked",
    "javascript_checked",
)


def page_text(page: Page) -> str:
    """Seitentext einschließlich der Glyphen, die ein ActualText überdeckt."""
    text = str(page.get_text("text"))
    flags = glyph_text_flags("TEXTFLAGS_TEXT")
    if flags is not None:
        text += "\n" + str(page.get_text("text", flags=flags))
    return text


def _check_pages(doc: Document, matcher: TextMatcher, violations: list[str]) -> None:
    """Überprüft den Text und die Anmerkungen aller Seiten."""
    for idx in range(doc.page_count):
        pno = idx + 1
        page = doc[idx]
        violations.extend(matcher.violations(page_text(page), f"Seite {pno} (Text)"))
        for annot in page.annots() or []:
            info = annot.info or {}
            for k in ("content", "subject", "title"):
                val = str(info.get(k, "") or "")
                violations.extend(matcher.violations(val, f"Seite {pno} (Anmerkung {k})"))


def _check_metadata(doc: Document, matcher: TextMatcher, violations: list[str]) -> None:
    """Überprüft die Standard- und XMP-Metadaten."""
    for k, v in (doc.metadata or {}).items():
        if v:
            violations.extend(matcher.violations(str(v), f"Metadaten-Feld '{k}'"))
    with contextlib.suppress(Exception):
        xmp = doc.get_xml_metadata()
        violations.extend(matcher.violations(xmp or "", "XMP-Metadatenstrom"))


def _check_attachments(doc: Document, matcher: TextMatcher, violations: list[str]) -> None:
    """Überprüft eingebettete Anhänge auf verbotene Inhalte."""
    with contextlib.suppress(Exception):
        for name in doc.embfile_names():
            violations.extend(matcher.violations(name, f"Anhangsname '{name}'"))
            with contextlib.suppress(Exception):
                text_sample = bytes(doc.embfile_get(name)).decode("utf-8", errors="ignore")
                hint = f"Anhangsinhalt '{name}'"
                violations.extend(matcher.violations(text_sample, hint))


def _check_structure(doc: Document, matcher: TextMatcher, violations: list[str]) -> None:
    """Überprüft Lesezeichen, Formulare, Ziele, Ebenen, Alt-Texte und Skripte."""
    for item in collect_structure_texts(doc):
        violations.extend(matcher.violations(item.text, item.location))


def _unverifiable(doc: Document, threshold: float) -> tuple[list[int], list[str]]:
    pages = find_unverifiable_pages(doc, threshold)
    notes = [f"Seite {pno}: {reason}" for pno, reason in sorted(pages.items())]
    notes.extend(
        f"Anhang '{name}': binär oder komprimiert, Inhalt nicht prüfbar"
        for name in find_unverifiable_attachments(doc)
    )
    return sorted(pages), notes


def verify_redaction(
    pdf_bytes: bytes,
    forbidden_terms: list[str] | None = None,
    patterns: list[PatternSpec] | None = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
    image_coverage_threshold: float = DEFAULT_IMAGE_COVERAGE_THRESHOLD,
) -> VerificationResult:
    """Prüft ein PDF unabhängig auf das Vorhandensein verbotener Begriffe und Muster.

    Geprüft werden Seitentext (auch ausgeblendete Ebenen und von ActualText
    überdeckte Glyphen), Anmerkungen, Metadaten, XMP, Anhänge sowie Lesezeichen,
    Formularfelder, Verknüpfungen, benannte Ziele, Seitenbeschriftungen,
    Ebenennamen, Alternativtexte und JavaScript. Begriffe werden auch über
    Zeilenumbruch und Silbentrennung erkannt; ``whole_word`` beschränkt sie auf
    ganze Wörter. Bildinhalte und binäre Anhänge sind ohne OCR bzw. Dekodierung
    nicht prüfbar und stehen in ``unverifiable``.
    """
    matcher = TextMatcher(
        forbidden_terms, patterns, case_sensitive=case_sensitive, whole_word=whole_word
    )
    if not matcher:
        return VerificationResult(clean=True, violations=[], details={"checked_pages": 0})

    violations: list[str] = []
    doc, layers = open_with_all_layers(pdf_bytes)
    try:
        _check_pages(doc, matcher, violations)
        _check_metadata(doc, matcher, violations)
        _check_attachments(doc, matcher, violations)
        _check_structure(doc, matcher, violations)
        pages, notes = _unverifiable(doc, image_coverage_threshold)

        details: dict[str, object] = {"pages_checked": doc.page_count}
        details.update(dict.fromkeys(CHECKED_AREAS, True))
        details["hidden_layers_revealed"] = layers is not None
        details["glyphs_under_actualtext_checked"] = glyph_text_flags("TEXTFLAGS_TEXT") is not None

        return VerificationResult(
            clean=len(violations) == 0,
            violations=violations,
            details=details,
            unverifiable=notes,
            unverifiable_pages=pages,
        )
    finally:
        doc.close()
