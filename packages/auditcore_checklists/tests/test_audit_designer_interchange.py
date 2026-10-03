"""Interoperabilitätstests zwischen audit_designer und auditcore_checklists."""

from __future__ import annotations

import hashlib
import json

from auditcore_checklists import (
    AnswerType,
    CategoryDefinition,
    CategoryItemDefinition,
    ChecklistTree,
    NodeType,
    ProjectMetadata,
    export_package,
    import_package,
)


def _audit_designer_canonical_tree(tree_data: dict[str, object]) -> dict[str, object]:
    """Referenz-Implementierung aus audit_designer ChecklistPackageService._canonical_tree."""
    nodes: dict[str, object] = {}
    raw_nodes = tree_data.get("nodes")
    if isinstance(raw_nodes, dict):
        for nid, node in raw_nodes.items():
            if isinstance(node, dict):
                nodes[nid] = {
                    "node_type": node.get("node_type"),
                    "parent_id": node.get("parent_id"),
                    "branch": node.get("branch"),
                    "sort_order": node.get("sort_order", 0),
                    "content": node.get("content"),
                    "children": node.get("children", []),
                }
    return {"root_id": tree_data.get("root_id"), "nodes": nodes}


def _audit_designer_content_checksum(
    project_meta: dict[str, object],
    categories: dict[str, object],
    versions: list[dict[str, object]],
) -> str:
    """Referenz-Implementierung aus audit_designer ChecklistPackageService._content_checksum."""
    v_entries: list[dict[str, object]] = []
    for v in versions:
        tree_raw = v.get("tree_data")
        tree_dict: dict[str, object] = dict(tree_raw) if isinstance(tree_raw, dict) else {}
        v_entries.append(
            {
                "version_number": v["version_number"],
                "is_frozen": v["is_frozen"],
                "notes": v["notes"],
                "tree": _audit_designer_canonical_tree(tree_dict),
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
        "categories": categories,
        "versions": v_entries,
    }
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def test_parity_with_audit_designer_tree_and_checksum() -> None:
    # 1. Baum wie im audit_designer erzeugen
    empty = ChecklistTree.create_empty(title="Checkliste A")
    root_id = empty.root_id

    tree, heading = empty.add_node(
        node_type=NodeType.HEADING,
        parent_id=root_id,
        title="1. Allgemeines",
    )
    tree, question = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=heading.id,
        title="Welche Projektart liegt vor?",
        answer_type=AnswerType.CUSTOM_ENUM,
        category_id=42,
        public_remark="<p>Bitte Förderfähigkeit prüfen.</p>",
        remark_snippets={
            "Infrastruktur": "<p>Bauliche Maßnahme — Art. 73 prüfen.</p>",
            "KMU": "<p>Beihilferechtliche Würdigung nötig.</p>",
        },
    )
    tree, decision = tree.add_node(
        node_type=NodeType.DECISION,
        parent_id=heading.id,
        title="Wurden Einnahmen erzielt?",
    )
    tree, q_ja = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=decision.id,
        branch="JA",
        title="Höhe der Einnahmen?",
        answer_type=AnswerType.CURRENCY,
    )
    tree, q_nein = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=decision.id,
        branch="NEIN",
        title="Begründung?",
        answer_type=AnswerType.BOOLEAN,
    )

    categories = {
        "42": CategoryDefinition(
            name="Projektart",
            description="Test",
            icon_name="list",
            color="#003478",
            items=(
                CategoryItemDefinition(value="Infrastruktur", sort_order=0),
                CategoryItemDefinition(value="Forschung", sort_order=1),
                CategoryItemDefinition(value="KMU", sort_order=2),
            ),
        )
    }

    project = ProjectMetadata(
        name="Checkliste A",
        description="Vergleichstest",
        tags=("audit_designer", "paritaet"),
        aktenzeichen="AZ-42",
        geschaeftsjahr="2026",
        module="standard",
        current_version="0.1",
    )

    # Paket über auditcore_checklists exportieren
    pkg = export_package(
        project=project,
        tree=tree,
        categories=categories,
        version_number="0.1",
        notes="Erstversion",
    )

    # 2. Prüfsumme mit der originalen audit_designer-Logik gegenprüfen
    ref_checksum = _audit_designer_content_checksum(
        project_meta=pkg["project"],  # type: ignore[arg-type]
        categories=pkg["categories"],  # type: ignore[arg-type]
        versions=pkg["versions"],  # type: ignore[arg-type]
    )

    assert pkg["checksum"] == ref_checksum, (
        "Prüfsumme muss 100% paritätisch zu audit_designer sein!"
    )

    # 3. Paket importieren und Konsistenz verifizieren
    imported_project, imported_tree, imported_cats = import_package(pkg)
    assert imported_project.name == "Checkliste A"
    assert imported_project.current_version == "0.1"
    assert "42" in imported_cats
    assert imported_cats["42"].name == "Projektart"
    assert len(imported_tree.nodes) == 6
    assert imported_tree.get_node(question.id).content.category_id == 42
    assert imported_tree.get_node(decision.id).node_type == NodeType.DECISION
