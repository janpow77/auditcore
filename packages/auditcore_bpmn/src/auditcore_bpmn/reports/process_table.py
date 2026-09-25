"""Tabellarische Prozessbeschreibung.

Spalten: Schritt, Akteur, Rechtsgrundlage, Kontrolle, Nachweis, IT-System, Frist, KA/BK.
"""

from __future__ import annotations

from ..extensions import Extensions
from ..model import BpmnDocument, BpmnElement, as_document
from ..vocabulary import ROLES, label

Row = dict[str, str | int]

PROCESS_TABLE_COLUMNS = {
    "nr": "Nr.",
    "schritt": "Schritt",
    "akteur": "Akteur",
    "rechtsgrundlage": "Rechtsgrundlage",
    "kontrolle": "Kontrolle",
    "nachweis": "Nachweis",
    "it_system": "IT-System",
    "frist": "Frist",
    "ka_bk": "KA/BK",
}


def flow_order(document: BpmnDocument) -> list[BpmnElement]:
    """Flussknoten in Ablaufreihenfolge (Breitensuche ab Startereignissen), übrige danach."""
    queue = [n.id for n in document.flow_nodes if n.type == "startEvent" and not document.incoming(n.id)]
    seen: dict[str, BpmnElement] = {}
    while queue:
        current = document.elements.get(queue.pop(0))
        if current is None or current.id in seen or not current.is_flow_node:
            continue
        seen[current.id] = current
        queue.extend(flow.target for flow in document.outgoing(current.id) if flow.target)
    return list(seen.values()) + [n for n in document.flow_nodes if n.id not in seen]


def actor_label(document: BpmnDocument, element: BpmnElement) -> str:
    """Akteur eines Elements (Rolle und Anzeigename oder Lane)."""
    where, actor = document.actor_of(element)
    if actor is not None and actor.role:
        role = ROLES.get(actor.role)
        text = label(role.labels) if role else actor.role
        return f"{text} ({actor.display_name})" if actor.display_name else text
    return where.label if where is not None else ""


def data_objects(document: BpmnDocument, element: BpmnElement) -> list[BpmnElement]:
    """Über Datenassoziationen verbundene Datenobjekte und -speicher einer Aktivität."""
    result = []
    for association in document.by_type("dataOutputAssociation", "dataInputAssociation"):
        if association.parent_id == element.id:
            ref = association.target if association.type == "dataOutputAssociation" else association.source
            if ref in document.elements:
                result.append(document.elements[ref or ""])
    return result


def _evidence(ext: Extensions, data: list[BpmnElement]) -> str:
    items = [c.evidence for c in ext.controls if c.evidence]
    for item in data:
        places = [n.storage_location for n in item.extensions.evidence if n.storage_location]
        items.append(item.label + (f" ({', '.join(places)})" if places else ""))
    return "; ".join(i for i in items if i)


def _systems(ext: Extensions, data: list[BpmnElement]) -> str:
    systems = {n.it_system for d in data for n in d.extensions.evidence if n.it_system}
    systems |= {m.text for m in ext.markers if m.type == "system" and m.text}
    return "; ".join(sorted(systems))


def _controls(ext: Extensions) -> str:
    return "; ".join(
        (c.label or c.id or "Kontrolle") + (" (Schlüsselkontrolle)" if c.key_control else "") for c in ext.controls
    )


def _row(document: BpmnDocument, element: BpmnElement, number: int) -> Row:
    ext, data = element.extensions, data_objects(document, element)
    return {
        "nr": number,
        "schritt": element.label,
        "typ": element.type,
        "akteur": actor_label(document, element),
        "rechtsgrundlage": "; ".join(r.display for r in ext.legal_bases),
        "kontrolle": _controls(ext),
        "nachweis": _evidence(ext, data),
        "it_system": _systems(ext, data),
        "frist": "; ".join(d.display for d in ext.deadlines),
        "ka_bk": "; ".join(r.display for r in ext.audit_references),
        "element_id": element.id,
    }


def process_table(source: str | bytes | BpmnDocument, *, activities_only: bool = True) -> list[Row]:
    """Prozessbeschreibung in Ablaufreihenfolge."""
    document = as_document(source)
    nodes = [n for n in flow_order(document) if n.is_activity or not activities_only]
    return [_row(document, node, number) for number, node in enumerate(nodes, start=1)]
