"""Versionsvergleich, Soll/Ist-Abgleich und Einfärben."""

from __future__ import annotations

from helpers import fixture_text

from auditcore_bpmn.comparison import (
    DIFF_COLORS,
    apply_colors,
    colors_from_markers,
    compare,
    compare_target_actual,
    match_elements,
)
from auditcore_bpmn.model import parse_bpmn
from auditcore_bpmn.namespaces import BIOC_NS, BPMNDI_NS, q

SOLL = fixture_text("synthetic/flowaudit_1_1_vollstaendig.bpmn")


def _changed() -> str:
    return (
        SOLL.replace('name="Auszahlung anweisen"', 'name="Auszahlung freigeben"')
        .replace(
            '<bpmn:endEvent id="Ende" name="Ausgezahlt"/>',
            '<bpmn:endEvent id="Ende2" name="Ausgezahlt"/><bpmn:task id="Neu" name="Ablegen"/>',
        )
        .replace('targetRef="Ende"', 'targetRef="Ende2"')
    )


def test_matching_by_id_then_unique_name() -> None:
    mapping = match_elements(parse_bpmn(SOLL), parse_bpmn(_changed()))
    assert mapping["Pruefen"] == "Pruefen" and mapping["Ende"] == "Ende2"


def test_compare_kinds_fields_synopsis_and_colors() -> None:
    comparison = compare(SOLL, _changed())
    kinds = {c.kind for c in comparison.changes}
    assert {"geaendert", "hinzugefuegt", "unveraendert"} <= kinds
    renamed = next(c for c in comparison.of_kind("geaendert") if c.old_id == "Zahlen")
    assert ("name", "Auszahlung anweisen", "Auszahlung freigeben") in renamed.fields
    assert [c.new_id for c in comparison.of_kind("hinzugefuegt")] == ["Neu"]
    rows = comparison.synopsis()
    assert {
        "element": "Auszahlung freigeben",
        "feld": "name",
        "alt": "Auszahlung anweisen",
        "neu": "Auszahlung freigeben",
        "aenderung": "geändert",
    } in rows
    old, new = comparison.colors()
    assert new["Neu"] == DIFF_COLORS["hinzugefuegt"] and old["Zahlen"] == DIFF_COLORS["geaendert"]
    assert comparison.to_dict()["changes"] and not comparison.unchanged
    assert compare(SOLL, SOLL).unchanged


def test_removed_elements() -> None:
    reduced = SOLL.replace(
        '<bpmn:task id="Zahlen" name="Auszahlung anweisen">', '<bpmn:task id="Zahlen2" name="Anders">'
    )
    comparison = compare(SOLL, reduced)
    assert [c.old_id for c in comparison.of_kind("entfallen")] == ["Zahlen"]
    assert comparison.colors()[0]["Zahlen"] == DIFF_COLORS["entfallen"]
    assert any(r["aenderung"] == "entfallen" for r in comparison.synopsis())


def test_target_actual_binary_result_with_reasons() -> None:
    actual = (
        SOLL.replace('variante="soll"', 'variante="ist" bezugDiagramm="soll"')
        .replace(
            '<flowaudit:kontrolle id="K1" bezeichnung="Belegprüfung nach Checkliste"',
            '<flowaudit:kontrolle id="K9" bezeichnung="Andere"',
        )
        .replace('ergebnis="erfuellt"', 'ergebnis="nicht_erfuellt"')
        .replace("<bpmn:flowNodeRef>Zahlen</bpmn:flowNodeRef>", "")
        .replace(
            "<bpmn:flowNodeRef>Pruefen</bpmn:flowNodeRef>",
            "<bpmn:flowNodeRef>Pruefen</bpmn:flowNodeRef><bpmn:flowNodeRef>Zahlen</bpmn:flowNodeRef>",
        )
    )
    result = compare_target_actual(SOLL, actual)
    by_id = {r.target_id: r for r in result.results}
    assert by_id["Start"].met and not by_id["Pruefen"].met and not by_id["Zahlen"].met
    reasons = " ".join(by_id["Pruefen"].reasons)
    assert "Kontrolle fehlt im Ist" in reasons and "Prüfschritt im Ist nicht erfüllt" in reasons
    assert "Andere Stelle" in by_id["Zahlen"].reasons[0]
    assert result.met + result.not_met == len(result.results) and result.to_dict()["not_met"] == 2


def test_target_actual_missing_and_additional() -> None:
    actual = SOLL.replace('<bpmn:endEvent id="Ende" name="Ausgezahlt"/>', '<bpmn:endEvent id="X" name="Anders"/>')
    result = compare_target_actual(SOLL, actual)
    missing = next(r for r in result.results if r.target_id == "Ende")
    assert missing.reasons == ("Im Ist nicht vorhanden.",) and result.additional_in_actual == ("X",)


def test_colors_from_markers_and_apply() -> None:
    xml = fixture_text("synthetic/antragsstrecke_altbestand.bpmn")
    assert colors_from_markers(SOLL) == {}
    marked = SOLL.replace(
        '<flowaudit:kennzeichen typ="zahlung"/>',
        '<flowaudit:kennzeichen typ="zahlung"/><flowaudit:kennzeichen typ="feststellung_finanziell"/>',
    )
    assert colors_from_markers(marked) == {"Zahlen": ("#fce8e6", "#b3261e")}
    colored = parse_bpmn(apply_colors(xml, {"Antrag": ("#e6f4ea", "#1e8e3e")}))
    shape = next(s for s in colored.root.iter(q(BPMNDI_NS, "BPMNShape")) if s.get("bpmnElement") == "Antrag")
    assert shape.get(q(BIOC_NS, "fill")) == "#e6f4ea"
    without_ns = apply_colors(SOLL, {"Pruefen": ("#000000", "#ffffff")})
    assert "Pruefen" in without_ns
