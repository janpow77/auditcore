"""Schwärzung versteckter Ablagen: Metadaten, Kommentare, Alternativtexte (Prüfplan S, A)."""

from __future__ import annotations

import random
import re
import time

import pymupdf as fitz
import pytest
import redaction_corpus as kc
from redaction_support import (
    SECRET,
    apply_with,
    engine_apply,
    engine_plan,
    make_pdf,
    page_text,
    plan_of,
    raw,
    raw_pages,
    redacted,
)

from auditcore_pdf import redaction as R
from auditcore_pdf.redaction.raw_scan import _RawScanner

# ── S: Sicherheit der Entfernung ────────────────────────────────


def test_s01_s02_page_text_and_raw_bytes_clean():
    out = redacted(kc.pdf_from_lines([f"Kontakt: {SECRET}"]), ["email"])
    assert kc.leaks(out, SECRET) == []


@pytest.mark.parametrize(
    "where",
    [
        "metadata",
        "annotation",
        "toc",
        "link",
        "widget",
        "attachment",
        "white_text",
        "outside_cropbox",
    ],
)
def test_s03_to_s06_hidden_content_removed(where):
    src = kc.single_hidden_pdf(SECRET, where)
    assert kc.leaks(src, SECRET)  # Vorbedingung: der Fund ist lesbar
    out = redacted(src, ["email"])
    assert kc.leaks(out, SECRET) == []


@pytest.mark.parametrize("sanitize", [True, False])
def test_s03_hidden_content_without_sanitize(sanitize):
    # Auch ohne Bereinigung verschwinden die ausgewählten versteckten Fundstellen.
    pdf = kc.hidden_content_pdf(SECRET)
    out, report = apply_with(pdf, plan_of(pdf, ["email"]), sanitize=sanitize)
    assert kc.leaks(out, SECRET) == []
    assert report.hidden_removed > 0


def test_s07_image_pixels_under_finding_removed():
    src = kc.text_over_image_pdf(SECRET)
    with fitz.open(stream=src, filetype="pdf") as doc:
        box = doc[0].search_for(SECRET)[0]
    out = redacted(src, ["email"])
    with fitz.open(stream=out, filetype="pdf") as doc:
        pix = doc[0].get_pixmap(clip=box, dpi=72)
        red = sum(
            1
            for y in range(pix.height)
            for x in range(pix.width)
            if pix.pixel(x, y)[:3] == (200, 30, 30)
        )
        assert red == 0, f"{red} rote Pixel unter der Schwärzung"
        assert doc[0].get_images()  # Rest des Bildes bleibt erhalten


def test_s09_old_revision_not_shipped():
    old = "geheim@example.org"
    src = kc.old_revision_pdf(old, f"Kontakt: {SECRET}")
    # Vorbedingung: die erste gespeicherte Fassung enthält den alten Text noch
    assert len(kc.revisions(src)) == 2
    assert old in page_text(kc.revisions(src)[0])
    out = redacted(src, ["email"])
    assert len(kc.revisions(out)) == 1
    assert kc.leaks(out, old) == []


# ── A-H1: Alternativtexte, ActualText, PieceInfo, XFA ──────────


