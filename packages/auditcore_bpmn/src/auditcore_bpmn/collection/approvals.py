"""Freigaben: SHA-256 des freigegebenen XML, freigegebene Stände sind unveränderlich."""

from __future__ import annotations

from dataclasses import replace

from ..errors import CollectionError
from ..validation import ValidationIssue, issue
from .collection import DiagramCollection
from .model import Approval, sha256_xml


def approve(
    collection: DiagramCollection,
    diagram_id: str,
    xml: str | bytes,
    version: str,
    *,
    cutoff_date: str | None = None,
    approved_on: str | None = None,
    approved_by: str | None = None,
) -> Approval:
    """Hält den Hash eines Stands fest; dieselbe Version mit anderem Inhalt wird abgewiesen."""
    entry = collection.entry(diagram_id)
    digest = sha256_xml(xml)
    for existing in entry.approvals:
        if existing.version == version:
            if existing.sha256 != digest:
                raise CollectionError(
                    f"Version {version} von „{diagram_id}“ ist bereits freigegeben; "
                    "Änderungen erfordern eine neue Version."
                )
            return existing
    approval = Approval(version, digest, cutoff_date, approved_on, approved_by)
    entry.approvals.append(approval)
    return approval


def check_approval(
    collection: DiagramCollection, diagram_id: str, xml: str | bytes, version: str | None = None
) -> ValidationIssue | None:
    """``None``, wenn das XML dem freigegebenen Stand entspricht, sonst ``BPMN-K008``."""
    entry = collection.entry(diagram_id)
    candidates = [a for a in entry.approvals if version is None or a.version == version]
    if not candidates:
        raise CollectionError(f"Für „{diagram_id}“ gibt es keinen freigegebenen Stand {version or ''}".strip() + ".")
    approval = candidates[-1]
    if approval.sha256 == sha256_xml(xml):
        return None
    return replace(issue("BPMN-K008", None, version=approval.version, diagramm=entry.name), diagram_id=diagram_id)
