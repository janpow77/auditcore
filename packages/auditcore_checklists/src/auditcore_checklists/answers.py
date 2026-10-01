"""Antwortverwaltung und Zustandserfassung für die Checklisten-Ausführung."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from .errors import JsonObject, JsonValue, to_json_value
from .models import ChecklistAnswer, FindingSeverity, FindingType


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _answer_to_dict(ans: ChecklistAnswer) -> JsonObject:
    return {
        "node_id": ans.node_id,
        "value": ans.value,
        "is_na": ans.is_na,
        "remark_user": ans.remark_user,
        "doc_refs": list(ans.doc_refs),
        "befund_typ": ans.befund_typ.value,
        "finding_severity": ans.finding_severity.value if ans.finding_severity else None,
        "finding_text": ans.finding_text,
        "answered_at": ans.answered_at,
        "answered_by": ans.answered_by,
    }


def _answer_from_dict(raw: Mapping[str, object]) -> ChecklistAnswer:
    btype_raw = raw.get("befund_typ")
    btype = FindingType(str(btype_raw)) if btype_raw else FindingType.NONE
    fsev_raw = raw.get("finding_severity")
    fsev = FindingSeverity(str(fsev_raw)) if fsev_raw else None
    raw_refs = raw.get("doc_refs")
    doc_refs = tuple(str(x) for x in raw_refs) if isinstance(raw_refs, (list, tuple)) else ()
    return ChecklistAnswer(
        node_id=str(raw.get("node_id", "")),
        value=to_json_value(raw.get("value")),
        is_na=bool(raw.get("is_na", False)),
        remark_user=str(raw["remark_user"]) if raw.get("remark_user") is not None else None,
        doc_refs=doc_refs,
        befund_typ=btype,
        finding_severity=fsev,
        finding_text=str(raw["finding_text"]) if raw.get("finding_text") is not None else None,
        answered_at=str(raw["answered_at"]) if raw.get("answered_at") else None,
        answered_by=str(raw["answered_by"]) if raw.get("answered_by") else None,
    )


class ExecutionState:
    """Hält und verwaltet den Erfassungsstand aller Antworten eines Prüflaufs."""

    def __init__(self, answers: Mapping[str, ChecklistAnswer] | None = None) -> None:
        self._answers: dict[str, ChecklistAnswer] = dict(answers or {})

    @property
    def answers(self) -> Mapping[str, ChecklistAnswer]:
        """Alle hinterlegten Antworten nach Knoten-ID."""
        return self._answers

    def get_answer(self, node_id: str) -> ChecklistAnswer | None:
        """Gibt die Antwort zu einem Knoten zurück oder None."""
        return self._answers.get(node_id)

    def record_answer(
        self,
        node_id: str,
        value: JsonValue = None,
        is_na: bool = False,
        remark_user: str | None = None,
        doc_refs: Sequence[str] | None = None,
        befund_typ: FindingType = FindingType.NONE,
        finding_severity: FindingSeverity | None = None,
        finding_text: str | None = None,
        answered_by: str | None = None,
    ) -> ExecutionState:
        """Erfasst oder aktualisiert eine Antwort für einen Knoten."""
        now = _iso_now()
        new_answer = ChecklistAnswer(
            node_id=node_id,
            value=value,
            is_na=is_na,
            remark_user=remark_user,
            doc_refs=tuple(doc_refs or ()),
            befund_typ=befund_typ,
            finding_severity=finding_severity,
            finding_text=finding_text,
            answered_at=now,
            answered_by=answered_by,
        )
        updated = dict(self._answers)
        updated[node_id] = new_answer
        return ExecutionState(answers=updated)

    def set_not_applicable(
        self,
        node_id: str,
        remark_user: str | None = None,
        answered_by: str | None = None,
    ) -> ExecutionState:
        """Markiert einen Prüfpunkt als 'Entfällt' (is_na=True)."""
        return self.record_answer(
            node_id=node_id,
            value=None,
            is_na=True,
            remark_user=remark_user,
            answered_by=answered_by,
        )

    def clear_answer(self, node_id: str) -> ExecutionState:
        """Entfernt eine erfasste Antwort zu einem Knoten."""
        if node_id not in self._answers:
            return self
        updated = {k: v for k, v in self._answers.items() if k != node_id}
        return ExecutionState(answers=updated)

    def to_dict(self) -> JsonObject:
        """Serialisiert den gesamten Antwortstand."""
        res: JsonObject = {nid: _answer_to_dict(ans) for nid, ans in self._answers.items()}
        return res

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ExecutionState:
        """Stellt den Antwortstand aus einem Wörterbuch wieder her."""
        answers: dict[str, ChecklistAnswer] = {}
        for nid, raw in data.items():
            if isinstance(raw, Mapping):
                answers[str(nid)] = _answer_from_dict(raw)
        return cls(answers=answers)