def _alt_text_pdf() -> bytes:
    def build(doc, page):
        page.insert_text((72, 60), "Bearbeiter Krause", fontsize=11)
        x = page.get_contents()[0]
        s = (
            doc.xref_stream(x)
            .replace(b"BT", b"/Span <</ActualText (Krause)>> BDC BT", 1)
            .replace(b"ET", b"ET EMC", 1)
        )
        doc.update_stream(x, s)
        pi = doc.get_new_xref()
        doc.update_object(pi, "<< /App << /Private (Original Krause) >> >>")
        doc.xref_set_key(page.xref, "PieceInfo", f"{pi} 0 R")
        xfa = doc.get_new_xref()
        doc.update_object(xfa, "<<>>")
        doc.update_stream(xfa, b"<xfa:datasets><name>Krause</name></xfa:datasets>", new=True)
        af = doc.get_new_xref()
        doc.update_object(af, f"<< /Fields [] /XFA {xfa} 0 R >>")
        doc.xref_set_key(doc.pdf_catalog(), "AcroForm", f"{af} 0 R")
        st = doc.get_new_xref()
        doc.update_object(
            st, "<< /Type /StructTreeRoot /K [<< /S /Figure /Alt (Foto Krause) >>] >>"
        )
        doc.xref_set_key(doc.pdf_catalog(), "StructTreeRoot", f"{st} 0 R")
        doc.set_metadata({"title": "Akte"})
        info = int(doc.xref_get_key(-1, "Info")[1].split()[0])
        doc.xref_set_key(info, "Bearbeiter", "(Krause)")
        mx = doc.get_new_xref()
        doc.update_object(mx, "<< /Type /Metadata /Subtype /XML >>")
        doc.update_stream(mx, b"<x:xmpmeta><dc:creator>Krause</dc:creator></x:xmpmeta>", new=True)
        doc.xref_set_key(page.xref, "Metadata", f"{mx} 0 R")

    return make_pdf(build)


@pytest.mark.parametrize("sanitize", [True, False])
def test_a_h1_alt_actualtext_pieceinfo_xfa_custom_info(sanitize):
    pdf = _alt_text_pdf()
    out, report = apply_with(pdf, plan_of(pdf, terms=["Krause"]), sanitize=sanitize)
    with fitz.open(stream=out, filetype="pdf") as doc:
        blobs = [doc.xref_object(x) for x in range(1, doc.xref_length())]
        blobs += [
            (doc.xref_stream(x) or b"").decode("latin-1")
            for x in range(1, doc.xref_length())
            if doc.xref_is_stream(x)
        ]
    assert not any("Krause" in b for b in blobs)
    if sanitize:
        assert "Anwendungsdaten" in report.sanitized


@pytest.mark.parametrize("extra", [None, "Anschrift: Krausestr. 5", "Herr Krausen kam"])
@pytest.mark.parametrize("sanitize", [True, False])
def test_a_hn1_alt_text_not_excused_by_longer_word(extra, sanitize):
    # „Krausestr.“ darf einen lesbaren Alternativtext „Foto Krause“ nicht entschuldigen.

    def build(doc, page):
        page.insert_text((72, 60), "Bearbeiter Krause", fontsize=11)
        if extra:
            page.insert_text((72, 90), extra, fontsize=11)
        st = doc.get_new_xref()
        doc.update_object(
            st, "<< /Type /StructTreeRoot /K [<< /S /Figure /Alt (Foto Krause) >>] >>"
        )
        doc.xref_set_key(doc.pdf_catalog(), "StructTreeRoot", f"{st} 0 R")
        x = page.get_contents()[0]
        s = (
            doc.xref_stream(x)
            .replace(b"BT", b"/Span <</ActualText (Krause)>> BDC BT", 1)
            .replace(b"ET", b"ET EMC", 1)
        )
        doc.update_stream(x, s)

    pdf = make_pdf(build)
    out, _ = engine_apply(pdf, engine_plan(pdf, ["Krause"]), sanitize=sanitize)
    blob = raw(out)
    assert b"Foto Krause" not in blob and b"(Krause)" not in blob


def test_a_metadata_and_sanitize_notes():
    # Bereinigung ohne Fundstellen: Metadaten, XMP, Anhang und JavaScript gehen.
    def build(doc, page):
        page.insert_text((72, 72), "Sachverhalt", fontsize=11)
        doc.set_metadata({"author": "Prüfer Beispiel", "title": "Akte"})
        doc.set_xml_metadata("<x:xmpmeta><dc:title>Akte</dc:title></x:xmpmeta>")
        doc.embfile_add("notiz.txt", b"Notiz", filename="notiz.txt")
        js = doc.get_new_xref()
        doc.update_object(js, "<< /S /JavaScript /JS (app.alert(1)) >>")
        doc.xref_set_key(doc.pdf_catalog(), "OpenAction", f"{js} 0 R")

    pdf = make_pdf(build)
    plan = plan_of(pdf, terms=["nichtvorhanden"])
    cleanup = plan["cleanup"]
    assert set(cleanup["metadata_fields"]) >= {"author", "title"}
    assert cleanup["xmp"] and cleanup["attachments"] == 1 and cleanup["javascript"]
    out, report = apply_with(pdf, plan, selected=[])
    assert {"Metadaten", "XMP-Metadaten", "Dateianhänge", "JavaScript"} <= set(report.sanitized)
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert not doc.embfile_names()
        assert not (doc.metadata or {}).get("author")
        assert not doc.get_xml_metadata()


