"""Tests für die strukturelle Validierung fehlerhafter Checklisten-Bäume."""

from __future__ import annotations

from auditcore_checklists import (
    ChecklistNode,
    ChecklistTree,
    NodeContent,
    NodeType,
)


def _node(
    nid: str,
    node_type: NodeType,
    parent_id: str | None,
    children: tuple[str, ...] = (),
) -> ChecklistNode:
    return ChecklistNode(
        id=nid,
        node_type=node_type,
        parent_id=parent_id,
        content=NodeContent(title=f"Knoten {nid}"),
        children=children,
    )


def test_fehlender_wurzelknoten_wird_gemeldet() -> None:
    tree = ChecklistTree(root_id="wurzel", nodes={"a": _node("a", NodeType.HEADING, None)})
    findings = tree.validate()
    assert len(findings) == 1
    assert findings[0].code == "MISSING_ROOT"
    assert findings[0].severity == "ERROR"
    assert findings[0].node_id == "wurzel"


def test_strukturfehler_werden_einzeln_gemeldet() -> None:
    nodes = {
        "r": _node("r", NodeType.HEADING, None, children=("q", "geist")),
        # Frage mit Kindknoten verletzt die Blattregel
        "q": _node("q", NodeType.QUESTION, "r", children=("h",)),
        "h": _node("h", NodeType.HINT, "q"),
        # Verwaister Knoten ohne Elternknoten
        "frei": _node("frei", NodeType.HEADING, None),
        # Verweis auf nicht existierenden Elternknoten
        "lose": _node("lose", NodeType.QUESTION, "fehlt"),
    }
    findings = ChecklistTree(root_id="r", nodes=nodes).validate()
    codes = {(f.node_id, f.code) for f in findings}

    assert ("q", "LEAF_HAS_CHILDREN") in codes
    assert ("r", "DANGLING_CHILD") in codes
    assert ("frei", "NO_PARENT") in codes
    assert ("frei", "ORPHAN_NODE") in codes
    assert ("lose", "DANGLING_PARENT") in codes
    assert ("lose", "ORPHAN_NODE") in codes
    # Erreichbare, korrekt verknüpfte Knoten erzeugen keine Meldung
    assert not any(f.node_id == "h" for f in findings)

    severities = {f.code: f.severity for f in findings}
    assert severities["ORPHAN_NODE"] == "WARNING"
    assert severities["DANGLING_CHILD"] == "ERROR"
