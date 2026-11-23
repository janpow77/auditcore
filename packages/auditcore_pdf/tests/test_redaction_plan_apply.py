"""Schwärzung mit Pflichtvorschau: Plan → Auswahl → Anwendung (Prüfplan G, A)."""

from __future__ import annotations

import pymupdf as fitz
import pytest
import redaction_corpus as kc
from redaction_support import (
    SECRET,
    apply_with,
    dejavu,
    engine_apply,
    engine_plan,
    make_pdf,
    page_text,
    plan_of,
    selection_payload,
    skip_redaction_below,
)

from auditcore_pdf import redaction as R

# ── G: Plan, Auswahl, Anwendung ─────────────────────────────────


def test_g01_plan_lists_text_and_hidden_findings():
    plan = plan_of(kc.hidden_content_pdf(SECRET), ["email"])
    locations = {c["location"] for c in plan["candidates"]}
    assert "Seitentext" in locations
    assert {"Lesezeichen", "Kommentar", "Link", "XMP-Metadaten"} <= locations
    assert any(loc.startswith("Formularfeld") for loc in locations)
    assert any(loc.startswith("Dateianhang") for loc in locations)
    assert any(loc.startswith("Metadaten") for loc in locations)
    text = [c for c in plan["candidates"] if c["kind"] == "text"][0]
    x0, y0, x1, y1 = text["rects"][0]
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    assert plan["cleanup"]["attachments"] == 1
    assert plan["version"] == R.PLAN_VERSION
    assert plan["page_count"] == len(plan["pages"]) == 1
    hidden = [c for c in plan["candidates"] if c["kind"] == "hidden"]
    assert all(c["pdf_rect"] is None or len(c["pdf_rect"]) == 4 for c in hidden)


def test_g02_deselected_finding_stays_readable():
    pdf = kc.pdf_from_lines(["Herr Meier schreibt.", "Frau Meier antwortet."])
    plan = plan_of(pdf, terms=["Meier"])
    assert plan["total"] == 2
    first, _second = plan["candidates"]
    out, report = apply_with(pdf, plan, selected=[first["id"]])
    text = page_text(out)
    assert "Herr" in text and "Frau Meier" in text
    assert text.count("Meier") == 1
    assert report.redactions == 1 and report.deselected == 1
    assert report.to_dict()["verified"] is True


def test_g03_identical_plan_ids_are_stable():
    pdf = kc.pdf_from_lines([f"Kontakt {SECRET}", "Konto DE89 3704 0044 0532 0130 00"])
    a = plan_of(pdf, ["email", "iban"])
    b = plan_of(pdf, ["email", "iban"])
    assert [c["id"] for c in a["candidates"]] == [c["id"] for c in b["candidates"]]


def test_g04_plan_for_other_file_is_stale():
    pdf = kc.pdf_from_lines([f"Kontakt {SECRET}"])
    plan = plan_of(pdf, ["email"])
    other = kc.pdf_from_lines([f"Anderer Kontakt {SECRET}"])
    with pytest.raises(R.RedactionStaleError, match="anderen Datei"):
        apply_with(other, plan)


def test_g05_unknown_id_is_stale():
    pdf = kc.pdf_from_lines([f"Kontakt {SECRET}"])
    plan = plan_of(pdf, ["email"])
    with pytest.raises(R.RedactionStaleError, match="passen nicht mehr"):
        apply_with(pdf, plan, selected=["0" * 16])


def test_g05_stale_selection_after_changed_criteria():
    # Kennungen aus einem Plan mit anderen Kriterien passen nicht mehr.
    pdf = kc.pdf_from_lines([f"Kontakt {SECRET}", "Herr Meier"])
    plan = plan_of(pdf, ["email"])
    plan["criteria"] = {"patterns": [], "terms": ["Meier"]}
    with pytest.raises(R.RedactionStaleError):
        apply_with(pdf, plan)


def test_g06_manual_area_redacts_text():
    pdf = kc.pdf_from_lines(["Unterschrift: Max Mustermann", "Rest bleibt"])
    plan = plan_of(pdf, terms=["nichtvorhanden"])
    assert plan["total"] == 0
    page = plan["pages"][0]
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        box = doc[0].search_for("Max Mustermann")[0]
    w, h = page["width"], page["height"]
    area = [box.x0 / w, box.y0 / h, box.x1 / w, box.y1 / h]
    out, report = apply_with(pdf, plan, selected=[], areas=[{"page": 1, "rect": area}])
    text = page_text(out)
    assert "Mustermann" not in text and "Rest bleibt" in text
    assert report.areas == 1 and report.pages == [1]


