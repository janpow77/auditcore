"""Fachliche Regeln BPMN-F…: Diagramm-Infos, Rechtsgrundlagen, Kennzeichen, Akteure, Prüfbezüge."""

from __future__ import annotations

import pytest
from helpers import doc, ext, linear, linear_with
from rulecheck import elements, hits

from auditcore_bpmn.model import ACTIVITIES
from auditcore_bpmn.profiles import load_profile


def _info(**attrs: str) -> str:
    base = {"schemaVersion": "1.1", "titel": "T", "status": "entwurf", "foerderperiode": "2021-2027"}
    base.update(attrs)
    rendered = " ".join(f'{k}="{v}"' for k, v in base.items() if v)
    return f"<flowaudit:diagrammInfo {rendered}/>"


def _with_info(info: str, body: str = "") -> str:
    return doc(ext(info) + (body or linear("T1")))


def test_f001_legal_basis_expected_for_activities() -> None:
    xml = doc(
        linear_with("<flowaudit:rechtsgrundlage>§ 44 LHO</flowaudit:rechtsgrundlage>")
        + '<bpmn:userTask id="T2" name="B"/>'
    )
    assert elements(xml, "BPMN-F001") == ["T2"]
    assert not hits(xml, "BPMN-F001", legal_basis_types=frozenset({"task"}))
    assert "callActivity" in ACTIVITIES


def test_f002_f003_f004_info_and_status() -> None:
    assert elements(doc(linear("T1")), "BPMN-F002") == [None]
    assert elements(_with_info(_info(status="")), "BPMN-F003") == ["P1"]
    found = hits(_with_info(_info(status="fertig")), "BPMN-F004")
    assert found[0].params["wert"] == "fertig" and "in_pruefung" in found[0].params["zulaessig"]


def test_f005_f006_f007_f009_dates() -> None:
    assert hits(_with_info(_info(gueltigBis="2026-09-24")), "BPMN-F005")
    assert not hits(_with_info(_info(gueltigBis="2026-09-25")), "BPMN-F005")
    assert hits(_with_info(_info(gueltigAb="2026-09-26")), "BPMN-F006")
    assert hits(_with_info(_info(gueltigAb="2027-01-01", gueltigBis="2026-12-31")), "BPMN-F007")
    bad = hits(_with_info(_info(gueltigAb="01.01.2026", freigegebenAm="gestern")), "BPMN-F009")
    assert {i.params["feld"] for i in bad} == {"gueltig_ab", "freigegeben_am"}


def test_f008_approval_needs_who_and_when() -> None:
    assert hits(_with_info(_info(status="freigegeben")), "BPMN-F008")
    assert not hits(
        _with_info(_info(status="freigegeben", freigegebenDurch="Leitung", freigegebenAm="2026-01-01")), "BPMN-F008"
    )


def test_f010_structured_legal_basis_without_act() -> None:
    body = linear_with('<flowaudit:rechtsgrundlage artikel="74"/>')
    assert elements(doc(body), "BPMN-F010") == ["T1"]


def test_f011_f012_markers() -> None:
    marked = ext('<flowaudit:kennzeichen typ="gibtsnicht"/><flowaudit:kennzeichen typ="rechtsgrundlage"/>')
    xml = doc(
        linear("T1").replace(
            '<bpmn:task id="T1" name="Aufgabe T1"/>', f'<bpmn:task id="T1" name="A">{marked}</bpmn:task>'
        )
    )
    assert [i.params["typ"] for i in hits(xml, "BPMN-F011")] == ["gibtsnicht"]
    assert elements(xml, "BPMN-F012") == ["T1"]


def test_f013_colors_and_f014_f015_funds_period() -> None:
    xml = _with_info(
        _info(kopfzeilenfarbe="blau", foerderperiode="2014-2020", profil="foerderperiode-2021-2027").replace(
            "/>",
            "><flowaudit:fonds>efre</flowaudit:fonds><flowaudit:fonds>esf</flowaudit:fonds></flowaudit:diagrammInfo>",
        )
    )
    assert hits(xml, "BPMN-F013")[0].params["feld"] == "kopfzeilenfarbe"
    assert [i.params["wert"] for i in hits(xml, "BPMN-F014")] == ["esf"]
    assert hits(xml, "BPMN-F015")[0].params["periode"] == "2021-2027"


