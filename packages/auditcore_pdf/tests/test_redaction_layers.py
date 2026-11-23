"""Schwärzung auf Ebenen (OCG/OCMD) und beschnittenen Seiten (CropBox, MediaBox)."""

from __future__ import annotations

import re

import pymupdf as fitz
import pytest
from redaction_support import (
    apply_with,
    dejavu,
    engine_apply,
    engine_plan,
    make_pdf,
    page_properties_key,
    page_text,
    plan_of,
    raw,
    raw_streams,
)

from auditcore_pdf import redaction as R

# ── Ebenen ──────────────────────────────────────────────────────


def test_a_h1_hidden_layer_and_outside_mediabox():
    # Text auf ausgeblendeter Ebene und außerhalb der MediaBox.

    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar", fontsize=11)
        ocg = doc.add_ocg("intern", on=False)
        page.insert_text((72, 100), "Krause intern", fontsize=11, oc=ocg)
        xref = page.get_contents()[0]
        page.insert_font("helv")
        doc.update_stream(
            xref,
            doc.xref_stream(xref) + b"\nBT /helv 11 Tf 1 0 0 1 72 -200 Tm (Krause unten) Tj ET",
        )

    pdf = make_pdf(build)
    plan = plan_of(pdf, terms=["Krause"])
    assert len(plan["candidates"]) == 2
    out, _ = apply_with(pdf, plan)
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert doc.get_layer().get("off"), "Ebene bleibt ausgeblendet"
    assert b"Krause" not in raw_streams(out)


def test_a_mn6_ocmd_all_off_layer_found_and_removed():
    def build(doc, page):
        page.insert_text((72, 72), "Sichtbar Krause", fontsize=11)
        g = doc.add_ocg("an", on=True)
        md = doc.get_new_xref()
        doc.update_object(md, f"<< /Type /OCMD /OCGs [{g} 0 R] /P /AllOff >>")
        page.insert_font("helv")
        res = page.get_contents()[0]
        rx, pre = page_properties_key(doc, page)
        doc.xref_set_key(rx, pre + "Properties", f"<< /MD1 {md} 0 R >>")
        doc.update_stream(
            res,
            doc.xref_stream(res)
            + b"\n/OC /MD1 BDC BT /helv 11 Tf 1 0 0 1 72 600 Tm (Krause verborgen) Tj ET EMC",
        )

    pdf = make_pdf(build)
    plan = engine_plan(pdf, ["Krause"])
    assert len(plan.candidates) == 2
    out, _ = engine_apply(pdf, plan)
    assert b"Krause verborgen" not in raw(out)
    with fitz.open(stream=out, filetype="pdf") as d:
        ocmd = [x for x in range(1, d.xref_length()) if d.xref_get_key(x, "Type")[1] == "/OCMD"]
        assert d.xref_get_key(ocmd[0], "P")[1] == "/AllOff"


def test_a_n3_1_layer_hidden_by_usage_viewstate():
    # Ebene mit /Usage/View/ViewState /OFF: MuPDF blendet sie aus. Der Text
    # muss trotzdem gefunden und geschwärzt werden.
    font = dejavu()

    def build(doc, page):
        ocg = doc.add_ocg("Notizen", on=True)
        doc.xref_set_key(ocg, "Usage", "<< /View << /ViewState /OFF >> >>")
        page.insert_text((72, 72), "Herr Krause", fontsize=11, fontname="dv", fontfile=font)
        page.insert_text(
            (72, 300), "Krause wohnt Hauptstr. 1", fontsize=11, fontname="dv", fontfile=font, oc=ocg
        )

    pdf = make_pdf(build)
    plan = engine_plan(pdf, ["Krause"])
    assert len(plan.candidates) == 2
    out, _ = engine_apply(pdf, plan, sanitize=False)
    with fitz.open(stream=out, filetype="pdf") as d:
        ocgs = [x for x in range(1, d.xref_length()) if d.xref_get_key(x, "Type")[1] == "/OCG"]
        assert d.xref_get_key(ocgs[0], "Usage/View/ViewState")[1] == "/OFF"  # wiederhergestellt
        for x in ocgs:
            d.xref_set_key(x, "Usage", "null")
        assert "Krause" not in "".join(p.get_text() for p in d)


