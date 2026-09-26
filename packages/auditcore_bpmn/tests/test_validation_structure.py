"""Strukturregeln BPMN-S…: je Regel ein auslösender und ein unauffälliger Fall."""

from __future__ import annotations

from helpers import BPMN, doc, flow, linear
from rulecheck import elements, hits

CLEAN = doc(linear("T1", "T2"))


def test_clean_process_has_no_structure_issues() -> None:
    assert all(not hits(CLEAN, f"BPMN-S0{n:02d}") for n in (1, 2, 3, 10, 11, 12, 13, 14, 15, 16, 20, 21, 22, 50))


def test_s001_root_and_s002_no_process() -> None:
    wrong_root = f'<bpmn:process xmlns:bpmn="{BPMN}" id="P"/>'
    assert elements(wrong_root, "BPMN-S001") == [None]
    empty = f'<bpmn:definitions xmlns:bpmn="{BPMN}"/>'
    assert elements(empty, "BPMN-S002") == [None]


def test_s003_duplicate_ids() -> None:
    assert elements(doc(linear("T1") + '<bpmn:task id="T1"/>'), "BPMN-S003") == ["T1"]


def test_s010_s011_start_and_end() -> None:
    xml = doc('<bpmn:task id="T" name="A"/>')
    assert elements(xml, "BPMN-S010") == ["P1"] and elements(xml, "BPMN-S011") == ["P1"]
    assert not hits(doc(""), "BPMN-S010")


def test_s012_orphan_s013_s014_missing_flows() -> None:
    xml = doc(
        linear("T1") + '<bpmn:task id="Waise" name="W"/><bpmn:task id="NurAus" name="A"/>'
        '<bpmn:task id="NurEin" name="B"/>' + flow("X1", "NurAus", "E") + flow("X2", "T1", "NurEin")
    )
    assert elements(xml, "BPMN-S012") == ["Waise"]
    assert elements(xml, "BPMN-S013") == ["NurAus"] and elements(xml, "BPMN-S014") == ["NurEin"]


def test_s012_exemptions() -> None:
    compensation = doc(linear("T1") + '<bpmn:task id="K" name="K" isForCompensation="true"/>')
    assert not hits(compensation, "BPMN-S012")
    event_sub = doc(
        linear("T1") + '<bpmn:subProcess id="ES" triggeredByEvent="true"><bpmn:startEvent id="ESS"/>'
        '<bpmn:endEvent id="ESE"/>' + flow("EF", "ESS", "ESE") + "</bpmn:subProcess>"
    )
    assert "ESS" not in elements(event_sub, "BPMN-S013")
    ad_hoc = doc(linear("T1") + '<bpmn:adHocSubProcess id="AH"><bpmn:task id="Frei" name="F"/></bpmn:adHocSubProcess>')
    assert "Frei" not in elements(ad_hoc, "BPMN-S012")


def test_s015_s016_start_end_flows() -> None:
    xml = doc(linear("T1") + flow("R1", "T1", "S") + flow("R2", "E", "T1"))
    assert elements(xml, "BPMN-S015") == ["S"] and elements(xml, "BPMN-S016") == ["E"]


def test_s020_s021_s022_sequence_flows() -> None:
    xml = doc(
        linear("T1")
        + '<bpmn:sequenceFlow id="Offen" sourceRef="T1"/>'
        + flow("Fremd", "T1", "Nirgends")
        + '<bpmn:subProcess id="SP" name="U"><bpmn:task id="Innen" name="I"/></bpmn:subProcess>'
        + flow("Grenze", "T1", "Innen")
    )
    assert elements(xml, "BPMN-S020") == ["Offen"]
    assert [i.params["ref"] for i in hits(xml, "BPMN-S021")] == ["Nirgends"]
    assert elements(xml, "BPMN-S022") == ["Grenze"]


def test_s023_s024_message_flows() -> None:
    collaboration = (
        '<bpmn:participant id="Pool" processRef="P1"/>'
        '<bpmn:messageFlow id="Innen" sourceRef="T1" targetRef="T2"/>'
        '<bpmn:messageFlow id="Kaputt" sourceRef="T1" targetRef="Fehlt"/>'
    )
    xml = doc(linear("T1", "T2"), collaboration=collaboration)
    assert elements(xml, "BPMN-S023") == ["Innen"] and elements(xml, "BPMN-S024") == ["Kaputt"]


def test_s030_s032_s051_branching_gateways() -> None:
    body = (
        '<bpmn:startEvent id="S"/><bpmn:exclusiveGateway id="G"/><bpmn:inclusiveGateway id="G2" name="Frage?"/>'
        '<bpmn:endEvent id="E"/>'
        + flow("F0", "S", "G")
        + flow("F1", "G", "G2", "a")
        + flow("F2", "G", "E")
        + flow("F3", "G2", "E")
        + flow("F4", "G2", "E")
    )
    xml = doc(body)
    assert elements(xml, "BPMN-S030") == ["G"] and elements(xml, "BPMN-S032") == ["G2"]
    assert elements(xml, "BPMN-S051") == ["G"]
    with_default = xml.replace('<bpmn:exclusiveGateway id="G"/>', '<bpmn:exclusiveGateway id="G" default="F2"/>')
    assert not hits(with_default, "BPMN-S030")