# ── Lesezeichen (A-TOC, M-N1, M-N3) ─────────────────────────────


def test_a_toc_only_selected_hit_replaced():
    def build(doc, page):
        page.insert_text((72, 60), "Text", fontsize=11)
        doc.set_toc([[1, "Anhörung Krause und Meier", 1]])

    pdf = make_pdf(build)
    plan = plan_of(pdf, terms=["Krause", "Meier"])
    krause = [c["id"] for c in plan["candidates"] if c["text"] == "Krause"]
    out, _ = apply_with(pdf, plan, selected=krause, sanitize=False)
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert doc.get_toc()[0][1] == f"Anhörung {R.REDACTED_MARK} und Meier"


def test_a_mn1_deselected_bookmark_kept_despite_term_in_selected_email():
    def build(doc, page):
        page.insert_text((72, 100), "Kontakt max.mustermann@example.org", fontsize=11)
        doc.set_toc([[1, "Akte Mustermann", 1]])

    pdf = make_pdf(build)
    plan = engine_plan(pdf, ["Mustermann"], ["email"])
    keep = [c.id for c in plan.candidates if c.kind == "text"]
    out, _ = engine_apply(pdf, plan, keep, sanitize=False)
    with fitz.open(stream=out, filetype="pdf") as d:
        assert d.get_toc()[0][1] == "Akte Mustermann"
        assert "example.org" not in d[0].get_text()


@pytest.mark.parametrize("sep", ["​", "­"], ids=["nullbreite", "weich"])
def test_a_mn3_bookmark_with_invisible_characters(sep):
    def build(doc, page):
        page.insert_text((72, 60), "Text", fontsize=11)
        doc.set_toc([[1, f"Krause und Kra{sep}use", 1]])

    pdf = make_pdf(build)
    out, _ = engine_apply(pdf, engine_plan(pdf, ["Krause"]), sanitize=False)
    with fitz.open(stream=out, filetype="pdf") as d:
        assert d.get_toc()[0][1] == R.REDACTED_MARK


# ── Rohsuche in Objekten (M-N5, N3) ─────────────────────────────


