"""JSON-(De-)Serialisierung der Sammlung (Schema ``auditcore_bpmn.diagram-collection/1``)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ..errors import CollectionError
from ..extensions import DiagramInfo, from_dict, to_dict
from .collection import DiagramCollection
from .model import Approval, DiagramEntry, DiagramExcerpt, Folder, check_id

COLLECTION_SCHEMA = "auditcore_bpmn.diagram-collection/1"


def _compact(values: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


def _excerpt_to_dict(excerpt: DiagramExcerpt) -> dict[str, Any]:
    return {
        "process_ids": list(excerpt.process_ids),
        "calls": [list(x) for x in excerpt.calls],
        "link_throws": [list(x) for x in excerpt.link_throws],
        "link_catches": [list(x) for x in excerpt.link_catches],
        "activities": excerpt.activities,
        "activities_with_legal_basis": excerpt.activities_with_legal_basis,
        "keys": excerpt.keys,
    }


def _entry_to_dict(entry: DiagramEntry) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": entry.id,
        "name": entry.name,
        "folder_id": entry.folder_id,
        "tags": list(entry.tags),
        "position": entry.position,
        "excerpt": _excerpt_to_dict(entry.excerpt),
        "approvals": [_compact(vars(a)) for a in entry.approvals],
    }
    if entry.info is not None:
        data["info"] = to_dict(entry.info)
    return data


def collection_to_dict(collection: DiagramCollection) -> dict[str, Any]:
    """JSON-Daten der Sammlung."""
    return {
        "schema": COLLECTION_SCHEMA,
        "id": collection.id,
        "name": collection.name,
        "folders": [_compact(vars(f)) for f in sorted(collection.folders.values(), key=lambda f: f.id)],
        "tags": [_compact(vars(t)) for t in sorted(collection.tags.values(), key=lambda t: t.id)],
        "diagrams": [_entry_to_dict(d) for d in sorted(collection.diagrams.values(), key=lambda d: d.id)],
    }


def collection_to_json(collection: DiagramCollection) -> str:
    """JSON-Text der Sammlung."""
    return json.dumps(collection_to_dict(collection), ensure_ascii=False, indent=2) + "\n"


def _pairs(values: Any) -> list[tuple[str, str]]:
    return [(str(a), str(b)) for a, b in values or ()]


def _excerpt(data: Mapping[str, Any]) -> DiagramExcerpt:
    return DiagramExcerpt(
        process_ids=[str(x) for x in data.get("process_ids", ())],
        calls=_pairs(data.get("calls")),
        link_throws=_pairs(data.get("link_throws")),
        link_catches=_pairs(data.get("link_catches")),
        activities=int(data.get("activities", 0)),
        activities_with_legal_basis=int(data.get("activities_with_legal_basis", 0)),
        keys={kind: {k: list(v) for k, v in values.items()} for kind, values in (data.get("keys") or {}).items()},
    )


def _entry(item: Mapping[str, Any]) -> DiagramEntry:
    return DiagramEntry(
        id=check_id(item["id"], "Diagramm"),
        name=str(item.get("name", item["id"])),
        folder_id=item.get("folder_id"),
        tags=[str(t) for t in item.get("tags", ())],
        position=int(item.get("position", 0)),
        info=from_dict(DiagramInfo, item["info"]) if item.get("info") else None,
        excerpt=_excerpt(item.get("excerpt") or {}),
        approvals=[Approval(**a) for a in item.get("approvals", ())],
    )


def _fill(collection: DiagramCollection, data: Mapping[str, Any]) -> None:
    for folder in data.get("folders", ()):
        collection.folders[check_id(folder["id"], "Ordner")] = Folder(
            folder["id"],
            folder["name"],
            folder.get("parent_id"),
            int(folder.get("position", 0)),
            folder.get("description"),
        )
    for tag in data.get("tags", ()):
        collection.add_tag(tag["id"], tag["name"], tag.get("color"))
    for item in data.get("diagrams", ()):
        entry = _entry(item)
        collection.diagrams[entry.id] = entry


def collection_from_dict(data: Mapping[str, Any]) -> DiagramCollection:
    """Sammlung aus JSON-Daten (Schema, IDs und Ordnerzyklen geprüft)."""
    if data.get("schema") != COLLECTION_SCHEMA:
        raise CollectionError(f"Sammlungsschema {data.get('schema')!r} wird nicht unterstützt.")
    collection = DiagramCollection(str(data.get("id", "sammlung")), str(data.get("name", "Diagrammsammlung")))
    try:
        _fill(collection, data)
    except CollectionError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise CollectionError(f"Sammlung ist unvollständig oder fehlerhaft: {error!r}") from error
    for folder_id in collection.folders:
        collection.ancestors(folder_id)
    return collection


def collection_from_json(text: str) -> DiagramCollection:
    """Sammlung aus JSON-Text."""
    return collection_from_dict(json.loads(text))
