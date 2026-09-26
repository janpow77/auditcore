"""Elementmodell: Typen, Pools, Lanes, Flüsse, Ereignisse, Daten, Diagramm-Infos."""

from __future__ import annotations

from helpers import INFO_OK, doc, ext, fixture_text, flow

from auditcore_bpmn.model import FLOW_NODES, BpmnDocument, category, parse_bpmn


def _typen() -> BpmnDocument:
    return parse_bpmn(fixture_text("synthetic/typen_kollaboration.bpmn"))


def test_categories() -> None:
    assert category("userTask") == "activity" and category("boundaryEvent") == "event"
    assert category("eventBasedGateway") == "gateway" and category("dataStoreReference") == "data"
    assert category("group") == "artifact" and category("messageFlow") == "connection"
    assert category("lane") == "container" and category("message") == "other"
    assert "callActivity" in FLOW_NODES and "dataObject" not in FLOW_NODES


def test_collaboration_pools_lanes_and_processes() -> None:
    document = _typen()
    assert [p.id for p in document.participants] == ["Pool_Stelle", "Pool_System"]
    assert {p.id for p in document.processes} == {"Process_Stelle", "Process_System"}
    task = document.elements["Erfassen"]
    assert task.process_id == "Process_Stelle" and task.participant_id == "Pool_Stelle"
    assert task.lane_ids == ("Lane_Sach",)
    lane, actor = document.actor_of(task)
    assert lane is not None and lane.id == "Lane_Sach" and actor is not None and actor.display_name == "Beispielstelle"
    system_task = document.elements["Berechnen"]
    pool, pool_actor = document.actor_of(system_task)
    assert pool is not None and pool.id == "Pool_System" and pool_actor is not None and pool_actor.role == "it"


def test_events_definitions_and_boundary() -> None:
    document = _typen()
    assert document.elements["Warten"].event_definitions == ("messageEventDefinition",)
    boundary = document.elements["Zeitueberschreitung"]
    assert boundary.attached_to == "Unter" and boundary.interrupting is False
    assert document.elements["LinkWurf"].link_name == "weiter"
    assert document.elements["Aufruf"].called_element == "Process_Auszahlung"
    inner = document.elements["U_Pruefen"]
    assert inner.parent_id == "Unter" and inner.process_id == "Process_Stelle"


def test_flows_and_data_associations() -> None:
    document = _typen()
    assert [f.id for f in document.outgoing("Erfassen")] == ["F2"]
    assert [f.id for f in document.incoming("Ende")] == ["F8", "F10"]
    assert {f.id for f in document.message_flows} == {"MF_1", "MF_2"}
    association = document.elements["DOA_1"]
    assert association.parent_id == "Erfassen" and association.target == "Akte"
    assert document.elements["Akte"].extensions.evidence[0].it_system == "Fachanwendung"
    assert document.elements["Erfassen"].attributes["{http://camunda.org/schema/1.0/bpmn}assignee"] == "nicht-auswerten"


def test_nested_lanes_assign_all_levels() -> None:
    body = (
        '<bpmn:laneSet id="LS"><bpmn:lane id="Aussen" name="Außen"><bpmn:childLaneSet id="CLS">'
        '<bpmn:lane id="Innen" name="Innen"><bpmn:flowNodeRef>T</bpmn:flowNodeRef></bpmn:lane>'
        "</bpmn:childLaneSet><bpmn:flowNodeRef>T</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet>"
        '<bpmn:task id="T" name="Aufgabe"/>'
    )
    document = parse_bpmn(doc(body))
    assert document.elements["T"].lane_ids == ("Aussen", "Innen")
    lane = document.lane_of(document.elements["T"])
    assert lane is not None and lane.id == "Innen" and document.elements["Innen"].parent_id == "Aussen"


def test_diagram_info_location_and_duplicates() -> None:
    xml = doc(
        '<bpmn:task id="T"/><bpmn:task id="T"/>' + flow("F", "T", "X", "a"),
        collaboration=ext(INFO_OK) + '<bpmn:participant id="Pool" processRef="P1"/>',
    )
    document = parse_bpmn(xml)
    assert document.diagram_info is not None and document.diagram_info_owner == "C1"
    assert document.duplicate_ids == ["T"]
    assert document.elements["F"].condition == "a"
    info_in_process = parse_bpmn(doc(ext(INFO_OK)))
    assert info_in_process.diagram_info_owner == "P1"


def test_esi_prefers_structured_over_legacy() -> None:
    structured = (
        '<flowaudit:esiAnforderungen profil="ESI"><flowaudit:esiAnforderung code="KA1">'
        "<flowaudit:kriterium>K1</flowaudit:kriterium></flowaudit:esiAnforderung></flowaudit:esiAnforderungen>"
    )
    document = parse_bpmn(doc(ext(structured), process='id="P1" esiProfile="ALT" esiCoreRequirements="KA9"'))
    assert document.esi is not None and document.esi.origin == "flowaudit-1.1"
    legacy = parse_bpmn(doc("", process='id="P1" esiCoreRequirements="KA9:K1"'))
    assert legacy.esi is not None and legacy.esi.profile == "ESI" and legacy.esi.requirements[0].code == "KA9"


def test_to_dict_is_json_ready() -> None:
    data = _typen().to_dict()
    assert data["is_bpmn"] is True and data["diagram_info"]["title"] == "Typabdeckung"
    task = next(e for e in data["elements"] if e["id"] == "Erfassen")
    assert task["lane_ids"] == ["Lane_Sach"] and task["category"] == "activity"
