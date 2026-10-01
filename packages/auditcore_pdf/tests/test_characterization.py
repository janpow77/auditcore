"""Charakterisierungstests entsprechend pdf-editor-characterization-20260929.json."""

from __future__ import annotations

import pymupdf as fitz

from auditcore_pdf import (
    RedactionPattern,
    SanitizationPolicy,
    extract_page_text,
    get_document_info,
    redact_document,
    verify_redaction,
)


def test_scenario_visible_text_and_hidden_copies(sensitive_pdf: bytes) -> None:
    """Szenario: Geheimnis in sichtbarem Text, Titel, Anhang und Kommentar."""
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(
            scrub_metadata=True,
            strip_attachments=True,
            strip_annotations=False,
        ),
        verify=True,
    )

    assert report.success is True
    assert report.verified is True

    # 1. Page secret removed & public context retained
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "STRENG_GEHEIM" not in p1_text
    assert "Öffentlicher Kontext vor dem Geheimnis." in p1_text
    assert "Öffentlicher Kontext nach dem Geheimnis." in p1_text

    # 2. Title secret removed
    info = get_document_info(redacted_pdf)
    assert "STRENG_GEHEIM" not in info.metadata.get("title", "")

    # 3. Attachment secret removed
    assert "geheimnis.txt" not in info.attachments

    # 4. Comment secret removed
    doc = fitz.open(stream=redacted_pdf, filetype="pdf")
    p1 = doc[0]
    for annot in p1.annots() or []:
        content = (annot.info or {}).get("content", "")
        assert "STRENG_GEHEIM" not in content
    doc.close()


def test_scenario_independent_text_extraction(sensitive_pdf: bytes) -> None:
    """Szenario: Unabhängige Textextraktion bestätigt Abwesenheit des Geheimnisses."""
    redacted_pdf, _ = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        verify=True,
    )
    v_res = verify_redaction(redacted_pdf, forbidden_terms=["STRENG_GEHEIM"])
    assert v_res.clean is True
    assert len(v_res.violations) == 0


def test_scenario_simple_search_case_sensitive(sensitive_pdf: bytes) -> None:
    """Szenario: Groß-/Kleinschreibung wird bei case_sensitive=True beachtet."""
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["WORT_GROSS"],
        case_sensitive=True,
        verify=True,
    )
    p1_text = extract_page_text(redacted_pdf, 1)
    # WORT_GROSS entfernt, wort_klein erhalten
    assert "WORT_GROSS" not in p1_text
    assert "wort_klein" in p1_text


def test_scenario_pattern_phrase_across_lines(sensitive_pdf: bytes) -> None:
    """Szenario: Phrase über Zeilenumbruch hinweg wird zuverlässig gefunden und geschwärzt."""
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["vertraulicher Aktenvorgang"],
        verify=True,
    )
    assert report.success is True
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "vertraulicher" not in p1_text
    assert "Aktenvorgang" not in p1_text


def test_scenario_scan_without_ocr(scanned_pdf: bytes) -> None:
    """Szenario: Gescannte Seite ohne Textebene wird erkannt und gemeldet."""
    redacted_pdf, report = redact_document(
        scanned_pdf,
        terms=["beliebig"],
        verify=False,
    )
    assert 1 in report.scanned_pages_without_ocr


def test_scenario_comment_applies_existing_redaction() -> None:
    """Szenario: Vorhandene Schwärzungsanmerkungen werden angewendet und dauerhaft entfernt."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(72, 100), "Geheime Passage hier.")
    # Vorhandene Redact-Anmerkung anlegen
    page.add_redact_annot(fitz.Rect(70, 85, 200, 110), fill=(0, 0, 0))
    raw_pdf = doc.tobytes()
    doc.close()

    redacted_pdf, report = redact_document(
        raw_pdf,
        policy=SanitizationPolicy(apply_existing_redactions=True),
        verify=False,
    )
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "Geheime Passage" not in p1_text


def test_scenario_pattern_redaction_email(sensitive_pdf: bytes) -> None:
    email_pat = RedactionPattern(
        name="email",
        regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    )
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        patterns=[email_pat],
        verify=True,
    )
    assert report.success is True
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "pruefer@flowaudit.de" not in p1_text
    assert "Kontakt:" in p1_text
