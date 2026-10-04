"""Metadaten-, Anhangs- und Anmerkungsbereinigung zur Verhinderung von Datenabflüssen."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from auditcore_pdf.matching import PatternSpec, TextMatcher
from auditcore_pdf.models import SanitizationPolicy

if TYPE_CHECKING:
    from pymupdf import Document

PDF_ANNOT_REDACT = 12

#: Von PyMuPDF berechnete, nicht schreibbare Metadatenfelder
_READONLY_METADATA = frozenset({"format", "encryption"})


def is_binary_attachment(data: bytes) -> bool:
    """Gilt ein Anhang als binär oder komprimiert und damit als nicht textlich prüfbar?"""
    if b"\x00" in data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def remove_xmp(doc: Document) -> list[str]:
    """Entfernt den XMP-Strom des Dokuments und alle XMP-Verweise an anderen Objekten."""
    removed: list[str] = []
    with contextlib.suppress(Exception):
        if doc.get_xml_metadata():
            doc.del_xml_metadata()
            removed.append("xmp_metadata")
    catalog = doc.pdf_catalog()
    count = 0
    for xref in range(1, doc.xref_length()):
        if xref != catalog and doc.xref_get_key(xref, "Metadata")[0] == "xref":
            doc.xref_set_key(xref, "Metadata", "null")
            count += 1
    if count:
        removed.append(f"xmp_objekte:{count}")
    return removed


def _clean_xmp_on_match(doc: Document, matcher: TextMatcher) -> list[str]:
    with contextlib.suppress(Exception):
        xml = doc.get_xml_metadata()
        if xml and matcher.matches(xml):
            doc.del_xml_metadata()
            return ["xmp_metadata"]
    return []


def _scrub_info(doc: Document, meta: dict[str, str], matcher: TextMatcher) -> list[str]:
    cleaned = [
        key
        for key, value in meta.items()
        if key not in _READONLY_METADATA and value and matcher.matches(str(value))
    ]
    if cleaned:
        doc.set_metadata({**meta, **dict.fromkeys(cleaned, "")})
    return cleaned


def sanitize_metadata(
    doc: Document,
    terms: list[str],
    patterns: list[PatternSpec],
    policy: SanitizationPolicy,
) -> list[str]:
    """Bereinigt Standard- und XMP-Metadaten des Dokuments.

    Geprüft werden alle schreibbaren Felder einschließlich Erstell- und Änderungsdatum.
    Mit ``policy.remove_xmp`` wird XMP bei jeder Metadatenbereinigung entfernt, weil
    XMP oft ältere Fassungen und kodierte Werte enthält, die eine Textsuche nicht
    sicher erfasst; sonst nur bei Treffer (``clean_xmp``).
    """
    meta = {str(k): str(v or "") for k, v in (doc.metadata or {}).items()}
    if policy.remove_all_metadata:
        doc.set_metadata(dict.fromkeys(meta, ""))
        xmp = remove_xmp(doc) if policy.clean_xmp or policy.remove_xmp else []
        return list(meta) + xmp
    if not policy.scrub_metadata:
        return []
    matcher = TextMatcher(terms, patterns)
    cleaned = _scrub_info(doc, meta, matcher)
    if policy.remove_xmp:
        cleaned.extend(remove_xmp(doc))
    elif policy.clean_xmp:
        cleaned.extend(_clean_xmp_on_match(doc, matcher))
    return cleaned


def _attachment_has_match(doc: Document, name: str, matcher: TextMatcher) -> bool:
    data = b""
    with contextlib.suppress(Exception):
        data = bytes(doc.embfile_get(name))
    return matcher.matches(name) or matcher.matches(data.decode("utf-8", errors="ignore"))


def sanitize_attachments(
    doc: Document,
    terms: list[str],
    patterns: list[PatternSpec],
    policy: SanitizationPolicy,
) -> list[str]:
    """Entfernt oder bereinigt eingebettete Dateien (EmbeddedFiles)."""
    removed: list[str] = []
    try:
        names = list(doc.embfile_names())
    except Exception:
        return removed

    matcher = TextMatcher(terms, patterns)
    for name in names:
        if policy.strip_attachments or _attachment_has_match(doc, name, matcher):
            with contextlib.suppress(Exception):
                doc.embfile_del(name)
                removed.append(name)
    return removed


def find_unverifiable_attachments(doc: Document) -> list[str]:
    """Namen der Anhänge, deren Inhalt binär oder komprimiert ist (nicht textlich prüfbar)."""
    unverifiable: list[str] = []
    with contextlib.suppress(Exception):
        for name in doc.embfile_names():
            if is_binary_attachment(bytes(doc.embfile_get(name))):
                unverifiable.append(str(name))
    return unverifiable


def sanitize_annotations(
    doc: Document,
    terms: list[str],
    patterns: list[PatternSpec],
    policy: SanitizationPolicy,
) -> int:
    """Entfernt oder bereinigt Notizen, Kommentare und Hervorhebungen mit vertraulichem Inhalt."""
    matcher = TextMatcher(terms, patterns)
    removed_count = 0
    for idx in range(doc.page_count):
        page = doc[idx]
        annots = list(page.annots() or [])
        for annot in annots:
            try:
                ann_type = annot.type[0]
            except (IndexError, TypeError):
                ann_type = -1

            # Bestehende Schwärzungsanmerkungen belassen, damit apply_redactions sie verarbeitet
            if ann_type == PDF_ANNOT_REDACT:
                continue

            info = annot.info or {}
            annot_text = " ".join(
                str(info.get(key, "") or "") for key in ("content", "subject", "title")
            ).strip()

            if policy.strip_annotations or matcher.matches(annot_text):
                with contextlib.suppress(Exception):
                    page.delete_annot(annot)
                    removed_count += 1
    return removed_count
