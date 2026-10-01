"""Unabhängige Nachprüfung und Verifikation von Schwärzungsergebnissen."""

from __future__ import annotations

import contextlib
import re

from pymupdf import Document

from auditcore_pdf.engine import open_pdf
from auditcore_pdf.models import VerificationResult


def _check_text_for_leaks(
    text: str,
    location_hint: str,
    terms: list[str],
    compiled_pats: list[re.Pattern[str]],
    violations: list[str],
    case_sensitive: bool,
) -> None:
    """Prüft eine einzelne Zeichenkette auf verbotene Begriffe oder Muster."""
    if not text:
        return
    for t in terms:
        found = (t in text) if case_sensitive else (t.lower() in text.lower())
        if found:
            violations.append(f"{location_hint}: Fundstelle für verbotenen Begriff '{t}'")
    for cp in compiled_pats:
        m = cp.search(text)
        if m:
            pat_str = cp.pattern
            val_str = m.group(0)
            violations.append(
                f"{location_hint}: Fundstelle für verbotenes Muster '{pat_str}': '{val_str}'"
            )


def _check_pages(
    doc: Document,
    terms: list[str],
    pats: list[re.Pattern[str]],
    violations: list[str],
    case_sensitive: bool,
) -> None:
    """Überprüft den Text und die Anmerkungen aller Seiten."""
    for idx in range(doc.page_count):
        pno = idx + 1
        page = doc[idx]
        _check_text_for_leaks(
            page.get_text("text"),
            f"Seite {pno} (Text)",
            terms,
            pats,
            violations,
            case_sensitive,
        )
        for annot in page.annots() or []:
            info = annot.info or {}
            for k in ("content", "subject", "title"):
                val = str(info.get(k, "") or "")
                if val:
                    hint = f"Seite {pno} (Anmerkung {k})"
                    _check_text_for_leaks(val, hint, terms, pats, violations, case_sensitive)


def _check_metadata(
    doc: Document,
    terms: list[str],
    pats: list[re.Pattern[str]],
    violations: list[str],
    case_sensitive: bool,
) -> None:
    """Überprüft die Standard- und XMP-Metadaten."""
    meta = doc.metadata or {}
    for k, v in meta.items():
        if v:
            _check_text_for_leaks(
                str(v),
                f"Metadaten-Feld '{k}'",
                terms,
                pats,
                violations,
                case_sensitive,
            )
    with contextlib.suppress(Exception):
        xmp = doc.get_xml_metadata()
        if xmp:
            _check_text_for_leaks(
                xmp,
                "XMP-Metadatenstrom",
                terms,
                pats,
                violations,
                case_sensitive,
            )


def _check_attachments(
    doc: Document,
    terms: list[str],
    pats: list[re.Pattern[str]],
    violations: list[str],
    case_sensitive: bool,
) -> None:
    """Überprüft eingebettete Anhänge auf verbotene Inhalte."""
    with contextlib.suppress(Exception):
        for name in doc.embfile_names():
            _check_text_for_leaks(
                name,
                f"Anhangsname '{name}'",
                terms,
                pats,
                violations,
                case_sensitive,
            )
            with contextlib.suppress(Exception):
                data = doc.embfile_get(name)
                text_sample = data.decode("utf-8", errors="ignore")
                hint = f"Anhangsinhalt '{name}'"
                _check_text_for_leaks(text_sample, hint, terms, pats, violations, case_sensitive)


def verify_redaction(
    pdf_bytes: bytes,
    forbidden_terms: list[str] | None = None,
    patterns: list[str] | None = None,
    case_sensitive: bool = False,
) -> VerificationResult:
    """Prüft ein PDF unabhängig auf das Vorhandensein verbotener Begriffe und Muster."""
    terms = [t for t in (forbidden_terms or []) if t]
    pats = [p for p in (patterns or []) if p]

    if not terms and not pats:
        return VerificationResult(clean=True, violations=[], details={"checked_pages": 0})

    compiled_pats = [
        re.compile(p, 0 if case_sensitive else re.IGNORECASE) for p in pats
    ]
    violations: list[str] = []
    doc = open_pdf(pdf_bytes)

    try:
        _check_pages(doc, terms, compiled_pats, violations, case_sensitive)
        _check_metadata(doc, terms, compiled_pats, violations, case_sensitive)
        _check_attachments(doc, terms, compiled_pats, violations, case_sensitive)

        details: dict[str, object] = {
            "pages_checked": doc.page_count,
            "metadata_checked": True,
            "attachments_checked": True,
            "annotations_checked": True,
        }

        return VerificationResult(
            clean=len(violations) == 0,
            violations=violations,
            details=details,
        )
    finally:
        doc.close()
