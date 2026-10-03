"""Tests für die Erfassung und Verwaltung von Antworten und Prüfbefunden."""

from __future__ import annotations

from auditcore_checklists import (
    ExecutionState,
    FindingSeverity,
    FindingType,
)


def test_record_and_get_answer() -> None:
    state = ExecutionState()
    assert state.get_answer("q1") is None

    state = state.record_answer(
        node_id="q1",
        value=True,
        remark_user="Auftraggeber-Eigenschaft bestätigt.",
        doc_refs=["BELEG-001.pdf", "BELEG-002.pdf"],
        answered_by="pruefer_1",
    )
    ans = state.get_answer("q1")
    assert ans is not None
    assert ans.node_id == "q1"
    assert ans.value is True
    assert ans.is_na is False
    assert ans.remark_user == "Auftraggeber-Eigenschaft bestätigt."
    assert ans.doc_refs == ("BELEG-001.pdf", "BELEG-002.pdf")
    assert ans.answered_by == "pruefer_1"
    assert ans.befund_typ == FindingType.NONE


def test_record_findings() -> None:
    state = ExecutionState()
    state = state.record_answer(
        node_id="q_mangel",
        value=False,
        befund_typ=FindingType.FORMAL,
        finding_severity=FindingSeverity.MODERATE,
        finding_text="Dokumentationspflicht nach § 8 VgV verletzt.",
    )
    ans = state.get_answer("q_mangel")
    assert ans is not None
    assert ans.befund_typ == FindingType.FORMAL
    assert ans.finding_severity == FindingSeverity.MODERATE
    assert ans.finding_text == "Dokumentationspflicht nach § 8 VgV verletzt."


def test_set_not_applicable() -> None:
    state = ExecutionState()
    state = state.set_not_applicable(
        node_id="q_entfaellt",
        remark_user="Nicht einschlägig, da keine Unteraufträge vergeben wurden.",
        answered_by="pruefer_2",
    )
    ans = state.get_answer("q_entfaellt")
    assert ans is not None
    assert ans.is_na is True
    assert ans.value is None
    assert ans.remark_user == "Nicht einschlägig, da keine Unteraufträge vergeben wurden."


def test_clear_answer() -> None:
    state = ExecutionState()
    state = state.record_answer(node_id="q1", value=123.45)
    assert state.get_answer("q1") is not None

    state = state.clear_answer("q1")
    assert state.get_answer("q1") is None


def test_answers_serialization_roundtrip() -> None:
    state = ExecutionState()
    state = state.record_answer(
        node_id="q1",
        value="Antworttext",
        befund_typ=FindingType.FINANCIAL,
        finding_severity=FindingSeverity.SIGNIFICANT,
        finding_text="Rückforderung von 15.000 EUR empfohlen.",
    )
    data = state.to_dict()
    restored = ExecutionState.from_dict(data)

    ans = restored.get_answer("q1")
    assert ans is not None
    assert ans.value == "Antworttext"
    assert ans.befund_typ == FindingType.FINANCIAL
    assert ans.finding_severity == FindingSeverity.SIGNIFICANT
    assert ans.finding_text == "Rückforderung von 15.000 EUR empfohlen."


def test_answers_property_and_clear_unknown_node() -> None:
    state = ExecutionState().record_answer(node_id="q1", value="JA")
    assert set(state.answers) == {"q1"}

    # Unbekannter Knoten: der Stand bleibt unverändert und wird nicht kopiert
    assert state.clear_answer("q_unbekannt") is state
    assert set(state.answers) == {"q1"}


def test_from_dict_ignores_invalid_entries_and_applies_defaults() -> None:
    restored = ExecutionState.from_dict(
        {
            "q1": {"node_id": "q1", "value": ["a", "b"], "doc_refs": "kein-Array"},
            "q2": "keine Zuordnung",
        }
    )
    assert set(restored.answers) == {"q1"}
    ans = restored.get_answer("q1")
    assert ans is not None
    assert ans.value == ["a", "b"]
    assert ans.doc_refs == ()
    assert ans.befund_typ == FindingType.NONE
    assert ans.finding_severity is None
    assert ans.remark_user is None
    assert ans.answered_at is None