def test_g07_rotated_page_rects_match_display():
    doc = fitz.open()
    page = doc.new_page(width=400, height=600)
    page.insert_text((50, 100), SECRET, fontsize=14)
    page.set_rotation(90)
    pdf = doc.tobytes()
    pix = page.get_pixmap(dpi=72)
    dark = [(x, y) for y in range(pix.height) for x in range(pix.width) if pix.pixel(x, y)[0] < 100]
    doc.close()
    plan = plan_of(pdf, ["email"])
    x0, y0, x1, y1 = plan["candidates"][0]["rects"][0]
    info = plan["pages"][0]
    assert (info["width"], info["height"]) == (600, 400)
    assert info["rotation"] == 90
    cx = sum(x for x, _ in dark) / len(dark) / pix.width
    cy = sum(y for _, y in dark) / len(dark) / pix.height
    assert x0 <= cx <= x1 and y0 <= cy <= y1
    # Bereich in Anzeigekoordinaten auf gedrehter Seite
    out, _ = apply_with(pdf, plan, selected=[], areas=[{"page": 1, "rect": [x0, y0, x1, y1]}])
    assert SECRET not in page_text(out)


def test_g08_fail_closed_when_text_survives(monkeypatch):
    # Lässt die Schwärzung Text stehen, wird nichts ausgeliefert.
    monkeypatch.setattr(fitz.Page, "apply_redactions", lambda self, *a, **k: True)
    pdf = kc.pdf_from_lines([f"Kontakt {SECRET}"])
    plan = plan_of(pdf, ["email"])
    with pytest.raises(R.RedactionVerificationError) as info:
        apply_with(pdf, plan)
    assert "Nachprüfung" in str(info.value)
    assert SECRET not in str(info.value)
    assert info.value.problems


def test_g09_sanitize_removes_metadata_and_attachments():
    pdf = kc.hidden_content_pdf(SECRET)
    plan = plan_of(pdf, ["email"])
    out, report = apply_with(pdf, plan)
    assert kc.leaks(out, SECRET) == []
    # Fundstellen in Metadaten und Anhängen sind schon als versteckte Inhalte entfernt.
    assert report.hidden_removed >= 5
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert not doc.embfile_names()
        assert not any((doc.metadata or {}).get(k) for k in ("author", "title", "subject"))


def test_g10_nothing_selected_only_sanitizes():
    # Ohne Auswahl wird trotzdem bereinigt und nachgeprüft.
    pdf = kc.pdf_from_lines(["Nur Sachverhalt"])
    plan = plan_of(pdf, ["email"], ["Meier"])
    out, report = apply_with(pdf, plan, selected=[])
    assert "Nur Sachverhalt" in page_text(out)
    assert report.redactions == 0
    with pytest.raises(R.RedactionError, match="Keine Fundstelle und kein Bereich"):
        apply_with(pdf, plan, selected=[], sanitize=False)


def test_g11_redact_all_without_findings():
    pdf = kc.pdf_from_lines(["Nur harmloser Text"])
    out, report, plan = R.redact_all(pdf, R.Criteria.from_input(["iban"]), sanitize=False)
    assert out == pdf and report.redactions == 0 and plan.candidates == []
    out, report, plan = R.redact_all(pdf, R.Criteria.from_input(["iban"]))
    assert out != pdf and plan.candidates == []


def test_g12_scanned_page_flagged_in_plan():
    plan = plan_of(kc.scanned_pdf(SECRET), ["email"])
    assert plan["pages_without_text"] == [1]
    assert plan["total"] == 0
    assert plan["pages"][0]["has_text"] is False


def test_g13_outside_cropbox_flagged():
    pdf = kc.single_hidden_pdf(SECRET, "outside_cropbox")
    plan = plan_of(pdf, ["email"])
    outside = [c for c in plan["candidates"] if c["outside_view"]]
    assert len(outside) == 1
    out, _ = apply_with(pdf, plan)
    assert kc.leaks(out, SECRET) == []
    with fitz.open(stream=out, filetype="pdf") as doc:
        assert doc[0].cropbox == fitz.Rect(0, 0, 595, 700)


