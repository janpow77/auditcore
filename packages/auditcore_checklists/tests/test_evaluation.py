"""Tests für Pfadauswertung, Entscheidungszweige und Befundstatistiken."""

from __future__ import annotations

import pytest

from auditcore_checklists import (
    ChecklistNode,
    ChecklistTree,
    ExecutionState,
    FindingSeverity,
    FindingType,
    NodeContent,
    NodeType,
    evaluate_checklist,
)


def test_evaluation_decision_positive_branch(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState()

    # Allgemeine Frage beantworten
    state = state.record_answer(node_id=node_map["question_general"], value=True)
    # Entscheidung mit "JA" beantworten
    state = state.record_answer(node_id=node_map["decision"], value="JA")

    result = evaluate_checklist(tree, state)

    # Aktive Fragen: question_general, decision, question_ja
    assert node_map["question_general"] in result.active_question_ids
    assert node_map["decision"] in result.active_question_ids
    assert node_map["question_ja"] in result.active_question_ids
    # question_nein darf NICHT aktiv sein
    assert node_map["question_nein"] not in result.active_question_ids

    assert result.total_active_questions == 3
    assert result.answered_count == 2
    assert result.unanswered_count == 1
    assert result.is_complete is False


def test_evaluation_decision_negative_branch(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState()

    state = state.record_answer(node_id=node_map["question_general"], value=True)
    # Entscheidung mit "NEIN" beantworten
    state = state.record_answer(node_id=node_map["decision"], value=False)
    # NEIN-Frage beantworten
    state = state.record_answer(node_id=node_map["question_nein"], value=True)

    result = evaluate_checklist(tree, state)

    assert node_map["question_nein"] in result.active_question_ids
    assert node_map["question_ja"] not in result.active_question_ids

    assert result.total_active_questions == 3
    assert result.answered_count == 3
    assert result.unanswered_count == 0
    assert result.is_complete is True
    assert result.progress_ratio == 1.0


def test_evaluation_decision_unanswered(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState()

    result = evaluate_checklist(tree, state)

    # Wenn die Entscheidung noch unbeantwortet ist, sind weder JA noch NEIN Zweige erreichbar
    assert node_map["question_general"] in result.active_question_ids
    assert node_map["decision"] in result.active_question_ids
    assert node_map["question_ja"] not in result.active_question_ids
    assert node_map["question_nein"] not in result.active_question_ids
    assert result.total_active_questions == 2
    assert result.answered_count == 0


def test_evaluation_findings_aggregation(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState()

    state = state.record_answer(
        node_id=node_map["question_general"],
        value=False,
        befund_typ=FindingType.FORMAL,
        finding_severity=FindingSeverity.HINT,
        finding_text="Formeller Fehler im Vergabevermerk.",
    )
    state = state.record_answer(node_id=node_map["decision"], value=True)
    state = state.record_answer(
        node_id=node_map["question_ja"],
        value=False,
        befund_typ=FindingType.FINANCIAL,
        finding_severity=FindingSeverity.SIGNIFICANT,
        finding_text="Unterlassene EU-Bekanntmachung führt zu 25 % Kürzung.",
    )

    result = evaluate_checklist(tree, state)

    assert result.total_findings == 2
    assert result.formal_findings == 1
    assert result.financial_findings == 1
    assert len(result.findings) == 2

    # Prüfung der Serialisierung
    as_dict = result.to_dict()
    assert as_dict["total_findings"] == 2
    assert as_dict["is_complete"] is True


@pytest.mark.parametrize(
    ("value", "expected_branch"),
    [
        ("ja", "question_ja"),
        (" yes ", "question_ja"),
        (1, "question_ja"),
        ("Nein", "question_nein"),
        ("0", "question_nein"),
        ("NO", "question_nein"),
    ],
)
def test_decision_text_values_select_branch(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
    value: str | int,
    expected_branch: str,
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState().record_answer(node_id=node_map["decision"], value=value)
    result = evaluate_checklist(tree, state)

    other = "question_nein" if expected_branch == "question_ja" else "question_ja"
    assert node_map[expected_branch] in result.active_question_ids
    assert node_map[other] not in result.active_question_ids


@pytest.mark.parametrize("value", ["vielleicht", None])
def test_decision_unclear_value_keeps_branches_closed(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
    value: str | None,
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState().record_answer(node_id=node_map["decision"], value=value)
    result = evaluate_checklist(tree, state)

    assert node_map["question_ja"] not in result.active_question_ids
    assert node_map["question_nein"] not in result.active_question_ids
    # Eine Antwort ohne Wert gilt weiterhin als offen
    if value is None:
        assert node_map["decision"] in result.unanswered_question_ids


def test_not_applicable_and_empty_answers(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    state = ExecutionState()
    state = state.set_not_applicable(node_map["question_general"], remark_user="Entfällt.")
    state = state.set_not_applicable(node_map["decision"])

    result = evaluate_checklist(tree, state)

    # Eine als „Entfällt“ markierte Entscheidung öffnet keinen Zweig
    assert result.total_active_questions == 2
    assert result.na_count == 2
    assert result.answered_count == 2
    assert result.is_complete is True
    assert result.to_dict()["progress_ratio"] == 1.0


def test_shared_child_is_counted_once() -> None:
    root = ChecklistNode(
        id="r",
        node_type=NodeType.HEADING,
        parent_id=None,
        content=NodeContent(title="Wurzel"),
        children=("h1", "h2"),
    )
    h1 = ChecklistNode(
        id="h1",
        node_type=NodeType.HEADING,
        parent_id="r",
        content=NodeContent(title="Kapitel 1"),
        children=("q",),
    )
    h2 = ChecklistNode(
        id="h2",
        node_type=NodeType.HEADING,
        parent_id="r",
        content=NodeContent(title="Kapitel 2"),
        sort_order=1,
        children=("q",),
    )
    q = ChecklistNode(
        id="q",
        node_type=NodeType.QUESTION,
        parent_id="h1",
        content=NodeContent(title="Gemeinsame Frage"),
    )
    tree = ChecklistTree(root_id="r", nodes={"r": root, "h1": h1, "h2": h2, "q": q})

    result = evaluate_checklist(tree, ExecutionState())

    # Mehrfach verlinkte Knoten werden nur einmal ausgewertet
    assert result.active_question_ids == ("q",)
    assert result.total_active_questions == 1


def test_missing_root_aborts_evaluation() -> None:
    # Ein Baum ohne Wurzelknoten ist nicht auswertbar; die Auswertung bricht ab.
    tree = ChecklistTree(root_id="fehlt", nodes={})
    with pytest.raises(KeyError):
        evaluate_checklist(tree, ExecutionState())