def test_s031_default_must_be_outgoing() -> None:
    xml = doc(
        linear("T1").replace('<bpmn:task id="T1" name="Aufgabe T1"/>', '<bpmn:task id="T1" name="A" default="F1"/>')
    )
    assert elements(xml, "BPMN-S031") == ["T1"]


def test_s033_s035_gateways() -> None:
    body = (
        '<bpmn:startEvent id="S"/><bpmn:parallelGateway id="PG"/><bpmn:parallelGateway id="PJ"/><bpmn:endEvent id="E"/>'
        + flow("F0", "S", "PG")
        + flow("F1", "PG", "PJ", "x")
        + flow("F2", "PG", "PJ")
        + flow("F3", "PJ", "E")
    )
    xml = doc(body)
    assert elements(xml, "BPMN-S035") == ["PG"]
    single = doc(
        '<bpmn:startEvent id="S"/><bpmn:exclusiveGateway id="G"/><bpmn:endEvent id="E"/>'
        + flow("F0", "S", "G")
        + flow("F1", "G", "E")
    )
    assert elements(single, "BPMN-S033") == ["G"]


def test_s034_event_based_gateway_targets() -> None:
    body = (
        '<bpmn:startEvent id="S"/><bpmn:eventBasedGateway id="EG"/>'
        '<bpmn:intermediateCatchEvent id="Z"><bpmn:timerEventDefinition/></bpmn:intermediateCatchEvent>'
        '<bpmn:task id="Falsch" name="F"/><bpmn:endEvent id="E"/>'
        + flow("F0", "S", "EG")
        + flow("F1", "EG", "Z")
        + flow("F2", "EG", "Falsch")
        + flow("F3", "Z", "E")
        + flow("F4", "Falsch", "E")
    )
    assert [i.params["ziel"] for i in hits(doc(body), "BPMN-S034")] == ["F"]


def test_s040_s041_s042_boundary_events() -> None:
    body = (
        linear("T1")
        + (
            '<bpmn:boundaryEvent id="B1" attachedToRef="T1"><bpmn:timerEventDefinition/></bpmn:boundaryEvent>'
            '<bpmn:boundaryEvent id="B2" attachedToRef="Fehlt"/>'
            '<bpmn:boundaryEvent id="B3" attachedToRef="T1"><bpmn:compensateEventDefinition/></bpmn:boundaryEvent>'
        )
        + flow("FB", "T1", "B2")
        + flow("FB2", "B2", "E")
    )
    xml = doc(body)
    assert elements(xml, "BPMN-S040") == ["B1"]
    assert elements(xml, "BPMN-S041") == ["B2"] and elements(xml, "BPMN-S042") == ["B2"]


def test_s050_task_names_and_s061_call_activity() -> None:
    xml = doc(linear("T1").replace('name="Aufgabe T1"', 'name=" "') + '<bpmn:callActivity id="CA" name="Aufruf"/>')
    assert elements(xml, "BPMN-S050") == ["T1"] and elements(xml, "BPMN-S061") == ["CA"]


def test_s060_link_without_catch() -> None:
    body = linear("T1") + (
        '<bpmn:intermediateThrowEvent id="LW"><bpmn:linkEventDefinition name="x"/></bpmn:intermediateThrowEvent>'
        + flow("FL", "T1", "LW")
    )
    assert elements(doc(body), "BPMN-S060") == ["LW"]
    with_catch = body + (
        '<bpmn:intermediateCatchEvent id="LF"><bpmn:linkEventDefinition name="x"/></bpmn:intermediateCatchEvent>'
        + flow("FL2", "LF", "E")
    )
    assert not hits(doc(with_catch), "BPMN-S060") and not hits(doc(with_catch), "BPMN-S013")


def test_s070_s071_associations() -> None:
    body = (
        linear("T1").replace(
            '<bpmn:task id="T1" name="Aufgabe T1"/>',
            '<bpmn:task id="T1" name="A"><bpmn:dataInputAssociation id="DIA"><bpmn:sourceRef>Weg</bpmn:sourceRef>'
            "<bpmn:targetRef>T1</bpmn:targetRef></bpmn:dataInputAssociation></bpmn:task>",
        )
        + '<bpmn:association id="AS" sourceRef="T1" targetRef="Nichts"/>'
    )
    xml = doc(body)
    assert elements(xml, "BPMN-S070") == ["DIA"] and elements(xml, "BPMN-S071") == ["AS"]
