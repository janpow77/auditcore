"""Präzision der Standardmuster und konservative Standardauswahl (Issue #239)."""

from __future__ import annotations

import re

import pymupdf as fitz
import pytest

from auditcore_pdf import (
    DEFAULT_PATTERNS,
    STANDARD_PATTERNS,
    SanitizationPolicy,
    extract_page_text,
    redact_document,
    verify_redaction,
)
from auditcore_pdf.matching import match_span


def _hits(name: str, text: str) -> list[str]:
    regex = re.compile(STANDARD_PATTERNS[name].regex, re.IGNORECASE)
    return [text[slice(*match_span(m))] for m in regex.finditer(text)]


HIT_CASES = [
    ("telefon", "Tel. 069 12345678", "069 12345678"),
    ("telefon", "Zentrale 0611 3200-0 erreichbar", "0611 3200-0"),
    ("telefon", "+49 69 1234567", "+49 69 1234567"),
    ("telefon", "+49 (0)69 1234567", "+49 (0)69 1234567"),
    ("telefon", "(069) 123456", "(069) 123456"),
    ("geburtsdatum", "geboren am 01.02.1980 in Kassel", "01.02.1980"),
    ("geburtsdatum", "Geb.-Datum: 1.2.1980", "1.2.1980"),
    ("geburtsdatum", "Geburtsdatum 31.12.2001", "31.12.2001"),
    ("geburtsdatum", "geb. 05.06.1975", "05.06.1975"),
    ("datum", "Bescheid vom 04.10.2026", "04.10.2026"),
    ("steuer_id", "IdNr 12 345 678 901", "12 345 678 901"),
    ("steuer_id", "IdNr 12345678901", "12345678901"),
    ("iban", "IBAN DE02 1203 0000 0123 4567 89", "DE02 1203 0000 0123 4567 89"),
    ("ust_id", "USt-IdNr. DE123456789", "DE123456789"),
    ("kreditkarte", "Karte 4111 1111 1111 1111", "4111 1111 1111 1111"),
    ("ip_adresse", "Server 192.168.0.1 antwortet", "192.168.0.1"),
    ("aktenzeichen", "Az. VK 12/2026", "VK 12/2026"),
]


@pytest.mark.parametrize(("name", "text", "expected"), HIT_CASES, ids=lambda v: str(v)[:24])
def test_standard_pattern_hits(name: str, text: str, expected: str) -> None:
    assert _hits(name, text) == [expected]


MISS_CASES = [
    ("telefon", "D:20261004120000+02'00'"),
    ("telefon", "2026-10-04T12:00:00+02:00"),
    ("telefon", "uuid:01234567-89ab-cdef-0123-456789abcdef"),
    ("telefon", "01067 Dresden"),
    ("telefon", "am 04.10.2026"),
    ("telefon", "Betrag 0,50 EUR"),
    # Bekannte Grenze: Rufnummern unter drei Ziffern ohne Durchwahlgruppe
    ("telefon", "Ruf 0611/32-0"),
    ("geburtsdatum", "Bescheid vom 04.10.2026"),
    ("datum", "Version 1.10.20261"),
    ("steuer_id", "D:20261004120000"),
    ("steuer_id", "01234567890"),
    ("iban", "abcd12 efgh ijkl"),
    ("ust_id", "de123456789"),
    ("kreditkarte", "4111 1111-1111 1111"),
    ("ip_adresse", "Wert 256.1.1.1"),
    ("aktenzeichen", "am 12/2026"),
]


@pytest.mark.parametrize(("name", "text"), MISS_CASES, ids=lambda v: str(v)[:24])
def test_standard_pattern_misses(name: str, text: str) -> None:
    assert _hits(name, text) == []


def test_default_patterns_are_a_conservative_subset() -> None:
    assert set(DEFAULT_PATTERNS) <= set(STANDARD_PATTERNS)
    assert {"datum", "steuer_id", "kreditkarte", "ip_adresse", "aktenzeichen"}.isdisjoint(
        DEFAULT_PATTERNS
    )
    assert all(STANDARD_PATTERNS[name].description for name in STANDARD_PATTERNS)


def _pdf_with_dates() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 100), "Bescheid vom 04.10.2026")
    page.insert_text(fitz.Point(72, 130), "Antragsteller geboren am 01.02.1980")
    page.insert_text(fitz.Point(72, 160), "Telefon 069 12345678")
    doc.set_metadata(
        {
            "title": "Neutral",
            "creationDate": "D:20261004120000+02'00'",
            "modDate": "D:20261004130000+02'00'",
        }
    )
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_birth_date_redacts_only_date_after_context_word() -> None:
    out, report = redact_document(_pdf_with_dates(), patterns=list(DEFAULT_PATTERNS))
    assert report.verified is True, report.verification_error
    text = extract_page_text(out, 1)
    assert "04.10.2026" in text
    assert "geboren am" in text
    assert "01.02.1980" not in text
    assert "12345678" not in text
    assert {f.pattern_name for f in report.findings} == {"geburtsdatum", "telefon"}


def test_metadata_timestamps_do_not_trigger_phone_pattern() -> None:
    """Issue #239: Erstell-/Änderungsdatum galten als Telefonnummer; jetzt kein Treffer."""
    pdf = _pdf_with_dates()
    res = verify_redaction(pdf, patterns=["telefon"])
    assert not any("Metadaten" in v for v in res.violations)
    _, report = redact_document(
        pdf, patterns=["telefon"], policy=SanitizationPolicy(scrub_metadata=True)
    )
    assert report.verified is True
    assert report.metadata_fields_cleaned == []


def test_metadata_dates_are_scrubbed_when_they_match() -> None:
    """Auch Erstell- und Änderungsdatum werden bereinigt, wenn ein Muster trifft."""
    out, report = redact_document(_pdf_with_dates(), patterns=[r"D:2026\d+"])
    assert set(report.metadata_fields_cleaned) >= {"creationDate", "modDate"}
    assert report.verified is True


def test_case_sensitive_search_keeps_context_word_case_insensitive() -> None:
    _, report = redact_document(
        _pdf_with_dates(), patterns=["geburtsdatum"], case_sensitive=True, verify=False
    )
    assert [f.matched_text for f in report.findings] == ["01.02.1980"]
