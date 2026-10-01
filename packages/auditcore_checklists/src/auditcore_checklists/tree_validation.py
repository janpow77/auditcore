"""Strukturelle Validierungsprüfungen für Checklisten-Bäume."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import ChecklistNode, NodeType, TreeValidationFinding


def validate_tree_structure(
    root_id: str,
    nodes: Mapping[str, ChecklistNode],
    reachable_ids: Sequence[str],
) -> list[TreeValidationFinding]:
    """Prüft die strukturelle Integrität des gesamten Baums."""
    findings: list[TreeValidationFinding] = []
    if root_id not in nodes:
        findings.append(
            TreeValidationFinding("ERROR", root_id, "MISSING_ROOT", "Wurzelknoten fehlt.")
        )
        return findings

    reachable_set = set(reachable_ids)
    for nid, node in nodes.items():
        if nid not in reachable_set:
            findings.append(
                TreeValidationFinding(
                    "WARNING", nid, "ORPHAN_NODE", f"Knoten '{nid}' ist nicht erreichbar."
                )
            )
        _validate_node_integrity(node, root_id, nodes, findings)
    return findings


def _validate_node_integrity(
    node: ChecklistNode,
    root_id: str,
    nodes: Mapping[str, ChecklistNode],
    findings: list[TreeValidationFinding],
) -> None:
    if node.id != root_id and not node.parent_id:
        findings.append(
            TreeValidationFinding(
                "ERROR",
                node.id,
                "NO_PARENT",
                f"Nicht-Wurzelknoten '{node.id}' hat keinen Elternknoten.",
            )
        )
    if node.parent_id and node.parent_id not in nodes:
        findings.append(
            TreeValidationFinding(
                "ERROR",
                node.id,
                "DANGLING_PARENT",
                f"Elternknoten '{node.parent_id}' existiert nicht.",
            )
        )
    if node.node_type in (NodeType.QUESTION, NodeType.HINT) and node.children:
        findings.append(
            TreeValidationFinding(
                "ERROR",
                node.id,
                "LEAF_HAS_CHILDREN",
                f"Blattknoten '{node.id}' darf keine Kindknoten haben.",
            )
        )
    for cid in node.children:
        if cid not in nodes:
            findings.append(
                TreeValidationFinding(
                    "ERROR",
                    node.id,
                    "DANGLING_CHILD",
                    f"Kindknoten '{cid}' existiert nicht.",
                )
            )
