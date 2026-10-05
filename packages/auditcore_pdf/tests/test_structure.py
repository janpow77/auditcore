"""Prüfung und Bereinigung von Text außerhalb der Seiteninhalte (Issue #239)."""

from __future__ import annotations

import pymupdf as fitz
import pytest

from auditcore_pdf import (
    SanitizationPolicy,
    extract_page_text,
    redact_document,
    sanitize_structure,
    verify_redaction,
)
from auditcore_pdf.structure import TextItem, collect_structure_texts, widget_texts
from auditcore_pdf.structure_clean import REDACTED_PLACEHOLDER

EXPECTED_LOCATIONS = (
    "Seite 1 (Text)",
    "Lesezeichen 1",
    "Formularfeld 1 (Seite 1)",
    "Verknüpfung 1 (Seite 1)",
    "Benanntes Ziel",
    "Seitenbeschriftung 1",
    "Ebenenname (Objekt",
    "JavaScript (Objekt",
    "Alternativtext (Objekt",
)


def _locations(violations: list[str]) -> set[str]:
    return {v.split(": Fundstelle")[0] for v in violations}


def test_verify_reports_every_structure_leak(structure_pdf: bytes) -> None:
    res = verify_redaction(structure_pdf, forbidden_terms=["LECK"])
    assert res.clean is False
    locations = _locations(res.violations)
    for expected in EXPECTED_LOCATIONS:
        assert any(loc.startswith(expected) for loc in locations), expected
    assert res.details["outline_checked"] is True
    assert res.details["hidden_layers_revealed"] is True
    assert res.details["glyphs_under_actualtext_checked"] is True
    assert res.fully_verified is False


def test_verify_finds_glyphs_hidden_behind_actualtext(structure_pdf: bytes) -> None:
    """„LECK_GLYPHE“ steht nur als Glyphen da; die Extraktion liefert ActualText."""
    assert "LECK_GLYPHE" not in extract_page_text(structure_pdf, 1)
    res = verify_redaction(structure_pdf, forbidden_terms=["LECK_GLYPHE"])
    assert res.violations == ["Seite 1 (Text): Fundstelle für verbotenen Begriff 'LECK_GLYPHE'"]


def test_redact_document_cleans_all_structure_leaks(structure_pdf: bytes) -> None:
    out, report = redact_document(structure_pdf, terms=["LECK"])
    assert report.verified is True, report.verification_error
    assert report.verification_error is None
    assert report.structure_cleaned == [
        "Lesezeichen: 1 Titel ersetzt",
        "Formularfeld auf Seite 1 entfernt",
        "Verknüpfung auf Seite 1 entfernt",
        "Benannte Ziele: 1 entfernt",
        "Seitenbeschriftungen entfernt",
        f"Ebenenname (Objekt {_ocg_xref(structure_pdf)}) ersetzt",
        "JavaScript: 2 Skripte geleert",
        "Alternativtexte/ActualText: 1 geleert",
    ]
    doc = fitz.open(stream=out, filetype="pdf")
    try:
        assert [entry[1] for entry in doc.get_toc()] == [
            REDACTED_PLACEHOLDER,
            "Unterkapitel neutral",
        ]
        assert list(doc[0].widgets()) == []
        assert doc.get_page_labels() == []
        assert doc.resolve_names() == {}
        assert [info["name"] for info in doc.get_ocgs().values()] == [REDACTED_PLACEHOLDER]
    finally:
        doc.close()


def _ocg_xref(pdf_bytes: bytes) -> int:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return int(next(iter(doc.get_ocgs())))
    finally:
        doc.close()


def test_structure_without_match_stays_unchanged(structure_pdf: bytes) -> None:
    """Ohne Treffer bleiben Lesezeichen, Felder und Ziele; nur JavaScript geht standardmäßig."""
    out, report = redact_document(structure_pdf, terms=["NICHT_VORHANDEN"])
    assert report.structure_cleaned == ["JavaScript: 2 Skripte geleert"]
    doc = fitz.open(stream=out, filetype="pdf")
    try:
        assert len(doc.get_toc()) == 2
        assert len(list(doc[0].widgets())) == 1
        assert doc.resolve_names() != {}
    finally:
        doc.close()


def test_strip_options_remove_whole_structures(structure_pdf: bytes) -> None:
    policy = SanitizationPolicy(
        strip_outline=True,
        strip_form_fields=True,
        strip_links=True,
        strip_named_destinations=True,
        strip_page_labels=True,
        strip_alt_texts=True,
    )
    out, report = redact_document(structure_pdf, terms=["NICHT_VORHANDEN"], policy=policy)
    assert "Lesezeichen: 2 entfernt" in report.structure_cleaned
    assert "Alternativtexte/ActualText: 2 geleert" in report.structure_cleaned
    remaining = [item.category for item in _structure_items(out)]
    assert set(remaining) <= {"optional_content"}


def _structure_items(pdf_bytes: bytes) -> list[TextItem]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return list(collect_structure_texts(doc))
    finally:
        doc.close()


def test_javascript_kept_when_disabled_and_without_match(structure_pdf: bytes) -> None:
    policy = SanitizationPolicy(strip_javascript=False)
    out, report = redact_document(structure_pdf, terms=["NICHT_VORHANDEN"], policy=policy)
    assert report.structure_cleaned == []
    assert any(item.category == "javascript" for item in _structure_items(out))


def test_javascript_removed_on_match_even_when_disabled(structure_pdf: bytes) -> None:
    policy = SanitizationPolicy(strip_javascript=False)
    _, report = redact_document(structure_pdf, terms=["LECK_JS"], policy=policy)
    assert "JavaScript: 2 Skripte geleert" in report.structure_cleaned
    assert report.verified is True


