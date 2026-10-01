"""Gemeinsame Test-Fixtures für auditcore_checklists."""

from __future__ import annotations

import pytest

from auditcore_checklists import (
    AnswerType,
    CategoryDefinition,
    CategoryItemDefinition,
    ChecklistTree,
    NodeType,
    ProjectMetadata,
)


@pytest.fixture
def empty_tree() -> ChecklistTree:
    """Leerer Prüfbaum mit Wurzelüberschrift."""
    return ChecklistTree.create_empty(title="Test-Checkliste")


@pytest.fixture
def populated_tree(empty_tree: ChecklistTree) -> tuple[ChecklistTree, dict[str, str]]:
    """Vollständig aufgebauter Baum mit Überschrift, Frage, Entscheidung und Zweigen."""
    root_id = empty_tree.root_id
    tree, h1 = empty_tree.add_node(
        node_type=NodeType.HEADING,
        parent_id=root_id,
        title="1. Vergaberechtliche Vorprüfung",
    )
    tree, q1 = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=h1.id,
        title="Liegt ein öffentlicher Auftraggeber vor?",
        answer_type=AnswerType.BOOLEAN,
    )
    tree, d1 = tree.add_node(
        node_type=NodeType.DECISION,
        parent_id=h1.id,
        title="Wurde der EU-Schwellenwert überschritten?",
    )
    tree, q_ja = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=d1.id,
        branch="JA",
        title="Wurde das Verfahren europaweit bekanntgemacht?",
        answer_type=AnswerType.BOOLEAN_JN,
    )
    tree, q_nein = tree.add_node(
        node_type=NodeType.QUESTION,
        parent_id=d1.id,
        branch="NEIN",
        title="Wurde die Unterschwellenvergabeordnung (UVgO) beachtet?",
        answer_type=AnswerType.BOOLEAN_JN,
    )
    node_map = {
        "root": root_id,
        "heading": h1.id,
        "question_general": q1.id,
        "decision": d1.id,
        "question_ja": q_ja.id,
        "question_nein": q_nein.id,
    }
    return tree, node_map


@pytest.fixture
def sample_categories() -> dict[str, CategoryDefinition]:
    """Beispiel-Kategorien für CUSTOM_ENUM-Antwortsets."""
    return {
        "cat_1": CategoryDefinition(
            name="Verfahrensart",
            description="Zulässige Vergabearten nach VgV",
            icon_name="list",
            color="#003478",
            items=(
                CategoryItemDefinition(value="Offenes Verfahren", sort_order=0),
                CategoryItemDefinition(value="Nicht offenes Verfahren", sort_order=1),
                CategoryItemDefinition(value="Verhandlungsverfahren", sort_order=2),
            ),
        )
    }


@pytest.fixture
def sample_project() -> ProjectMetadata:
    """Beispiel-Projektmetadaten."""
    return ProjectMetadata(
        name="Prüfung Zuwendungsprojekt Alpha",
        description="Prüfung der Vergabe- und Beihilfevorschriften",
        tags=("vergaberecht", "2026", "stichprobe"),
        aktenzeichen="PR-2026-0815",
        geschaeftsjahr="2026",
        module="standard",
        current_version="1.0",
    )
