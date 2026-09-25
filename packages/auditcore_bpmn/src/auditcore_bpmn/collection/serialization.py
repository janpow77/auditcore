"""JSON-(De-)Serialisierung der Sammlung (Schema ``auditcore_bpmn.diagram-collection/1``)."""

from __future__ import annotations

import json
from collections.abc import Mapping

from ..errors import CollectionError
from ..extensions import DiagramInfo, from_dict, to_dict
from ..jsondata import integer, items, mapping, optional_mapping, optional_text, strings, text
from .collection import DiagramCollection
from .model import Approval, DiagramEntry, DiagramExcerpt, Folder, check_id

COLLECTION_SCHEMA = "auditcore_bpmn.diagram-collection/1"


def _compact(values: Mapping[str, object]) -> dict[str, object]:
    return {k: v for k, v in values.items() if v is not None}


def _excerpt_to_dict(excerpt: DiagramExcerpt) -> dict[str, object]:
    return {
        "process_ids": list(excerpt.process_ids),
        "calls": [list(x) for x in excerpt.calls],
        "link_throws": [list(x) for x in excerpt.link_throws],
        "link_catches": [list(x) for x in excerpt.link_catches],
        "activities": excerpt.activities,
        "activities_with_legal_basis": excerpt.activities_with_legal_basis,
        "keys": excerpt.keys,
    }


def _entry_to_dict(entry: DiagramEntry) -> dict[str, object]:
    data: dict[str, object] = {
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


def collection_to_dict(collection: DiagramCollection) -> dict[str, object]:
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


def _pairs(values: object) -> list[tuple[str, str]]:
    pairs = []
    for pair in values if isinstance(values, list | tuple) else ():
        if not isinstance(pair, list | tuple) or len(pair) != 2:
            raise ValueError("Paar aus zwei Werten erwartet.")
        pairs.append((str(pair[0]), str(pair[1])))
    return pairs


def _keys(value: object) -> dict[str, dict[str, list[str]]]:
    return {
        kind: {key: list(strings(ids)) for key, ids in mapping(values, "Schlüssel").items()}
        for kind, values in optional_mapping(value, "Schlüsselindex").items()
    }


def _excerpt(data: Mapping[str, object]) -> DiagramExcerpt:
    return DiagramExcerpt(
        process_ids=list(strings(data.get("process_ids"))),
        calls=_pairs(data.get("calls")),
        link_throws=_pairs(data.get("link_throws")),
        link_catches=_pairs(data.get("link_catches")),
        activities=integer(data.get("activities"), "Aktivitäten", 0),
        activities_with_legal_basis=integer(data.get("activities_with_legal_basis"), "Aktivitäten", 0),
        keys=_keys(data.get("keys")),
    )


def _approval(data: Mapping[str, object]) -> Approval:
    return Approval(
        version=text(data.get("version"), "Version"),
        sha256=text(data.get("sha256"), "SHA-256"),
        cutoff_date=optional_text(data.get("cutoff_date")),
        approved_on=optional_text(data.get("approved_on")),
        approved_by=optional_text(data.get("approved_by")),
    )


def _entry(item: Mapping[str, object]) -> DiagramEntry:
    identifier = check_id(text(item.get("id"), "Diagramm-ID"), "Diagramm")
    info = item.get("info")
    return DiagramEntry(
        id=identifier,
        name=str(item.get("name", identifier)),
        folder_id=optional_text(item.get("folder_id")),
        tags=list(strings(item.get("tags"))),
        position=integer(item.get("position"), "Position", 0),
        info=from_dict(DiagramInfo, mapping(info, "Diagramm-Infos")) if info else None,
        excerpt=_excerpt(optional_mapping(item.get("excerpt"), "Auszug")),
        approvals=[_approval(a) for a in items(item.get("approvals"), "Freigaben")],
    )


def _folder(data: Mapping[str, object]) -> Folder:
    return Folder(
        check_id(text(data.get("id"), "Ordner-ID"), "Ordner"),
        text(data.get("name"), "Ordnername"),
        optional_text(data.get("parent_id")),
        integer(data.get("position"), "Position", 0),
        optional_text(data.get("description")),
    )


def _fill(collection: DiagramCollection, data: Mapping[str, object]) -> None:
    for raw_folder in items(data.get("folders"), "Ordner"):
        folder = _folder(raw_folder)
        collection.folders[folder.id] = folder
    for tag in items(data.get("tags"), "Tags"):
        collection.add_tag(
            text(tag.get("id"), "Tag-ID"), text(tag.get("name"), "Tagname"), optional_text(tag.get("color"))
        )
    for item in items(data.get("diagrams"), "Diagramme"):
        entry = _entry(item)
        collection.diagrams[entry.id] = entry


def collection_from_dict(data: Mapping[str, object]) -> DiagramCollection:
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
