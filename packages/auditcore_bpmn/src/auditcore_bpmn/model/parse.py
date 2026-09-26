"""BPMN-XML gehärtet in das Elementmodell lesen."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from ..extensions import DiagramInfo, EsiRequirements, legacy_esi, read_extensions
from ..namespaces import BPMN_NS, is_bpmn, local_name, q
from ..safe_xml import MAX_XML_SIZE, Backend, ParsedXml, parse_xml
from .elements import BpmnDocument, BpmnElement, category

_SKIPPED = frozenset({"extensionElements", "documentation", "incoming", "outgoing", "flowNodeRef"})


def _child_text(element: ET.Element, local: str) -> str | None:
    child = element.find(q(BPMN_NS, local))
    if child is None:
        return None
    return "".join(child.itertext()).strip() or None


def _documentation(element: ET.Element) -> str | None:
    parts = ["".join(c.itertext()).strip() for c in element.findall(q(BPMN_NS, "documentation"))]
    return "\n\n".join(part for part in parts if part) or None


def _event_definitions(element: ET.Element) -> tuple[str, ...]:
    names = [local_name(c.tag) for c in element if is_bpmn(c.tag) and local_name(c.tag).endswith("EventDefinition")]
    names += ["eventDefinitionRef" for _ in element.findall(q(BPMN_NS, "eventDefinitionRef"))]
    return tuple(names)


def _endpoints(element: ET.Element, element_type: str) -> tuple[str | None, str | None]:
    if element_type in ("dataInputAssociation", "dataOutputAssociation"):
        return (
            _child_text(element, "sourceRef") or element.get("sourceRef"),
            _child_text(element, "targetRef") or element.get("targetRef"),
        )
    return element.get("sourceRef"), element.get("targetRef")


def _interrupting(element: ET.Element, element_type: str) -> bool | None:
    raw = element.get("isInterrupting" if element_type == "startEvent" else "cancelActivity")
    return None if raw is None else raw.strip().lower() != "false"


def _condition(element: ET.Element) -> str | None:
    node = element.find(q(BPMN_NS, "conditionExpression"))
    if node is None:
        return None
    return "".join(node.itertext()).strip() or "(leer)"


class _Walker:
    """Durchläuft den Baum und sammelt Elemente, Lane-Zuordnungen und Pools."""

    def __init__(self, parsed: ParsedXml) -> None:
        self.parsed = parsed
        self.elements: dict[str, BpmnElement] = {}
        self.nodes: dict[str, ET.Element] = {}
        self.duplicates: list[str] = []
        self.lanes_of: dict[str, list[str]] = {}
        self.pool_of_process: dict[str, str] = {}

    def run(self) -> None:
        """Liest alle Elemente und ordnet Lanes zu."""
        for participant in self.parsed.root.iter(q(BPMN_NS, "participant")):
            ref, pid = participant.get("processRef"), participant.get("id")
            if ref and pid:
                self.pool_of_process.setdefault(ref, pid)
        self._walk(self.parsed.root, process=None, parent=None)
        for node_id, lane_ids in self.lanes_of.items():
            if node_id in self.elements:
                self.elements[node_id].lane_ids = tuple(lane_ids)

    def _register(self, node: ET.Element, element: BpmnElement) -> None:
        if element.id in self.elements:
            self.duplicates.append(element.id)
            return
        self.elements[element.id] = element
        self.nodes[element.id] = node

    def _walk(self, node: ET.Element, process: str | None, parent: str | None) -> None:
        for child in node:
            if not is_bpmn(child.tag) or local_name(child.tag) in _SKIPPED:
                continue
            element_type = local_name(child.tag)
            if element_type == "lane":
                self._lane(child, process, [])
                continue
            element_id = child.get("id")
            inner_process = element_id if element_type == "process" else process
            if element_id:
                self._register(child, self._element(child, element_type, process, parent))
            next_parent = element_id if element_id and element_type != "laneSet" else parent
            self._walk(child, inner_process, None if element_type == "definitions" else next_parent)

    def _lane(self, node: ET.Element, process: str | None, parents: list[str]) -> None:
        lane_id = node.get("id")
        chain = [*parents, lane_id] if lane_id else parents
        if lane_id:
            self._register(node, self._element(node, "lane", process, parents[-1] if parents else process))
        for ref in node.findall(q(BPMN_NS, "flowNodeRef")):
            target = (ref.text or "").strip()
            if target:
                assigned = self.lanes_of.setdefault(target, [])
                assigned.extend(lane for lane in chain if lane not in assigned)
        for child_set in node.findall(q(BPMN_NS, "childLaneSet")):
            for child in child_set.findall(q(BPMN_NS, "lane")):
                self._lane(child, process, chain)

    def _element(self, node: ET.Element, element_type: str, process: str | None, parent: str | None) -> BpmnElement:
        element_id = node.get("id", "")
        own_process = element_id if element_type == "process" else process
        if element_type == "participant":
            participant: str | None = element_id
        else:
            participant = self.pool_of_process.get(own_process or "")
        source, target = _endpoints(node, element_type)
        link = node.find(q(BPMN_NS, "linkEventDefinition"))
        return BpmnElement(
            id=element_id,
            type=element_type,
            name=node.get("name"),
            category=category(element_type),
            process_id=own_process,
            parent_id=parent,
            participant_id=participant,
            attributes=dict(node.attrib),
            documentation=_documentation(node),
            event_definitions=_event_definitions(node),
            link_name=link.get("name") if link is not None else None,
            attached_to=node.get("attachedToRef"),
            interrupting=_interrupting(node, element_type),
            default=node.get("default"),
            source=source,
            target=target,
            condition=_condition(node),
            called_element=node.get("calledElement"),
            is_compensation=(node.get("isForCompensation") or "").lower() == "true",
            is_event_subprocess=element_type == "subProcess" and (node.get("triggeredByEvent") or "").lower() == "true",
            process_ref=node.get("processRef"),
            extensions=read_extensions(node),
        )


def _diagram_info(elements: dict[str, BpmnElement]) -> tuple[DiagramInfo | None, str | None]:
    candidates = [e for e in elements.values() if e.type == "collaboration"]
    candidates += [e for e in elements.values() if e.type == "process"]
    for element in candidates:
        if element.extensions.diagram_info is not None:
            return element.extensions.diagram_info, element.id
    return None, None


def _esi(elements: dict[str, BpmnElement], root: ET.Element) -> EsiRequirements | None:
    for element_type in ("process", "subProcess"):
        for element in elements.values():
            if element.type == element_type and element.extensions.esi is not None:
                return element.extensions.esi
    for element_type in ("process", "subProcess"):
        for node in root.iter(q(BPMN_NS, element_type)):
            legacy = legacy_esi(node)
            if legacy is not None:
                return legacy
    return None


def document_from_xml(parsed: ParsedXml) -> BpmnDocument:
    """Baut das Modell aus einem bereits geparsten Dokument."""
    walker = _Walker(parsed)
    walker.run()
    info, owner = _diagram_info(walker.elements)
    return BpmnDocument(
        parsed=parsed,
        elements=walker.elements,
        duplicate_ids=walker.duplicates,
        diagram_info=info,
        diagram_info_owner=owner,
        esi=_esi(walker.elements, parsed.root),
        definitions_id=parsed.root.get("id"),
        target_namespace=parsed.root.get("targetNamespace"),
        is_bpmn=parsed.root.tag == q(BPMN_NS, "definitions"),
        xml_nodes=walker.nodes,
    )


def parse_bpmn(xml: str | bytes, *, max_size: int = MAX_XML_SIZE, backend: Backend = "auto") -> BpmnDocument:
    """Liest BPMN-XML gehärtet in das Elementmodell.

    :raises auditcore_bpmn.errors.BpmnXmlError: nicht wohlgeformt, unsicher oder zu groß.
    """
    return document_from_xml(parse_xml(xml, max_size=max_size, backend=backend))


def as_document(source: str | bytes | BpmnDocument) -> BpmnDocument:
    """XML lesen oder ein vorhandenes Modell durchreichen."""
    return source if isinstance(source, BpmnDocument) else parse_bpmn(source)
