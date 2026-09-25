"""Review state of hits, derived from the log, and the rules of the decision workflow.

States: ``open`` → ``confirmed`` / ``dismissed`` / ``deferred`` directly, or
via ``pending_second_review`` when the decision needs a second person
(Vier-Augen-Prinzip). ``deferred`` can be decided again; ``confirmed`` and
``dismissed`` are final. A rejected second review returns the hit to
``open``. The second reviewer must be a different person than the one who
proposed the decision.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import TypedDict

from ._types import ActorView, DecisionView, ReviewView, SecondReviewView
from .contract import (
    FINAL_STATUSES,
    STATUS_OPEN,
    STATUS_PENDING,
    Actor,
    DecisionRequest,
    SecondReviewRequest,
    conflict,
)
from .store import ReviewEvent

EVENT_RUN_CREATED = "run_created"
EVENT_DECISION = "decision_recorded"
EVENT_SECOND_REVIEW = "second_review_recorded"

STATUS_LABELS = {
    "open": "offen",
    "pending_second_review": "wartet auf Zweitprüfung",
    "confirmed": "bestätigt",
    "dismissed": "verworfen",
    "deferred": "zurückgestellt",
}


@dataclass
class HitReview:
    """Current review state of one hit."""

    status: str = STATUS_OPEN
    sequence: int = 0
    decision: DecisionView | None = None
    second_review: SecondReviewView | None = None
    events: int = 0

    def to_dict(self) -> ReviewView:
        """JSON view."""
        return {
            "status": self.status,
            "status_label": STATUS_LABELS[self.status],
            "sequence": self.sequence,
            "decision": self.decision,
            "second_review": self.second_review,
            "events": self.events,
        }


@dataclass
class ReviewState:
    """States of all hits of a run plus the run-wide last sequence."""

    hits: dict[str, HitReview] = field(default_factory=dict)
    last_sequence: int = 0

    def of(self, hit_id: str) -> HitReview:
        """State of a hit (``open`` if never touched)."""
        return self.hits.get(hit_id) or HitReview()


class DecisionData(TypedDict):
    """Event data of ``decision_recorded``."""

    outcome: str
    reason: str
    four_eyes: bool
    four_eyes_source: str | None


class SecondReviewData(TypedDict):
    """Event data of ``second_review_recorded``."""

    approve: bool
    reason: str
    outcome: str


def _text(event: ReviewEvent, key: str) -> str:
    value = event.data.get(key)
    return value if isinstance(value, str) else ""


def _flag(event: ReviewEvent, key: str) -> bool:
    return event.data.get(key) is True


def _actor(event: ReviewEvent) -> ActorView:
    return {"id": event.actor["id"], "display_name": event.actor["display_name"]}


def _decision_view(event: ReviewEvent) -> DecisionView:
    source = event.data.get("four_eyes_source")
    return {
        "outcome": _text(event, "outcome"),
        "reason": _text(event, "reason"),
        "four_eyes": _flag(event, "four_eyes"),
        "four_eyes_source": source if isinstance(source, str) else None,
        "actor": _actor(event),
        "at": event.at,
        "sequence": event.sequence,
    }


def _apply(state: HitReview, event: ReviewEvent) -> None:
    state.sequence = event.sequence
    state.events += 1
    if event.type == EVENT_DECISION:
        state.decision = _decision_view(event)
        state.second_review = None
        four_eyes = _flag(event, "four_eyes")
        state.status = STATUS_PENDING if four_eyes else _text(event, "outcome")
    elif event.type == EVENT_SECOND_REVIEW:
        approved = _flag(event, "approve")
        state.second_review = {
            "approve": approved,
            "reason": _text(event, "reason"),
            "actor": _actor(event),
            "at": event.at,
            "sequence": event.sequence,
        }
        state.status = _text(event, "outcome") if approved else STATUS_OPEN


def fold(events: Iterable[ReviewEvent]) -> ReviewState:
    """Derive the review state from the log."""
    state = ReviewState()
    for event in events:
        state.last_sequence = event.sequence
        if event.hit_id is None:
            continue
        hit = state.hits.setdefault(event.hit_id, HitReview())
        _apply(hit, event)
    return state


def _check_expected(hit: HitReview, expected: int | None) -> None:
    if expected is not None and expected != hit.sequence:
        raise conflict(
            "stale_state",
            "Der Treffer wurde inzwischen von anderer Seite bearbeitet. Bitte neu laden.",
            expected_sequence=expected,
            current_sequence=hit.sequence,
        )


def decision_data(
    hit: HitReview, request: DecisionRequest, *, four_eyes_outcomes: Sequence[str]
) -> DecisionData:
    """Check a decision against the current state; return the event data."""
    _check_expected(hit, request.expected_sequence)
    if hit.status in FINAL_STATUSES:
        raise conflict(
            "already_decided",
            f"Der Treffer ist bereits abschließend {STATUS_LABELS[hit.status]}.",
            status=hit.status,
        )
    if hit.status == STATUS_PENDING:
        raise conflict(
            "second_review_pending",
            "Für diesen Treffer steht die Zweitprüfung aus; erst danach ist eine neue "
            "Entscheidung möglich.",
        )
    required = request.outcome in four_eyes_outcomes
    four_eyes = request.four_eyes or required
    source = "policy" if required else ("requested" if four_eyes else None)
    return {
        "outcome": request.outcome,
        "reason": request.reason,
        "four_eyes": four_eyes,
        "four_eyes_source": source,
    }


def second_review_data(
    hit: HitReview, request: SecondReviewRequest, actor: Actor
) -> SecondReviewData:
    """Check a second review against the pending decision; return the event data."""
    _check_expected(hit, request.expected_sequence)
    if hit.status != STATUS_PENDING or hit.decision is None:
        raise conflict(
            "no_pending_decision", "Für diesen Treffer wartet keine Entscheidung auf Zweitprüfung."
        )
    if hit.decision["actor"]["id"] == actor.id:
        raise conflict(
            "same_person",
            "Die Zweitprüfung muss eine andere Person vornehmen als die, die entschieden hat.",
        )
    return {
        "approve": request.approve,
        "reason": request.reason,
        "outcome": hit.decision["outcome"],
    }
