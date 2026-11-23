"""Schwärzung: Muster, Begriffe und Korpus K01–K09 (Prüfplan F, L, K)."""

from __future__ import annotations

import time

import pymupdf as fitz
import pytest
import redaction_corpus as kc
from redaction_support import (
    DEJAVU,
    SECRET,
    criteria,
    dejavu,
    findings,
    make_pdf,
    page_text,
    redacted,
)

from auditcore_pdf import redaction as R
from auditcore_pdf.redaction import patterns as P

# ── F: Funktion ─────────────────────────────────────────────────


@pytest.mark.parametrize("case", kc.K02, ids=lambda c: c.expected[0][1])
def test_f01_pattern_finds_supported_format(case):
    pattern, text = case.expected[0]
    hits = {f.text for f in findings(kc.pdf_from_lines([case.line]), [pattern])}
    assert text in hits


@pytest.mark.parametrize("case", kc.K02_ERWEITERT, ids=lambda c: c.note)
def test_k02_extended_formats(case):
    # Erweiterte Schreibweisen aus Akten: die Bibliothek erkennt sie vollständig.
    pattern, text = case.expected[0]
    hits = [f.text for f in findings(kc.pdf_from_lines([case.line]), [pattern])]
    assert hits == [text]


@pytest.mark.parametrize("case", kc.K03, ids=lambda c: c.line[:30])
def test_f02_standard_patterns_spare_technical_text(case):
    hits = findings(kc.pdf_from_lines([case.line]), kc.STANDARD_PATTERNS)
    assert hits == [], [h.text for h in hits]


def test_k02_k03_cases_on_one_page():
    # Alle Fälle auf einer Seite: Soll-Treffer gefunden, Fachtext bleibt stehen.
    pdf = kc.cases_pdf(kc.K02 + kc.K03)
    texts = {f.text for f in findings(pdf, kc.STANDARD_PATTERNS)}
    for case in kc.K02:
        assert case.expected[0][1] in texts
    out = redacted(pdf, kc.STANDARD_PATTERNS)
    remaining = page_text(out)
    for case in kc.K03:
        for kept in case.keep:
            assert kept in remaining


def test_f03_overlapping_patterns_counted_once():
    pdf = kc.pdf_from_lines(["Konto DE89 3704 0044 0532 0130 00 bei der Bank"])
    plan = R.build_plan(pdf, criteria(kc.STANDARD_PATTERNS))
    assert plan.by_source() == {"iban": 1}


def test_f04_term_list_case_and_whole_word():
    pdf = kc.pdf_from_lines(["Herr Meier, Frau MEIER und der Meierhof"])
    assert {f.text for f in findings(pdf, terms=["meier"])} == {"Meier", "MEIER"}
    sensitive = [f.text for f in findings(pdf, terms=["Meier"], case_sensitive=True)]
    assert sensitive == ["Meier"]
    assert len(findings(pdf, terms=["Meier"], whole_word=False)) == 3


def test_f05_single_term_respects_match_case():
    pdf = kc.pdf_from_lines(["Herr MEIER und Herr Meier"])
    out, report, _plan = R.redact_all(pdf, criteria((), ["Meier"], True, False))
    assert report.redactions == 1
    assert "MEIER" in page_text(out)


def test_f06_term_across_line_break():
    pdf = kc.pdf_from_lines(["Antragstellerin ist Erika", "Musterfrau aus Kassel."])
    assert {f.text for f in findings(pdf, terms=["Erika Musterfrau"])} == {"Erika Musterfrau"}


def test_f06_term_with_hyphenation():
    pdf = kc.pdf_from_lines(["Frau Muster-", "frau wohnt dort."])
    assert findings(pdf, terms=["Musterfrau"])


def test_f07_no_match_across_columns():
    # Zwei Spalten dürfen nicht zu einem Treffer verschmelzen.
    assert findings(kc.two_columns_pdf(), terms=["Erika Musterfrau"]) == []


def test_f08_neighbour_words_stay_readable():
    pdf = kc.pdf_from_lines(["Kontakt: erika@example.org, Telefon folgt"])
    text = page_text(redacted(pdf, ["email"]))
    assert SECRET not in text
    assert "Kontakt:" in text and "Telefon" in text


