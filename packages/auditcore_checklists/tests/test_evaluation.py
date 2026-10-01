"""Tests für Pfadauswertung, Entscheidungszweige und Befundstatistiken."""

from __future__ import annotations

from auditcore_checklists import (
    ChecklistTree,
    ExecutionState,
    FindingSeverity,
    FindingType,
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