def test_f016_unknown_profile_falls_back() -> None:
    found = hits(_with_info(_info(profil="gibt-es-nicht")), "BPMN-F016")
    assert found[0].params == {"wert": "gibt-es-nicht", "profil": "foerderperiode-2021-2027"}


def test_f017_f018_confidentiality_and_variant() -> None:
    assert {i.params["feld"] for i in hits(_with_info(_info(vertraulichkeit="geheim", variante="x")), "BPMN-F017")} == {
        "vertraulichkeit",
        "variante",
    }
    assert hits(_with_info(_info(variante="ist")), "BPMN-F018")
    assert not hits(_with_info(_info(variante="ist", bezugDiagramm="soll-1")), "BPMN-F018")


def _lane(role: str | None, name: str = "Lane") -> str:
    actor = ext(f'<flowaudit:akteur rolle="{role}"/>') if role else ""
    return f'<bpmn:laneSet id="LS"><bpmn:lane id="L" name="{name}">{actor}<bpmn:flowNodeRef>T1</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet>'


def test_f020_f021_f022_actors() -> None:
    assert elements(doc(_lane(None) + linear("T1")), "BPMN-F020") == ["L"]
    assert hits(doc(_lane("xyz") + linear("T1")), "BPMN-F021")[0].params["rolle"] == "xyz"
    period_bound = hits(doc(_lane("bb") + linear("T1")), "BPMN-F022")
    assert period_bound[0].params["periode"] == "2021-2027"
    assert "Certifying authority" in period_bound[0].message("en")
    assert not hits(
        _with_info(_info(foerderperiode="2014-2020", profil="foerderperiode-2014-2020"), _lane("bb") + linear("T1")),
        "BPMN-F022",
    )
    assert hits(
        _with_info(_info(foerderperiode="2014-2020", profil="foerderperiode-2014-2020"), _lane("rfs") + linear("T1")),
        "BPMN-F022",
    )


@pytest.mark.parametrize(
    ("reference", "rule"),
    [
        ('ka="16"', "BPMN-F023"),
        ('ka="x"', "BPMN-F023"),
        ('ka="2" bk="3.1"', "BPMN-F024"),
        ('ka="2" art="pruefung"', "BPMN-F026"),
    ],
)
def test_f023_f024_f026_audit_references(reference: str, rule: str) -> None:
    body = linear_with(f"<flowaudit:pruefbezug {reference}/>")
    assert elements(doc(body), rule) == ["T1"]


def test_f023_against_2014_catalogue_and_f025_with_injected_criteria() -> None:
    body = linear_with('<flowaudit:pruefbezug ka="18" bk="18.1"/>')
    assert hits(doc(body), "BPMN-F023")
    assert not hits(doc(body), "BPMN-F023", profile=load_profile("foerderperiode-2014-2020"))
    profile = load_profile().with_assessment_criteria({2: [("2.1", "K")]})
    ok = body.replace('ka="18" bk="18.1"', 'ka="2" bk="2.1"')
    unknown = body.replace('ka="18" bk="18.1"', 'ka="2" bk="2.9"')
    assert not hits(doc(ok), "BPMN-F025", profile=profile)
    assert not hits(doc(unknown), "BPMN-F025") and hits(doc(unknown), "BPMN-F025", profile=profile)


def test_f023_also_for_findings_and_diagram_level() -> None:
    finding = '<flowaudit:feststellung ka="20" art="formell"><flowaudit:beschreibung>x</flowaudit:beschreibung></flowaudit:feststellung>'
    xml = _with_info(
        _info().replace("/>", '><flowaudit:pruefbezug ka="99"/></flowaudit:diagrammInfo>'),
        linear("T1").replace(
            '<bpmn:task id="T1" name="Aufgabe T1"/>', f'<bpmn:task id="T1" name="A">{ext(finding)}</bpmn:task>'
        ),
    )
    assert set(elements(xml, "BPMN-F023")) == {"P1", "T1"}


def test_f027_cross_references() -> None:
    refs = ext(
        '<flowaudit:verweis art="prueffeld" schluessel="3.1"/><flowaudit:verweis art="akte" schluessel="A"/>'
        '<flowaudit:verweis art="register"/>'
    )
    xml = doc(
        linear("T1").replace(
            '<bpmn:task id="T1" name="Aufgabe T1"/>', f'<bpmn:task id="T1" name="A">{refs}</bpmn:task>'
        )
    )
    assert [i.params["wert"] for i in hits(xml, "BPMN-F027")] == ["akte", "register"]
