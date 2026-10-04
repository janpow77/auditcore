"""Begriffssuche (Wortgrenzen, Zeilenumbruch, Trennung) und PDF-Zeichenketten."""

from __future__ import annotations

import re

import pymupdf as fitz
import pytest

from auditcore_pdf import RedactionPattern, extract_page_text, redact_document, verify_redaction
from auditcore_pdf.matching import TextMatcher, pattern_regexes, resolve_pattern, term_regex
from auditcore_pdf.pdfstrings import (
    blank_strings,
    decode_text,
    find_key_references,
    find_key_strings,
    parse_string_at,
    pdf_text_string,
)


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("ein vertraulicher Aktenvorgang", True),
        ("ein vertraulicher\nAktenvorgang", True),
        ("ein vertrau-\nlicher   Aktenvorgang", True),
        ("ein vertrau­licher Aktenvorgang", True),
        ("ein vertraulicherAktenvorgang", False),
    ],
    ids=["leerzeichen", "umbruch", "trennung", "weiches-trennzeichen", "ohne-abstand"],
)
def test_term_regex_spans_line_breaks_and_hyphenation(text: str, found: bool) -> None:
    regex = re.compile(term_regex("vertraulicher Aktenvorgang"), re.IGNORECASE)
    assert bool(regex.search(text)) is found


def test_term_regex_whole_word_uses_word_characters() -> None:
    regex = re.compile(term_regex("Max", whole_word=True))
    assert regex.search("Herr Max Muster")
    assert not regex.search("Maximal")
    assert not regex.search("Max_Muster")
    assert re.search(term_regex("Dr.", whole_word=True), "bei Dr. Muster")
    assert term_regex("   ") == ""


def test_text_matcher_and_pattern_resolution() -> None:
    custom = RedactionPattern(name="kunde", regex=r"K-\d{3}")
    matcher = TextMatcher(["", "geheim"], ["", "email", custom])
    assert bool(matcher) is True
    assert not bool(TextMatcher([""], [""]))
    assert matcher.matches("x@y.de") and matcher.matches("K-123")
    assert not matcher.matches("")
    assert matcher.violations("", "Ort") == []
    assert matcher.violations("GEHEIM", "Ort") == [
        "Ort: Fundstelle für verbotenen Begriff 'geheim'"
    ]
    assert resolve_pattern("email").name == "email"
    assert resolve_pattern(r"\d+").regex == r"\d+"
    assert pattern_regexes(["", custom]) == [r"K-\d{3}"]
    assert not TextMatcher(["geheim"], case_sensitive=True).matches("GEHEIM")


def _hyphenated_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 100), "Der vertrau-")
    page.insert_text(fitz.Point(72, 115), "liche Vermerk und der Maximalbetrag.")
    page.insert_text(fitz.Point(72, 130), "Herr Max ist zuständig.")
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_redact_and_verify_term_split_by_hyphenation() -> None:
    pdf = _hyphenated_pdf()
    assert verify_redaction(pdf, forbidden_terms=["vertrauliche"]).clean is False
    out, report = redact_document(pdf, terms=["vertrauliche"])
    assert {f.source for f in report.findings} == {"multiline"}
    assert report.verified is True
    text = extract_page_text(out, 1)
    assert "vertrau" not in text
    assert "liche Vermerk" not in text


def test_whole_word_option_in_verification() -> None:
    pdf = _hyphenated_pdf()
    out, report = redact_document(pdf, terms=["Max"], whole_word=True, verify=False)
    assert [f.matched_text for f in report.findings] == ["Max"]
    assert "Maximalbetrag" in extract_page_text(out, 1)
    assert verify_redaction(out, forbidden_terms=["Max"], whole_word=True).clean is True
    # Ohne Wortgrenze meldet die Nachprüfung den Wortbestandteil als Restrisiko.
    assert verify_redaction(out, forbidden_terms=["Max"]).clean is False


def test_parse_literal_strings_with_escapes() -> None:
    data = b"/Alt (a\\(b\\)c (x) \\101\\n\\\\\\q\\\r\nz\\\nw) /E <48 49 5> /ActualText /Name"
    found = find_key_strings(data, ("Alt", "E", "ActualText"))
    assert [(k.key, k.text) for k in found] == [("Alt", "a(b)c (x) A\n\\qzw"), ("E", "HIP")]
    assert data[found[1].start : found[1].end] == b"<48 49 5>"
    assert parse_string_at(b"(offen", 0) == (b"offen", 6)
    assert parse_string_at(b"(a\\", 0) == (b"a", 3)
    assert parse_string_at(b"<<", 0) is None
    assert parse_string_at(b"<zz>", 0) is None
    assert find_key_strings(b"/Alternate (x)", ("Alt",)) == []


def test_decode_blank_and_encode_strings() -> None:
    assert decode_text("﻿Ä".encode("utf-16-be")) == "Ä"
    assert decode_text(b"\xef\xbb\xbf\xc3\x84") == "Ä"
    assert decode_text(b"\xc4") == "Ä"
    assert blank_strings(b"/A (x) /B (yy)", [(3, 6), (10, 14)]) == b"/A () /B ()"
    assert pdf_text_string("Ä") == "<FEFF00C4>"
    assert find_key_references(b"/JS 12 0 R /JS (x)", "JS") == [12]
