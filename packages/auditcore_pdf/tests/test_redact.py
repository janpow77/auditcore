"""Tests für die Schwärzungslogik (Koordinaten, Begriffe, Muster, Zeilenumbrüche)."""

from __future__ import annotations

from auditcore_pdf import (
    RedactionBox,
    extract_page_text,
    redact_document,
)


def test_redact_explicit_box(sample_pdf: bytes) -> None:
    box = RedactionBox(page_number=1, rect=(70, 90, 200, 115), fill_color=(0, 0, 0))
    redacted_pdf, report = redact_document(sample_pdf, boxes=[box], verify=False)
    assert report.success is True
    assert 1 in report.pages_redacted

    # Auf Seite 1 wurde der Text überdeckt/entfernt
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "Seite 1 Inhalt" not in p1_text


def test_redact_term(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        verify=True,
    )
    assert report.success is True
    assert report.verified is True
    assert 1 in report.pages_redacted

    p1_text = extract_page_text(redacted_pdf, 1)
    assert "STRENG_GEHEIM" not in p1_text
    # Öffentlicher Kontext bleibt erhalten
    assert "Öffentlicher Kontext vor dem Geheimnis." in p1_text
    assert "Öffentlicher Kontext nach dem Geheimnis." in p1_text


def test_redact_case_sensitivity(sensitive_pdf: bytes) -> None:
    # Nur WORT_GROSS schwärzen
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["WORT_GROSS"],
        case_sensitive=True,
        verify=True,
    )
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "WORT_GROSS" not in p1_text
    assert "wort_klein" in p1_text


def test_redact_multiline_phrase(sensitive_pdf: bytes) -> None:
    # "vertraulicher Aktenvorgang" ist über zwei Zeilen gebrochen
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["vertraulicher Aktenvorgang"],
        verify=True,
    )
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "vertraulicher" not in p1_text
    assert "Aktenvorgang" not in p1_text


def test_redact_standard_patterns(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        patterns=["email", "iban"],
        verify=True,
    )
    assert report.success is True
    assert report.verified is True
    p1_text = extract_page_text(redacted_pdf, 1)
    assert "pruefer@flowaudit.de" not in p1_text
    assert "DE02120300000123456789" not in p1_text
    assert "Kontakt:" in p1_text
