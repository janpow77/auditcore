"""JSON views of runs, hit filters, summaries and the log."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import NotRequired, TypedDict

from ._types import HitView, ReviewView, RunSummary, RunView, SubjectView
from .contract import CONTRACT, REVIEW_STATUSES, invalid, split_filter
from .review import (
    EVENT_DECISION,
    EVENT_RUN_CREATED,
    EVENT_SECOND_REVIEW,
    STATUS_LABELS,
    ReviewState,
)
from .store import EventView, ReviewEvent, StoredRun

EVENT_LABELS = {
    EVENT_RUN_CREATED: "Prüflauf angelegt",
    EVENT_DECISION: "Entscheidung erfasst",
    EVENT_SECOND_REVIEW: "Zweitprüfung erfasst",
}
CONFIDENCES = ("exact", "high", "medium", "low", "fuzzy")


class HitContext(TypedDict):
    """Names a log entry refers to."""

    subject_name: str
    entry_name: str
    list_name: str


class LogEntry(EventView):
    """Log entry with labels for display."""

    type_label: str
    hit: NotRequired[HitContext | None]
    outcome_label: NotRequired[str]


class LogView(TypedDict):
    """The review log of a run."""

    contract: str
    run_id: str
    events: list[LogEntry]


@dataclass(frozen=True)
class HitFilter:
    """Server-side filter of hits; empty values do not filter."""

    statuses: tuple[str, ...] = ()
    lists: tuple[str, ...] = ()
    subjects: tuple[str, ...] = ()
    confidences: tuple[str, ...] = ()
    min_score: float | None = None

    @classmethod
    def from_query(cls, query: Mapping[str, str]) -> HitFilter:
        """Parse ``status``, ``list``, ``subject``, ``confidence`` and ``min_score``."""
        min_score = query.get("min_score")
        try:
            value = float(min_score) if min_score not in (None, "") else None
        except ValueError as exc:
            raise invalid("„min_score“ ist eine Zahl.", field="min_score") from exc
        return cls(
            statuses=split_filter(query.get("status"), REVIEW_STATUSES, "status"),
            lists=tuple(v for v in (query.get("list") or "").split(",") if v),
            subjects=tuple(v for v in (query.get("subject") or "").split(",") if v),
            confidences=split_filter(query.get("confidence"), CONFIDENCES, "confidence"),
            min_score=value,
        )

    def accepts(self, hit: HitView, review: ReviewView) -> bool:
        """True if the hit with its review state passes every set criterion."""
        checks = (
            (self.statuses, review["status"]),
            (self.lists, hit["list_key"]),
            (self.subjects, hit["subject_id"]),
            (self.confidences, hit["confidence"]),
        )
        if any(allowed and value not in allowed for allowed, value in checks):
            return False
        return self.min_score is None or hit["score"] >= self.min_score


def _counts(reviews: Iterable[ReviewView]) -> dict[str, int]:
    counts = dict.fromkeys(REVIEW_STATUSES, 0)
    for review in reviews:
        counts[review["status"]] += 1
    return counts


def summary(run: StoredRun, state: ReviewState) -> RunSummary:
    """Short view of a run for lists."""
    hits = [h for subject in run.result["subjects"] for h in subject["hits"]]
    reviews = [state.of(h["hit_id"]).to_dict() for h in hits]
    counts = _counts(reviews)
    open_count = counts["open"] + counts["pending_second_review"] + counts["deferred"]
    statuses = [s["status"] for s in run.result["subjects"]]
    return {
        "run_id": run.run_id,
        "created_at": run.created_at,
        "created_by": run.created_by,
        "kind": run.kind,
        "case_reference": run.request["case_reference"],
        "profile": dict(run.request["profile"]),
        "subject_count": len(statuses),
        "subjects_with_hits": statuses.count("HITS"),
        "subjects_incomplete": sum(s in ("INCOMPLETE", "NOT_SEARCHED") for s in statuses),
        "hit_count": len(reviews),
        "review_counts": counts,
        "review_complete": open_count == 0,
        "last_sequence": state.last_sequence,
    }


def _with_review(hit: HitView, state: ReviewState) -> HitView:
    view = hit.copy()
    view["review"] = state.of(hit["hit_id"]).to_dict()
    return view


def run_view(run: StoredRun, state: ReviewState, hit_filter: HitFilter) -> RunView:
    """Full run with subjects, filtered hits and their review state."""
    subjects: list[SubjectView] = []
    for subject in run.result["subjects"]:
        hits = [_with_review(h, state) for h in subject["hits"]]
        view = subject.copy()
        view["hits"] = [h for h in hits if "review" in h and hit_filter.accepts(h, h["review"])]
        view["hits_before_filter"] = len(hits)
        subjects.append(view)
    head = summary(run, state)
    return {
        **head,
        "contract": CONTRACT,
        "request": run.request,
        "sources": list(run.result["sources"]),
        "subjects": subjects,
    }


def _hit_context(run: StoredRun) -> dict[str, HitContext]:
    context: dict[str, HitContext] = {}
    for subject in run.result["subjects"]:
        for hit in subject["hits"]:
            context[hit["hit_id"]] = {
                "subject_name": subject["input"]["name"],
                "entry_name": hit["entry"]["name"],
                "list_name": hit["list_name"],
            }
    return context


def log_view(run: StoredRun, events: Sequence[ReviewEvent]) -> LogView:
    """The review log with labels and the names the hits refer to."""
    context = _hit_context(run)
    items: list[LogEntry] = []
    for event in events:
        base = event.to_dict()
        item: LogEntry = {
            "run_id": base["run_id"],
            "sequence": base["sequence"],
            "type": base["type"],
            "at": base["at"],
            "actor": base["actor"],
            "hit_id": base["hit_id"],
            "data": base["data"],
            "type_label": EVENT_LABELS.get(event.type, event.type),
        }
        if event.hit_id is not None:
            item["hit"] = context.get(event.hit_id)
        outcome = event.data.get("outcome")
        if isinstance(outcome, str):
            item["outcome_label"] = STATUS_LABELS.get(outcome, outcome)
        items.append(item)
    return {"contract": CONTRACT, "run_id": run.run_id, "events": items}


def hit_view(run: StoredRun, state: ReviewState, hit_id: str) -> HitView:
    """One hit with its current review state."""
    for subject in run.result["subjects"]:
        for hit in subject["hits"]:
            if hit["hit_id"] == hit_id:
                return _with_review(hit, state)
    raise KeyError(hit_id)