@pytest.mark.parametrize(
    "ocmd",
    [
        "<< /Type /OCMD /OCGs [{g} 0 R] /P /AllOff >>",
        "<< /Type /OCMD /VE [/Not {g} 0 R] >>",
        "<< /Type /OCMD /OCGs {g} 0 R /P /AnyOff >>",
    ],
    ids=["alloff", "ve", "einzeln"],
)
def test_a_n3_6_direct_ocmd_in_properties(ocmd):
    def build(doc, page):
        page.insert_text((72, 72), "Herr Krause", fontsize=11)
        g = doc.add_ocg("an", on=True)
        page.insert_font("helv")
        rx, pre = page_properties_key(doc, page)
        doc.xref_set_key(rx, pre + "Properties", "<< /MD1 " + ocmd.format(g=g) + " >>")
        res = page.get_contents()[0]
        doc.update_stream(
            res,
            doc.xref_stream(res)
            + b"\n/OC /MD1 BDC BT /helv 11 Tf 1 0 0 1 72 600 Tm (Krause Geheim) Tj ET EMC",
        )

    pdf = make_pdf(build)
    plan = engine_plan(pdf, ["Krause"])
    assert len(plan.candidates) == 2
    out, _ = engine_apply(pdf, plan)
    assert b"Krause Geheim" not in raw(out)


def test_a_n3_7_layer_state_restored_exactly():
    def build(doc, page):
        page.insert_text((72, 72), "Herr Krause", fontsize=11)
        g = doc.add_ocg("an", on=True)
        md = doc.get_new_xref()
        doc.update_object(md, f"<< /Type /OCMD /OCGs [{g} 0 R] /P (AllOff) >>")
        rx, pre = page_properties_key(doc, page)
        doc.xref_set_key(rx, pre + "Properties", f"<< /MD1 {md} 0 R >>")
        page.insert_font("helv")
        res = page.get_contents()[0]
        doc.update_stream(
            res,
            doc.xref_stream(res)
            + b"\n/OC /MD1 BDC BT /helv 11 Tf 1 0 0 1 72 600 Tm (Anlage) Tj ET EMC",
        )

    def norm(objs):
        return [re.sub(r"\d+ 0 R", "N 0 R", o) for o in objs]

    pdf = make_pdf(build)
    with fitz.open(stream=pdf, filetype="pdf") as d:
        before = [
            d.xref_object(x, compressed=True)
            for x in range(1, d.xref_length())
            if "OCMD" in d.xref_object(x)
        ]
        cat_before = d.xref_get_key(d.pdf_catalog(), "OCProperties/D")[1]
    out, _ = engine_apply(pdf, engine_plan(pdf, ["Krause"]), sanitize=False)
    with fitz.open(stream=out, filetype="pdf") as d:
        after = [
            d.xref_object(x, compressed=True)
            for x in range(1, d.xref_length())
            if "OCMD" in d.xref_object(x)
        ]
        assert norm(after) == norm(before) and len(after) == 1
        cat_after = d.xref_get_key(d.pdf_catalog(), "OCProperties/D")[1]
        assert norm([cat_after]) == norm([cat_before])


def test_layer_configurations_and_radio_groups():
    # Weitere Ebenenkonfigurationen (/Configs) und gesperrte Ebenen werden
    # vorübergehend aufgedeckt und danach unverändert wiederhergestellt.
    def build(doc, page):
        page.insert_text((72, 72), "Herr Krause", fontsize=11)
        a = doc.add_ocg("a", on=False)
        b = doc.add_ocg("b", on=True)
        page.insert_text((72, 300), "Krause auf Ebene", fontsize=11, oc=a)
        cat = doc.pdf_catalog()
        doc.xref_set_key(cat, "OCProperties/D/RBGroups", f"[[{a} 0 R {b} 0 R]]")
        doc.xref_set_key(cat, "OCProperties/D/Locked", f"[{a} 0 R]")
        doc.xref_set_key(
            cat, "OCProperties/Configs", f"[<< /Name (Druck) /OFF [{a} 0 R] /BaseState /OFF >>]"
        )

    pdf = make_pdf(build)
    with fitz.open(stream=pdf, filetype="pdf") as d:
        before = d.xref_get_key(d.pdf_catalog(), "OCProperties")[1]
    plan = engine_plan(pdf, ["Krause"])
    assert len(plan.candidates) == 2
    out, _ = engine_apply(pdf, plan, sanitize=False)
    assert "Krause" not in page_text(out)
    with fitz.open(stream=out, filetype="pdf") as d:
        after = d.xref_get_key(d.pdf_catalog(), "OCProperties")[1]
    assert re.sub(r"\d+ 0 R", "N", after) == re.sub(r"\d+ 0 R", "N", before)


# ── CropBox und MediaBox ────────────────────────────────────────


