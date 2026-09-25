"""FlowAudit-Erweiterung: Lesen, Schreiben, JSON und Abwärtskompatibilität zu Schema 1.0."""

from __future__ import annotations

from dataclasses import fields
from xml.etree import ElementTree as ET

import pytest
from helpers import BPMN, FA, fixture_text

from auditcore_bpmn.extensions import (
    Actor,
    AuditReference,
    Control,
    Deadline,
    DiagramInfo,
    EsiRequirements,
    Extensions,
    LegalBasis,
    Marker,
    Risk,
    from_dict,
    legacy_esi,
    read_element,
    read_extensions,
    to_dict,
    write_element,
    write_extensions,
)
from auditcore_bpmn.extensions.element import REPEATED, SINGLE
from auditcore_bpmn.model import parse_bpmn


def _task(inner: str = "") -> ET.Element:
    return ET.fromstring(f'<bpmn:task xmlns:bpmn="{BPMN}" xmlns:flowaudit="{FA}" id="T">{inner}</bpmn:task>')


def test_legacy_1_0_elements_are_read() -> None:
    task = _task(
        "<bpmn:extensionElements><flowaudit:rechtsgrundlage>§ 55 BHO</flowaudit:rechtsgrundlage>"
        '<flowaudit:rechtsgrundlage value="Art. 73 CPR"/><flowaudit:notiz>Alt</flowaudit:notiz>'
        "<flowaudit:interneNotiz>Neu</flowaudit:interneNotiz></bpmn:extensionElements>"
    )
    ext = read_extensions(task)
    assert [r.text for r in ext.legal_bases] == ["§ 55 BHO", "Art. 73 CPR"]
    assert ext.internal_note == "Alt"
    assert not ext.legal_bases[0].is_structured


def test_full_fixture_reads_every_element_type() -> None:
    document = parse_bpmn(fixture_text("synthetic/flowaudit_1_1_vollstaendig.bpmn"))
    ext = document.elements["Pruefen"].extensions
    assert ext.legal_bases[0].citation() == "Artikel 74 Absatz 1 Buchstabe a der Verordnung (EU) 2021/1060"
    assert ext.controls[0].key_control is True and ext.controls[0].description == "Vollständige Prüfung."
    assert ext.risks[0].controls == ("K1",)
    assert ext.deadlines[0].legal_bases[0].point == "b"
    assert {c.kind for c in ext.cross_references} == {"prueffeld", "feststellung_ref"}
    assert ext.audit_steps[0].tester == "Max Mustermann" and ext.audit_steps[0].remark == "ohne Befund"
    assert ext.findings[0].recommendation == "Vermerkvorlage ergänzen."
    assert ext.sources[0].text == "Gespräch mit der Fachebene"
    assert ext.internal_note == "Nur intern."
    info = document.diagram_info
    assert info is not None and info.funds == ("efre", "jtf") and info.variant == "soll"
    assert info.risks[0].category == "doppelfinanzierung" and info.cross_references[0].key == "A1"
    assert document.elements["Lane_Pruef"].extensions.actor == Actor(role="vb", display_name="Prüfreferat")


@pytest.mark.parametrize("cls", [t for _n, t in (*REPEATED.values(), *SINGLE.values())])
def test_every_type_roundtrips_xml_and_json(cls: type) -> None:
    values = {}
    for item in fields(cls):
        kind = item.metadata.get("kind")
        if kind == "elements":
            values[item.name] = ()
        elif kind in ("texts", "tokens"):
            values[item.name] = ("eins", "zwei")
        elif item.metadata.get("bool"):
            values[item.name] = True
        elif kind != "internal":
            values[item.name] = f"Wert {item.name} äöü"
    obj = cls(**values)
    tag = next(name for name, (_a, c) in (*REPEATED.items(), *SINGLE.items()) if c is cls)
    assert read_element(cls, write_element(obj, tag)) == obj
    assert from_dict(cls, to_dict(obj)) == obj


def test_from_dict_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unbekannte Felder"):
        from_dict(Marker, {"type": "frist", "farbe": "rot"})


def test_nested_elements_roundtrip() -> None:
    info = DiagramInfo(
        title="T",
        legal_bases=(LegalBasis(act="BHO", section="44"),),
        audit_references=(AuditReference("2", "2.3"),),
        risks=(Risk(id="R", controls=("K1", "K2")),),
        keywords=("a",),
    )
    assert read_element(DiagramInfo, write_element(info, "diagrammInfo")) == info
    deadline = Deadline(value="80", unit="tage", legal_bases=(LegalBasis(text="Art. 74"),))
    assert read_element(Deadline, write_element(deadline, "frist")) == deadline


