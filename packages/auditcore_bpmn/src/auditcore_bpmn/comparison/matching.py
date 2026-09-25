"""Zuordnung der Elemente zweier Stände und vergleichbare Merkmale."""

from __future__ import annotations

import re
from typing import Any

from ..model import BpmnDocument, BpmnElement

COMPARED_CATEGORIES = frozenset({"activity", "event", "gateway", "data", "container"})


def normal(name: str | None) -> str:
    """Name für den Vergleich: Leerraum vereinheitlicht, Groß-/Kleinschreibung ignoriert."""
    return re.sub(r"\s+", " ", (name or "").strip()).casefold()


def comparable(document: BpmnDocument) -> list[BpmnElement]:
    """Elemente, die verglichen werden (Knoten, Daten, Pools, Lanes)."""
    return [e for e in document if e.category in COMPARED_CATEGORIES and e.type != "laneSet"]


def _by_name(elements: list[BpmnElement], excluded: set[str]) -> dict[tuple[str, str], list[str]]:
    groups: dict[tuple[str, str], list[str]] = {}
    for element in elements:
        if element.id not in excluded and normal(element.name):
            groups.setdefault((element.type, normal(element.name)), []).append(element.id)
    return groups


def match_elements(old: BpmnDocument, new: BpmnDocument) -> dict[str, str]:
    """Element-ID alt → neu: zuerst gleiche ID, dann eindeutig gleicher Typ und Name."""
    old_elements, new_elements = comparable(old), comparable(new)
    new_by_id = {e.id: e for e in new_elements}
    mapping = {e.id: e.id for e in old_elements if e.id in new_by_id and new_by_id[e.id].category == e.category}
    old_groups = _by_name(old_elements, set(mapping))
    new_groups = _by_name(new_elements, set(mapping.values()))
    for key, ids in old_groups.items():
        partners = new_groups.get(key, [])
        if len(ids) == 1 and len(partners) == 1:
            mapping[ids[0]] = partners[0]
    return mapping


def body(document: BpmnDocument, element: BpmnElement) -> str | None:
    """Stelle: Rolle (mit Anzeigename) oder Name der Lane bzw. des Pools."""
    where, actor = document.actor_of(element)
    if actor is not None and actor.role:
        return actor.role + (f" ({actor.display_name})" if actor.display_name else "")
    return where.label if where is not None else None


def neighbours(document: BpmnDocument, element: BpmnElement, direction: str) -> list[str]:
    """Namen der Vorgänger (``in``) bzw. Nachfolger (``out``)."""
    flows = document.outgoing(element.id) if direction == "out" else document.incoming(element.id)
    result = []
    for flow in flows:
        other = document.elements.get((flow.target if direction == "out" else flow.source) or "")
        if other is not None:
            result.append(normal(other.name) or other.type)
    return sorted(result)


def features(document: BpmnDocument, element: BpmnElement) -> dict[str, Any]:
    """Vergleichsmerkmale eines Elements."""
    return {
        "typ": element.type,
        "name": (element.name or "").strip(),
        "stelle": body(document, element),
        "nachfolger": neighbours(document, element, "out"),
        "vorgaenger": neighbours(document, element, "in"),
        "dokumentation": element.documentation or "",
        "erweiterungen": element.extensions.to_dict(),
    }
