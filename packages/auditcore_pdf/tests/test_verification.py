"""Tests für die unabhängige Nachprüfung von Schwärzungen."""

from __future__ import annotations

import pymupdf as fitz

from auditcore_pdf import (
    verify_redaction,
)


def test_verify_redaction_clean(sample_pdf: bytes) -> None:
    res = verify_redaction(sample_pdf, forbidden_terms=["NICHT_VORHANDEN"])
    assert res.clean is True
    assert len(res.violations) == 0


def test_verify_redaction_detects_violation(sensitive_pdf: bytes) -> None:
    res = verify_redaction(sensitive_pdf, forbidden_terms=["STRENG_GEHEIM"])
    assert res.clean is False
    assert len(res.violations) > 0
    # Verletzungen in Text, Titel, Anmerkung oder Anhang
    violation_texts = " ".join(res.violations)
    assert "STRENG_GEHEIM" in violation_texts


def test_verify_redaction_without_criteria_is_clean(sensitive_pdf: bytes) -> None:
    """Ohne Begriffe und Muster gibt es nichts zu prüfen; leere Einträge zählen nicht."""
    res = verify_redaction(sensitive_pdf, forbidden_terms=["", ""], patterns=[""])
    assert res.clean is True
    assert res.violations == []
    assert res.details == {"checked_pages": 0}


def test_verify_redaction_detects_pattern_with_location(sensitive_pdf: bytes) -> None:
    res = verify_redaction(sensitive_pdf, patterns=[r"[\w.]+@flowaudit\.de"])
    assert res.clean is False
    assert any(
        v.startswith("Seite 1 (Text): Fundstelle für verbotenes Muster")
        and "'pruefer@flowaudit.de'" in v
        for v in res.violations
    )
    assert res.details["pages_checked"] == 1


def test_verify_redaction_checks_xmp_and_attachments() -> None:
    """XMP-Strom und Anhänge werden geprüft; ein leerer Anhang löst keine Fundstelle aus."""
    doc = fitz.open()
    doc.new_page()
    doc.set_xml_metadata("<x:xmpmeta><dc>Bearbeiter VERTRAULICH_XMP</dc></x:xmpmeta>")
    doc.embfile_add("leer.txt", b"", filename="leer.txt")
    doc.embfile_add("anlage.txt", b"Anlage mit VERTRAULICH_ANLAGE", filename="anlage.txt")
    pdf_bytes = bytes(doc.tobytes())
    doc.close()

    res = verify_redaction(
        pdf_bytes,
        forbidden_terms=["VERTRAULICH_XMP", "VERTRAULICH_ANLAGE"],
        case_sensitive=True,
    )
    assert res.clean is False
    assert "XMP-Metadatenstrom: Fundstelle für verbotenen Begriff 'VERTRAULICH_XMP'" in (
        res.violations
    )
    assert (
        "Anhangsinhalt 'anlage.txt': Fundstelle für verbotenen Begriff 'VERTRAULICH_ANLAGE'"
        in res.violations
    )
    assert not any("leer.txt" in v for v in res.violations)
