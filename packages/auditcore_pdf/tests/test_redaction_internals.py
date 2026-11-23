"""Randfälle der Schwärzung: Schutzpfade, defekte Objekte, interne Helfer.

Einige Zweige sind über die öffentliche Schnittstelle nur mit defekten
Dateien oder Bibliotheksfehlern erreichbar. Sie werden hier gezielt mit
Attrappen oder ersetzten Methoden angestoßen, damit auch die Schutzpfade
geprüft sind.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pymupdf as fitz
import pytest
from redaction_support import (
    engine_apply,
    engine_plan,
    fake_ner,
    findings,
    lines_pdf,
    make_pdf,
    page_text,
    plan_texts,
    raw,
    raw_pages,
)

from auditcore_pdf import redaction as R
from auditcore_pdf.redaction import layers as L
from auditcore_pdf.redaction import patterns as P
from auditcore_pdf.redaction.common import HIDDEN_GROUP, _flat
from auditcore_pdf.redaction.criteria import _matches, _Rule
from auditcore_pdf.redaction.expectation import _Expectation
from auditcore_pdf.redaction.groups import _inside_other, _positions, _same_text
from auditcore_pdf.redaction.hidden import _info_xref
from auditcore_pdf.redaction.layers import _ViewTransform
from auditcore_pdf.redaction.ner_text import (
    _hard_parts,
    _line_segments,
    _merge_spans,
    _short_segments,
)
from auditcore_pdf.redaction.page_text import _page_text, _PageText, _PageTextBuilder
from auditcore_pdf.redaction.pdf_strings import _decode_literal, _decode_pdf_bytes, _pdf_strings
from auditcore_pdf.redaction.plan import Candidate
from auditcore_pdf.redaction.raw_scan import (
    _font_file_xrefs,
    _raw_contains,
    _RawContents,
    _RawScanner,
)
from auditcore_pdf.redaction.scan import _PageScanner
from auditcore_pdf.redaction.selection import Selection
from auditcore_pdf.redaction.verify import _verify, _word_in

NAME = "Erika Musterfrau"


def _all_selected(pdf: bytes, terms=(NAME,), sanitize=True):
    crit = R.Criteria((), tuple(terms), False, True)
    plan = R.build_plan(pdf, crit)
    sel = Selection(plan.sha256, crit, frozenset(c.id for c in plan.candidates), (), sanitize)
    return plan, sel


def _raising_for(method, should_raise):
    """Ersetzt eine Document-Methode, die für bestimmte Aufrufe ausfällt."""

    def run(self, *args, **kwargs):
        if should_raise(*args):
            raise RuntimeError("defektes Objekt")
        return method(self, *args, **kwargs)

    return run


# ── Musterprüfungen ─────────────────────────────────────────────


def test_pattern_validators_reject_edge_values():
    assert not P._iban_ok("DE89 3704 0044 0532 0130 00")  # Leerzeichen: nicht alphanumerisch
    assert not P._iban_ok("DE8937040044053201300ä")
    assert not P._tax_id_ok("01234567891")  # führende Null
    assert P._tax_id_ok("10000000000")  # Prüfziffer 10 wird zu 0
    assert P._validate_phone("Tel. 12345", 5, 10) is None  # zu wenige Ziffern
    assert P._validate_ip("IP 300.1.1.1", 3, 12) is None
    assert findings(lines_pdf(["Server 300.10.10.10 antwortet"]), ["ip_adresse"]) == []


def test_empty_regex_matches_are_skipped():
    # Ein Ausdruck, der auch leer passt, liefert keine leeren Fundstellen.
    rule = _Rule("x", re.compile(r"a*"))
    assert list(_matches(rule, "baab")) == [(1, 3)]


# ── Zeichenketten in PDF-Objekten ───────────────────────────────


def test_pdf_string_decoding_edges():
    assert _decode_pdf_bytes(b"\xef\xbb\xbfMusterfrau") == "Musterfrau"
    assert _decode_literal("Erika\\") == "Erika"  # Rückstrich am Ende
    assert _decode_literal("a\\nb\\tc") == "a\nb\tc"
    assert _decode_literal("Muster\\\r\nfrau") == "Musterfrau"  # Fortsetzung mit CRLF
    assert list(_pdf_strings("/T <4142")) == []  # Hex-Zeichenkette ohne Ende


def test_pdf_strings_nesting_escapes_and_hex_edges():
    # Verschachtelte Klammern und maskierte Klammer bleiben in einer Zeichenkette.
    src = "/T (Akte (Muster\\) frau)) /U <41424> /V <zz> /W << /X 1 >>"
    found = list(_pdf_strings(src))
    assert found[0] == (3, src.index(" /U"), "Akte (Muster) frau)")
    # Ungerade Ziffernzahl: mit 0 aufgefüllt („AB@“); ungültige Hexziffern übersprungen.
    assert [t for _s, _e, t in found[1:]] == ["AB@"]


# ── Seitentext ──────────────────────────────────────────────────


def _line(chars, bbox=(10, 10, 100, 20)):
    return {"bbox": bbox, "spans": [{"chars": [{"c": c, "bbox": b} for c, b in chars]}]}


def test_page_text_builder_edges():
    b = _PageTextBuilder()
    b.add_line(_line([("​", (10, 10, 11, 20))]))  # nur unsichtbare Zeichen
    assert b.result().text == ""
    b.add_line(_line([("̈", (10, 10, 12, 20)), ("a", (12, 10, 18, 20))]))
    assert b.result().text == "a"  # Kombinationszeichen ohne Grundbuchstaben entfällt
    b.add_line(_line([("½", (10, 30, 22, 40)), ("¨", (22, 30, 28, 40))], (10, 30, 28, 40)))
    pt = b.result()
    assert pt.text.endswith("1⁄2 ̈")
    split = [r for c, r in zip(pt.text, pt.rects, strict=True) if c in "1⁄2"]
    assert split[0][2] == pytest.approx(14) and split[2][0] == pytest.approx(18)


def test_page_text_skips_non_text_blocks():
    fake = SimpleNamespace(
        get_text=lambda *a, **k: {
            "blocks": [{"type": 1}, {"type": 0, "lines": [_line([("A", (1, 1, 5, 9))])]}]
        }
    )
    assert _page_text(fake).text == "A"


def test_compatibility_characters_are_searchable():
    # „½“ (Helvetica, WinAnsi) zerfällt in „1⁄2“; die Breite wird aufgeteilt.
    pdf = lines_pdf(["Anteil ½ an Musterfrau"])
    assert [f.text for f in findings(pdf, terms=["Musterfrau"])] == ["Musterfrau"]


# ── Fundstellen auf der Seite ───────────────────────────────────


def test_page_scanner_ignores_matches_without_glyphs():
    pt = _PageText("a  b", [(0, 0, 5, 9), None, None, (9, 0, 14, 9)], [0, 0, 0, 0], [])
    with fitz.open() as doc:
        scanner = _PageScanner(0, pt, _ViewTransform(doc.new_page()))
        scanner.add("x", 1, 3, 0)
    assert scanner.found == []


def test_hyphen_term_also_found_without_hyphen():
    # Getrennt und ungetrennt auf derselben Seite: beide Fundstellen.
    pdf = lines_pdf(["Frau Muster-", "frau und Musterfrau kamen."])
    assert len(findings(pdf, terms=["Musterfrau"])) == 2


# ── Erwartung und Nachprüfung ───────────────────────────────────


def test_expectation_with_unsure_position_counts_by_text():
    pt = _PageText("Erika Musterfrau", [(0, 0, 1, 1)] * 16, [0] * 16, [])
    exp = _Expectation([pt])
    wrong = Candidate("a", "text", "x", "Max Mustermann", page=1, start=0, end=16)
    outside = Candidate("b", "text", "x", "Erika", page=5, start=0, end=5)
    exp.add_candidates([wrong, outside])
    assert exp.masks[0] is None and exp.masks[4] is None
    exp.cover(0, [1, 2])  # bleibt unsicher
    assert exp.masks[0] is None


def test_nested_hidden_candidates_count_once():
    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar", fontsize=11)
        doc.set_metadata({"title": "Antrag Erika Musterfrau"})

    pdf = make_pdf(build)
    plan, sel = _all_selected(pdf, terms=(NAME, "Musterfrau"))
    hidden = [c for c in plan.candidates if c.kind != "text"]
    assert len(hidden) == 2
    short = min(hidden, key=lambda c: len(c.text))
    assert _inside_other(short, hidden)
    out, _ = R.apply_plan(pdf, sel)
    assert b"Musterfrau" not in raw(out)


def test_group_helpers_edges():
    assert _positions("abc", "") == []
    assert _same_text("Muster-\x00frau", "Musterfrau")
    assert not _same_text("Muster", "Musterfrau")
    assert not _word_in("erika", " ")


def _metadata_pdf() -> bytes:
    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar", fontsize=11)
        doc.set_metadata({"author": "Erika Musterfrau"})

    return make_pdf(build)


def test_verify_reports_metadata_left_after_sanitize():
    pdf = _metadata_pdf()
    sel = Selection("x", R.Criteria((), (), False, True), frozenset(), (), True)
    with pytest.raises(R.RedactionVerificationError) as err:
        _verify(pdf, sel, {}, {})
    assert "Metadaten oder Anhänge nicht entfernt" in str(err.value.problems)


def test_verify_reports_raw_leftovers():
    # Text in einem Objekt, das kein Seitentext und keine Ablage ist.
    def extra(doc):
        x = doc.get_new_xref()
        doc.update_object(x, "<< /Notiz (Erika Musterfrau) >>")

    out = raw_pages([b"BT /F1 11 Tf 72 720 Td (Sichtbar) Tj ET"], extra)
    sel = Selection("x", R.Criteria((), (), False, True), frozenset(), (), False)
    key = _flat(NAME)
    with pytest.raises(R.RedactionVerificationError) as err:
        _verify(out, sel, {(HIDDEN_GROUP, key): 0}, {(HIDDEN_GROUP, key): {NAME}})
    assert any("Rohdaten" in p for p in err.value.problems)


# ── Rohdatensuche ───────────────────────────────────────────────


def test_raw_scanner_long_forms_with_same_prefix():
    table = {b"erika musterfrau a": "A", b"erika musterfrau b": "B"}
    hits: set[str] = set()
    _RawScanner(table, False).scan(b"xx erika musterfrau a", hits)
    assert hits == {"A"}


class _BrokenDoc:
    """Dokument, dessen Objekte sich nicht lesen lassen."""

    def __iter__(self):
        return iter([SimpleNamespace(get_contents=lambda: [])])

    def xref_length(self):
        return 3

    def xref_get_key(self, xref, key):
        raise RuntimeError("defekt")


def test_raw_scan_skips_unreadable_objects():
    doc = _BrokenDoc()
    assert _font_file_xrefs(doc) == set()
    assert _RawContents(doc).blobs(1) == ()
    assert _raw_contains(doc, ["Musterfrau"]) == (set(), set())


def test_raw_scan_stops_when_everything_found():
    def extra(doc):
        for _ in range(3):
            x = doc.get_new_xref()
            doc.update_object(x, "<< /Notiz (Erika Musterfrau) >>")

    out = raw_pages([b"BT /F1 11 Tf 72 720 Td (Sichtbar) Tj ET"], extra)
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert _raw_contains(doc, [NAME]) == ({NAME}, set())


# ── Versteckte Ablagen ──────────────────────────────────────────


def test_unreadable_trailer_and_attachment(monkeypatch):
    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar", fontsize=11)
        doc.embfile_add("notiz.txt", b"Erika Musterfrau", filename="notiz.txt")

    pdf = make_pdf(build)
    monkeypatch.setattr(
        fitz.Document,
        "embfile_get",
        _raising_for(fitz.Document.embfile_get, lambda *a: True),
    )
    monkeypatch.setattr(
        fitz.Document,
        "xref_get_key",
        _raising_for(fitz.Document.xref_get_key, lambda xref, key: xref == -1),
    )
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        assert _info_xref(doc) == 0
    plan = R.build_plan(pdf, R.Criteria((), (NAME,), False, True))
    # Der Anhang zählt mit seinem Namen, der Inhalt ist nicht lesbar.
    assert all("Musterfrau" not in c.text for c in plan.candidates)


# ── Bereinigung bei defekten Objekten ───────────────────────────


def _alt_pdf() -> bytes:
    content = (
        b"/Span << /ActualText (Erika Musterfrau /Alt <41>) >> BDC "
        b"BT /F1 11 Tf 72 720 Td (Erika Musterfrau) Tj ET EMC"
    )
    return raw_pages([content])


def test_stream_text_key_inside_replaced_string():
    # „/Alt“ innerhalb einer schon ersetzten ActualText-Zeichenkette zählt nicht neu.
    pdf = _alt_pdf()
    _plan, sel = _all_selected(pdf)
    out, report = R.apply_plan(pdf, sel)
    assert b"Musterfrau" not in raw(out)
    assert report.redactions >= 1


@pytest.mark.parametrize(
    "method, step",
    [
        ("xref_object", "_scrub_strings"),
        ("xref_is_stream", "_scrub_strings"),
        ("xref_get_keys", "_sanitize"),
    ],
)
def test_scrub_skips_unreadable_objects(monkeypatch, method, step):
    # Ein Objekt, das sich nicht lesen lässt, bricht die Bereinigung nicht ab.
    from auditcore_pdf.redaction import apply as A

    pdf = _alt_pdf()
    _plan, sel = _all_selected(pdf)
    active: list[bool] = []
    real_step = getattr(A, step)

    def guarded(*args, **kwargs):
        active.append(True)
        try:
            return real_step(*args, **kwargs)
        finally:
            active.clear()

    monkeypatch.setattr(A, step, guarded)
    original = getattr(fitz.Document, method)
    monkeypatch.setattr(
        fitz.Document, method, _raising_for(original, lambda xref, *a: bool(active) and xref == 1)
    )
    out, _report = R.apply_plan(pdf, sel)
    assert "Musterfrau" not in page_text(out)


def test_custom_info_keys_cleared_when_metadata_stays(monkeypatch):
    # Lässt set_metadata({}) das Info-Wörterbuch stehen, werden alle Schlüssel geleert.
    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar", fontsize=11)
        doc.set_metadata({"title": "Akte", "author": "Sachbearbeitung"})

    pdf = make_pdf(build)
    monkeypatch.setattr(fitz.Document, "set_metadata", lambda self, m: None)
    sel = Selection(
        R.build_plan(pdf, R.Criteria((), (), False, True)).sha256,
        R.Criteria((), (), False, True),
        frozenset(),
        (),
        True,
    )
    out, report = R.apply_plan(pdf, sel)
    assert "Metadaten" in report.sanitized
    assert b"Sachbearbeitung" not in raw(out)


def test_layer_restore_tolerates_broken_object(monkeypatch):
    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar", fontsize=11)
        ocg = doc.add_ocg("intern", on=False)
        page.insert_text((72, 100), "Erika Musterfrau intern", fontsize=11, oc=ocg)

    pdf = make_pdf(build)
    _plan, sel = _all_selected(pdf)

    def boom(*a, **k):
        raise RuntimeError("defekt")

    monkeypatch.setattr(L, "re", SimpleNamespace(escape=re.escape, sub=boom))
    out, _report = R.apply_plan(pdf, sel)
    assert "Musterfrau" not in page_text(out)


# ── Formularfelder und Kommentare ───────────────────────────────


def test_annotations_under_redaction_are_removed():
    def build(doc, page):
        page.insert_text((72, 72), "Antrag Erika Musterfrau", fontsize=11)
        hit = page.search_for(NAME)[0]
        page.add_highlight_annot(hit)
        page.add_text_annot((400, 400), "Unbeteiligt")

    pdf = make_pdf(build)
    plan = engine_plan(pdf, terms=[NAME])
    out, _report = engine_apply(pdf, plan)
    with fitz.open(stream=out, filetype="pdf") as doc:
        kinds = [a.type[1] for a in doc[0].annots()]
    assert kinds == ["Text"]


# ── KI-Hilfsfunktionen ──────────────────────────────────────────


def test_ner_text_helpers_edges():
    assert _hard_parts(" (Jan Reiter), ", 0, 15) == [(2, 12)]
    pt = _PageText(" Jan  \x00 ", [None] * 8, [0, 0, 0, 0, 0, 0, -1, 1], [])
    assert _line_segments(pt) == [(1, 4)]
    assert _short_segments("Jan Reiter  \x00Eva") == [(0, 10), (13, 16)]
    assert _merge_spans([(5, 9), (0, 3), (2, 6), (12, 14)]) == [(0, 9), (12, 14)]


def test_ner_list_form_needs_full_span():
    # Die KI meldet in der Listenform „Preis, Petra“ nur einen Teil: kein Beleg.
    found = plan_texts(lines_pdf(["Preis, Petra"]), fake_ner("Petra"))
    assert all(t != "Preis, Petra" for _p, _s, t in found)
