"""Soll/Ist-Abgleich: je Soll-Element binär „erfüllt“ oder „nicht erfüllt“ mit Begründung."""

from __future__ import annotations

from dataclasses import dataclass

from ..model import BpmnDocument, BpmnElement, as_document
from .matching import body, match_elements, neighbours


@dataclass(frozen=True)
class TargetActualResult:
    """Ergebnis je Soll-Element: erfüllt oder nicht, mit Gründen."""

    target_id: str
    name: str
    met: bool
    actual_id: str | None = None
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """JSON-fähige Darstellung."""
        return {
            "target_id": self.target_id,
            "name": self.name,
            "met": self.met,
            "actual_id": self.actual_id,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class TargetActualComparison:
    """Ergebnis des Soll/Ist-Abgleichs."""

    results: tuple[TargetActualResult, ...]
    additional_in_actual: tuple[str, ...] = ()

    @property
    def met(self) -> int:
        """Anzahl erfüllter Soll-Elemente."""
        return sum(1 for r in self.results if r.met)

    @property
    def not_met(self) -> int:
        """Anzahl nicht erfüllter Soll-Elemente."""
        return len(self.results) - self.met

    def to_dict(self) -> dict[str, object]:
        """JSON-fähige Darstellung."""
        return {
            "met": self.met,
            "not_met": self.not_met,
            "results": [r.to_dict() for r in self.results],
            "additional_in_actual": list(self.additional_in_actual),
        }


def _missing_controls(target: BpmnElement, actual: BpmnElement) -> list[str]:
    present = actual.extensions.controls
    return [
        c.label or c.id or "Kontrolle"
        for c in target.extensions.controls
        if not any((x.id and x.id == c.id) or (x.label and x.label == c.label) for x in present)
    ]


def _reasons(target_doc: BpmnDocument, target: BpmnElement, actual_doc: BpmnDocument, actual: BpmnElement) -> list[str]:
    reasons = []
    if actual.type != target.type:
        reasons.append(f"Elementtyp abweichend: Soll {target.type}, Ist {actual.type}.")
    wanted, found = body(target_doc, target), body(actual_doc, actual)
    if wanted and wanted != found:
        reasons.append(f"Andere Stelle: Soll „{wanted}“, Ist „{found or '–'}“.")
    missing = _missing_controls(target, actual)
    if missing:
        reasons.append("Kontrolle fehlt im Ist: " + ", ".join(missing) + ".")
    lost = set(neighbours(target_doc, target, "out")) - set(neighbours(actual_doc, actual, "out"))
    if lost:
        reasons.append("Nachfolger fehlen im Ist: " + ", ".join(sorted(lost)) + ".")
    if any(step.result == "nicht_erfuellt" for step in actual.extensions.audit_steps):
        reasons.append("Prüfschritt im Ist nicht erfüllt.")
    return reasons


def compare_target_actual(
    target: str | bytes | BpmnDocument, actual: str | bytes | BpmnDocument
) -> TargetActualComparison:
    """Soll (Beschreibung des Verwaltungs- und Kontrollsystems) gegen Ist (Durchlauftest).

    Je Flussknoten des Soll: vorhanden, gleicher Typ, gleiche Stelle, Kontrollen
    und Nachfolger vorhanden, keine nicht erfüllten Prüfschritte. Arbeitshilfe;
    die Würdigung bleibt beim Prüfer.
    """
    target_doc, actual_doc = as_document(target), as_document(actual)
    mapping = match_elements(target_doc, actual_doc)
    results = []
    for element in target_doc.flow_nodes:
        partner_id = mapping.get(element.id)
        if partner_id is None:
            results.append(TargetActualResult(element.id, element.label, False, None, ("Im Ist nicht vorhanden.",)))
            continue
        reasons = _reasons(target_doc, element, actual_doc, actual_doc.elements[partner_id])
        results.append(TargetActualResult(element.id, element.label, not reasons, partner_id, tuple(reasons)))
    matched = set(mapping.values())
    return TargetActualComparison(tuple(results), tuple(e.id for e in actual_doc.flow_nodes if e.id not in matched))