def _pdf_with_indirect_structures() -> bytes:
    """JavaScript als Strom, Namensbaum als indirektes Objekt, XMP an einer Seite."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 100), "Neutral")
    catalog = doc.pdf_catalog()
    script, action = doc.get_new_xref(), doc.get_new_xref()
    doc.update_object(script, "<< >>")
    doc.update_stream(script, b"app.alert('STROM_GEHEIM');")
    doc.update_object(action, f"<< /S /JavaScript /JS {script} 0 R >>")
    doc.xref_set_key(catalog, "OpenAction", f"{action} 0 R")
    dests, names = doc.get_new_xref(), doc.get_new_xref()
    doc.update_object(dests, f"<< /Names [(ZIEL_GEHEIM) [{page.xref} 0 R /Fit]] >>")
    doc.update_object(names, f"<< /Dests {dests} 0 R >>")
    doc.xref_set_key(catalog, "Names", f"{names} 0 R")
    xmp = doc.get_new_xref()
    doc.update_object(xmp, "<< /Type /Metadata /Subtype /XML >>")
    doc.update_stream(xmp, b"<x:xmpmeta>SEITEN_XMP_GEHEIM</x:xmpmeta>", compress=False)
    doc.xref_set_key(page.xref, "Metadata", f"{xmp} 0 R")
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_indirect_javascript_names_and_page_xmp() -> None:
    pdf = _pdf_with_indirect_structures()
    terms = ["STROM_GEHEIM", "ZIEL_GEHEIM", "SEITEN_XMP_GEHEIM"]
    before = _locations(verify_redaction(pdf, forbidden_terms=terms).violations)
    assert {loc.split(" (")[0] for loc in before} == {
        "JavaScript",
        "Benanntes Ziel",
        "XMP-Metadatenstrom",
    }
    out, report = redact_document(pdf, terms=terms)
    assert report.verified is True, report.verification_error
    assert "xmp_objekte:1" in report.metadata_fields_cleaned
    assert "Benannte Ziele: 1 entfernt" in report.structure_cleaned


def test_binary_streams_are_not_rewritten() -> None:
    """Farbprofile und Schriften bleiben unangetastet, Formular-XObjects werden geleert."""
    doc = fitz.open()
    doc.new_page()
    streams = {}
    for name, header in (
        ("icc", "<< /N 3 >>"),
        ("font", "<< /Length1 20 >>"),
        ("form", "<< /Type /XObject /Subtype /Form /BBox [0 0 1 1] >>"),
    ):
        xref = doc.get_new_xref()
        doc.update_object(xref, header)
        doc.update_stream(xref, b"/Alt (BINAER_ALT)", compress=False)
        streams[name] = xref
    try:
        cleaned = sanitize_structure(doc, [], [], SanitizationPolicy(strip_alt_texts=True))
        assert cleaned == ["Alternativtexte/ActualText: 1 geleert"]
        assert doc.xref_stream(streams["icc"]) == b"/Alt (BINAER_ALT)"
        assert doc.xref_stream(streams["font"]) == b"/Alt (BINAER_ALT)"
        assert doc.xref_stream(streams["form"]) == b"/Alt ()"
    finally:
        doc.close()


def test_sanitize_structure_direct_call_with_choice_field() -> None:
    doc = fitz.open()
    page = doc.new_page()
    widget = fitz.Widget()
    widget.field_type = fitz.PDF_WIDGET_TYPE_COMBOBOX
    widget.field_name = "auswahl"
    widget.choice_values = ["neutral", "WAHL_GEHEIM"]
    widget.field_value = "neutral"
    widget.rect = fitz.Rect(72, 100, 300, 120)
    page.add_widget(widget)
    try:
        assert "WAHL_GEHEIM" in widget_texts(next(iter(page.widgets())))
        cleaned = sanitize_structure(doc, ["WAHL_GEHEIM"], [], SanitizationPolicy())
        assert cleaned == ["Formularfeld auf Seite 1 entfernt"]
    finally:
        doc.close()


@pytest.mark.parametrize(
    ("choice", "expected"),
    [(["a", "b"], ["x", "a", "b"]), ([("e", "Anzeige")], ["x", "e", "Anzeige"])],
    ids=["einfach", "paar"],
)
def test_widget_texts_flattens_choices(choice: list[object], expected: list[str]) -> None:
    class _Widget:
        field_name = "x"
        field_value = True
        field_label = ""
        choice_values = choice

    assert widget_texts(_Widget()) == expected


def test_hidden_layer_text_is_redacted_and_layer_stays_hidden(layered_pdf: bytes) -> None:
    assert "GEHEIM_EBENE" not in extract_page_text(layered_pdf, 1)
    res = verify_redaction(layered_pdf, forbidden_terms=["GEHEIM_EBENE"])
    assert res.violations == ["Seite 1 (Text): Fundstelle für verbotenen Begriff 'GEHEIM_EBENE'"]

    out, report = redact_document(layered_pdf, terms=["GEHEIM_EBENE"])
    assert report.findings_count == 1
    assert report.verified is True
    doc = fitz.open(stream=out, filetype="pdf")
    try:
        states = {info["name"]: info["on"] for info in doc.get_ocgs().values()}
        assert states == {"Ausgeblendet": False, "Sichtbar": True}
    finally:
        doc.close()


def test_hidden_layer_redaction_can_be_disabled(layered_pdf: bytes) -> None:
    policy = SanitizationPolicy(redact_hidden_layers=False)
    _, report = redact_document(layered_pdf, terms=["GEHEIM_EBENE"], policy=policy)
    assert report.findings_count == 0
    assert report.verified is False
    assert report.verification_error is not None
    assert "GEHEIM_EBENE" in report.verification_error
