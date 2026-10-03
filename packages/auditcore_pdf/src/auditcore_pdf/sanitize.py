"""Metadaten-, Anhangs- und Anmerkungsbereinigung zur Verhinderung von Datenabflüssen."""

from __future__ import annotations

import contextlib
import re
from typing import TYPE_CHECKING

from auditcore_pdf.models import SanitizationPolicy

if TYPE_CHECKING:
    from pymupdf import Document

PDF_ANNOT_REDACT = 12


def _matches_any(text: str, terms: list[str], patterns: list[str]) -> bool:
    """Prüft, ob der gegebene Text einen der Begriffe oder regulären Ausdrücke enthält."""
    if not text:
        return False
    if any(t and t.lower() in text.lower() for t in terms):
        return True
    return any(p and bool(re.search(p, text, re.IGNORECASE)) for p in patterns)


def sanitize_metadata(
    doc: Document,
    terms: list[str],
    patterns: list[str],
    policy: SanitizationPolicy,
) -> list[str]:
    """Bereinigt Standard- und XMP-Metadaten des Dokuments."""
    cleaned_fields: list[str] = []
    meta = dict(doc.metadata or {})

    standard_keys = ["title", "author", "subject", "keywords", "creator", "producer"]

    if policy.remove_all_metadata:
        empty_meta = {k: "" for k in meta}
        doc.set_metadata(empty_meta)
        if policy.clean_xmp:
            with contextlib.suppress(Exception):
                doc.del_xml_metadata()
        return list(meta.keys())

    if policy.scrub_metadata:
        updated = False
        new_meta = dict(meta)
        for k in standard_keys:
            val = str(meta.get(k, "") or "")
            if val and _matches_any(val, terms, patterns):
                new_meta[k] = ""
                cleaned_fields.append(k)
                updated = True
        if updated:
            doc.set_metadata(new_meta)

        # XMP-Metadatenstrom prüfen und bei Bedarf bereinigen
        if policy.clean_xmp:
            with contextlib.suppress(Exception):
                xml = doc.get_xml_metadata()
                if xml and _matches_any(xml, terms, patterns):
                    doc.del_xml_metadata()
                    cleaned_fields.append("xmp_metadata")

    return cleaned_fields


def sanitize_attachments(
    doc: Document,
    terms: list[str],
    patterns: list[str],
    policy: SanitizationPolicy,
) -> list[str]:
    """Entfernt oder bereinigt eingebettete Dateien (EmbeddedFiles)."""
    removed: list[str] = []
    try:
        names = list(doc.embfile_names())
    except Exception:
        return removed

    for name in names:
        should_remove = policy.strip_attachments
        if not should_remove:
            if _matches_any(name, terms, patterns):
                should_remove = True
            else:
                with contextlib.suppress(Exception):
                    data = doc.embfile_get(name)
                    text_sample = data.decode("utf-8", errors="ignore")
                    if _matches_any(text_sample, terms, patterns):
                        should_remove = True
        if should_remove:
            with contextlib.suppress(Exception):
                doc.embfile_del(name)
                removed.append(name)
    return removed


def sanitize_annotations(
    doc: Document,
    terms: list[str],
    patterns: list[str],
    policy: SanitizationPolicy,
) -> int:
    """Entfernt oder bereinigt Notizen, Kommentare und Hervorhebungen mit vertraulichem Inhalt."""
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
            content = str(info.get("content", "") or "")
            subject = str(info.get("subject", "") or "")
            title = str(info.get("title", "") or "")
            annot_text = f"{content} {subject} {title}".strip()

            should_delete = policy.strip_annotations
            if not should_delete and annot_text and _matches_any(annot_text, terms, patterns):
                should_delete = True

            if should_delete:
                with contextlib.suppress(Exception):
                    page.delete_annot(annot)
                    removed_count += 1
    return removed_count