def test_f08_partial_word_only_redacts_match():
    pdf = kc.pdf_from_lines(["Der Meierhof liegt am Ort"])
    assert "hof" in page_text(redacted(pdf, terms=["Meier"], whole_word=False))


def test_f08_punctuation_survives():
    pdf = kc.pdf_from_lines(["(erika@example.org), weiter"])
    text = page_text(redacted(pdf, ["email"]))
    assert "(" in text and ")," in text


def test_f09_preview_count_matches_redaction():
    pdf = kc.pdf_from_lines(
        ["Konto DE89 3704 0044 0532 0130 00", "Mail erika@example.org", "Name Erika Musterfrau"]
    )
    crit = criteria(["iban", "email"], ["Erika Musterfrau"])
    plan = R.build_plan(pdf, crit)
    _out, report, _ = R.redact_all(pdf, crit)
    assert plan.to_dict()["total"] == report.redactions == 3


def test_f10_regex_characters_in_terms_are_literal():
    pdf = kc.pdf_from_lines(["axb und a.b sowie (x)"])
    assert [f.text for f in findings(pdf, terms=["a.b"])] == ["a.b"]
    assert [f.text for f in findings(pdf, terms=["(x)"])] == ["(x)"]


def test_f10_term_limits_are_not_silent():
    terms = [f"Begriff{i:03d}" for i in range(R.MAX_TERMS + 1)]
    with pytest.raises(R.RedactionError, match="Höchstens 200 Begriffe"):
        criteria((), terms)
    with pytest.raises(R.RedactionError, match="höchstens 200 Zeichen"):
        criteria((), ["x" * (R.MAX_TERM_LENGTH + 1)])
    with pytest.raises(R.RedactionError, match="Unbekannte Muster: gibtsnicht"):
        criteria(["gibtsnicht"])
    # Doppelte und leere Begriffe zählen nicht mit.
    crit = criteria(["email", "email"], ["  Meier ", "Meier", "", "  "])
    assert crit.patterns == ("email",) and crit.terms == ("Meier",)
    assert crit.to_dict() == {
        "patterns": ["email"],
        "terms": ["Meier"],
        "case_sensitive": False,
        "whole_word": True,
    }


def test_f11_result_is_valid_pdf():
    out = redacted(kc.pdf_from_lines(["Mail erika@example.org"] * 3), ["email"])
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert doc.page_count == 1
        assert not doc.is_repaired


def test_f12_unrelated_content_preserved():
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=420, height=595)
        page.insert_text((60, 80), f"Seite {i + 1} mit erika@example.org", fontsize=11)
        page.insert_text((60, 120), "Unbeteiligter Sachverhalt", fontsize=11)
        page.insert_link(
            {
                "kind": fitz.LINK_URI,
                "from": fitz.Rect(60, 300, 200, 315),
                "uri": "https://example.org/",
            }
        )
    doc[1].set_rotation(90)
    src = doc.tobytes()
    doc.close()
    out = redacted(src, ["email"])
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert doc.page_count == 3
        assert doc[1].rotation == 90
        assert doc[0].rect.width == 420
        assert all("Unbeteiligter Sachverhalt" in p.get_text() for p in doc)
        assert all(p.get_links() for p in doc)


# ── Musterprüfungen im Einzelnen ────────────────────────────────


@pytest.mark.parametrize(
    "line, pattern, expected",
    [
        ("Konto DE89 3704 0044 0532 0130 01 falsch", "iban", []),
        ("Konto DE89-3704 ungültig", "iban", []),
        ("Konto ÄÖ89 3704 0044 0532 0130 00 bei", "iban", []),
        ("Karte 4111 1111 1111 1111 bitte", "kreditkarte", ["4111 1111 1111 1111"]),
        ("Karte 4111 1111 1111 1112 bitte", "kreditkarte", []),
        ("geboren am 31.02.1980 in Kassel", "geburtsdatum", []),
        ("geboren am 14.03.1978 in Kassel", "geburtsdatum", ["14.03.1978"]),
    ],
)
def test_pattern_validators(line, pattern, expected):
    hits = [f.text for f in findings(kc.pdf_from_lines([line]), [pattern])]
    assert hits == expected


