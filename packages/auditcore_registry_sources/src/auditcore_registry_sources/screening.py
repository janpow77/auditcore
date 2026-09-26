"""Name screening against sanctions list snapshots (optional extra ``fuzzy``).

Reproduces the characterized method of audit_designer and flowworkshop as
explicit profiles: normalisation through ``auditcore_entity_matching``
(profile named in the screening profile), ``rapidfuzz`` token-set ratio over
names *and* aliases, the best comparison form per entry, a deterministic
date-of-birth/country adjustment and the score classes of the normalisation
profile.

**A hit is an indication for manual review, never a finding.** Every hit
carries the matched spelling, the raw and the adjusted score, the
adjustments with reasons and uncertainty indicators. Every requested list
has a finding: a list without inventory is *not searched* and must not look
like a list without hits. A result without hits proves nothing about lists
that were not searched (status ``INCOMPLETE``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ._screening_index import EntryLike, ListIndex, ScreeningHit
from ._screening_rules import (
    Adjustment,
    LimitRule,
    ScreeningSettings,
    adjust_score,
    birth_years,
    split_multivalue,
)
from ._types import JsonObject, JsonValue
from .errors import QueryError
from .model import ListSnapshot
from .profiles import RegistryProfile

__all__ = [
    "NOT_SEARCHED_NOTE",
    "Adjustment",
    "EntryLike",
    "LimitRule",
    "ListFinding",
    "ListIndex",
    "ScreeningHit",
    "ScreeningResult",
    "ScreeningSettings",
    "adjust_score",
    "birth_years",
    "screen",
    "split_multivalue",
    "validate_query",
]

NOT_SEARCHED_NOTE = (
    "Für diese Liste liegt kein Bestand vor. Sie wurde nicht abgefragt; das Ergebnis "
    "sagt über sie nichts aus."
)


@dataclass(frozen=True)
class ListFinding:
    """What one requested list contributed; ``searched`` is the decisive value."""

    list_key: str
    list_name: str
    source_key: str | None
    searched: bool
    entry_count: int
    as_of: str | None
    retrieved_at: str | None
    hit_count: int
    note: str | None = None

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "list_key": self.list_key,
            "list_name": self.list_name,
            "source_key": self.source_key,
            "searched": self.searched,
            "entry_count": self.entry_count,
            "as_of": self.as_of,
            "retrieved_at": self.retrieved_at,
            "hit_count": self.hit_count,
            "note": self.note,
        }


@dataclass(frozen=True)
class ScreeningResult:
    """Screening result contract (``auditcore_registry_sources.screening/1``)."""

    status: str
    query: str
    normalized_query: str
    min_score: float
    limit: int
    profile: Mapping[str, str]
    normalization: Mapping[str, str]
    findings: tuple[ListFinding, ...]
    hits: tuple[ScreeningHit, ...]
    total_hits: int
    truncated: bool
    notice: str
    limitations: tuple[str, ...]
    decisions: tuple[Mapping[str, JsonValue], ...] = field(default_factory=tuple)

    @property
    def coverage_complete(self) -> bool:
        """True only if every requested list was searched."""
        return all(f.searched for f in self.findings)

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "contract": "auditcore_registry_sources.screening/1",
            "status": self.status,
            "query": self.query,
            "normalized_query": self.normalized_query,
            "min_score": self.min_score,
            "limit": self.limit,
            "profile": dict(self.profile),
            "normalization": dict(self.normalization),
            "coverage_complete": self.coverage_complete,
            "findings": [f.to_dict() for f in self.findings],
            "hits": [h.to_dict() for h in self.hits],
            "total_hits": self.total_hits,
            "truncated": self.truncated,
            "notice": self.notice,
            "limitations": list(self.limitations),
            "decisions": [dict(d) for d in self.decisions],
        }


def validate_query(
    settings: ScreeningSettings,
    name: str,
    *,
    min_score: float | None,
    schema: str | None,
) -> tuple[str, float, str | None]:
    """Check the input against the profile; return name, minimum score and schema."""
    if not isinstance(name, str) or not name.strip():
        raise QueryError("Pflichtangabe fehlt: Name.")
    stripped = name.strip()
    if len(stripped) < settings.min_query_length:
        raise QueryError(
            f"Bitte mindestens {settings.min_query_length} Zeichen angeben; kürzere Eingaben "
            "treffen so viele Einträge, dass das Ergebnis nichts aussagt."
        )
    value = settings.default_min_score if min_score is None else float(min_score)
    low, high = settings.min_score_range
    if not low <= value <= high:
        raise QueryError(f"Der Mindestwert liegt zwischen {low:g} und {high:g}.")
    chosen = None
    if schema:
        allowed = {s.casefold(): s for s in settings.entity_schemas}
        chosen = allowed.get(schema.casefold())
        if chosen is None:
            raise QueryError(
                f"Unbekannter Eintragstyp; zulässig: {', '.join(settings.entity_schemas)}."
            )
    return stripped, value, chosen


def _search_snapshot(
    snapshot: ListSnapshot,
    settings: ScreeningSettings,
    query: str,
    *,
    limit: int,
    min_score: float,
    schema: str | None,
    birth_date: str | None,
    country: str | None,
) -> tuple[ListFinding, list[ScreeningHit], bool]:
    """Finding, hits and truncation flag of one list; a list without inventory is not searched."""
    sanctions_list = snapshot.list
    if not snapshot.entries:
        finding = ListFinding(
            sanctions_list.key,
            sanctions_list.name,
            sanctions_list.source_key,
            searched=False,
            entry_count=0,
            as_of=snapshot.as_of,
            retrieved_at=snapshot.retrieved_at,
            hit_count=0,
            note=snapshot.note or NOT_SEARCHED_NOTE,
        )
        return finding, [], False
    index = ListIndex(
        settings,
        snapshot.entries,
        list_key=sanctions_list.key,
        list_name=sanctions_list.name,
        source_key=sanctions_list.source_key,
    )
    found, cut = index.search_detailed(
        query,
        limit=limit,
        min_score=min_score,
        schema=schema,
        birth_date=birth_date,
        country=country,
    )
    finding = ListFinding(
        sanctions_list.key,
        sanctions_list.name,
        sanctions_list.source_key,
        searched=True,
        entry_count=len(snapshot.entries),
        as_of=snapshot.as_of,
        retrieved_at=snapshot.retrieved_at,
        hit_count=len(found),
        note=snapshot.note,
    )
    return finding, found, cut


def _status(hits: Sequence[ScreeningHit], findings: Sequence[ListFinding]) -> str:
    """``HITS``, ``NOT_SEARCHED``, ``INCOMPLETE`` or ``NO_HITS``."""
    searched = [f for f in findings if f.searched]
    if hits:
        return "HITS"
    if not searched:
        return "NOT_SEARCHED"
    if len(searched) < len(findings):
        return "INCOMPLETE"
    return "NO_HITS"


def screen(
    name: str,
    snapshots: Sequence[ListSnapshot],
    profile: RegistryProfile,
    *,
    limit: int = 15,
    min_score: float | None = None,
    schema: str | None = None,
    birth_date: str | None = None,
    country: str | None = None,
) -> ScreeningResult:
    """Screen a name against list snapshots under an explicitly chosen profile."""
    settings = ScreeningSettings.from_profile(profile)
    if limit < 1:
        raise QueryError("Das Trefferlimit muss mindestens 1 sein.")
    query, value, chosen_schema = validate_query(settings, name, min_score=min_score, schema=schema)
    per_list = settings.per_list_limit.apply(limit)
    list_truncated = False
    findings: list[ListFinding] = []
    hits: list[ScreeningHit] = []
    for snapshot in snapshots:
        finding, found, cut = _search_snapshot(
            snapshot,
            settings,
            query,
            limit=per_list,
            min_score=value,
            schema=chosen_schema,
            birth_date=birth_date,
            country=country,
        )
        list_truncated = list_truncated or cut
        findings.append(finding)
        hits.extend(found)
    hits.sort(key=lambda h: h.score, reverse=True)
    status = _status(hits, findings)
    limitations = list(settings.limitations)
    if status in ("NO_HITS", "INCOMPLETE"):
        limitations.append(
            "Ein Ergebnis ohne Treffer belegt keine Unbedenklichkeit; es bezieht sich nur auf "
            "die abgefragten Listen in ihrem angegebenen Stand."
        )
    return ScreeningResult(
        status=status,
        query=query,
        normalized_query=settings.norm(query),
        min_score=value,
        limit=limit,
        profile=profile.reference,
        normalization=settings.normalization.reference,
        findings=tuple(findings),
        hits=tuple(hits[:limit]),
        total_hits=len(hits),
        truncated=list_truncated or len(hits) > limit,
        notice=settings.notice,
        limitations=tuple(limitations),
        decisions=profile.decisions,
    )
