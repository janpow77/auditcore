"""Tests für Baumoperationen, Hierarchie, Zweigprüfung und Zykluserkennung."""

from __future__ import annotations

import pytest

from auditcore_checklists import (
    AnswerType,
    ChecklistTree,
    CycleDetectedError,
    InvalidBranchError,
    NodeNotFoundError,
    NodeType,
    TreeStructureError,
)


def test_create_empty_tree(empty_tree: ChecklistTree) -> None:
    root = empty_tree.get_root()
    assert root.id == empty_tree.root_id
    assert root.node_type == NodeType.HEADING
    assert root.parent_id is None
    assert root.content.title == "Test-Checkliste"
    assert len(root.children) == 0


def test_add_node_rules(empty_tree: ChecklistTree) -> None:
    root_id = empty_tree.root_id
    tree, h1 = empty_tree.add_node(
        node_type=NodeType.HEADING,
        parent_id=root_id,
        title="Kapitel 1",
    )
    assert h1.parent_id == root_id
    assert h1.id in tree.get_node(root_id).children

    tree, q1 = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=h1.id,
        title="Frage 1.1",
        answer_type=AnswerType.TEXT,
    )
    assert q1.content.answer_type == AnswerType.TEXT

    # Fragen können keine Unterknoten haben
    with pytest.raises(TreeStructureError, match="Fragen und Hinweise"):
        tree.add_node(
            node_type=NodeType.QUESTION,
            parent_id=q1.id,
            title="Unzulässige Unterfrage",
        )


def test_decision_and_branch_validation(empty_tree: ChecklistTree) -> None:
    root_id = empty_tree.root_id
    tree, d1 = empty_tree.add_node(
        node_type=NodeType.DECISION,
        parent_id=root_id,
        title="Schwellenwert erreicht?",
    )
    assert d1.content.answer_type == AnswerType.BOOLEAN_JN

    # Unterknoten unter Entscheidung erfordert 'JA' oder 'NEIN'
    with pytest.raises(InvalidBranchError, match="erfordern 'JA' oder 'NEIN'"):
        tree.add_node(
            node_type=NodeType.QUESTION,
            parent_id=d1.id,
            title="Fehlender Zweig",
        )

    with pytest.raises(InvalidBranchError, match="erfordern 'JA' oder 'NEIN'"):
        tree.add_node(
            node_type=NodeType.QUESTION,
            parent_id=d1.id,
            branch="VIELLEICHT",
            title="Ungültiger Zweig",
        )

    # Gültige Zweige anlegen
    tree, q_ja = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=d1.id,
        branch="JA",
        title="Zweig JA Frage",
    )
    tree, q_nein = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=d1.id,
        branch="NEIN",
        title="Zweig NEIN Frage",
    )
    assert q_ja.branch == "JA"
    assert q_nein.branch == "NEIN"

    # Zweig unter Überschrift ist verboten
    tree, h2 = tree.add_node(
        node_type=NodeType.HEADING,
        parent_id=root_id,
        title="Kapitel 2",
    )
    with pytest.raises(InvalidBranchError, match="Nicht-Entscheidungen dürfen keinen Zweig"):
        tree.add_node(
            node_type=NodeType.QUESTION,
            parent_id=h2.id,
            branch="JA",
            title="Unzulässiger Zweig",
        )


def test_update_node(populated_tree: tuple[ChecklistTree, dict[str, str]]) -> None:
    tree, node_map = populated_tree
    qid = node_map["question_general"]

    updated_tree, updated_node = tree.update_node(
        node_id=qid,
        title="Aktualisierter Fragentitel",
        hints=["Hinweis 1", "Hinweis 2"],
        public_remark="Öffentliche Prüfbemerkung",
        status="in_progress",
    )
    assert updated_node.content.title == "Aktualisierter Fragentitel"
    assert updated_node.content.hints == ("Hinweis 1", "Hinweis 2")
    assert updated_node.content.public_remark == "Öffentliche Prüfbemerkung"
    assert updated_node.internal.status == "in_progress"


def test_delete_node(populated_tree: tuple[ChecklistTree, dict[str, str]]) -> None:
    tree, node_map = populated_tree
    root_id = node_map["root"]

    # Wurzel darf nicht gelöscht werden
    with pytest.raises(TreeStructureError, match="Wurzelknoten darf nicht gelöscht werden"):
        tree.delete_node(root_id)

    # Entscheidung löschen (sollte rekursiv q_ja und q_nein mitlöschen)
    decision_id = node_map["decision"]
    tree_after = tree.delete_node(decision_id)

    assert decision_id not in tree_after.nodes
    assert node_map["question_ja"] not in tree_after.nodes
    assert node_map["question_nein"] not in tree_after.nodes

    # Aus Elternknoten entfernt
    heading = tree_after.get_node(node_map["heading"])
    assert decision_id not in heading.children