# ── Unlesbare und geschützte Dateien (R) ────────────────────────


def test_r01_encrypted_pdf_rejected_cleanly():
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), SECRET)
    enc = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="geheim", owner_pw="geheim")
    doc.close()
    with pytest.raises(R.RedactionError, match="passwortgeschützt"):
        plan_of(enc, ["email"])


def test_r03_garbage_rejected_cleanly():
    with pytest.raises(R.RedactionError, match="keine lesbare PDF"):
        plan_of(b"kein PDF", ["email"])


def test_r04_pdf_without_pages_rejected(monkeypatch):
    # Eine PDF ohne Seiten lässt sich mit MuPDF nicht speichern; die Prüfung
    # greift beim Öffnen und wird über eine leere Seitenzahl ausgelöst.
    pdf = kc.pdf_from_lines(["x"])
    monkeypatch.setattr(fitz.Document, "page_count", property(lambda self: 0))
    with pytest.raises(R.RedactionError, match="keine Seiten"):
        plan_of(pdf, terms=["x"])


# ── Auswahl aus ungeprüftem JSON ────────────────────────────────


@pytest.mark.parametrize(
    "payload, message",
    [
        ("kaputt", "JSON-Objekt sein"),
        ([], "JSON-Objekt sein"),
        ({"selected": "abc"}, "„selected“"),
        ({"selected": [1]}, "„selected“"),
        ({"selected": [], "criteria": "kaputt"}, "„criteria“ muss"),
        ({"selected": [], "criteria": {"patterns": "email"}}, "criteria.patterns"),
        ({"selected": [], "criteria": {"terms": [1, 2]}}, "criteria.terms"),
        ({"selected": [], "criteria": {"patterns": ["nix"]}}, "Unbekannte Muster"),
        ({"selected": [], "areas": "x"}, "Höchstens 500 Bereiche"),
        ({"selected": [], "areas": [{}] * 501}, "Höchstens 500 Bereiche"),
        ({"selected": [], "areas": ["x"]}, "braucht „page“ und „rect“"),
        ({"selected": [], "areas": [{"page": 1}]}, "ganze Zahl"),
        ({"selected": [], "areas": [{"page": True, "rect": [0, 0, 1, 1]}]}, "ganze Zahl"),
        ({"selected": [], "areas": [{"page": 1.5, "rect": [0, 0, 1, 1]}]}, "ganze Zahl"),
        ({"selected": [], "areas": [{"page": 1, "rect": 5}]}, "ganze Zahl"),
        ({"selected": [], "areas": [{"page": 1, "rect": [0, 0, 1]}]}, "ganze Zahl"),
        ({"selected": [], "areas": [{"page": 1, "rect": ["a", 0, 1, 1]}]}, "ganze Zahl"),
        ({"selected": [], "areas": [{"page": 1, "rect": [float("nan"), 0, 1, 1]}]}, "ganze"),
        ({"selected": [], "areas": [{"page": 1, "rect": [float("inf"), 0, 1, 1]}]}, "ganze"),
        ({"selected": [], "areas": [{"page": 1, "rect": [10**400, 0, 1, 1]}]}, "ganze Zahl"),
    ],
)
def test_a_m5_malformed_selection_rejected(payload, message):
    with pytest.raises(R.RedactionError, match=message):
        R.Selection.from_dict(payload)


def test_selection_from_dict_defaults_and_area_normalisation():
    sel = R.Selection.from_dict(
        {
            "selected": ["a"],
            "areas": [
                {"page": 2, "rect": [0.8, 0.9, -0.5, 0.1]},  # vertauscht und über den Rand
                {"page": 1, "rect": [0.5, 0.5, 0.5, 0.7]},  # ohne Fläche: verworfen
                {"page": 1, "rect": [1.2, 0.1, 1.5, 0.2]},  # ganz außerhalb: verworfen
            ],
        }
    )
    assert sel.sha256 == "" and sel.sanitize is True
    assert sel.criteria == R.Criteria()
    assert sel.areas == (R.Area(2, (0.0, 0.1, 0.8, 0.9)),)


