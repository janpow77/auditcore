"""Vollständige Schwärzungslogik mit Koordinaten-, Begriffs- und Mustererkennung."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from auditcore_pdf.engine import glyph_text_flags, make_rect, open_pdf
from auditcore_pdf.imagecheck import find_unverifiable_pages
from auditcore_pdf.layers import LayerState, open_with_all_layers, restore_layers
from auditcore_pdf.matching import MatchRule, PatternSpec, TextMatcher, match_span
from auditcore_pdf.models import (
    RedactionBox,
    RedactionFinding,
    RedactionPattern,
    RedactionReport,
    SanitizationPolicy,
)
from auditcore_pdf.sanitize import (
    find_unverifiable_attachments,
    sanitize_annotations,
    sanitize_attachments,
    sanitize_metadata,
)
from auditcore_pdf.structure_clean import sanitize_structure
from auditcore_pdf.verification import verify_redaction

if TYPE_CHECKING:
    from pymupdf import Document, Page, Rect

PDF_ANNOT_REDACT = 12

Word = tuple[float, float, float, float, str]


def _page_words(page: Page) -> list[list[Word]]:
    """Wortlisten der Seite: sichtbarer Text und, falls abweichend, Glyphen unter ActualText."""
    variants = [page.get_text("words")]
    flags = glyph_text_flags("TEXTFLAGS_WORDS")
    if flags is not None:
        glyphs = page.get_text("words", flags=flags)
        if glyphs != variants[0]:
            variants.append(glyphs)
    return [
        [(float(w[0]), float(w[1]), float(w[2]), float(w[3]), str(w[4])) for w in words]
        for words in variants
    ]


def _find_in_words(
    pno: int, words: list[Word], pattern: re.Pattern[str], pattern_name: str | None
) -> list[RedactionFinding]:
    """Findet Fundstellen eines Musters im Wortstrom einer Seite, auch zeilenübergreifend."""
    word_spans: list[tuple[int, int, int]] = []
    cur_pos = 0
    for idx, word in enumerate(words):
        word_spans.append((cur_pos, cur_pos + len(word[4]), idx))
        cur_pos += len(word[4]) + 1
    full_stream = " ".join(word[4] for word in words)

    findings: list[RedactionFinding] = []
    for m in pattern.finditer(full_stream):
        m_start, m_end = match_span(m)
        matched = [
            idx for w_start, w_end, idx in word_spans if max(m_start, w_start) < min(m_end, w_end)
        ]
        source = "multiline" if len(matched) > 1 else "text"
        findings.extend(
            RedactionFinding(pno, words[idx][:4], full_stream[m_start:m_end], pattern_name, source)
            for idx in matched
        )
    return findings


def _find_on_page(page: Page, rules: list[MatchRule]) -> list[RedactionFinding]:
    pno = int(page.number) + 1
    findings = [
        finding
        for words in _page_words(page)
        for rule in rules
        for finding in _find_in_words(pno, words, rule.regex, rule.pattern_name)
    ]
    # Glyphen und ActualText liefern oft dieselben Wörter; doppelte Stellen entfallen.
    return list(dict.fromkeys(findings))


def find_redaction_targets(
    doc: Document,
    terms: list[str] | None = None,
    patterns: list[PatternSpec] | None = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
) -> tuple[list[RedactionFinding], list[int]]:
    """Durchsucht das Dokument nach Begriffen und Mustern über alle Seiten.

    Begriffe werden über Zeilenumbruch und Silbentrennung hinweg gefunden; mit
    ``whole_word`` nur als ganzes Wort. Ohne ``whole_word`` (Standard) wird jedes
    Wort geschwärzt, das den Begriff enthält – das erfasst auch gebeugte Formen
    und Zusammensetzungen („Müllers“, „Müllerstraße“) und lässt keine Wortreste stehen.
    """
    matcher = TextMatcher(terms, patterns, case_sensitive=case_sensitive, whole_word=whole_word)
    findings: list[RedactionFinding] = []
    scanned_pages: list[int] = []
    for idx in range(doc.page_count):
        page = doc[idx]
        if not page.get_text("text").strip() and len(page.get_images()) > 0:
            scanned_pages.append(idx + 1)
        findings.extend(_find_on_page(page, matcher.rules))
    return findings, scanned_pages


def _apply_page_redactions(
    doc: Document,
    findings: list[RedactionFinding],
    fill_color: tuple[float, float, float],
    apply_existing: bool,
) -> list[int]:
    """Wendet die Schwärzungen auf die betroffenen Seiten an."""
    by_page: dict[int, list[Rect]] = {}
    for f in findings:
        by_page.setdefault(f.page_number, []).append(make_rect(*f.rect))

    pages_redacted: list[int] = []
    for idx in range(doc.page_count):
        pno = idx + 1
        page = doc[idx]
        rects_to_apply = by_page.get(pno, [])
        has_existing = any(
            (annot.type[0] if annot.type else -1) == PDF_ANNOT_REDACT
            for annot in page.annots() or []
        )
        if rects_to_apply or (has_existing and apply_existing):
            for r in rects_to_apply:
                page.add_redact_annot(r, fill=fill_color)
            page.apply_redactions()
            pages_redacted.append(pno)
    return pages_redacted


def _merge_explicit_boxes(
    findings: list[RedactionFinding],
    boxes: list[RedactionBox] | None,
) -> list[RedactionFinding]:
    """Fügt explizite Koordinaten-Boxen zu den Fundstellen hinzu."""
    return list(findings) + [
        RedactionFinding(
            page_number=b.page_number,
            rect=b.rect,
            matched_text=b.label or "explicit_box",
            pattern_name="explicit_box",
            source="box",
        )
        for b in boxes or []
    ]


@dataclass
class _Cleanup:
    """Ergebnisse der begleitenden Bereinigung."""

    metadata: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    annotations: int = 0
    structure: list[str] = field(default_factory=list)
    unverifiable_items: list[str] = field(default_factory=list)


def _sanitize(
    doc: Document,
    terms: list[str] | None,
    patterns: list[PatternSpec] | None,
    policy: SanitizationPolicy,
) -> _Cleanup:
    """Bereinigt Metadaten, Anhänge, Anmerkungen und Strukturbereiche."""
    term_list, pattern_list = list(terms or []), list(patterns or [])
    cleanup = _Cleanup(
        metadata=sanitize_metadata(doc, term_list, pattern_list, policy),
        attachments=sanitize_attachments(doc, term_list, pattern_list, policy),
        annotations=sanitize_annotations(doc, term_list, pattern_list, policy),
        structure=sanitize_structure(doc, term_list, pattern_list, policy),
    )
    cleanup.unverifiable_items = [
        f"Anhang '{name}': binär oder komprimiert, Inhalt nicht prüfbar"
        for name in find_unverifiable_attachments(doc)
    ]
    return cleanup


def _verify_output(
    out_bytes: bytes,
    terms: list[str] | None,
    patterns: list[PatternSpec] | None,
    case_sensitive: bool,
    threshold: float,
) -> tuple[bool, str | None]:
    """Nachprüfung als Teilzeichenfolge (strenger als ``whole_word``) samt Prüfbarkeit."""
    result = verify_redaction(
        out_bytes,
        forbidden_terms=terms,
        patterns=patterns,
        case_sensitive=case_sensitive,
        image_coverage_threshold=threshold,
    )
    problems = result.violations + [f"nicht prüfbar: {note}" for note in result.unverifiable]
    return result.fully_verified, "; ".join(problems) or None


def _open_for_redaction(pdf_bytes: bytes, reveal: bool) -> tuple[Document, LayerState | None]:
    if reveal:
        return open_with_all_layers(pdf_bytes)
    return open_pdf(pdf_bytes), None


def redact_document(
    pdf_bytes: bytes,
    boxes: list[RedactionBox] | None = None,
    terms: list[str] | None = None,
    patterns: list[str | RedactionPattern] | None = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
    policy: SanitizationPolicy | None = None,
    fill_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    verify: bool = True,
) -> tuple[bytes, RedactionReport]:
    """Führt eine vollständige und überprüfbare Schwärzung eines PDF-Dokuments durch.

    Ausgeblendete Ebenen werden für Suche und Schwärzung eingeblendet und danach
    wieder ausgeblendet (``policy.redact_hidden_layers``). Seiten mit nicht
    prüfbarem Bildinhalt stehen in ``unverifiable_pages``; ``verified`` ist dann
    ``False``.
    """
    policy = policy or SanitizationPolicy()
    doc, layers = _open_for_redaction(pdf_bytes, policy.redact_hidden_layers)
    try:
        findings, scanned_pages = find_redaction_targets(
            doc, terms, patterns, case_sensitive=case_sensitive, whole_word=whole_word
        )
        all_findings = _merge_explicit_boxes(findings, boxes)
        pages_redacted = _apply_page_redactions(
            doc, all_findings, fill_color, policy.apply_existing_redactions
        )
        if layers is not None:
            restore_layers(doc, layers)
        unverifiable = find_unverifiable_pages(doc, policy.image_coverage_threshold)
        cleanup = _sanitize(doc, terms, patterns, policy)
        out_bytes = bytes(doc.tobytes(garbage=3, deflate=True, clean=True))
        verified, error = (
            _verify_output(
                out_bytes, terms, patterns, case_sensitive, policy.image_coverage_threshold
            )
            if verify
            else (False, None)
        )
        report = RedactionReport(
            success=True,
            findings_count=len(all_findings),
            findings=all_findings,
            pages_redacted=pages_redacted,
            metadata_fields_cleaned=cleanup.metadata,
            attachments_removed=cleanup.attachments,
            annotations_removed=cleanup.annotations,
            scanned_pages_without_ocr=scanned_pages,
            verified=verified,
            verification_error=error,
            structure_cleaned=cleanup.structure,
            unverifiable_pages=sorted(unverifiable),
            unverifiable_items=cleanup.unverifiable_items,
        )
        return out_bytes, report
    finally:
        doc.close()
