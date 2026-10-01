"""Tests für Baumoperationen, Hierarchie, Zweigprüfung und Zykluserkennung."""

from __future__ import annotations

import pytest

from auditcore_checklists import (
    AnswerType,
    ChecklistTree,
    CycleDetectedError,
    InvalidBranchError,
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