def test_a_h3_area_limits_per_page():
    pdf = kc.pdf_from_lines(["Text"])
    plan = plan_of(pdf, terms=["Text"])
    many = [{"page": 1, "rect": [0.1, 0.1, 0.2, 0.2]}] * (R.MAX_AREAS_PER_PAGE + 1)
    with pytest.raises(R.RedactionError, match="je Seite \\(Seite 1\\)"):
        apply_with(pdf, plan, areas=many)


def test_area_on_missing_page_rejected():
    pdf = kc.pdf_from_lines(["Text"])
    plan = plan_of(pdf, terms=["Text"])
    with pytest.raises(R.RedactionError, match="Seite 3: Seite gibt es nicht"):
        apply_with(pdf, plan, areas=[{"page": 3, "rect": [0.1, 0.1, 0.2, 0.2]}])


def test_selection_payload_roundtrip_is_json():
    pdf = kc.pdf_from_lines([f"Kontakt {SECRET}"])
    plan = plan_of(pdf, ["email"])
    sel = R.Selection.from_dict(selection_payload(plan, sanitize=False))
    assert sel.sanitize is False and sel.sha256 == plan["sha256"]
    assert sel.selected == {c["id"] for c in plan["candidates"]}


# ── A: Befunde der Code-Prüfungen ───────────────────────────────


@pytest.mark.parametrize(
    "lines, terms",
    [
        (["Herr Mustermann kam.", "Gez. MUSTERMANN"], ["Mustermann"]),
        (["Max Mustermann kam.", "Gez. Herr Mustermann"], ["Max Mustermann", "Mustermann"]),
    ],
    ids=["schreibweise", "verschachtelt"],
)
def test_a_k1_variants_and_nesting_fail_closed(monkeypatch, lines, terms):
    # K1: Schreibvarianten und verschachtelte Begriffe werden mitgezählt.
    pdf = kc.pdf_from_lines(lines)
    plan = plan_of(pdf, terms=terms)
    first_line = min(c["pdf_rect"][1] for c in plan["candidates"])
    skip_redaction_below(monkeypatch, first_line + 5)
    with pytest.raises(R.RedactionVerificationError, match="Seite 1"):
        apply_with(pdf, plan)


def test_a_k1_listbox_option_removed():
    # K1: Darstellung eines Auswahlfelds steht im Seitentext – das Feld wird entfernt.

    def build(doc, page):
        page.insert_text((72, 60), "Akte Krüger", fontsize=11)
        w = fitz.Widget()
        w.field_type = fitz.PDF_WIDGET_TYPE_LISTBOX
        w.field_name = "liste"
        w.rect = fitz.Rect(72, 150, 300, 220)
        w.choice_values = ["Meier", "KRÜGER", "Schmidt"]
        w.field_value = "Meier"
        page.add_widget(w)

    pdf = make_pdf(build)
    out, _ = apply_with(pdf, plan_of(pdf, terms=["Krüger"]))
    assert "krüger" not in page_text(out).casefold()
    assert b"KR\xc3\x9cGER" not in out


def test_a_m7_term_inside_deselected_email_stays_own_finding():
    pdf = kc.pdf_from_lines(["Kontakt max.mustermann@example.org"])
    plan = plan_of(pdf, ["email"], ["mustermann"])
    assert sorted(c["source"] for c in plan["candidates"]) == ["begriff:mustermann", "email"]
    only_term = [c["id"] for c in plan["candidates"] if c["source"].startswith("begriff:")]
    out, _ = apply_with(pdf, plan, selected=only_term)
    assert "mustermann" not in page_text(out).casefold()


@pytest.mark.parametrize("skip", [False, True], ids=["greift", "ausfall"])
def test_a_m3_area_verified_on_cropped_page(monkeypatch, skip):
    # M3: Eigener Bereich auf beschnittener Seite wird nachgeprüft.

    def build(doc, page):
        page.insert_text((120, 160), "Gutachter Krause", fontsize=11)
        page.set_cropbox(fitz.Rect(50, 50, 545, 792))

    pdf = make_pdf(build)
    plan = plan_of(pdf, terms=["Krause"])
    rect = plan["candidates"][0]["rects"][0]
    if skip:
        skip_redaction_below(monkeypatch, -1)
        with pytest.raises(R.RedactionVerificationError):
            apply_with(pdf, plan, selected=[], areas=[{"page": 1, "rect": rect}])
        return
    out, _ = apply_with(pdf, plan, selected=[], areas=[{"page": 1, "rect": rect}])
    text = page_text(out)
    assert "Krause" not in text and "Gutachter" in text


