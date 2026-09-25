"""Typed JSON shapes of contract ``screening_review/1`` (mirrored in ``@flowaudit/ui``)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict

JsonObject = Mapping[str, object]


class ActorView(TypedDict):
    """Person as recorded in runs and events."""

    id: str
    display_name: str


class SubjectInput(TypedDict):
    """One screened name as entered."""

    subject_id: str
    name: str
    birth_date: str | None
    country: str | None
    schema: str | None
    reference: str | None


class EntryView(TypedDict):
    """A list entry, spelled as the list spells it."""

    entry_id: str
    schema: str
    name: str
    aliases: list[str]
    aliases_total: int
    birth_date: str
    countries: str
    addresses: str
    identifiers: str
    sanctions: str
    program_ids: str
    first_seen: str
    last_seen: str
    dataset: str


class BreakdownStep(TypedDict):
    """One step from the comparison forms to the score."""

    step: str
    label: str
    value: NotRequired[str]
    detail: NotRequired[str]
    points: NotRequired[float]
    kind: NotRequired[str]


class Scale(TypedDict):
    """Score range of a method."""

    min: float
    max: float


ScoreClass = TypedDict("ScoreClass", {"class": str, "label": str, "from": float})

Breakdown = TypedDict(
    "Breakdown",
    {
        "method": str,
        "scale": Scale,
        "steps": list[BreakdownStep],
        "min_score": float,
        "classes": list[ScoreClass],
        "class": str,
        "class_label": str,
        "consistent": bool,
    },
)


class DecisionView(TypedDict):
    """The last decision on a hit."""

    outcome: str
    reason: str
    four_eyes: bool
    four_eyes_source: str | None
    actor: ActorView
    at: str
    sequence: int


class SecondReviewView(TypedDict):
    """The last second review of a pending decision."""

    approve: bool
    reason: str
    actor: ActorView
    at: str
    sequence: int


class ReviewView(TypedDict):
    """Review state of a hit."""

    status: str
    status_label: str
    sequence: int
    decision: DecisionView | None
    second_review: SecondReviewView | None
    events: int


class HitView(TypedDict):
    """A hit with comparison data and score breakdown."""

    hit_id: str
    subject_id: str
    list_key: str
    list_name: str
    source_key: str | None
    entry: EntryView
    matched_name: str
    matched_field: str
    raw_score: float
    score: float
    confidence: str
    dob_conflict: bool
    country_conflict: bool
    below_min_score: bool
    indicators: list[str]
    breakdown: Breakdown
    review: NotRequired[ReviewView]


class FindingView(TypedDict):
    """What one requested list contributed for one name."""

    list_key: str
    list_name: str
    source_key: str | None
    searched: bool
    entry_count: int
    as_of: str | None
    retrieved_at: str | None
    hit_count: int
    note: str | None


class SubjectView(TypedDict):
    """Result for one screened name."""

    subject_id: str
    input: SubjectInput
    status: str
    normalized_query: str
    min_score: float
    findings: list[FindingView]
    hits: list[HitView]
    total_hits: int
    truncated: bool
    notice: str
    limitations: list[str]
    hits_before_filter: NotRequired[int]


class FreshnessView(TypedDict):
    """Age of a list state and its judgement."""

    status: str
    label: str
    age_days: float | None
    stale_after_days: float | None


class SourceView(TypedDict):
    """State (Quellenstand) of one list."""

    list: JsonObject
    kind: str
    entry_count: int
    as_of: str | None
    retrieved_at: str | None
    content_sha256: str | None
    note: str | None
    searchable: bool
    freshness: FreshnessView


class RunRequestRecord(TypedDict):
    """The request of a run as stored."""

    kind: str
    profile: dict[str, str]
    lists: list[str]
    min_score: float | None
    limit: int
    case_reference: str | None
    subjects: list[SubjectInput]


class RunResultRecord(TypedDict):
    """The result of a run as stored (never changed afterwards)."""

    subjects: list[SubjectView]
    sources: list[SourceView]


class RunSummary(TypedDict):
    """Short view of a run."""

    run_id: str
    created_at: str
    created_by: ActorView
    kind: str
    case_reference: str | None
    profile: dict[str, str]
    subject_count: int
    subjects_with_hits: int
    subjects_incomplete: int
    hit_count: int
    review_counts: dict[str, int]
    review_complete: bool
    last_sequence: int


class RunView(RunSummary):
    """Full view of a run."""

    contract: str
    request: RunRequestRecord
    sources: list[SourceView]
    subjects: list[SubjectView]
