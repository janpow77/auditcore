"""Regeln der Prüfbehörden-Funktionen BPMN-P…."""

from __future__ import annotations

from helpers import doc, ext, flow
from rulecheck import elements, hits


def _task(task_id: str, *children: str, name: str = "Aufgabe") -> str:
    return f'<bpmn:task id="{task_id}" name="{name}">{ext(*children) if children else ""}</bpmn:task>'


def _process(*tasks: str, extra: str = "") -> str:
    ids = ["S", *[t.split('"')[1] for t in tasks], "E"]
    flows = "".join(flow(f"F{i}", a, b) for i, (a, b) in enumerate(zip(ids, ids[1:], strict=False)))
    return doc('<bpmn:startEvent id="S"/><bpmn:endEvent id="E"/>' + "".join(tasks) + flows + extra)


def test_p001_control_without_evidence() -> None:
    xml = _process(
        _task("T1", '<flowaudit:kontrolle id="K1"/>'), _task("T2", '<flowaudit:kontrolle id="K2" nachweis="Vermerk"/>')
    )
    assert elements(xml, "BPMN-P001") == ["T1"]
    with_data = _process(
        '<bpmn:task id="T1" name="A">'
        + ext('<flowaudit:kontrolle id="K1"/>')
        + '<bpmn:dataOutputAssociation id="DOA"><bpmn:targetRef>D</bpmn:targetRef></bpmn:dataOutputAssociation></bpmn:task>',
        extra='<bpmn:dataObjectReference id="D" name="Vermerk"/>',
    )
    assert not hits(with_data, "BPMN-P001")


def test_p002_data_without_storage_location() -> None:
    xml = _process(
        _task("T1"),
        extra=(
            '<bpmn:dataObjectReference id="Ohne" name="Akte" dataObjectRef="Obj"/><bpmn:dataObject id="Obj"/>'
            '<bpmn:dataStoreReference id="Mit" name="Register">'
            + ext('<flowaudit:nachweis aufbewahrungsort="Archiv"/>')
            + "</bpmn:dataStoreReference>"
            '<bpmn:dataStore id="FreierSpeicher" name="Speicher"/>'
        ),
    )
    assert elements(xml, "BPMN-P002") == ["Ohne", "FreierSpeicher"]


def test_p003_deadline_without_legal_basis() -> None:
    xml = _process(
        _task("T1", '<flowaudit:frist wert="10" einheit="tage"/>'),
        _task(
            "T2",
            '<flowaudit:frist wert="80" einheit="tage"><flowaudit:rechtsgrundlage>Art. 74</flowaudit:rechtsgrundlage></flowaudit:frist>',
        ),
        _task("T3", "<flowaudit:rechtsgrundlage>§ 1 X</flowaudit:rechtsgrundlage>", '<flowaudit:frist wert="1"/>'),
    )
    assert elements(xml, "BPMN-P003") == ["T1"]
    assert hits(xml, "BPMN-P003")[0].params["frist"] == "10 tage"


def test_p004_key_control_untested_and_p012_unknown_control() -> None:
    xml = _process(
        _task("T1", '<flowaudit:kontrolle id="K1" schluesselkontrolle="true" nachweis="V"/>'),
        _task("T2", '<flowaudit:kontrolle id="K2" schluesselkontrolle="true" nachweis="V"/>'),
        _task(
            "T3",
            '<flowaudit:pruefschritt id="PS" ergebnis="erfuellt" kontrolle="K2"/>',
            '<flowaudit:pruefschritt id="PS2" kontrolle="K9"/>',
        ),
    )
    assert elements(xml, "BPMN-P004") == ["T1"]
    assert hits(xml, "BPMN-P012")[0].params == {"schritt": "PS2", "kontrolle": "K9"}


def test_p005_p006_risks() -> None:
    xml = _process(
        _task(
            "T1",
            '<flowaudit:kontrolle id="K1" nachweis="V"/>',
            '<flowaudit:risiko id="R1"/>',
            '<flowaudit:risiko id="R2" kontrollen="K1 K7"/>',
        )
    )
    assert elements(xml, "BPMN-P005") == ["T1"]
    assert hits(xml, "BPMN-P006")[0].params["kontrolle"] == "K7"


def test_p007_unknown_values() -> None:
    xml = _process(
        _task(
            "T1",
            '<flowaudit:kontrolle id="K1" art="spontan" durchfuehrung="manuell" nachweis="V"/>',
            '<flowaudit:risiko id="R1" kontrollen="K1" inhaerent="extrem"/>',
            '<flowaudit:pruefschritt ergebnis="gut"/>',
            '<flowaudit:frist wert="1" einheit="stunden"><flowaudit:rechtsgrundlage>x</flowaudit:rechtsgrundlage></flowaudit:frist>',
            '<flowaudit:quelle art="gerücht"/>',
        )
    )
    assert sorted(i.params["feld"] for i in hits(xml, "BPMN-P007")) == [
        "art",
        "art",
        "einheit",
        "ergebnis",
        "inhaerent",
    ]


def test_p008_duplicate_ids() -> None:
    xml = _process(
        _task("T1", '<flowaudit:kontrolle id="X" nachweis="V"/>'),
        _task("T2", '<flowaudit:risiko id="X" kontrollen="X"/>'),
    )
    assert hits(xml, "BPMN-P008")[0].params["id"] == "X"


def test_p009_finding_needs_type_and_description() -> None:
    xml = _process(
        _task("T1", '<flowaudit:feststellung art="formell"/>'),
        _task(
            "T2",
            '<flowaudit:feststellung art="finanziell" einstufung="gering" status="offen">'
            "<flowaudit:beschreibung>Beleg fehlt</flowaudit:beschreibung></flowaudit:feststellung>",
        ),
    )
    assert elements(xml, "BPMN-P009") == ["T1"]


def test_p010_failed_step_and_p011_marker_without_key_control() -> None:
    xml = _process(
        _task(
            "T1",
            '<flowaudit:pruefschritt id="PS1" ergebnis="nicht_erfuellt"/>',
            '<flowaudit:kennzeichen typ="schluesselkontrolle"/>',
        )
    )
    assert hits(xml, "BPMN-P010")[0].params["schritt"] == "PS1"
    assert elements(xml, "BPMN-P011") == ["T1"]
