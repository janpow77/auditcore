"""Stand des Durchlauftests: Prüfschritte je Flussknoten und nicht durchlaufene Aktivitäten."""

from __future__ import annotations

from typing import Any

from ..model import BpmnDocument, as_document
from .process_table import flow_order


def walkthrough_status(source: str | bytes | BpmnDocument) -> dict[str, Any]:
    """Ergebnisse je Prüfschritt und nicht durchlaufene Aktivitäten."""
    document = as_document(source)
    counts: dict[str, int] = {}
    steps = []
    untested = []
    for element in flow_order(document):
        if not element.extensions.audit_steps:
            if element.is_activity:
                untested.append(element.id)
            continue
        for step in element.extensions.audit_steps:
            result = step.result or "offen"
            counts[result] = counts.get(result, 0) + 1
            steps.append(
                {
                    "element": element.label,
                    "element_id": element.id,
                    "fall": step.case or "",
                    "beleg": step.document or "",
                    "ergebnis": result,
                    "datum": step.date or "",
                    "kontrolle": step.control or "",
                    "stichprobe": step.sample_size or "",
                    "bemerkung": step.remark or "",
                }
            )
    return {"results": dict(sorted(counts.items())), "steps": steps, "untested": untested}
