"""Neutralisieren: Rollen statt Namen, Personen-/Befund-/Kennnummern entfernt, Bericht."""

from __future__ import annotations

from helpers import fixture_text

from auditcore_bpmn.model import parse_bpmn
from auditcore_bpmn.neutralize import neutralize

ALT = fixture_text("synthetic/antragsstrecke_altbestand.bpmn")
VOLL = fixture_text("synthetic/flowaudit_1_1_vollstaendig.bpmn")


def test_legacy_diagram_is_neutralized() -> None:
    result = neutralize(ALT, replacements={"Beispielministerium": "Verwaltungsbehörde"})
    xml = result.xml
    for forbidden in (
        "Beispielbank",
        "Beispielministerium",
        "Beispielagentur",
        "foerderung@beispiel.example",
        "25.000,00 EUR",
        "Muster Solar GmbH",
        "4711123",
        "SEE912345678901",
        "T01 F1",
        "(F3)",
        "#fce8e6",
        "#ffe0e0",
    ):
        assert forbidden not in xml, forbidden
    document = parse_bpmn(xml)
    assert document.elements["Lane_Bank"].name == "Zwischengeschaltete Stelle"
    assert document.elements["Lane_VB"].name == "Verwaltungsbehörde"
    assert document.elements["Pruefung"].name == "Zwischengeschaltete Stelle: Antrag prüfen"
    assert "#c8e6c9" in xml and "Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060" in xml
    summary = result.summary()
    assert {"anzeigename", "email", "betrag", "unternehmen", "kennnummer", "feststellungsbezug", "befundfarbe"} <= set(
        summary
    )
    assert all(r.old is None for r in result.replacements)


def test_flowaudit_details_removed_and_originals_optional() -> None:
    result = neutralize(VOLL, keep_originals=True)
    document = parse_bpmn(result.xml)
    ext = document.elements["Pruefen"].extensions
    assert ext.internal_note is None and ext.audit_steps == () and ext.findings == ()
    assert [c.kind for c in ext.cross_references] == ["prueffeld"] and ext.sources == ()
    assert ext.controls and ext.risks and ext.legal_bases
    info = document.diagram_info
    assert info is not None and info.author is None and info.approved_by is None
    assert document.elements["Lane_Pruef"].extensions.actor.display_name is None  # type: ignore[union-attr]
    assert document.elements["Lane_Pruef"].name == "Verwaltungsbehörde"
    assert any(r.old == "Prüfung" for r in result.replacements)
    assert result.to_dict()["summary"]["entfernt"] >= 5


def test_unknown_bodies_become_numbered_and_confidential_parts_removed() -> None:
    xml = (
        VOLL.replace('<flowaudit:akteur rolle="vb" anzeigename="Kasse"/>', "")
        .replace('name="Zahlstelle"', 'name="Kasse Nord"')
        .replace('<flowaudit:kennzeichen typ="zahlung"/>', '<flowaudit:kennzeichen typ="zahlung" vertraulich="true"/>')
    )
    document = parse_bpmn(neutralize(xml).xml)
    assert document.elements["Lane_Zahl"].name == "Stelle 1"
    assert document.elements["Zahlen"].extensions.markers == ()
