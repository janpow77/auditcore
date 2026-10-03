"""Portabler Checklisten-Paketaustausch (.checklist.json) kompatibel zu audit_designer."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from .errors import (
    JsonObject,
    JsonValue,
    PackageFormatError,
    to_int,
    to_json_object,
    to_json_value,
)
from .models import (
    CategoryDefinition,
    CategoryItemDefinition,
    ProjectMetadata,
)
from .tree import ChecklistTree

PACKAGE_FORMAT = "audit-designer-checklist-package"
FORMAT_VERSION = 1


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def compute_canonical_tree(tree_data: Mapping[str, object]) -> JsonObject:
    """Extrahiert den Strukturkern eines Baums ohne volatile Metadaten."""
    raw_nodes = tree_data.get("nodes")
    nodes: JsonObject = {}
    if isinstance(raw_nodes, Mapping):
        for nid, raw_node in raw_nodes.items():
            if isinstance(raw_node, Mapping):
                raw_children = raw_node.get("children", ())
                children: list[JsonValue] = (
                    [to_json_value(c) for c in raw_children]
                    if isinstance(raw_children, (list, tuple))
                    else []
                )
                nodes[str(nid)] = {
                    "node_type": to_json_value(raw_node.get("node_type")),
                    "parent_id": to_json_value(raw_node.get("parent_id")),
                    "branch": to_json_value(raw_node.get("branch")),
                    "sort_order": to_int(raw_node.get("sort_order"), 0),
                    "content": to_json_value(raw_node.get("content")),
                    "children": children,
                }
    return {
        "root_id": to_json_value(tree_data.get("root_id")),
        "nodes": nodes,
    }


def compute_package_checksum(
    project_meta: Mapping[str, object],
    categories: Mapping[str, object],
    versions: Sequence[Mapping[str, object]],
) -> str:
    """Berechnet die deterministische sha256-Prüfsumme des Strukturinhalts."""
    versions_list: list[JsonObject] = []
    for v in versions:
        v_tree = v.get("tree_data")
        tree_map: Mapping[str, object] = v_tree if isinstance(v_tree, Mapping) else {}
        versions_list.append(
            {
                "version_number": to_json_value(v.get("version_number")),
                "is_frozen": to_json_value(v.get("is_frozen")),
                "notes": to_json_value(v.get("notes")),
                "tree": compute_canonical_tree(tree_map),
            }
        )
    canonical = {
        "project": {
            k: project_meta.get(k)
            for k in (
                "name",
                "description",
                "tags",
                "aktenzeichen",
                "geschaeftsjahr",
                "module",
            )
        },
        "categories": dict(categories),
        "versions": versions_list,
    }
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def _strip_discussions_from_dict(tree_dict: JsonObject) -> JsonObject:
    cloned = copy.deepcopy(tree_dict)
    nodes = cloned.get("nodes")
    if isinstance(nodes, dict):
        for n in nodes.values():
            if isinstance(n, dict):
                internal = n.get("internal")
                if isinstance(internal, dict):
                    internal["team_notes"] = []
    return cloned


def _serialize_export_categories(
    categories: Mapping[str, CategoryDefinition] | None,
) -> JsonObject:
    result: JsonObject = {}
    if not categories:
        return result
    for cid, cat in categories.items():
        result[str(cid)] = {
            "name": cat.name,
            "description": cat.description,
            "icon_name": cat.icon_name,
            "color": cat.color,
            "items": [{"value": it.value, "sort_order": it.sort_order} for it in cat.items],
        }
    return result


def _build_project_meta_dict(project: ProjectMetadata, current_version: str) -> JsonObject:
    return {
        "name": project.name,
        "description": project.description,
        "tags": [to_json_value(t) for t in project.tags],
        "aktenzeichen": project.aktenzeichen,
        "geschaeftsjahr": project.geschaeftsjahr,
        "module": project.module,
        "current_version": current_version,
    }


def export_package(
    project: ProjectMetadata,
    tree: ChecklistTree,
    categories: Mapping[str, CategoryDefinition] | None = None,
    *,
    version_number: str = "1.0",
    is_frozen: bool = False,
    notes: str = "",
    include_discussions: bool = True,
    include_history: bool = False,
) -> JsonObject:
    """Erzeugt ein portables Checklisten-Paket (.checklist.json)."""
    raw_tree = tree.to_dict()
    if not include_discussions:
        raw_tree = _strip_discussions_from_dict(raw_tree)

    serialized_categories = _serialize_export_categories(categories)
    version_entry: JsonObject = {
        "version_number": version_number,
        "is_frozen": is_frozen,
        "notes": notes,
        "created_at": _iso_now(),
        "tree_data": raw_tree,
    }
    if include_history:
        version_entry["history"] = []

    proj_meta = _build_project_meta_dict(project, version_number)
    checksum = compute_package_checksum(proj_meta, serialized_categories, [version_entry])

    return {
        "format": PACKAGE_FORMAT,
        "format_version": FORMAT_VERSION,
        "exported_at": _iso_now(),
        "source": {"app": "auditcore_checklists", "module": project.module},
        "checksum": checksum,
        "options": {
            "history": include_history,
            "discussions": include_discussions,
        },
        "project": proj_meta,
        "categories": serialized_categories,
        "qchess_answer_sets": {},
        "versions": [version_entry],
    }


def normalize_package_payload(payload: object, fallback_name: str | None = None) -> JsonObject:
    """Führt native Pakete, Altsicherungen und Rohbäume in das Paketschema über."""
    if not isinstance(payload, Mapping):
        raise PackageFormatError("Eingabe enthält kein gültiges JSON-Objekt.")

    # 1. Natives Paket
    if payload.get("format") == PACKAGE_FORMAT or (
        isinstance(payload.get("versions"), Sequence) and "project" in payload
    ):
        return _normalize_native(payload, fallback_name)

    # 2. Altsicherung (full_backup)
    if payload.get("export_type") == "full_backup":
        return _normalize_legacy_backup(payload, fallback_name)

    # 3. Roher Baum ({root_id, nodes})
    if "root_id" in payload and "nodes" in payload:
        return _normalize_raw_tree(payload, fallback_name)

    raise PackageFormatError("Unbekanntes Checklisten-Format; weder Paket, Backup noch Baum.")


def _normalize_native(payload: Mapping[str, object], fallback_name: str | None) -> JsonObject:
    fmt_v = payload.get("format_version", FORMAT_VERSION)
    if isinstance(fmt_v, int) and fmt_v > FORMAT_VERSION:
        raise PackageFormatError(
            f"Paket-Format v{fmt_v} ist neuer als unterstützt (v{FORMAT_VERSION})."
        )
    proj_meta = to_json_object(payload.get("project"))
    if not proj_meta.get("name") and fallback_name:
        proj_meta["name"] = fallback_name
    versions_list: list[JsonValue] = []
    raw_v = payload.get("versions")
    if isinstance(raw_v, Sequence):
        for v in raw_v:
            if isinstance(v, Mapping):
                versions_list.append(to_json_object(v))
    return {
        "format": PACKAGE_FORMAT,
        "format_version": FORMAT_VERSION,
        "exported_at": str(payload.get("exported_at", "")),
        "source": to_json_object(payload.get("source")),
        "checksum": str(payload.get("checksum", "")),
        "options": to_json_object(payload.get("options")),
        "project": proj_meta,
        "categories": to_json_object(payload.get("categories")),
        "qchess_answer_sets": to_json_object(payload.get("qchess_answer_sets")),
        "versions": versions_list,
    }


def _normalize_legacy_backup(
    payload: Mapping[str, object], fallback_name: str | None
) -> JsonObject:
    proj_meta = to_json_object(payload.get("project"))
    name = str(proj_meta.get("name") or fallback_name or "Importierte Checkliste")
    proj_meta["name"] = name
    tree = to_json_object(payload.get("tree_data"))
    v_entry: JsonObject = {
        "version_number": str(proj_meta.get("current_version", "1.0")),
        "is_frozen": False,
        "notes": "Altsicherung (full_backup)",
        "created_at": _iso_now(),
        "tree_data": tree,
    }
    return {
        "format": PACKAGE_FORMAT,
        "format_version": FORMAT_VERSION,
        "exported_at": _iso_now(),
        "source": {"app": "legacy_backup"},
        "checksum": compute_package_checksum(proj_meta, {}, [v_entry]),
        "options": {"history": False, "discussions": True},
        "project": proj_meta,
        "categories": {},
        "qchess_answer_sets": {},
        "versions": [v_entry],
    }


def _normalize_raw_tree(payload: Mapping[str, object], fallback_name: str | None) -> JsonObject:
    name = fallback_name or "Importierter Baum"
    proj_meta: JsonObject = {
        "name": name,
        "description": "",
        "tags": [],
        "aktenzeichen": None,
        "geschaeftsjahr": None,
        "module": "standard",
        "current_version": "1.0",
    }
    v_entry: JsonObject = {
        "version_number": "1.0",
        "is_frozen": False,
        "notes": "Roher Baum",
        "created_at": _iso_now(),
        "tree_data": to_json_object(payload),
    }
    return {
        "format": PACKAGE_FORMAT,
        "format_version": FORMAT_VERSION,
        "exported_at": _iso_now(),
        "source": {"app": "raw_tree"},
        "checksum": compute_package_checksum(proj_meta, {}, [v_entry]),
        "options": {"history": False, "discussions": True},
        "project": proj_meta,
        "categories": {},
        "qchess_answer_sets": {},
        "versions": [v_entry],
    }


def validate_package(payload: object) -> list[str]:
    """Validiert die Konsistenz und Struktur eines Checklisten-Pakets."""
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["Paket ist kein gültiges Wörterbuch-Objekt."]

    if payload.get("format") != PACKAGE_FORMAT:
        errors.append(f"Format muss '{PACKAGE_FORMAT}' sein.")

    fmt_v = payload.get("format_version")
    if not isinstance(fmt_v, int) or fmt_v > FORMAT_VERSION:
        errors.append(f"Format-Version {fmt_v} wird nicht unterstützt.")

    proj = payload.get("project")
    if not isinstance(proj, Mapping) or not str(proj.get("name", "")).strip():
        errors.append("Paket enthält keine gültigen Projektdaten mit Namen.")

    versions = payload.get("versions")
    if not isinstance(versions, Sequence) or not versions:
        errors.append("Paket enthält keine Versionen.")
    else:
        for idx, v in enumerate(versions):
            if not isinstance(v, Mapping) or "tree_data" not in v:
                errors.append(f"Version {idx} enthält kein 'tree_data'.")

    return errors


def import_package(
    payload: object, fallback_name: str | None = None
) -> tuple[ProjectMetadata, ChecklistTree, dict[str, CategoryDefinition]]:
    """Liest und parst ein Checklisten-Paket in Domänenobjekte."""
    normalized = normalize_package_payload(payload, fallback_name=fallback_name)
    validation_errs = validate_package(normalized)
    if validation_errs:
        raise PackageFormatError(f"Paketvalidierung fehlgeschlagen: {'; '.join(validation_errs)}")

    proj_raw = to_json_object(normalized.get("project"))
    raw_tags = proj_raw.get("tags")
    tags = tuple(str(t) for t in raw_tags) if isinstance(raw_tags, (list, tuple)) else ()
    project = ProjectMetadata(
        name=str(proj_raw.get("name", "Unbenannt")),
        description=str(proj_raw.get("description", "")),
        tags=tags,
        aktenzeichen=str(proj_raw["aktenzeichen"]) if proj_raw.get("aktenzeichen") else None,
        geschaeftsjahr=str(proj_raw["geschaeftsjahr"]) if proj_raw.get("geschaeftsjahr") else None,
        module=str(proj_raw.get("module", "standard")),
        current_version=str(proj_raw.get("current_version", "1.0")),
    )

    # validate_package hat eine nichtleere Versionsliste bereits erzwungen.
    versions = normalized.get("versions")
    latest_version = versions[-1] if isinstance(versions, Sequence) and versions else {}
    tree_raw = latest_version.get("tree_data") if isinstance(latest_version, Mapping) else {}
    tree = ChecklistTree.from_dict(tree_raw if isinstance(tree_raw, Mapping) else {})

    categories: dict[str, CategoryDefinition] = {}
    cats_raw = normalized.get("categories")
    if isinstance(cats_raw, Mapping):
        for cid, cdef in cats_raw.items():
            if isinstance(cdef, Mapping):
                items: list[CategoryItemDefinition] = []
                raw_items = cdef.get("items")
                if isinstance(raw_items, Sequence):
                    for it in raw_items:
                        if isinstance(it, Mapping):
                            items.append(
                                CategoryItemDefinition(
                                    value=str(it.get("value", "")),
                                    sort_order=to_int(it.get("sort_order"), 0),
                                )
                            )
                categories[str(cid)] = CategoryDefinition(
                    name=str(cdef.get("name", "")),
                    description=str(cdef.get("description", "")),
                    icon_name=str(cdef.get("icon_name", "list")),
                    color=str(cdef.get("color", "#003478")),
                    items=tuple(items),
                )

    return project, tree, categories
