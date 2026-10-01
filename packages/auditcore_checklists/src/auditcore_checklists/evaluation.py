"""Auswertungslogik für Prüfpfade, Entscheidungsverzweigungen und Befunde."""

from __future__ import annotations

from dataclasses import dataclass

from .answers import ExecutionState
from .errors import JsonObject
from .models import ChecklistAnswer, FindingSeverity, FindingType, NodeType
from .tree import ChecklistTree


@dataclass(frozen=True)
class FindingSummary:
    """Zusammenfassender Prüfbefund zu einem beantworteten Knoten."""

    node_id: str
    node_title: str
    befund_typ: FindingType
    finding_severity: FindingSeverity | None = None
    finding_text: str | None = None
    remark_user: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    """Gesamtergebnis der Auswertung eines Checklisten-Prüflaufs."""

    total_active_questions: int
    answered_count: int
    unanswered_count: int
    na_count: int
    progress_ratio: float
    is_complete: bool
    total_findings: int
    formal_findings: int
    financial_findings: int
    active_question_ids: tuple[str, ...] = ()
    unanswered_question_ids: tuple[str, ...] = ()
    findings: tuple[FindingSummary, ...] = ()

    def to_dict(self) -> JsonObject:
        """Ergebnis als serialisierbares Wörterbuch ausgeben."""
        return {
            "total_active_questions": self.total_active_questions,
            "answered_count": self.answered_count,
            "unanswered_count": self.unanswered_count,
            "na_count": self.na_count,
            "progress_ratio": round(self.progress_ratio, 4),
            "is_complete": self.is_complete,
            "total_findings": self.total_findings,
            "formal_findings": self.formal_findings,
            "financial_findings": self.financial_findings,
            "active_question_ids": list(self.active_question_ids),
            "unanswered_question_ids": list(self.unanswered_question_ids),
            "findings": [
                {
                    "node_id": f.node_id,
                    "node_title": f.node_title,
                    "befund_typ": f.befund_typ.value,
                    "finding_severity": f.finding_severity.value if f.finding_severity else None,
                    "finding_text": f.finding_text,
                    "remark_user": f.remark_user,
                }
                for f in self.findings
            ],
        }


def _is_decision_positive(ans: ChecklistAnswer | None) -> bool | None:
    if ans is None or ans.is_na or ans.value is None:
        return None
    val = ans.value
    if isinstance(val, bool):
        return val
    val_str = str(val).strip().upper()
    if val_str in ("JA", "TRUE", "1", "YES"):
        return True
    if val_str in ("NEIN", "FALSE", "0", "NO"):
        return False
    return None


def _collect_reachable_ids(tree: ChecklistTree, state: ExecutionState) -> list[str]:
    reachable: list[str] = []
    queue = [tree.root_id]
    visited: set[str] = set()

    while queue:
        curr_id = queue.pop(0)
        if curr_id in visited:
            continue
        visited.add(curr_id)
        reachable.append(curr_id)

        node = tree.nodes.get(curr_id)
        if not node:
            continue

        if node.node_type == NodeType.DECISION:
            ans = state.get_answer(curr_id)
            decision = _is_decision_positive(ans)
            if decision is True:
                queue.extend(c.id for c in tree.get_children(curr_id, branch="JA"))
            elif decision is False:
                queue.extend(c.id for c in tree.get_children(curr_id, branch="NEIN"))
        elif node.node_type == NodeType.HEADING:
            queue.extend(c.id for c in tree.get_children(curr_id))

    return reachable


def evaluate_checklist(tree: ChecklistTree, state: ExecutionState) -> EvaluationResult:
    """Wertet die Checkliste basierend auf dem aktuellen Erfassungsstand aus."""
    reachable_ids = _collect_reachable_ids(tree, state)
    active_questions: list[str] = []
    unanswered: list[str] = []
    findings: list[FindingSummary] = []
    answered_cnt = 0
    na_cnt = 0
    formal_cnt = 0
    financial_cnt = 0

    for nid in reachable_ids:
        node = tree.nodes[nid]
        if node.node_type not in (NodeType.QUESTION, NodeType.DECISION):
            continue
        active_questions.append(nid)
        ans = state.get_answer(nid)
        if ans is None:
            unanswered.append(nid)
            continue

        if ans.is_na:
            na_cnt += 1
            answered_cnt += 1
        elif ans.value is not None:
            answered_cnt += 1
        else:
            unanswered.append(nid)

        if ans.befund_typ == FindingType.FORMAL:
            formal_cnt += 1
            findings.append(_build_finding_summary(node.content.title, ans))
        elif ans.befund_typ == FindingType.FINANCIAL:
            financial_cnt += 1
            findings.append(_build_finding_summary(node.content.title, ans))

    total = len(active_questions)
    ratio = (answered_cnt / total) if total > 0 else 1.0
    return EvaluationResult(
        total_active_questions=total,
        answered_count=answered_cnt,
        unanswered_count=len(unanswered),
        na_count=na_cnt,
        progress_ratio=ratio,
        is_complete=(len(unanswered) == 0),
        total_findings=len(findings),
        formal_findings=formal_cnt,
        financial_findings=financial_cnt,
        active_question_ids=tuple(active_questions),
        unanswered_question_ids=tuple(unanswered),
        findings=tuple(findings),
    )


def _build_finding_summary(title: str, ans: ChecklistAnswer) -> FindingSummary:
    return FindingSummary(
        node_id=ans.node_id,
        node_title=title,
        befund_typ=ans.befund_typ,
        finding_severity=ans.finding_severity,
        finding_text=ans.finding_text,
        remark_user=ans.remark_user,
    )
