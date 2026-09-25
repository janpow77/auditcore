"""Regeln der Sammlung (``BPMN-K…``)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from dataclasses import replace

from ..errors import CollectionError
from ..validation import ValidationIssue, issue
from .collection import DiagramCollection
from .queries import process_owners, references

Issues = Iterator[ValidationIssue]


def _folders(collection: DiagramCollection) -> Issues:
    for folder in collection.folders.values():
        try:
            collection.ancestors(folder.id)
        except CollectionError:
            yield issue("BPMN-K004", None, ordner=folder.id)
    for entry in collection.diagrams.values():
        if entry.folder_id is not None and entry.folder_id not in collection.folders:
            yield issue("BPMN-K004", None, ordner=entry.folder_id)


def _tags_and_targets(collection: DiagramCollection) -> Issues:
    for entry in collection.diagrams.values():
        for tag in entry.tags:
            if tag not in collection.tags:
                yield issue("BPMN-K005", None, diagramm=entry.id, tag=tag)
        info = entry.info
        if (
            info
            and info.variant == "ist"
            and info.reference_diagram
            and info.reference_diagram not in collection.diagrams
        ):
            yield issue("BPMN-K007", None, diagramm=entry.id, bezug=info.reference_diagram)


def _duplicates(collection: DiagramCollection) -> Issues:
    counts = Counter([*collection.folders, *collection.tags, *collection.diagrams])
    for identifier, count in counts.items():
        if count > 1:
            yield issue("BPMN-K006", None, id=identifier)
    for process_id, diagram_ids in sorted(process_owners(collection).items()):
        if len(diagram_ids) > 1:
            yield issue("BPMN-K003", None, prozess=process_id, diagramme=", ".join(diagram_ids))


def _unresolved(collection: DiagramCollection) -> Issues:
    for link in references(collection):
        if link.resolved:
            continue
        name = collection.diagrams[link.source_diagram].name
        if link.kind == "aufruf":
            found = issue("BPMN-K001", link.source_element, name=link.source_element, diagramm=name, ziel=link.key)
        else:
            found = issue("BPMN-K002", link.source_element, link=link.key, diagramm=name)
        yield replace(found, diagram_id=link.source_diagram)


def validate_collection(collection: DiagramCollection) -> list[ValidationIssue]:
    """Ordner, Tags, IDs, mehrdeutige Prozesse und nicht auflösbare Verweise."""
    return [*_folders(collection), *_tags_and_targets(collection), *_duplicates(collection), *_unresolved(collection)]