def test_a_f1_overlapping_selection_counts_once():
    # Begriff in ausgewählter E-Mail-Adresse und derselbe Name abgewählt an
    # anderer Stelle: kein falscher Alarm, der Name bleibt lesbar.
    pdf = kc.pdf_from_lines(["Max Mustermann wohnt hier.", "Kontakt: max.mustermann@example.org"])
    plan = plan_of(pdf, ["email"], ["Mustermann"])
    name = min(
        (c for c in plan["candidates"] if c["source"].startswith("begriff:")),
        key=lambda c: c["pdf_rect"][1],
    )
    keep = [c["id"] for c in plan["candidates"] if c["id"] != name["id"]]
    out, _ = apply_with(pdf, plan, selected=keep)
    text = page_text(out)
    assert "Max Mustermann" in text and "example.org" not in text
    assert text.count("Mustermann") == 1


def test_a_f1_area_over_selected_finding_counts_once():
    pdf = kc.pdf_from_lines(["Herr Krause kam.", "Gez. Krause"])
    plan = plan_of(pdf, terms=["Krause"])
    first, _second = sorted(plan["candidates"], key=lambda c: c["pdf_rect"][1])
    out, _ = apply_with(
        pdf, plan, selected=[first["id"]], areas=[{"page": 1, "rect": first["rects"][0]}]
    )
    assert page_text(out).count("Krause") == 1


@pytest.mark.parametrize(
    "lines, terms, patterns",
    [
        (["Es erschien Max", "Mustermann und sagte aus."], ["Max Mustermann"], []),
        (["IBAN DE89 3704 0044", "0532 0130 00 bitte"], [], ["iban"]),
    ],
)
def test_a_mn2_partial_failure_of_multiline_finding(monkeypatch, lines, terms, patterns):
    # M-N2: Greift die Schwärzung nur in der ersten Zeile einer mehrzeiligen
    # Fundstelle, muss die Nachprüfung das melden.

    def build(doc, page):
        for k, line in enumerate(lines):
            page.insert_text((72, 72 + 14 * k), line, fontsize=11)

    pdf = make_pdf(build)
    plan = engine_plan(pdf, terms, patterns)
    assert len(plan.candidates) == 1 and len(plan.candidates[0].rects) == 2
    skip_redaction_below(monkeypatch, 70)
    with pytest.raises(R.RedactionVerificationError):
        engine_apply(pdf, plan)


def test_a_mn4_embedded_font_names_no_false_alarm():
    font = dejavu()

    def build(doc, page):
        page.insert_text((72, 72), "Frau Vera Schmidt", fontsize=11, fontfile=font, fontname="dv")

    pdf = make_pdf(build)
    out, _ = engine_apply(pdf, engine_plan(pdf, ["Vera"]))
    assert "Vera" not in page_text(out)


def test_a_n3_2_word_split_in_content_stream_no_false_alarm():
    from redaction_support import raw_pages

    pdf = raw_pages(
        [
            b"BT /F1 12 Tf 72 700 Td (Herr Krause) Tj ET",
            b"BT /F1 12 Tf 72 700 Td (Krause) Tj (stra\\337e 5) Tj ET",
        ]
    )
    plan = engine_plan(pdf, ["Krause"])
    out, _ = engine_apply(pdf, plan, sanitize=False)
    assert "Krausestraße" in page_text(out).replace("\n", "")


def test_candidate_helpers():
    pdf = kc.pdf_from_lines(["Es erschien Max", "Mustermann und sagte aus."])
    plan = engine_plan(pdf, ["Max Mustermann"], ["email"])
    (cand,) = plan.candidates
    box = cand.union_rect()
    assert box is not None and box[1] < box[3]
    assert R.Candidate("x", "hidden", "email", "t").union_rect() is None
    assert plan.text_candidates == [cand]
    assert plan.by_source() == {"begriff:Max Mustermann": 1}
