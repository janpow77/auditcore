"""Prozesskennzahlen – legacy-treue Übernahme von ``bpmn_analyzer.py`` (audit_designer).

Quelle: ``janpow77/audit_designer@eff41a4c``
``backend/app/modules/flowstat/services/bpmn_analyzer.py`` (Blob ``0cfaf87a``).
Rechenregeln, Rundung, Reihenfolge der Aufgaben und Attributaliasse sind
unverändert und durch Charakterisierungstests gegen das Original belegt
(``tests/fixtures/legacy_observed.json``). Bewusste Abweichungen stehen in
``docs/behavior-changes.md``: gehärtetes Parsen, ``unique_*`` in Reihenfolge
des ersten Auftretens, Personalkosten über den Port ``personnel_rate`` statt
einer Datenbanksitzung.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from typing import Any
from xml.etree import ElementTree as ET

from ..namespaces import BPMN_NS, BPMNDI_NS, DC_NS, DI_NS, FLOWAUDIT_NAMESPACE
from ..safe_xml import safe_fromstring

#: Stundensatz je Besoldungs-/Entgeltgruppe; ``None``, wenn unbekannt.
PersonnelRateLookup = Callable[[str], float | None]


@dataclass
class TaskProperties:
    """Properties eines einzelnen Tasks (Feldnamen wie im Original)."""

    task_id: str
    task_name: str
    task_type: str
    process_owner: str | None = None
    process_department: str | None = None
    process_type: str | None = None
    resources_personnel: str | None = None
    resources_systems: str | None = None
    resources_documents: str | None = None
    duration_estimated: str | None = None
    duration_unit: str | None = None
    personnel_grade: str | None = None
    personnel_count: int | None = None
    cost_estimate: float | None = None
    effort_person_days: float | None = None
    frequency: int | None = None
    documentation: str | None = None
    legal_basis: str | None = None
    internal_note: str | None = None
    calculated_personnel_cost: float | None = None


@dataclass
class ProcessAnalysis:
    """Aggregierte Prozessanalyse (Feldnamen wie im Original)."""

    diagram_name: str
    total_tasks: int
    total_cost: float
    total_cost_with_personnel: float
    total_duration_minutes: float
    total_person_days: float
    annual_frequency: int
    annual_cost: float
    annual_cost_with_personnel: float
    annual_person_days: float
    unique_owners: list[str]
    unique_departments: list[str]
    unique_systems: list[str]
    tasks: list[dict[str, Any]]
    tasks_with_cost: int
    tasks_with_duration: int
    tasks_with_owner: int
    tasks_with_personnel: int
    avg_task_cost: float
    avg_task_duration_minutes: float
    total_personnel_cost: float


def _unique(values: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _parse_number(value: str | None, kind: Callable[[str], Any]) -> Any:
    """``kind(value)`` oder ``None`` bei leerem oder ungültigem Wert (wie im Original)."""
    try:
        return kind(value) if value else None
    except (ValueError, TypeError):
        return None


#: Faktoren je Einheit, in dieser Reihenfolge multipliziert wie im Original
#: (``value * 60 * 8`` ist nicht immer bitgleich mit ``value * 480``).
_UNITS: tuple[tuple[tuple[str, ...], tuple[int, ...]], ...] = (
    (("minute", "min"), ()),
    (("stunde", "hour", "std"), (60,)),
    (("tag", "day"), (60, 8)),
    (("woche", "week"), (60, 8, 5)),
    (("monat", "month"), (60, 8, 20)),
)


def convert_duration_to_minutes(duration: str | None, unit: str | None) -> float:
    """Dauer in Minuten (Tag = 8 h, Woche = 5 Tage, Monat = 20 Tage; unbekannt = Minuten)."""
    value = _parse_number(duration, float)
    if value is None:
        return 0.0
    lowered = (unit or "Minuten").lower()
    factors = next((f for names, f in _UNITS if any(name in lowered for name in names)), ())
    result: float = value
    for factor in factors:
        result = result * factor
    return result


class BpmnAnalyzer:
    """BPMN-XML-Analyse der FlowStat-Attribute (legacy-treu)."""

    NAMESPACES = {"bpmn": BPMN_NS, "bpmndi": BPMNDI_NS, "dc": DC_NS, "di": DI_NS, "flowaudit": FLOWAUDIT_NAMESPACE}
    #: Reihenfolge der Suche wie im Original (erst alle ``task``, dann ``userTask`` …).
    TASK_TYPES = (
        ("task", "Task"),
        ("userTask", "UserTask"),
        ("serviceTask", "ServiceTask"),
        ("manualTask", "ManualTask"),
        ("scriptTask", "ScriptTask"),
        ("businessRuleTask", "BusinessRuleTask"),
        ("sendTask", "SendTask"),
        ("receiveTask", "ReceiveTask"),
        ("subProcess", "SubProcess"),
    )

    def __init__(self, xml_content: str | bytes, personnel_rate: PersonnelRateLookup | None = None) -> None:
        self.xml_content = xml_content
        self.root = safe_fromstring(xml_content)
        self.personnel_rate = personnel_rate

    def extract_all_tasks(self) -> list[TaskProperties]:
        """Alle Aufgaben, gruppiert nach Typ in der Reihenfolge des Originals."""
        return [
            self._extract_task_properties(element, label)
            for local, label in self.TASK_TYPES
            for element in self.root.findall(f".//bpmn:{local}", self.NAMESPACES)
        ]

    def _extract_task_properties(self, element: ET.Element, task_type: str = "Task") -> TaskProperties:
        task_id = element.get("id", "")
        documentation = element.find("bpmn:documentation", self.NAMESPACES)
        attribute = self._get_attribute
        return TaskProperties(
            task_id=task_id,
            task_name=element.get("name", task_id),
            task_type=task_type,
            documentation=documentation.text if documentation is not None else None,
            process_owner=element.get("processOwner"),
            process_department=element.get("processDepartment"),
            process_type=element.get("processType"),
            resources_personnel=attribute(element, "resourcesPersonnel", "resource"),
            resources_systems=element.get("resourcesSystems"),
            resources_documents=element.get("resourcesDocuments"),
            duration_estimated=attribute(element, "durationEstimated", "duration", "durationMinutes"),
            duration_unit=element.get("durationUnit", "Minuten"),
            personnel_grade=element.get("personnelGrade"),
            legal_basis=self._get_extension_text(element, "rechtsgrundlage"),
            internal_note=self._get_extension_text(element, "interneNotiz", "notiz"),
            cost_estimate=_parse_number(attribute(element, "costEstimate", "cost"), float),
            effort_person_days=_parse_number(element.get("effortPersonDays"), float),
            frequency=_parse_number(attribute(element, "frequency", "frequencyPerYear"), int),
            personnel_count=_parse_number(attribute(element, "personnelCount", "personnel_count", "personnel"), int),
        )

    @staticmethod
    def _get_extension_text(element: ET.Element, *local_names: str) -> str | None:
        """Erster nicht leerer FlowAudit-Eintrag (Text, sonst Attribut ``value``)."""
        extension = element.find(f"{{{BPMN_NS}}}extensionElements")
        if extension is None:
            return None
        for local_name in local_names:
            for child in extension.findall(f"{{{FLOWAUDIT_NAMESPACE}}}{local_name}"):
                value = (child.text or "").strip() or (child.get("value") or "").strip()
                if value:
                    return value
        return None

    @staticmethod
    def _get_attribute(element: ET.Element, *names: str) -> str | None:
        """Unqualifizierte und namensraumqualifizierte Altattribute per Lokalname."""
        for name in names:
            value = element.get(name)
            if value not in (None, ""):
                return value
            qualified = [v for k, v in element.attrib.items() if k.rsplit("}", 1)[-1] == name and v]
            if qualified:
                return qualified[0]
        return None

    def _calculate_personnel_cost(self, task: TaskProperties) -> float | None:
        """Personalkosten = Anzahl × Stundensatz × Stunden (gerundet auf 2 Stellen)."""
        if not task.personnel_grade or not task.personnel_count or self.personnel_rate is None:
            return None
        hourly_cost = self.personnel_rate(task.personnel_grade)
        if hourly_cost is None:
            return None
        minutes = convert_duration_to_minutes(task.duration_estimated, task.duration_unit)
        return round(task.personnel_count * hourly_cost * (minutes / 60), 2) if minutes > 0 else None

    def _convert_duration_to_minutes(self, duration: str | None, unit: str | None) -> float:
        return convert_duration_to_minutes(duration, unit)

    def analyze_process(self, diagram_name: str = "BPMN-Prozess") -> ProcessAnalysis:
        """Vollständige Prozessanalyse wie im Original."""
        tasks = self.extract_all_tasks()
        total_personnel_cost = 0.0
        for task in tasks:
            personnel_cost = self._calculate_personnel_cost(task)
            if personnel_cost:
                task.calculated_personnel_cost = personnel_cost
                total_personnel_cost += personnel_cost
        return _aggregate(diagram_name, tasks, total_personnel_cost)

    def extract_esi_requirements(self) -> dict[str, Any]:
        """Rohe ESI-Kernanforderungen aus Prozess- bzw. Unterprozess-Attributen (legacy)."""
        for local in ("process", "subProcess"):
            for element in self.root.findall(f".//bpmn:{local}", self.NAMESPACES):
                profile, raw = element.get("esiProfile"), element.get("esiCoreRequirements")
                if profile or raw:
                    return self._esi_result(profile, raw)
        return {
            "profile": None,
            "requirements_raw": None,
            "requirements_parsed": {},
            "total_requirements": 0,
            "total_criteria": 0,
        }

    def _esi_result(self, profile: str | None, raw: str | None) -> dict[str, Any]:
        parsed = self._parse_esi_requirements_string(raw) if raw else {}
        return {
            "profile": profile or "ESI",
            "requirements_raw": raw or "",
            "requirements_parsed": parsed,
            "total_requirements": len(parsed),
            "total_criteria": sum(len(c) for c in parsed.values()),
        }

    def _parse_esi_requirements_string(self, requirements_str: str) -> dict[str, list[str]]:
        """``KA1:K1,K2;KA2`` → ``{"KA1": ["K1", "K2"], "KA2": []}``."""
        result: dict[str, list[str]] = {}
        for entry in (requirements_str or "").split(";"):
            entry = entry.strip()
            if not entry:
                continue
            code, separator, criteria = entry.partition(":")
            if separator:
                result[code.strip()] = [c.strip() for c in criteria.strip().split(",") if c.strip()]
            else:
                result[entry] = []
        return result

    def export_to_dict(self) -> dict[str, Any]:
        """Analyse als Dictionary."""
        return asdict(self.analyze_process())


def _totals(tasks: list[TaskProperties]) -> dict[str, float]:
    """Summen in der Reihenfolge und Form des Originals (Gleitkommagleichheit)."""
    return {
        "cost": sum(t.cost_estimate or 0 for t in tasks),
        "duration": sum(convert_duration_to_minutes(t.duration_estimated, t.duration_unit) for t in tasks),
        "person_days": sum(t.effort_person_days or 0 for t in tasks),
        "annual_cost": sum((t.cost_estimate or 0) * (t.frequency or 1) for t in tasks),
        "annual_cost_personnel": sum(
            ((t.cost_estimate or 0) + (t.calculated_personnel_cost or 0)) * (t.frequency or 1) for t in tasks
        ),
        "annual_person_days": sum((t.effort_person_days or 0) * (t.frequency or 1) for t in tasks),
    }


def _counts(tasks: list[TaskProperties]) -> dict[str, int]:
    return {
        "cost": sum(1 for t in tasks if t.cost_estimate is not None),
        "duration": sum(1 for t in tasks if t.duration_estimated is not None),
        "owner": sum(1 for t in tasks if t.process_owner is not None),
        "personnel": sum(1 for t in tasks if t.personnel_grade is not None and t.personnel_count is not None),
    }


def _aggregate(diagram_name: str, tasks: list[TaskProperties], total_personnel_cost: float) -> ProcessAnalysis:
    totals, counts = _totals(tasks), _counts(tasks)
    frequencies = [t.frequency for t in tasks if t.frequency is not None]
    count = len(tasks)
    return ProcessAnalysis(
        diagram_name=diagram_name,
        total_tasks=count,
        total_cost=round(totals["cost"], 2),
        total_cost_with_personnel=round(totals["cost"] + total_personnel_cost, 2),
        total_duration_minutes=round(totals["duration"], 2),
        total_person_days=round(totals["person_days"], 2),
        annual_frequency=max(frequencies) if frequencies else 1,
        annual_cost=round(totals["annual_cost"], 2),
        annual_cost_with_personnel=round(totals["annual_cost_personnel"], 2),
        annual_person_days=round(totals["annual_person_days"], 2),
        unique_owners=_unique(t.process_owner for t in tasks),
        unique_departments=_unique(t.process_department for t in tasks),
        unique_systems=_unique(t.resources_systems for t in tasks),
        tasks=[asdict(t) for t in tasks],
        tasks_with_cost=counts["cost"],
        tasks_with_duration=counts["duration"],
        tasks_with_owner=counts["owner"],
        tasks_with_personnel=counts["personnel"],
        avg_task_cost=round(totals["cost"] / count if count else 0, 2),
        avg_task_duration_minutes=round(totals["duration"] / count if count else 0, 2),
        total_personnel_cost=round(total_personnel_cost, 2),
    )


def analyze_bpmn(
    xml_content: str | bytes, diagram_name: str = "BPMN-Prozess", personnel_rate: PersonnelRateLookup | None = None
) -> dict[str, Any]:
    """Kurzform wie im Original (``db_session`` → ``personnel_rate``)."""
    return asdict(BpmnAnalyzer(xml_content, personnel_rate=personnel_rate).analyze_process(diagram_name))