@pytest.mark.parametrize(
    "mediabox, cropbox, rotate",
    [
        ("[100 100 700 900]", "[100 100 700 900]", 0),
        ("[100 100 700 900]", "[200 200 600 800]", 0),
        ("[0 -800 600 0]", "[50 -700 550 -100]", 90),
    ],
)
def test_a_h2_offset_mediabox(mediabox, cropbox, rotate):
    # H2: Versetzte MediaBox führte zu Abstürzen und falschen Anzeigerechtecken.

    def build(doc, page):
        page.insert_font("helv")
        c = doc.get_new_xref()
        doc.update_object(c, "<<>>")
        doc.update_stream(c, b"BT /helv 11 Tf 1 0 0 1 300 500 Tm (Krause) Tj ET", new=True)
        doc.xref_set_key(page.xref, "Contents", f"{c} 0 R")
        doc.xref_set_key(page.xref, "MediaBox", mediabox)
        doc.xref_set_key(page.xref, "CropBox", cropbox)
        doc.xref_set_key(page.xref, "Rotate", str(rotate))

    pdf = make_pdf(build)
    plan = plan_of(pdf, terms=["Krause"])
    assert len(plan["candidates"]) == 1
    if rotate == 0:
        # Anzeige-Rechteck gegen die Lage bei pdf.js prüfen: x = 300 im Nutzerraum
        crop = [float(v) for v in cropbox.strip("[]").split()]
        x0 = plan["candidates"][0]["rects"][0][0]
        assert abs(x0 - (300 - crop[0]) / (crop[2] - crop[0])) < 0.01
    out, _ = apply_with(pdf, plan)
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert doc.xref_get_key(doc[0].xref, "CropBox")[1] == cropbox
    assert b"Krause" not in raw_streams(out)


@pytest.mark.parametrize("box", [(-20, -20, 700, 900), (300, -50, 700, 400)])
@pytest.mark.parametrize("patterns", [(), ("ki_namen",)])
def test_cropbox_beyond_mediabox_plan_and_apply(box, patterns):
    # Eine CropBox darf über die MediaBox hinausragen. Vorschau und Anwendung
    # laufen dann durch, und die CropBox bleibt unverändert.
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((320, 100), "Das sagte Jan Reiter gestern.", fontsize=11)
    doc.xref_set_key(page.xref, "CropBox", "[{} {} {} {}]".format(*box))
    pdf = doc.tobytes()

    def ner(texts):
        return [[m.span() for m in re.finditer("Jan Reiter", t)] for t in texts]

    crit = R.Criteria(patterns, () if patterns else ("Jan Reiter",), False, True)
    plan = R.build_plan(pdf, crit, ner)
    assert [c.text for c in plan.candidates] == ["Jan Reiter"]
    sel = R.Selection(plan.sha256, crit, frozenset(c.id for c in plan.candidates), (), True)
    out, _ = R.apply_plan(pdf, sel, ner)
    with fitz.open(stream=out) as res:
        assert res.xref_get_key(res[0].xref, "CropBox") == ("array", "[{} {} {} {}]".format(*box))
        assert "Reiter" not in res[0].get_text(clip=fitz.INFINITE_RECT())


def test_ner_keeps_cropbox_for_page_geometry():
    # Die KI-Erkennung legt die CropBox nur vorübergehend auf die MediaBox;
    # Seitengröße und Koordinaten des Plans bleiben dieselben wie ohne KI.
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((100, 200), "Das sagte Reiter gestern.", fontsize=11)
    page.set_cropbox(fitz.Rect(50, 100, 545, 742))
    pdf = doc.tobytes()

    def ner(texts):
        return [[m.span() for m in re.finditer("Reiter", t)] for t in texts]

    with_ner = R.build_plan(pdf, R.Criteria(("ki_namen",), (), False, True), ner)
    plain = R.build_plan(pdf, R.Criteria((), ("Reiter",), False, True))
    sizes = {(p.pages[0].width, p.pages[0].height) for p in (with_ner, plain)}
    assert sizes == {(495, 642)}
    assert [(c.rects, c.view_rects) for c in with_ner.candidates] == [
        (c.rects, c.view_rects) for c in plain.candidates
    ]


@pytest.mark.parametrize("rotate", [90, 180, 270])
def test_area_on_rotated_cropped_page(rotate):
    # Eigener Bereich auf gedrehter, beschnittener Seite trifft den Text.
    def build(doc, page):
        page.insert_text((120, 200), "Gutachter Krause", fontsize=11)
        page.set_cropbox(fitz.Rect(50, 50, 545, 792))
        page.set_rotation(rotate)

    pdf = make_pdf(build)
    plan = plan_of(pdf, terms=["Krause"])
    rect = plan["candidates"][0]["rects"][0]
    out, _ = apply_with(pdf, plan, selected=[], areas=[{"page": 1, "rect": rect}])
    text = page_text(out)
    assert "Krause" not in text and "Gutachter" in text