def test_write_extensions_replaces_only_named_kinds_and_keeps_foreign() -> None:
    task = _task(
        '<bpmn:documentation>Doku</bpmn:documentation><bpmn:extensionElements><x:fremd xmlns:x="urn:x"/>'
        "<flowaudit:rechtsgrundlage>alt</flowaudit:rechtsgrundlage><flowaudit:notiz>alt</flowaudit:notiz>"
        '<flowaudit:kennzeichen typ="frist"/></bpmn:extensionElements>'
    )
    write_extensions(task, Extensions(legal_bases=(LegalBasis(text="neu"),), internal_note="neu"))
    ext = read_extensions(task)
    assert [r.text for r in ext.legal_bases] == ["neu"] and ext.internal_note == "neu"
    assert ext.markers == (Marker("frist"),)
    container = task[1]
    assert task[0].tag == f"{{{BPMN}}}documentation" and container.tag == f"{{{BPMN}}}extensionElements"
    assert any(child.tag == "{urn:x}fremd" for child in container)
    write_extensions(task, Extensions(), replace=["kennzeichen"])
    assert read_extensions(task).markers == ()


def test_write_extensions_creates_after_documentation_and_removes_empty_container() -> None:
    task = _task("<bpmn:documentation>A</bpmn:documentation><bpmn:documentation>B</bpmn:documentation>")
    write_extensions(task, Extensions(controls=(Control(id="K"),)))
    assert task[2].tag == f"{{{BPMN}}}extensionElements"
    write_extensions(task, Extensions(), replace=["kontrolle"])
    assert len(task) == 2
    untouched = _task()
    write_extensions(untouched, Extensions())
    assert len(untouched) == 0


def test_legacy_esi_attributes() -> None:
    process = ET.fromstring('<p esiProfile="ESI-2021" esiCoreRequirements="KA1:K1, K2;KA2;;"/>')
    esi = legacy_esi(process)
    assert isinstance(esi, EsiRequirements) and esi.origin == "legacy-attribute"
    assert [(r.code, r.criteria) for r in esi.requirements] == [("KA1", ("K1", "K2")), ("KA2", ())]
    assert legacy_esi(ET.fromstring("<p/>")) is None


@pytest.mark.parametrize(
    ("basis", "long", "short"),
    [
        (
            LegalBasis(act="VO (EU) 2021/1060", article="73", paragraph="2", point="b"),
            "Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060",
            "Art. 73 Abs. 2 Buchst. b VO (EU) 2021/1060",
        ),
        (
            LegalBasis(act="LHO", section="44", paragraph="1", sentence="2"),
            "§ 44 Absatz 1 Satz 2 LHO",
            "§ 44 Abs. 1 S. 2 LHO",
        ),
        (LegalBasis(act="VV zu § 44 LHO", number="4.2"), "VV Nummer 4.2 zu § 44 LHO", "VV Nr. 4.2 zu § 44 LHO"),
        (
            LegalBasis(act="Delegierte VO (EU) Nr. 480/2014", annex="IV"),
            "Anhang IV der Delegierten Verordnung (EU) Nr. 480/2014",
            "Anhang IV Delegierte VO (EU) Nr. 480/2014",
        ),
        (
            LegalBasis(act="Richtlinie 2014/24/EU", article="57", subparagraph="2"),
            "Artikel 57 Unterabsatz 2 der Richtlinie 2014/24/EU",
            "Art. 57 UAbs. 2 RL 2014/24/EU",
        ),
        (LegalBasis(text="Freitext"), "Freitext", "Freitext"),
    ],
)
def test_citation_forms(basis: LegalBasis, long: str, short: str) -> None:
    assert basis.citation() == long and basis.short_citation() == short
    assert basis.normalized().text == long


def test_display_prefers_free_text_and_audit_reference_display() -> None:
    assert LegalBasis(text="frei", act="BHO", section="7").display == "frei"
    assert LegalBasis(act="BHO", section="7").display == "§ 7 BHO"
    assert AuditReference("2", "2.3").display == "KA 2 · BK 2.3"
    assert AuditReference("x").key_requirement_number is None
    assert Deadline(value="80", unit="tage", basis="ab Eingang").display == "80 tage (ab Eingang)"


def test_extensions_to_dict_and_marker_types() -> None:
    ext = Extensions(markers=(Marker("frist"), Marker("zahlung")), internal_note="n", actor=Actor(role="vb"))
    assert ext.marker_types() == ("frist", "zahlung") and not ext.is_empty
    assert ext.to_dict() == {
        "internal_note": "n",
        "markers": [{"type": "frist"}, {"type": "zahlung"}],
        "actor": {"role": "vb"},
    }
