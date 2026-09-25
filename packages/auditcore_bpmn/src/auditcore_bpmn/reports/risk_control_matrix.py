"""Risiko-Kontroll-Matrix (RCM): eine Zeile je Risiko und zugeordneter Kontrolle."""

from __future__ import annotations

from typing import Any

from ..extensions import Control, Risk
from ..model import BpmnDocument, BpmnElement, as_document

Row = dict[str, Any]
_CONTROL_FIELDS = (
    "kontrolle_id",
    "kontrolle",
    "schluesselkontrolle",
    "art",
    "durchfuehrung",
    "haeufigkeit",
    "nachweis",
    "verantwortlich",
    "test",
)


def _risk_row(place: str, risk: Risk) -> Row:
    return {
        "risiko_id": risk.id or "",
        "risiko": risk.label or "",
        "kategorie": risk.category or "",
        "inhaerent": risk.inherent or "",
        "kontrollrisiko": risk.control_risk or "",
        "restrisiko": risk.residual or "",
        "ort": place,
    }


def _control_row(control_id: str, found: tuple[BpmnElement, Control] | None, tests: list[str]) -> Row:
    if found is None:
        return {**dict.fromkeys(_CONTROL_FIELDS, ""), "kontrolle_id": control_id, "kontrolle": "(unbekannt)"}
    element, control = found
    return {
        "kontrolle_id": control_id,
        "kontrolle": control.label or "",
        "schluesselkontrolle": "ja" if control.key_control else "nein",
        "art": control.control_type or "",
        "durchfuehrung": control.execution or "",
        "haeufigkeit": control.frequency or "",
        "nachweis": control.evidence or "",
        "verantwortlich": control.responsible or "",
        "test": ", ".join(tests),
        "ort": element.label,
    }


def _risks(document: BpmnDocument) -> list[tuple[str, Risk]]:
    risks = [(element.label, risk) for element in document for risk in element.extensions.risks]
    if document.diagram_info is not None:
        risks += [("Diagramm", risk) for risk in document.diagram_info.risks]
    return risks


def risk_control_matrix(source: str | bytes | BpmnDocument) -> list[Row]:
    """Risiken mit Bewertung, zugeordnete Kontrollen und Testergebnisse der Prüfschritte."""
    document = as_document(source)
    controls = {c.id: (e, c) for e in document for c in e.extensions.controls if c.id}
    tests: dict[str, list[str]] = {}
    for element in document:
        for step in element.extensions.audit_steps:
            if step.control:
                tests.setdefault(step.control, []).append(step.result or "offen")
    rows = []
    for place, risk in _risks(document):
        base = _risk_row(place, risk)
        if not risk.controls:
            rows.append({**base, **dict.fromkeys(_CONTROL_FIELDS, "")})
        rows += [{**base, **_control_row(cid, controls.get(cid), tests.get(cid, []))} for cid in risk.controls]
    return rows