def test_a_mn5_raw_scanner_matches_flat_alternation():
    # Die Vorauswahl über Präfixe findet dasselbe wie eine flache Alternative
    # mit Wortgrenzen.
    rnd = random.Random(7)
    forms = sorted(
        {
            "".join(rnd.choice("abc.@") for _ in range(rnd.randint(1, 6))).encode()
            for _ in range(300)
        }
    )
    alternation = b"|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
    flat = re.compile(
        rb"(?<![A-Za-z0-9/])(" + alternation + rb")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    scanner = _RawScanner({f: f.decode() for f in forms}, True)
    for _ in range(2000):
        blob = "".join(rnd.choice("abcABC.@ x/") for _ in range(40)).encode()
        hits: set[str] = set()
        scanner.scan(blob.lower(), hits)
        expected = {m.group(1).lower().decode() for m in flat.finditer(blob)}
        assert expected <= hits
        # Mehr Treffer nur durch überlappende Fundorte, die finditer überspringt.
        for h in hits - expected:
            pattern = rb"(?<![A-Za-z0-9/])" + re.escape(h.encode()) + rb"(?![A-Za-z0-9])"
            assert re.search(pattern, blob, re.IGNORECASE)


def test_a_mn5_short_term_still_replaced_in_alt_text():
    # Der Begriffsindex darf kurze Begriffe (unter drei Zeichen) nicht verlieren.

    def build(doc, page):
        page.insert_text((72, 60), "Herr Li kam", fontsize=11)
        st = doc.get_new_xref()
        doc.update_object(st, "<< /Type /StructTreeRoot /K [<< /S /Figure /Alt (Foto Li) >>] >>")
        doc.xref_set_key(doc.pdf_catalog(), "StructTreeRoot", f"{st} 0 R")

    pdf = make_pdf(build)
    out, _ = engine_apply(pdf, engine_plan(pdf, ["Li"]), sanitize=False)
    assert b"Foto Li" not in raw(out)


def test_a_n3_3_indirect_alt_text_replaced():
    def extra(doc):
        s = doc.get_new_xref()
        doc.update_object(s, "(Foto: Herr Krause, geb. 03.04.1961)")
        x = doc.get_new_xref()
        doc.update_object(x, f"<< /Type /StructElem /S /Figure /Alt {s} 0 R >>")
        doc.xref_set_key(
            doc.pdf_catalog(), "StructTreeRoot", f"<< /Type /StructTreeRoot /K [{x} 0 R] >>"
        )

    pdf = raw_pages(
        [
            b"BT /F1 12 Tf 72 700 Td (Herr Krause) Tj ET",
            b"BT /F1 12 Tf 72 700 Td (Ansprechpartner Krause) Tj ET",
        ],
        extra,
    )
    plan = engine_plan(pdf, ["Krause"])
    out, _ = engine_apply(pdf, plan, [c.id for c in plan.candidates if c.page == 1], sanitize=False)
    assert b"03.04.1961" not in raw(out)
    assert "Ansprechpartner Krause" in page_text(out)


def test_a_n3_5_short_key_leaves_foreign_alt_text():
    def extra(doc):
        x = doc.get_new_xref()
        doc.update_object(x, "<< /Type /StructElem /S /Figure /Alt (Abbildung: Lageplan) >>")
        doc.xref_set_key(
            doc.pdf_catalog(), "StructTreeRoot", f"<< /Type /StructTreeRoot /K {x} 0 R >>"
        )

    pdf = raw_pages([b"BT /F1 12 Tf 72 700 Td (Kennung AB) Tj ET"], extra)
    out, _ = engine_apply(pdf, engine_plan(pdf, ["AB"]), sanitize=False)
    assert b"Abbildung: Lageplan" in raw(out)
    assert "AB" not in page_text(out)


def test_a_n3_4_scanner_short_form_does_not_slow_long_forms():
    table = {f"+49 6{i:07d}".encode(): f"n{i}" for i in range(5000)}
    table[b"anna"] = "Anna"
    scanner = _RawScanner(table, True)
    blob = (b"+49 " * 20000) + b" +49 60000042 anna "
    t = time.time()
    hits: set[str] = set()
    scanner.scan(blob.lower(), hits)
    assert hits == {"n42", "Anna"}
    assert time.time() - t < 5


@pytest.mark.parametrize(
    "literal, expected",
    [
        (b"(Kra\\165se)", "Krause"),  # Oktal-Escape
        (b"<4B72617573 65>", "Krause"),  # Hex-String mit Leerraum
        (b"<FEFF004B0072006100750073>", "Kraus"),  # UTF-16 mit BOM
        (b"(Kra\\\nuse)", "Krause"),  # Zeilenfortsetzung
        (b"(Kr\\(a\\)use)", None),  # Klammern gehören zum Text
    ],
    ids=["oktal", "hex", "utf16", "fortsetzung", "klammern"],
)
def test_encoded_strings_in_objects_are_found(literal, expected):
    # Fundtexte in Objekten werden auch in kodierter Schreibweise gefunden.
    def extra(doc):
        x = doc.get_new_xref()
        doc.update_object(x, "<< /Type /StructElem /S /Figure /Alt " + literal.decode() + " >>")
        doc.xref_set_key(
            doc.pdf_catalog(), "StructTreeRoot", f"<< /Type /StructTreeRoot /K {x} 0 R >>"
        )

    pdf = raw_pages([b"BT /F1 12 Tf 72 700 Td (Herr Krause und Kraus) Tj ET"], extra)
    terms = [expected] if expected else ["Krause"]
    out, _ = engine_apply(pdf, engine_plan(pdf, terms), sanitize=False)
    if expected:
        assert literal not in raw(out)
