"""BVA-Validierung – legacy-treue Übernahme von ``validate_bpmn_bva`` (audit_designer).

Quelle: ``janpow77/audit_designer@eff41a4c`` ``backend/app/modules/flowstat/api/bpmn.py``
(Blob ``e7853d7b``), Funktion ``validate_bpmn_bva``. Prüfungen, Meldungstexte
und Reihenfolge sind unverändert (Charakterisierungstests). Einzige bewusste
Abweichung: Dokumente mit DOCTYPE werden abgewiesen (das Original ließ eine
DTD ohne Entitäten zu); die Meldung beginnt wie jede Parserfehlermeldung mit
„BPMN-XML ist nicht wohlgeformt:“.

Die fachlichen Prüfregeln mit stabilen Regel-IDs stehen in
:mod:`auditcore_bpmn.validation`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from xml.etree import ElementTree as ET

from ..errors import BpmnXmlError
from ..namespaces import BPMN_NS
from ..safe_xml import safe_fromstring


@dataclass
class BvaValidationResult:
    """Ergebnis wie ``BpmnValidationResult`` des Originals."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSON-fähige Darstellung."""
        return asdict(self)


TASK_TYPES = frozenset(
    {
        "task",
        "userTask",
        "serviceTask",
        "manualTask",
        "scriptTask",
        "businessRuleTask",
        "sendTask",
        "receiveTask",
        "subProcess",
    }
)
GATEWAY_TYPES = frozenset({"exclusiveGateway", "parallelGateway", "inclusiveGateway"})


def assert_well_formed_xml(xml_content: str | bytes) -> None:
    """Wirft :class:`BpmnXmlError` mit der Meldung des Originals (dort HTTP 422)."""
    try:
        safe_fromstring(xml_content)
    except (ET.ParseError, ValueError) as exc:
        raise BpmnXmlError(f"BPMN-XML ist nicht wohlgeformt: {exc}") from exc


def _local(element: ET.Element) -> str:
    return str(element.tag).rsplit("}", 1)[-1]


def _index_ids(elements: list[ET.Element], errors: list[str]) -> dict[str, ET.Element]:
    by_id: dict[str, ET.Element] = {}
    for element in elements:
        element_id = element.get("id")
        if not element_id:
            continue
        if element_id in by_id:
            errors.append(f"Element-ID '{element_id}' ist mehrfach vergeben")
        else:
            by_id[element_id] = element
    return by_id


def _check_flow_end(flow_id: str, name: str, ref: str | None, by_id: dict[str, ET.Element], errors: list[str]) -> bool:
    if not ref:
        errors.append(f"Sequenzfluss '{flow_id}' hat keine {name}")
        return False
    if ref not in by_id:
        errors.append(f"Sequenzfluss '{flow_id}' verweist auf unbekannte {name} '{ref}'")
        return False
    return True


def _check_flows(elements: list[ET.Element], by_id: dict[str, ET.Element], errors: list[str]) -> dict[str, int]:
    outgoing: dict[str, int] = {}
    for flow in (e for e in elements if _local(e) == "sequenceFlow"):
        flow_id = flow.get("id", "(ohne ID)")
        source = flow.get("sourceRef")
        if _check_flow_end(flow_id, "sourceRef", source, by_id, errors) and source:
            outgoing[source] = outgoing.get(source, 0) + 1
        _check_flow_end(flow_id, "targetRef", flow.get("targetRef"), by_id, errors)
    return outgoing


def _check_events(elements: list[ET.Element], errors: list[str]) -> None:
    if not any(_local(e) == "startEvent" for e in elements):
        errors.append("Kein Start-Event vorhanden (BVA: Jeder Prozess benötigt mind. 1 Start-Event)")
    if not any(_local(e) == "endEvent" for e in elements):
        errors.append("Kein End-Event vorhanden (BVA: Jeder Prozess benötigt mind. 1 End-Event)")


def _check_gateways(elements: list[ET.Element], outgoing: dict[str, int], errors: list[str]) -> None:
    for gateway in (e for e in elements if _local(e) in GATEWAY_TYPES):
        count = outgoing.get(gateway.get("id", ""), 0)
        if count > 3:
            gateway_id = gateway.get("id", "(ohne ID)")
            errors.append(f"Gateway '{gateway_id}' hat {count} ausgehende Flüsse (BVA Best Practice: max. 3)")


def _check_names(elements: list[ET.Element], warnings: list[str]) -> None:
    for task in (e for e in elements if _local(e) in TASK_TYPES):
        task_id = task.get("id", "(ohne ID)")
        name = task.get("name")
        if name is None:
            warnings.append(f"Aufgabe '{task_id}' hat keinen Namen (BVA: Alle Elemente sollten beschriftet sein)")
        elif not name.strip():
            warnings.append(f"Aufgabe '{task_id}' hat einen leeren Namen")


def validate_bpmn_bva(xml_content: str | bytes) -> BvaValidationResult:
    """Start/Ende vorhanden, IDs eindeutig, Flussreferenzen, max. 3 Gateway-Ausgänge, Namen."""
    try:
        root = safe_fromstring(xml_content)
    except (ET.ParseError, ValueError) as exc:
        return BvaValidationResult(valid=False, errors=[f"BPMN-XML ist nicht wohlgeformt: {exc}"], warnings=[])
    errors: list[str] = []
    warnings: list[str] = []
    prefix = f"{{{BPMN_NS}}}"
    if root.tag != f"{prefix}definitions":
        errors.append("Wurzelelement muss bpmn:definitions im BPMN-2.0-Namespace sein")
    elements = [e for e in root.iter() if isinstance(e.tag, str) and e.tag.startswith(prefix)]
    if not any(_local(e) == "process" for e in elements):
        errors.append("Kein bpmn:process vorhanden")
    by_id = _index_ids(elements, errors)
    outgoing = _check_flows(elements, by_id, errors)
    _check_events(elements, errors)
    _check_gateways(elements, outgoing, errors)
    _check_names(elements, warnings)
    return BvaValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
