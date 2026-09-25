"""Elementtypen von BPMN 2.0 und das Element-/Dokumentmodell."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree as ET

from ..extensions import Actor, DiagramInfo, EsiRequirements, Extensions, to_dict
from ..safe_xml import ParsedXml

TASKS = frozenset(
    {"task", "userTask", "manualTask", "serviceTask", "scriptTask", "businessRuleTask", "sendTask", "receiveTask"}
)
SUBPROCESSES = frozenset({"subProcess", "adHocSubProcess", "transaction"})
ACTIVITIES = TASKS | SUBPROCESSES | {"callActivity"}
EVENTS = frozenset(
    {
        "startEvent",
        "endEvent",
        "intermediateThrowEvent",
        "intermediateCatchEvent",
        "boundaryEvent",
        "implicitThrowEvent",
    }
)
GATEWAYS = frozenset({"exclusiveGateway", "inclusiveGateway", "parallelGateway", "complexGateway", "eventBasedGateway"})
FLOW_NODES = ACTIVITIES | EVENTS | GATEWAYS
DATA = frozenset({"dataObject", "dataObjectReference", "dataStore", "dataStoreReference", "dataInput", "dataOutput"})
ARTIFACTS = frozenset({"textAnnotation", "group"})
CONNECTIONS = frozenset({"sequenceFlow", "messageFlow", "association", "dataInputAssociation", "dataOutputAssociation"})
CONTAINERS = frozenset({"process", "collaboration", "participant", "laneSet", "lane"})

_CATEGORIES = (
    (ACTIVITIES, "activity"),
    (EVENTS, "event"),
    (GATEWAYS, "gateway"),
    (DATA, "data"),
    (ARTIFACTS, "artifact"),
    (CONNECTIONS, "connection"),
    (CONTAINERS, "container"),
)


def category(element_type: str) -> str:
    """Grobe Einordnung eines BPMN-Elementtyps."""
    return next((name for members, name in _CATEGORIES if element_type in members), "other")


@dataclass
class BpmnElement:
    """Ein BPMN-Element mit Kennung."""

    id: str
    type: str
    name: str | None
    category: str
    process_id: str | None = None
    parent_id: str | None = None
    participant_id: str | None = None
    lane_ids: tuple[str, ...] = ()
    attributes: dict[str, str] = field(default_factory=dict)
    documentation: str | None = None
    event_definitions: tuple[str, ...] = ()
    link_name: str | None = None
    attached_to: str | None = None
    interrupting: bool | None = None
    default: str | None = None
    source: str | None = None
    target: str | None = None
    condition: str | None = None
    called_element: str | None = None
    is_compensation: bool = False
    is_event_subprocess: bool = False
    process_ref: str | None = None
    extensions: Extensions = field(default_factory=Extensions)

    @property
    def is_flow_node(self) -> bool:
        """``True`` für Aktivitäten, Ereignisse und Gateways."""
        return self.type in FLOW_NODES

    @property
    def is_task(self) -> bool:
        """``True`` für Aufgaben aller Typen."""
        return self.type in TASKS

    @property
    def is_activity(self) -> bool:
        """``True`` für Aufgaben, Unterprozesse und Aufrufaktivitäten."""
        return self.type in ACTIVITIES

    @property
    def label(self) -> str:
        """Name oder, falls leer, ID."""
        return (self.name or "").strip() or self.id

    def to_dict(self) -> dict[str, Any]:
        """JSON-fähige Darstellung ohne leere Werte."""
        data: dict[str, Any] = {"id": self.id, "type": self.type, "category": self.category}
        for key in (
            "name",
            "process_id",
            "parent_id",
            "participant_id",
            "documentation",
            "link_name",
            "attached_to",
            "interrupting",
            "default",
            "source",
            "target",
            "condition",
            "called_element",
            "process_ref",
        ):
            if getattr(self, key) is not None:
                data[key] = getattr(self, key)
        for key in ("lane_ids", "event_definitions"):
            if getattr(self, key):
                data[key] = list(getattr(self, key))
        for key in ("is_compensation", "is_event_subprocess"):
            if getattr(self, key):
                data[key] = True
        if not self.extensions.is_empty:
            data["extensions"] = self.extensions.to_dict()
        return data


@dataclass
class BpmnDocument:
    """Gelesenes BPMN-Dokument; der XML-Baum bleibt für gezielte Änderungen zugänglich."""

    parsed: ParsedXml
    elements: dict[str, BpmnElement]
    duplicate_ids: list[str]
    diagram_info: DiagramInfo | None
    diagram_info_owner: str | None
    esi: EsiRequirements | None
    definitions_id: str | None
    target_namespace: str | None
    is_bpmn: bool
    xml_nodes: dict[str, ET.Element] = field(default_factory=dict, repr=False)

    @property
    def root(self) -> ET.Element:
        """Wurzelelement des XML-Baums."""
        return self.parsed.root

    def xml_element(self, element_id: str) -> ET.Element:
        """XML-Knoten eines Elements (für gezielte Änderungen)."""
        return self.xml_nodes[element_id]

    def by_type(self, *types: str) -> list[BpmnElement]:
        """Elemente der genannten Typen in Dokumentreihenfolge."""
        return [e for e in self.elements.values() if e.type in types]

    @property
    def processes(self) -> list[BpmnElement]:
        """Alle Prozesse."""
        return self.by_type("process")

    @property
    def participants(self) -> list[BpmnElement]:
        """Alle Pools."""
        return self.by_type("participant")

    @property
    def lanes(self) -> list[BpmnElement]:
        """Alle Lanes (auch verschachtelte)."""
        return self.by_type("lane")

    @property
    def flow_nodes(self) -> list[BpmnElement]:
        """Alle Flussknoten."""
        return [e for e in self.elements.values() if e.is_flow_node]

    @property
    def activities(self) -> list[BpmnElement]:
        """Alle Aktivitäten."""
        return [e for e in self.elements.values() if e.is_activity]

    @property
    def sequence_flows(self) -> list[BpmnElement]:
        """Alle Sequenzflüsse."""
        return self.by_type("sequenceFlow")

    @property
    def message_flows(self) -> list[BpmnElement]:
        """Alle Nachrichtenflüsse."""
        return self.by_type("messageFlow")

    def incoming(self, element_id: str, flow_type: str = "sequenceFlow") -> list[BpmnElement]:
        """Eingehende Flüsse eines Elements."""
        return [f for f in self.by_type(flow_type) if f.target == element_id]

    def outgoing(self, element_id: str, flow_type: str = "sequenceFlow") -> list[BpmnElement]:
        """Ausgehende Flüsse eines Elements."""
        return [f for f in self.by_type(flow_type) if f.source == element_id]

    def participant_of(self, element: BpmnElement) -> BpmnElement | None:
        """Pool eines Elements (über seinen Prozess) oder der Pool selbst."""
        if element.type == "participant":
            return element
        return self.elements.get(element.participant_id or "")

    def lane_of(self, element: BpmnElement) -> BpmnElement | None:
        """Innerste Lane eines Flussknotens."""
        lanes = [self.elements[i] for i in element.lane_ids if i in self.elements]
        return lanes[-1] if lanes else None

    def actor_of(self, element: BpmnElement) -> tuple[BpmnElement | None, Actor | None]:
        """Stelle eines Elements: innerste Lane mit Akteur, sonst Pool mit Akteur.

        Ohne erfasste Rolle ist der Akteur ``None`` und die Stelle die
        innerste Lane bzw. der Pool.
        """
        for lane_id in reversed(element.lane_ids):
            lane = self.elements.get(lane_id)
            if lane is not None and lane.extensions.actor is not None:
                return lane, lane.extensions.actor
        pool = self.participant_of(element)
        if pool is not None and pool.extensions.actor is not None:
            return pool, pool.extensions.actor
        return (self.lane_of(element) or pool), None

    def __iter__(self) -> Iterator[BpmnElement]:
        return iter(self.elements.values())

    def to_dict(self) -> dict[str, Any]:
        """JSON-fähige Darstellung des Modells."""
        return {
            "definitions_id": self.definitions_id,
            "target_namespace": self.target_namespace,
            "is_bpmn": self.is_bpmn,
            "diagram_info": to_dict(self.diagram_info) if self.diagram_info else None,
            "diagram_info_owner": self.diagram_info_owner,
            "esi": to_dict(self.esi) if self.esi else None,
            "duplicate_ids": list(self.duplicate_ids),
            "elements": [element.to_dict() for element in self.elements.values()],
        }