def test_source_labels():
    assert R.source_label("begriff:Meier") == "Begriff „Meier“"
    assert R.source_label(R.MANUAL_SOURCE) == "Bereich"
    assert R.source_label(R.NER_PROPAGATED_ID) == "Namen (im Dokument nachgesucht)"
    assert R.source_label("email") == R.PATTERNS["email"].label
    assert R.source_label("unbekannt") == "unbekannt"
    assert all(spec.label and spec.hint for spec in R.PATTERNS.values())
    assert P.PATTERNS is R.PATTERNS


# ── L: Leistung ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "line",
    ["1" * 5000, " " * 5000 + "x", "a@" + "a." * 2500, "+49 " + "1 " * 2500, "DE" + "1" * 5000],
    ids=["ziffern", "leerzeichen", "email", "telefon", "iban"],
)
def test_l07_no_catastrophic_backtracking(line):
    pdf = kc.pdf_from_lines([line[:400]] * 10, fontsize=4)
    start = time.perf_counter()
    findings(pdf, kc.STANDARD_PATTERNS)
    assert time.perf_counter() - start < 5.0


def test_l01_k09_dense_pages_within_budget():
    # K09: 40 dichte Seiten (die Anwendung prüft 100) bleiben im Zeitrahmen.
    pdf = kc.big_pdf(40)
    start = time.perf_counter()
    out = redacted(pdf, ["iban", "email"], ["Erika Musterfrau"])
    elapsed = time.perf_counter() - start
    assert SECRET not in page_text(out)
    assert elapsed < 60, f"{elapsed:.1f} s für 40 dichte Seiten"


def test_k09_sparse_document_keeps_text():
    pdf = kc.big_pdf(5, lines_per_page=10, dense=False)
    out = redacted(pdf, terms=["Erika Musterfrau"])
    assert "Musterfrau" not in page_text(out)


# ── Normalisierung (H4) ─────────────────────────────────────────


@pytest.mark.parametrize(
    "text, term",
    [
        ("Frau ﬁscher kam", "fischer"),
        ("Herr Müller kam", "Müller"),
        ("Herr Mus​termann kam", "Mustermann"),
        ("Herr STRASSER kam", "Straßer"),
    ],
    ids=["ligatur", "nfd", "nullbreite", "eszett"],
)
def test_a_h4_normalisation(text, term):
    font = dejavu()
    if "\u200b" in text and font != str(DEJAVU):
        # Die Ersatzschrift hat keine Glyphe für U+200B; MuPDF liest dann „\x00“.
        pytest.skip("Ersatzschrift ohne Glyphe für das Nullbreite-Leerzeichen")

    def build(doc, page):
        page.insert_text((72, 72), text, fontsize=11, fontfile=font, fontname="dv")

    plan = R.build_plan(make_pdf(build), R.Criteria.from_input([], [term]))
    assert len(plan.candidates) == 1


def test_eszett_spelling_with_builtin_font():
    # „ss“ im Begriff trifft „ß“ im Text und umgekehrt (eingebaute Schrift).
    pdf = kc.pdf_from_lines(["Herr Strasser und Frau Straßer"])
    assert len(findings(pdf, terms=["Straßer"])) == 2
    assert len(findings(pdf, terms=["Strasser"])) == 2
    assert len(findings(pdf, terms=["Straßer"], case_sensitive=True)) == 1


def test_a_h4_double_name_and_same_baseline():
    wrapped = kc.wrapped_paragraph_pdf(
        "Es erschien Frau Erika Müller-Lüdenscheidt und erklärte sich.", width=150
    )
    found = R.build_plan(wrapped, R.Criteria.from_input([], ["Müller-Lüdenscheidt"])).candidates
    assert len(found) == 1

    def build(doc, page):
        page.insert_text((72, 100), "Antragsteller: Max", fontsize=11)
        page.insert_text((200, 100), "Mustermann", fontsize=11)

    plan = R.build_plan(make_pdf(build), R.Criteria.from_input([], ["Max Mustermann"]))
    assert [c.text for c in plan.candidates] == ["Max Mustermann"]
