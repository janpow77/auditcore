"""Altbestand anreichern: Vorschläge aus Dokumentation, Namen und Farben; gezielte Übernahme."""

from __future__ import annotations

from helpers import fixture_text

from auditcore_bpmn.enrichment import apply_suggestions, strip_role_prefix, suggest
from auditcore_bpmn.extensions import AuditReference, CrossReference
from auditcore_bpmn.model import parse_bpmn

ALT = fixture_text("synthetic/antragsstrecke_altbestand.bpmn")


def _by(kind: str, element: str | None = None) -> list:  # type: ignore[type-arg]
    return [s for s in suggest(ALT) if s.kind == kind and (element is None or s.element_id == element)]


def test_legal_bases_in_normal_form() -> None:
    antrag = [s.value.citation() for s in _by("rechtsgrundlage", "Antrag")]
    assert antrag == ["Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060"]
    pruefung = [s.value.citation() for s in _by("rechtsgrundlage", "Pruefung")]
    assert pruefung == ["Artikel 74 Absatz 2 Unterabsatz 2", "§ 23 LHO", "§ 44 LHO", "VV Nummer 4.2 zu § 44 LHO"]


def test_criteria_findings_fields_registers_and_sources() -> None:
    pool = [s.value for s in _by("pruefbezug", "Pool_1")]
    assert pool == [AuditReference("2", "2.4"), AuditReference("2", "2.6")]
    assert [s.value for s in _by("pruefbezug", "Stellungnahme")] == [AuditReference("2", "2.3")]
    references = [s.value for s in _by("verweis", "Pruefung")]
    assert (
        CrossReference("feststellung_ref", "T01 F1") in references
        and CrossReference("feststellung_ref", "T01 F2") in references
    )
    assert CrossReference("prueffeld", "3.21", "Antragsprüfcheckliste Muster V 1.2") in references
    assert {r.key for r in references if r.kind == "register"} == {"A1", "B2"}
    source = _by("quelle", "Pool_1")[0].value
    assert source.location == "Förderhandbuch Muster V 1.0, Kapitel 3.2 (PDF-Seiten 10 bis 12)"
    assert _by("quelle", "Stellungnahme")[0].value.location.startswith(
        "EFRE-Förderrichtlinie Muster, Teil II Nummer 1.6"
    )


def test_actor_prefix_and_color_suggestions() -> None:
    actors = {s.element_id: s.value.role for s in _by("akteur")}
    assert actors == {"Lane_Antrag": "beg", "Lane_Bank": "zgs", "Lane_Fach": "ftd", "Lane_VB": "vb"}
    assert {s.element_id: s.value for s in _by("rolle_praefix")}["Stellungnahme"] == "ftd"
    colors = {s.element_id: s.value.type for s in _by("kennzeichen")}
    assert colors == {"Pruefung": "feststellung", "Nachforderung": "soll_ohne_regelung", "Bescheid": "ohne_befund"}
    assert all(isinstance(s.to_dict()["value"], (dict, str)) for s in suggest(ALT))


def test_apply_selected_suggestions_without_overwriting() -> None:
    chosen = [s for s in suggest(ALT) if s.element_id in ("Pruefung", "Lane_Bank")]
    xml = apply_suggestions(ALT, chosen)
    document = parse_bpmn(xml)
    ext = document.elements["Pruefung"].extensions
    assert len(ext.legal_bases) == 4 and ext.markers[0].type == "feststellung" and len(ext.cross_references) == 5
    assert document.elements["Lane_Bank"].extensions.actor.role == "zgs"  # type: ignore[union-attr]
    again = parse_bpmn(apply_suggestions(xml, chosen))
    assert again.elements["Pruefung"].extensions == ext
    assert parse_bpmn(apply_suggestions(ALT, [])).elements["Pruefung"].extensions.is_empty


def test_strip_role_prefix() -> None:
    assert strip_role_prefix("Beispielbank: Antrag prüfen") == "Antrag prüfen"
    assert strip_role_prefix("Antrag prüfen") == "Antrag prüfen"
