"""Erzeugt die Vorlagenbibliothek des Profils ``foerderperiode-2021-2027``.

Die Vorlagen sind **synthetisch**: allgemeingültige Abläufe, abgeleitet aus
VO (EU) 2021/1060 (Artikel wie im Profil verzeichnet), ohne Behörden-,
Programm- oder Personennamen und ohne Nutzerdiagramme (deren Übernahme ist
nicht freigegeben). Jede Vorlage hat Pools/Lanes mit Akteur-Rolle,
Diagramm-Infos (Status ``entwurf``), Rechtsgrundlagen, Prüfbezüge und DI::

    python tools/build_templates.py src/auditcore_bpmn/templates
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auditcore_bpmn.extensions import (  # noqa: E402
    Actor,
    AuditReference,
    Control,
    Deadline,
    DiagramInfo,
    Evidence,
    Extensions,
    LegalBasis,
    Marker,
    write_extensions,
)
from auditcore_bpmn.namespaces import BPMN_NS, BPMNDI_NS, DC_NS, DI_NS, FLOWAUDIT_NAMESPACE, q  # noqa: E402
from auditcore_bpmn.serialize import serialize_element  # noqa: E402
from auditcore_bpmn.vocabulary import ROLES, label  # noqa: E402

CPR = "Verordnung (EU) 2021/1060"
SIZES = {
    "task": (100, 80),
    "startEvent": (36, 36),
    "endEvent": (36, 36),
    "exclusiveGateway": (50, 50),
    "dataObjectReference": (36, 50),
}
LANE_HEIGHT = 160


def art(
    article: str, paragraph: str | None = None, point: str | None = None, subparagraph: str | None = None
) -> LegalBasis:
    return LegalBasis(
        act=CPR, article=article, paragraph=paragraph, point=point, subparagraph=subparagraph
    ).normalized()


def annex(number: str, point: str | None = None) -> LegalBasis:
    return LegalBasis(act=CPR, annex=number, number=point).normalized()


@dataclass
class Node:
    id: str
    type: str
    name: str
    lane: str
    column: int
    ext: Extensions = field(default_factory=Extensions)


@dataclass
class Template:
    id: str
    title: str
    description: str
    lanes: list[str]
    nodes: list[Node]
    flows: list[tuple[str, str, str | None]]
    references: tuple[AuditReference, ...] = ()
    data_links: list[tuple[str, str]] = field(default_factory=list)


def ka(number: int, audit_type: str | None = None) -> AuditReference:
    return AuditReference(key_requirement=str(number), audit_type=audit_type)


def templates() -> list[Template]:
    return [
        Template(
            "antragsverfahren",
            "Antragsverfahren und Auswahl der Vorhaben",
            "Auswahl der Vorhaben nach genehmigten Kriterien und Mitteilung der Bedingungen für die Unterstützung.",
            ["bga", "vb", "beg"],
            [
                Node("Start", "startEvent", "Förderaufruf geplant", "bga", 0),
                Node(
                    "Kriterien",
                    "task",
                    "Methodik und Kriterien für die Auswahl genehmigen",
                    "bga",
                    1,
                    Extensions(legal_bases=(art("40", "2", "a"),), audit_references=(ka(2),)),
                ),
                Node(
                    "Aufruf",
                    "task",
                    "Aufruf zur Einreichung von Vorschlägen veröffentlichen",
                    "vb",
                    2,
                    Extensions(legal_bases=(art("49", "2"),), markers=(Marker("veroeffentlichung"),)),
                ),
                Node("Antrag", "task", "Antrag einreichen", "beg", 3),
                Node(
                    "Pruefung",
                    "task",
                    "Antrag anhand der Auswahlkriterien prüfen",
                    "vb",
                    4,
                    Extensions(
                        legal_bases=(art("73", "1"), art("73", "2")),
                        audit_references=(ka(2),),
                        markers=(Marker("pruefpunkt"), Marker("checkliste")),
                        controls=(
                            Control(
                                id="K-AUSWAHL",
                                label="Prüfung nach Auswahlcheckliste",
                                key_control=True,
                                control_type="praeventiv",
                                execution="manuell",
                                evidence="ausgefüllte Checkliste",
                            ),
                        ),
                    ),
                ),
                Node("G_Auswahl", "exclusiveGateway", "Auswahlkriterien erfüllt?", "vb", 5),
                Node(
                    "Bedingungen",
                    "task",
                    "Dokument mit den Bedingungen für die Unterstützung übermitteln",
                    "vb",
                    6,
                    Extensions(
                        legal_bases=(art("73", "3"),),
                        audit_references=(ka(3),),
                        markers=(Marker("bewilligung"), Marker("bescheid")),
                    ),
                ),
                Node("Ablehnung", "task", "Ablehnung mitteilen", "vb", 6, Extensions(legal_bases=(art("73", "1"),))),
                Node("Ende_Ja", "endEvent", "Vorhaben ausgewählt", "vb", 7),
                Node("Ende_Nein", "endEvent", "Antrag abgelehnt", "beg", 7),
            ],
            [
                ("Start", "Kriterien", None),
                ("Kriterien", "Aufruf", None),
                ("Aufruf", "Antrag", None),
                ("Antrag", "Pruefung", None),
                ("Pruefung", "G_Auswahl", None),
                ("G_Auswahl", "Bedingungen", "ja"),
                ("G_Auswahl", "Ablehnung", "nein"),
                ("Bedingungen", "Ende_Ja", None),
                ("Ablehnung", "Ende_Nein", None),
            ],
            (ka(2), ka(3)),
        ),
        Template(
            "verwaltungskontrolle",
            "Verwaltungsüberprüfung (VerwK) eines Auszahlungsantrags",
            "Risikobasierte Verwaltungsprüfung und Vor-Ort-Überprüfung vor der Auszahlung.",
            ["beg", "vb"],
            [
                Node("Start", "startEvent", "Auszahlung beantragt", "beg", 0),
                Node("Einreichen", "task", "Auszahlungsantrag mit Belegen einreichen", "beg", 1),
                Node(
                    "Verwaltungspruefung",
                    "task",
                    "Verwaltungsprüfung des Auszahlungsantrags",
                    "vb",
                    2,
                    Extensions(
                        legal_bases=(art("74", "1", "a"), art("74", "2")),
                        audit_references=(ka(4, "verwk"),),
                        markers=(Marker("pruefpunkt"),),
                        controls=(
                            Control(
                                id="K-VERWK",
                                label="Verwaltungsprüfung nach Checkliste",
                                key_control=True,
                                control_type="praeventiv",
                                execution="manuell",
                            ),
                        ),
                    ),
                ),
                Node(
                    "Vermerk",
                    "dataObjectReference",
                    "Prüfvermerk",
                    "vb",
                    2,
                    Extensions(
                        evidence=(
                            Evidence(
                                document_type="Prüfvermerk",
                                storage_location="elektronische Akte",
                                retention_period="fünf Jahre ab dem 31. Dezember des Jahres der letzten Zahlung (Artikel 82 Absatz 1)",
                            ),
                        )
                    ),
                ),
                Node("G_VorOrt", "exclusiveGateway", "Vor-Ort-Überprüfung erforderlich?", "vb", 3),
                Node(
                    "VorOrt",
                    "task",
                    "Vor-Ort-Überprüfung durchführen",
                    "vb",
                    4,
                    Extensions(legal_bases=(art("74", "2", subparagraph="2"),), audit_references=(ka(4, "verwk"),)),
                ),
                Node("G_Join", "exclusiveGateway", "", "vb", 5),
                Node(
                    "Auszahlung",
                    "task",
                    "Auszahlung an den Begünstigten anweisen",
                    "vb",
                    6,
                    Extensions(
                        legal_bases=(art("74", "1", "b"),),
                        markers=(Marker("zahlung"), Marker("frist")),
                        deadlines=(
                            Deadline(
                                value="80",
                                unit="tage",
                                basis="ab Einreichung des Auszahlungsantrags",
                                legal_bases=(art("74", "1", "b"),),
                            ),
                        ),
                    ),
                ),
                Node("Ende", "endEvent", "Betrag ausgezahlt", "vb", 7),
            ],
            [
                ("Start", "Einreichen", None),
                ("Einreichen", "Verwaltungspruefung", None),
                ("Verwaltungspruefung", "G_VorOrt", None),
                ("G_VorOrt", "VorOrt", "ja"),
                ("G_VorOrt", "G_Join", "nein"),
                ("VorOrt", "G_Join", None),
                ("G_Join", "Auszahlung", None),
                ("Auszahlung", "Ende", None),
            ],
            (ka(4, "verwk"),),
            [("Verwaltungspruefung", "Vermerk")],
        ),
        Template(
            "zahlungsantrag",
            "Zahlungsantrag an die Kommission",
            "Zusammenstellung der Ausgaben und Einreichung des Zahlungsantrags durch die Stelle mit Rechnungsführungsfunktion.",
            ["rfs", "kom"],
            [
                Node("Start", "startEvent", "Einreichungszeitraum erreicht", "rfs", 0),
                Node(
                    "Ausgaben",
                    "task",
                    "Förderfähige Ausgaben aus der Buchführung zusammenstellen",
                    "rfs",
                    1,
                    Extensions(legal_bases=(art("76", "1", "a"),), audit_references=(ka(10),)),
                ),
                Node(
                    "Erstellen",
                    "task",
                    "Zahlungsantrag nach Anhang XXIII erstellen",
                    "rfs",
                    2,
                    Extensions(legal_bases=(art("91", "3"),), audit_references=(ka(10),)),
                ),
                Node(
                    "Einreichen",
                    "task",
                    "Zahlungsantrag bei der Kommission einreichen",
                    "rfs",
                    3,
                    Extensions(legal_bases=(art("91", "1"),)),
                ),
                Node(
                    "Zahlung",
                    "task",
                    "Zwischenzahlung leisten",
                    "kom",
                    4,
                    Extensions(
                        legal_bases=(art("93", "1"),),
                        markers=(Marker("zahlung"),),
                        deadlines=(
                            Deadline(
                                value="60",
                                unit="tage",
                                basis="ab Eingang des Zahlungsantrags",
                                legal_bases=(art("93", "1"),),
                            ),
                        ),
                    ),
                ),
                Node("Ende", "endEvent", "Zwischenzahlung erhalten", "rfs", 5),
            ],
            [
                ("Start", "Ausgaben", None),
                ("Ausgaben", "Erstellen", None),
                ("Erstellen", "Einreichen", None),
                ("Einreichen", "Zahlung", None),
                ("Zahlung", "Ende", None),
            ],
            (ka(10),),
        ),
        Template(
            "rechnungslegung",
            "Rechnungslegung und Gewährpaket",
            "Rechnungslegung, Verwaltungserklärung, Bestätigungsvermerk und jährlicher Kontrollbericht bis zum 15. Februar.",
            ["rfs", "vb", "pb"],
            [
                Node("Start", "startEvent", "Geschäftsjahr abgeschlossen", "rfs", 0),
                Node(
                    "Rechnung",
                    "task",
                    "Rechnungslegung nach Anhang XXIV erstellen",
                    "rfs",
                    1,
                    Extensions(legal_bases=(art("98", "1", "a"), art("76", "1", "b")), audit_references=(ka(10),)),
                ),
                Node(
                    "Erklaerung",
                    "task",
                    "Verwaltungserklärung erstellen",
                    "vb",
                    2,
                    Extensions(legal_bases=(art("74", "1", "f"),), audit_references=(ka(8),)),
                ),
                Node(
                    "Pruefung",
                    "task",
                    "Prüfung der Rechnungslegung",
                    "pb",
                    3,
                    Extensions(legal_bases=(art("77", "1"),), audit_references=(ka(14, "rechnungslegungspruefung"),)),
                ),
                Node(
                    "Vermerk",
                    "task",
                    "Bestätigungsvermerk und jährlichen Kontrollbericht erstellen",
                    "pb",
                    4,
                    Extensions(legal_bases=(art("77", "3"),), audit_references=(ka(15),)),
                ),
                Node(
                    "Gewaehr",
                    "task",
                    "Gewährpaket bei der Kommission einreichen",
                    "vb",
                    5,
                    Extensions(
                        legal_bases=(art("98", "1"),),
                        markers=(Marker("frist"),),
                        deadlines=(
                            Deadline(
                                value="15. Februar",
                                basis="für das vorangegangene Geschäftsjahr",
                                legal_bases=(art("98", "1"),),
                            ),
                        ),
                    ),
                ),
                Node("Ende", "endEvent", "Gewährpaket eingereicht", "vb", 6),
            ],
            [
                ("Start", "Rechnung", None),
                ("Rechnung", "Erklaerung", None),
                ("Erklaerung", "Pruefung", None),
                ("Pruefung", "Vermerk", None),
                ("Vermerk", "Gewaehr", None),
                ("Gewaehr", "Ende", None),
            ],
            (ka(8), ka(10), ka(14), ka(15)),
        ),
        Template(
            "unregelmaessigkeiten",
            "Unregelmäßigkeiten: Behandlung und Meldung",
            "Feststellung, Meldung nach Anhang XII und Finanzkorrektur von Unregelmäßigkeiten.",
            ["vb", "kom"],
            [
                Node("Start", "startEvent", "Hinweis auf Unregelmäßigkeit", "vb", 0),
                Node(
                    "Feststellen",
                    "task",
                    "Unregelmäßigkeit feststellen und bewerten",
                    "vb",
                    1,
                    Extensions(legal_bases=(art("74", "1", "d"),), audit_references=(ka(7),)),
                ),
                Node(
                    "G_Melden",
                    "exclusiveGateway",
                    "Meldepflichtig nach Anhang XII?",
                    "vb",
                    2,
                    Extensions(legal_bases=(annex("XII"),)),
                ),
                Node(
                    "Melden",
                    "task",
                    "Unregelmäßigkeit melden",
                    "vb",
                    3,
                    Extensions(
                        legal_bases=(art("69", "2"), annex("XII", "1.4")),
                        markers=(Marker("frist"),),
                        deadlines=(
                            Deadline(
                                value="2",
                                unit="monate",
                                basis="nach Ende des Quartals der Feststellung",
                                legal_bases=(annex("XII", "1.4"),),
                            ),
                        ),
                    ),
                ),
                Node("Empfang", "task", "Meldung entgegennehmen", "kom", 4),
                Node("G_Join", "exclusiveGateway", "", "vb", 5),
                Node(
                    "Korrektur",
                    "task",
                    "Finanzkorrektur vornehmen",
                    "vb",
                    6,
                    Extensions(legal_bases=(art("103", "1"),)),
                ),
                Node("Ende", "endEvent", "Unregelmäßigkeit behandelt", "vb", 7),
            ],
            [
                ("Start", "Feststellen", None),
                ("Feststellen", "G_Melden", None),
                ("G_Melden", "Melden", "ja"),
                ("G_Melden", "G_Join", "nein"),
                ("Melden", "Empfang", None),
                ("Empfang", "G_Join", None),
                ("G_Join", "Korrektur", None),
                ("Korrektur", "Ende", None),
            ],
            (ka(7),),
        ),
        Template(
            "vorhabenpruefung",
            "Vorhabenprüfung",
            "Prüfung einer Stichprobe von Vorhaben durch die Prüfbehörde mit kontradiktorischem Verfahren.",
            ["pb", "vb", "beg"],
            [
                Node("Start", "startEvent", "Geschäftsjahr zur Prüfung", "pb", 0),
                Node(
                    "Stichprobe",
                    "task",
                    "Stichprobe ziehen",
                    "pb",
                    1,
                    Extensions(legal_bases=(art("79", "1"),), audit_references=(ka(13, "vorhabenpruefung"),)),
                ),
                Node(
                    "Pruefen",
                    "task",
                    "Vorhabenprüfung durchführen",
                    "pb",
                    2,
                    Extensions(legal_bases=(art("77", "1"),), audit_references=(ka(13, "vorhabenpruefung"),)),
                ),
                Node(
                    "Unterlagen",
                    "task",
                    "Unterlagen bereitstellen",
                    "beg",
                    3,
                    Extensions(legal_bases=(art("82", "1"),)),
                ),
                Node(
                    "Entwurf",
                    "task",
                    "Berichtsentwurf übermitteln",
                    "pb",
                    4,
                    Extensions(audit_references=(ka(13, "vorhabenpruefung"),)),
                ),
                Node(
                    "Stellungnahme",
                    "task",
                    "Stellungnahme abgeben",
                    "vb",
                    5,
                    Extensions(markers=(Marker("stellungnahme"),)),
                ),
                Node(
                    "Bericht",
                    "task",
                    "Endgültigen Prüfbericht erstellen",
                    "pb",
                    6,
                    Extensions(audit_references=(ka(13, "vorhabenpruefung"),)),
                ),
                Node("Ende", "endEvent", "Vorhabenprüfung abgeschlossen", "pb", 7),
            ],
            [
                ("Start", "Stichprobe", None),
                ("Stichprobe", "Pruefen", None),
                ("Pruefen", "Unterlagen", None),
                ("Unterlagen", "Entwurf", None),
                ("Entwurf", "Stellungnahme", None),
                ("Stellungnahme", "Bericht", None),
                ("Bericht", "Ende", None),
            ],
            (ka(13, "vorhabenpruefung"),),
        ),
        Template(
            "systempruefung",
            "Systemprüfung",
            "Prüfung der Funktionsfähigkeit des Verwaltungs- und Kontrollsystems anhand der Kernanforderungen.",
            ["pb", "vb"],
            [
                Node("Start", "startEvent", "Systemprüfung nach Prüfstrategie", "pb", 0),
                Node(
                    "Planen",
                    "task",
                    "Systemprüfung planen",
                    "pb",
                    1,
                    Extensions(legal_bases=(art("78", "1"),), audit_references=(ka(12, "systempruefung"),)),
                ),
                Node(
                    "Durchlauf",
                    "task",
                    "Durchlauftest durchführen",
                    "pb",
                    2,
                    Extensions(legal_bases=(art("77", "1"),), audit_references=(ka(12, "systempruefung"),)),
                ),
                Node(
                    "Bewerten",
                    "task",
                    "Kernanforderungen nach Anhang XI bewerten",
                    "pb",
                    3,
                    Extensions(legal_bases=(art("69", "1"), annex("XI")), audit_references=(ka(12, "systempruefung"),)),
                ),
                Node("Entwurf", "task", "Berichtsentwurf übermitteln", "pb", 4),
                Node(
                    "Stellungnahme",
                    "task",
                    "Stellungnahme abgeben",
                    "vb",
                    5,
                    Extensions(markers=(Marker("stellungnahme"),)),
                ),
                Node(
                    "Bericht",
                    "task",
                    "Endgültigen Systemprüfbericht erstellen",
                    "pb",
                    6,
                    Extensions(audit_references=(ka(12, "systempruefung"),)),
                ),
                Node("Ende", "endEvent", "Systemprüfung abgeschlossen", "pb", 7),
            ],
            [
                ("Start", "Planen", None),
                ("Planen", "Durchlauf", None),
                ("Durchlauf", "Bewerten", None),
                ("Bewerten", "Entwurf", None),
                ("Entwurf", "Stellungnahme", None),
                ("Stellungnahme", "Bericht", None),
                ("Bericht", "Ende", None),
            ],
            (ka(12, "systempruefung"),),
        ),
    ]


def _bounds(parent: ET.Element, x: float, y: float, w: float, h: float) -> None:
    ET.SubElement(parent, q(DC_NS, "Bounds"), {"x": str(int(x)), "y": str(int(y)), "width": str(w), "height": str(h)})


def build(template: Template) -> ET.Element:
    root = ET.Element(
        q(BPMN_NS, "definitions"),
        {"id": f"Definitions_{template.id}", "targetNamespace": "https://flowaudit.de/bpmn/vorlagen"},
    )
    collaboration = ET.SubElement(root, q(BPMN_NS, "collaboration"), {"id": "Collaboration_1"})
    info = DiagramInfo(
        profile="foerderperiode-2021-2027",
        title=template.title,
        description=template.description,
        status="entwurf",
        programming_period="2021-2027",
        version="1",
        audit_references=template.references,
        keywords=("Vorlage",),
    )
    participant = ET.SubElement(
        collaboration, q(BPMN_NS, "participant"), {"id": "Pool_1", "name": template.title, "processRef": "Process_1"}
    )
    write_extensions(collaboration, Extensions(diagram_info=info))
    process = ET.SubElement(root, q(BPMN_NS, "process"), {"id": "Process_1", "isExecutable": "false"})
    lane_set = ET.SubElement(process, q(BPMN_NS, "laneSet"), {"id": "LaneSet_1"})
    lanes = {}
    for code in template.lanes:
        lane = ET.SubElement(lane_set, q(BPMN_NS, "lane"), {"id": f"Lane_{code}", "name": label(ROLES[code].labels)})
        write_extensions(lane, Extensions(actor=Actor(role=code)))
        lanes[code] = lane
    nodes = {}
    for node in template.nodes:
        attributes = {"id": node.id}
        if node.name:
            attributes["name"] = node.name
        element = ET.SubElement(process, q(BPMN_NS, node.type), attributes)
        write_extensions(element, node.ext)
        nodes[node.id] = element
        if node.type != "dataObjectReference":
            ET.SubElement(lanes[node.lane], q(BPMN_NS, "flowNodeRef")).text = node.id
    for node in template.nodes:
        if node.type == "dataObjectReference":
            ET.SubElement(process, q(BPMN_NS, "dataObject"), {"id": f"{node.id}_Objekt"})
            nodes[node.id].set("dataObjectRef", f"{node.id}_Objekt")
    for source, target in template.data_links:
        association = ET.SubElement(nodes[source], q(BPMN_NS, "dataOutputAssociation"), {"id": f"DA_{source}_{target}"})
        ET.SubElement(association, q(BPMN_NS, "targetRef")).text = target
    for index, (source, target, name) in enumerate(template.flows, start=1):
        attributes = {"id": f"Flow_{index}", "sourceRef": source, "targetRef": target}
        if name:
            attributes["name"] = name
        ET.SubElement(process, q(BPMN_NS, "sequenceFlow"), attributes)
    _diagram(root, template, participant)
    return root


def _position(template: Template, node: Node) -> tuple[float, float, int, int]:
    width, height = SIZES[node.type]
    lane_top = 60 + template.lanes.index(node.lane) * LANE_HEIGHT
    center_y = lane_top + LANE_HEIGHT / 2 + (45 if node.type == "dataObjectReference" else 0)
    center_x = 230 + node.column * 170 + (0 if node.type != "dataObjectReference" else 20)
    return center_x - width / 2, center_y - height / 2, width, height


def _diagram(root: ET.Element, template: Template, participant: ET.Element) -> None:
    diagram = ET.SubElement(root, q(BPMNDI_NS, "BPMNDiagram"), {"id": "BPMNDiagram_1"})
    plane = ET.SubElement(diagram, q(BPMNDI_NS, "BPMNPlane"), {"id": "BPMNPlane_1", "bpmnElement": "Collaboration_1"})
    width = 180 + (max(n.column for n in template.nodes) + 1) * 170
    shape = ET.SubElement(
        plane,
        q(BPMNDI_NS, "BPMNShape"),
        {"id": "Pool_1_di", "bpmnElement": participant.get("id", ""), "isHorizontal": "true"},
    )
    _bounds(shape, 100, 60, width, len(template.lanes) * LANE_HEIGHT)
    for index, code in enumerate(template.lanes):
        lane_shape = ET.SubElement(
            plane,
            q(BPMNDI_NS, "BPMNShape"),
            {"id": f"Lane_{code}_di", "bpmnElement": f"Lane_{code}", "isHorizontal": "true"},
        )
        _bounds(lane_shape, 130, 60 + index * LANE_HEIGHT, width - 30, LANE_HEIGHT)
    boxes = {}
    for node in template.nodes:
        x, y, w, h = _position(template, node)
        boxes[node.id] = (x, y, w, h)
        node_shape = ET.SubElement(plane, q(BPMNDI_NS, "BPMNShape"), {"id": f"{node.id}_di", "bpmnElement": node.id})
        _bounds(node_shape, x, y, w, h)
    for index, (source, target, _name) in enumerate(template.flows, start=1):
        sx, sy, sw, sh = boxes[source]
        tx, ty, tw, th = boxes[target]
        start, end = (sx + sw, sy + sh / 2), (tx, ty + th / 2)
        points = (
            [start]
            if start[1] == end[1]
            else [start, ((start[0] + end[0]) / 2, start[1]), ((start[0] + end[0]) / 2, end[1])]
        )
        edge = ET.SubElement(
            plane, q(BPMNDI_NS, "BPMNEdge"), {"id": f"Flow_{index}_di", "bpmnElement": f"Flow_{index}"}
        )
        for px, py in [*points, end]:
            ET.SubElement(edge, q(DI_NS, "waypoint"), {"x": str(int(px)), "y": str(int(py))})
    for source, target in template.data_links:
        sx, sy, sw, sh = boxes[source]
        tx, ty, tw, _th = boxes[target]
        edge = ET.SubElement(
            plane, q(BPMNDI_NS, "BPMNEdge"), {"id": f"DA_{source}_{target}_di", "bpmnElement": f"DA_{source}_{target}"}
        )
        ET.SubElement(edge, q(DI_NS, "waypoint"), {"x": str(int(sx + sw / 2)), "y": str(int(sy + sh))})
        ET.SubElement(edge, q(DI_NS, "waypoint"), {"x": str(int(tx + tw / 2)), "y": str(int(ty))})


NAMESPACES = [
    ("bpmn", BPMN_NS),
    ("bpmndi", BPMNDI_NS),
    ("dc", DC_NS),
    ("di", DI_NS),
    ("flowaudit", FLOWAUDIT_NAMESPACE),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for template in templates():
        target = args.output / f"{template.id}.bpmn"
        target.write_text(serialize_element(build(template), NAMESPACES), encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
