"""Auszug eines Diagramms für die Sammlung (Prozesse, Verweise, Kennzahlen, Schlüsselindex)."""

from __future__ import annotations

from ..extensions import DiagramInfo, Extensions
from ..model import ACTIVITIES, BpmnDocument
from .model import KEY_KINDS, DiagramExcerpt

_REFERENCE_KINDS = ("prueffeld", "feststellung_ref", "register")


class _KeyIndex:
    def __init__(self) -> None:
        self.keys: dict[str, dict[str, list[str]]] = {kind: {} for kind in KEY_KINDS}

    def add(self, kind: str, value: str | None, element_id: str) -> None:
        """Nimmt einen Schlüsselwert eines Elements auf."""
        if value:
            ids = self.keys[kind].setdefault(str(value).strip(), [])
            if element_id not in ids:
                ids.append(element_id)

    def add_extensions(self, element_id: str, ext: Extensions) -> None:
        """Schlüssel aus den Erweiterungen eines Elements."""
        for reference in ext.audit_references:
            self.add("ka", reference.key_requirement, element_id)
            self.add("bk", reference.assessment_criterion, element_id)
        for finding in ext.findings:
            self.add("ka", finding.key_requirement, element_id)
            self.add("bk", finding.assessment_criterion, element_id)
            self.add("feststellung_ref", finding.reference, element_id)
        for link in ext.cross_references:
            if link.kind in _REFERENCE_KINDS:
                self.add(link.kind, link.key, element_id)
        if ext.actor is not None:
            self.add("rolle", ext.actor.role, element_id)
        for marker in ext.markers:
            self.add("kennzeichen", marker.type, element_id)

    def add_info(self, owner: str, info: DiagramInfo) -> None:
        """Schlüssel aus den Diagramm-Infos."""
        for reference in info.audit_references:
            self.add("ka", reference.key_requirement, owner)
            self.add("bk", reference.assessment_criterion, owner)
        for link in info.cross_references:
            if link.kind in _REFERENCE_KINDS:
                self.add(link.kind, link.key, owner)

    def result(self) -> dict[str, dict[str, list[str]]]:
        """Index ohne leere Arten."""
        return {kind: values for kind, values in self.keys.items() if values}


def excerpt_from_document(document: BpmnDocument) -> DiagramExcerpt:
    """Auszug für die Sammlung aus einem gelesenen Diagramm."""
    index = _KeyIndex()
    for element in document:
        index.add_extensions(element.id, element.extensions)
    if document.diagram_info is not None:
        index.add_info(document.diagram_info_owner or "diagramm", document.diagram_info)
    activities = [e for e in document.flow_nodes if e.type in ACTIVITIES]
    return DiagramExcerpt(
        process_ids=[p.id for p in document.processes],
        calls=[(e.id, e.called_element) for e in document.by_type("callActivity") if e.called_element],
        link_throws=[(e.id, e.link_name) for e in document.by_type("intermediateThrowEvent") if e.link_name],
        link_catches=[(e.id, e.link_name) for e in document.by_type("intermediateCatchEvent") if e.link_name],
        activities=len(activities),
        activities_with_legal_basis=sum(1 for e in activities if e.extensions.legal_bases),
        keys=index.result(),
    )
