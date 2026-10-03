"""Vollständige Schwärzungslogik mit Koordinaten-, Begriffs- und Mustererkennung."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from auditcore_pdf.engine import make_rect, open_pdf
from auditcore_pdf.models import (
    STANDARD_PATTERNS,
    RedactionBox,
    RedactionFinding,
    RedactionPattern,
    RedactionReport,
    SanitizationPolicy,
)
from auditcore_pdf.sanitize import (
    sanitize_annotations,
    sanitize_attachments,
    sanitize_metadata,
)
from auditcore_pdf.verification import verify_redaction

if TYPE_CHECKING:
    from pymupdf import Document, Page, Rect

PDF_ANNOT_REDACT = 12


def _find_phrase_matches_on_page(
    page: Page,
    pattern: re.Pattern[str],
    pattern_name: str | None = None,
) -> list[RedactionFinding]:
    """Findet Fundstellen eines Musters auf einer Seite, auch zeilenübergreifend."""
    findings: list[RedactionFinding] = []
    pno = int(page.number) + 1
    raw_words = page.get_text("words")
    if not raw_words:
        return findings

    # Wortstrom aufbauen und Zeichenpositionen auf Wortindizes abbilden
    stream_parts: list[str] = []
    word_spans: list[tuple[int, int, int]] = []
    cur_pos = 0

    for idx, w in enumerate(raw_words):
        w_text = str(w[4])
        start = cur_pos
        end = start + len(w_text)
        word_spans.append((start, end, idx))
        stream_parts.append(w_text)
        cur_pos = end + 1

    full_stream = " ".join(stream_parts)

    for m in pattern.finditer(full_stream):
        m_start, m_end = m.span()
        matched_text = m.group(0)

        # Überlappende Wörter identifizieren
        matched_indices = [
            idx for w_start, w_end, idx in word_spans if max(m_start, w_start) < min(m_end, w_end)
        ]

        if not matched_indices:
            continue

        is_multi = len(matched_indices) > 1
        for idx in matched_indices:
            mw = raw_words[idx]
            rect = (float(mw[0]), float(mw[1]), float(mw[2]), float(mw[3]))
            findings.append(
                RedactionFinding(
                    page_number=pno,
                    rect=rect,
                    matched_text=matched_text,
                    pattern_name=pattern_name,
                    source="multiline" if is_multi else "text",
                )
            )

    return findings


def _compile_search_patterns(
    terms: list[str] | None,
    patterns: list[str | RedactionPattern] | None,
    case_sensitive: bool,
    whole_word: bool,
) -> list[tuple[re.Pattern[str], str | None]]:
    """Kompiliert Suchbegriffe und Muster in reguläre Ausdrücke."""
    compiled: list[tuple[re.Pattern[str], str | None]] = []
    flags = 0 if case_sensitive else re.IGNORECASE

    for term in terms or []:
        if not term:
            continue
        escaped_parts = [re.escape(part) for part in term.split()]
        joined = r"\s+".join(escaped_parts)
        if whole_word:
            joined = rf"\b{joined}\b"
        compiled.append((re.compile(joined, flags), None))

    for pat in patterns or []:
        if isinstance(pat, str):
            std = STANDARD_PATTERNS.get(pat)
            regex_str = std.regex if std is not None else pat
            p_name = std.name if std is not None else pat
            compiled.append((re.compile(regex_str, flags), p_name))
        elif isinstance(pat, RedactionPattern):
            compiled.append((re.compile(pat.regex, flags), pat.name))

    return compiled


def find_redaction_targets(
    doc: Document,
    terms: list[str] | None = None,
    patterns: list[str | RedactionPattern] | None = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
) -> tuple[list[RedactionFinding], list[int]]:
    """Durchsucht das Dokument nach Begriffen und Mustern über alle Seiten."""
    findings: list[RedactionFinding] = []
    scanned_pages: list[int] = []

    compiled = _compile_search_patterns(terms, patterns, case_sensitive, whole_word)

    for idx in range(doc.page_count):
        pno = idx + 1
        page = doc[idx]
        text = page.get_text("text").strip()
        images = page.get_images()

        if not text and len(images) > 0:
            scanned_pages.append(pno)

        for regex, p_name in compiled:
            findings.extend(_find_phrase_matches_on_page(page, regex, p_name))

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
        r = make_rect(*f.rect)
        by_page.setdefault(f.page_number, []).append(r)

    pages_redacted: list[int] = []

    for idx in range(doc.page_count):
        pno = idx + 1
        page = doc[idx]
        rects_to_apply = by_page.get(pno, [])

        has_existing = False
        for annot in page.annots() or []:
            ann_type = annot.type[0] if annot.type else -1
            if ann_type == PDF_ANNOT_REDACT:
                has_existing = True
                break

        if rects_to_apply or (has_existing and apply_existing):
            for r in rects_to_apply:
                page.add_redact_annot(r, fill=fill_color)
            page.apply_redactions()
            pages_redacted.append(pno)

    return pages_redacted


def _collect_pattern_strings(
    patterns: list[str | RedactionPattern] | None,
) -> list[str]:
    """Extrahiert die Regex-Muster als Zeichenketten."""
    result: list[str] = []
    for p in patterns or []:
        if isinstance(p, str):
            std = STANDARD_PATTERNS.get(p)
            result.append(std.regex if std else p)
        elif isinstance(p, RedactionPattern):
            result.append(p.regex)
    return result


def _merge_explicit_boxes(
    findings: list[RedactionFinding],
    boxes: list[RedactionBox] | None,
) -> list[RedactionFinding]:
    """Fügt explizite Koordinaten-Boxen zu den Fundstellen hinzu."""
    all_findings = list(findings)
    for b in boxes or []:
        all_findings.append(
            RedactionFinding(
                page_number=b.page_number,
                rect=b.rect,
                matched_text=b.label or "explicit_box",
                pattern_name="explicit_box",
                source="box",
            )
        )
    return all_findings


def _sanitize_and_export(
    doc: Document,
    terms: list[str] | None,
    patterns: list[str | RedactionPattern] | None,
    policy: SanitizationPolicy,
) -> tuple[bytes, list[str], list[str], int]:
    """Bereinigt Metadaten, Anhänge und Anmerkungen und exportiert das PDF."""
    term_strings = list(terms or [])
    pattern_strings = _collect_pattern_strings(patterns)
    cleaned_meta = sanitize_metadata(doc, term_strings, pattern_strings, policy)
    removed_att = sanitize_attachments(doc, term_strings, pattern_strings, policy)
    removed_ann = sanitize_annotations(doc, term_strings, pattern_strings, policy)
    out_bytes = bytes(doc.tobytes(garbage=3, deflate=True, clean=True))
    return out_bytes, cleaned_meta, removed_att, removed_ann


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
    """Führt eine vollständige und überprüfbare Schwärzung eines PDF-Dokuments durch."""
    policy = policy or SanitizationPolicy()
    doc = open_pdf(pdf_bytes)

    try:
        findings, scanned_pages = find_redaction_targets(
            doc,
            terms=terms,
            patterns=patterns,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
        )
        all_findings = _merge_explicit_boxes(findings, boxes)
        pages_redacted = _apply_page_redactions(
            doc, all_findings, fill_color, policy.apply_existing_redactions
        )
        out_bytes, cleaned_meta, removed_att, removed_ann = _sanitize_and_export(
            doc, terms, patterns, policy
        )

        verification_error: str | None = None
        verified = False
        if verify:
            pattern_strings = _collect_pattern_strings(patterns)
            v_res = verify_redaction(
                out_bytes,
                forbidden_terms=terms,
                patterns=pattern_strings,
                case_sensitive=case_sensitive,
            )
            verified = v_res.clean
            if not v_res.clean:
                verification_error = "; ".join(v_res.violations)

        report = RedactionReport(
            success=True,
            findings_count=len(all_findings),
            findings=all_findings,
            pages_redacted=pages_redacted,
            metadata_fields_cleaned=cleaned_meta,
            attachments_removed=removed_att,
            annotations_removed=removed_ann,
            scanned_pages_without_ocr=scanned_pages,
            verified=verified,
            verification_error=verification_error,
        )
        return out_bytes, report
    finally:
        doc.close()