def test_move_node_and_cycle_detection(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    h1_id = node_map["heading"]
    q1_id = node_map["question_general"]

    # Neues Kapitel
    tree, h2 = tree.add_node(
        node_type=NodeType.HEADING,
        parent_id=node_map["root"],
        title="2. Neues Kapitel",
    )

    # Frage 1 von h1 nach h2 verschieben
    tree_moved = tree.move_node(node_id=q1_id, new_parent_id=h2.id)
    assert tree_moved.get_node(q1_id).parent_id == h2.id
    assert q1_id in tree_moved.get_node(h2.id).children
    assert q1_id not in tree_moved.get_node(h1_id).children

    # Zykluserkennung: Versuch, h1 unter die darin liegende Entscheidung zu schieben
    with pytest.raises(CycleDetectedError, match="Zyklus erzeugen"):
        tree_moved.move_node(node_id=h1_id, new_parent_id=node_map["decision"])


def test_tree_validation(populated_tree: tuple[ChecklistTree, dict[str, str]]) -> None:
    tree, _ = populated_tree
    findings = tree.validate()
    # Der ordnungsgemäß aufgebaute Baum hat keine Fehler
    errors = [f for f in findings if f.severity == "ERROR"]
    assert len(errors) == 0


def test_roundtrip_serialization(populated_tree: tuple[ChecklistTree, dict[str, str]]) -> None:
    tree, _ = populated_tree
    data = tree.to_dict()
    restored = ChecklistTree.from_dict(data)

    assert restored.root_id == tree.root_id
    assert len(restored.nodes) == len(tree.nodes)
    for nid, node in tree.nodes.items():
        restored_node = restored.get_node(nid)
        assert restored_node.node_type == node.node_type
        assert restored_node.parent_id == node.parent_id
        assert restored_node.branch == node.branch
        assert restored_node.content.title == node.content.title
        assert restored_node.children == node.children


def test_get_node_unknown_raises(empty_tree: ChecklistTree) -> None:
    with pytest.raises(NodeNotFoundError) as exc:
        empty_tree.get_node("unbekannt")
    assert exc.value.node_id == "unbekannt"


def test_from_dict_rejects_invalid_data() -> None:
    with pytest.raises(TreeStructureError, match="kein gültiges 'nodes'-Objekt"):
        ChecklistTree.from_dict({"root_id": "r", "nodes": ["r"]})
    with pytest.raises(TreeStructureError, match="Wurzelknoten 'r' ist nicht"):
        ChecklistTree.from_dict({"root_id": "r", "nodes": {"x": {"node_type": "HEADING"}}})


def test_from_dict_applies_defaults_for_sparse_nodes() -> None:
    tree = ChecklistTree.from_dict({"root_id": "r", "nodes": {"r": {}, "kaputt": "kein Knoten"}})
    root = tree.get_root()
    assert set(tree.nodes) == {"r"}
    assert root.node_type == NodeType.HEADING
    assert root.content.title == "Unbenannt"
    assert root.internal.status == "pending"
    assert root.internal.team_notes == ()


def test_from_dict_parses_team_notes() -> None:
    tree = ChecklistTree.from_dict(
        {
            "root_id": "r",
            "nodes": {
                "r": {
                    "node_type": "HEADING",
                    "content": {"title": "Wurzel"},
                    "internal": {
                        "status": "resolved",
                        "team_notes": [
                            {
                                "id": "n2",
                                "username": "pruefer_2",
                                "message": "Erledigt.",
                                "timestamp": "2026-10-02T10:00:00+00:00",
                                "user_id": ["ungültig"],
                                "parent_note_id": "n1",
                            },
                            "keine Notiz",
                        ],
                    },
                }
            },
        }
    )
    notes = tree.get_root().internal.team_notes
    assert len(notes) == 1
    assert notes[0].parent_note_id == "n1"
    assert notes[0].user_id is None
    assert tree.get_root().internal.status == "resolved"


def test_canonical_data_excludes_internal(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    canonical = tree.canonical_data()
    assert canonical["root_id"] == tree.root_id
    nodes = canonical["nodes"]
    assert isinstance(nodes, dict)
    assert set(nodes) == set(tree.nodes)
    decision = nodes[node_map["decision"]]
    assert isinstance(decision, dict)
    assert "internal" not in decision
    assert decision["node_type"] == "DECISION"
    assert decision["children"] == [node_map["question_ja"], node_map["question_nein"]]

    # Zeitstempel ändern sich, die kanonische Struktur nicht
    updated, _ = tree.update_node(node_map["heading"], status="resolved")
    assert updated.canonical_data() == canonical


def test_move_root_and_into_leaf_forbidden(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    with pytest.raises(TreeStructureError, match="Wurzelknoten kann nicht verschoben"):
        tree.move_node(node_map["root"], node_map["heading"])
    with pytest.raises(TreeStructureError, match="keine Unterknoten aufnehmen"):
        tree.move_node(node_map["decision"], node_map["question_general"])


def test_move_node_with_sort_order_into_decision_branch(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    decision_id = node_map["decision"]
    q1_id = node_map["question_general"]

    moved = tree.move_node(q1_id, decision_id, new_branch="JA", new_sort_order=0)

    decision = moved.get_node(decision_id)
    assert decision.children[0] == q1_id
    assert moved.get_node(q1_id).branch == "JA"
    # Sortierung wird je Zweig getrennt neu vergeben
    ja_children = moved.get_children(decision_id, branch="JA")
    assert [c.id for c in ja_children] == [q1_id, node_map["question_ja"]]
    assert [c.sort_order for c in ja_children] == [0, 1]
    assert moved.get_node(node_map["question_nein"]).sort_order == 0


def test_delete_node_in_decision_reindexes_branch(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    decision_id = node_map["decision"]
    tree, extra = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=decision_id,
        branch="JA",
        title="Wurde die Bekanntmachungsfrist eingehalten?",
    )
    assert extra.sort_order == 1

    after = tree.delete_node(node_map["question_ja"])

    assert after.get_node(extra.id).sort_order == 0
    assert after.get_node(node_map["question_nein"]).sort_order == 0
