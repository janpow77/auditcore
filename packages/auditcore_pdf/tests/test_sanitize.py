"""Tests für Metadaten-, Anhangs- und Anmerkungsbereinigung."""

from __future__ import annotations

import pymupdf as fitz

from auditcore_pdf import (
    SanitizationPolicy,
    get_document_info,
    redact_document,
)


def test_sanitize_metadata(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(scrub_metadata=True),
        verify=True,
    )
    info = get_document_info(redacted_pdf)
    # Titel enthielt "Bericht mit STRENG_GEHEIM im Titel" und muss bereinigt sein
    assert "STRENG_GEHEIM" not in info.metadata.get("title", "")
    assert "title" in report.metadata_fields_cleaned


def test_sanitize_attachments(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(strip_attachments=True),
        verify=True,
    )
    info = get_document_info(redacted_pdf)
    assert len(info.attachments) == 0
    assert "geheimnis.txt" in report.attachments_removed


def test_sanitize_annotations(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(strip_annotations=False),
        verify=True,
    )
    # Anmerkung enthielt STRENG_GEHEIM und wurde gelöscht
    doc = fitz.open(stream=redacted_pdf, filetype="pdf")
    p1 = doc[0]
    annots = list(p1.annots() or [])
    for a in annots:
        content = (a.info or {}).get("content", "")
        assert "STRENG_GEHEIM" not in content
    doc.close()
    assert report.annotations_removed >= 1
