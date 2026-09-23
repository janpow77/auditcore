"""Transparent fuzzy match components (optional extra ``fuzzy`` = rapidfuzz).

The selection reproduces the source strategy: every candidate is scored with
each profile scorer (``token_set_ratio``, ``WRatio``), per scorer the best
``per_scorer_limit`` hits at or above ``min_score`` are considered, and the
highest single score wins; on ties the earlier candidate and the earlier
scorer win. Every component score is returned so that a reviewer can see why
a candidate was proposed. Thresholds are explicit arguments or named
profiles; they are fachliche settings, not general defaults.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .errors import DependencyError, ProfileError
from .profiles import Profile


def _rapidfuzz() -> tuple[Any, Any]:
    try:
        from rapidfuzz import fuzz, process
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für unscharfe Vergleiche ist 'auditcore_entity_matching[fuzzy]' zu installieren."
        ) from exc
    return fuzz, process


@dataclass(frozen=True)
class Candidate:
    """A candidate record; ``normalized`` must use the same profile as the query."""

    id: str | int
    normalized: str


@dataclass(frozen=True)
class MatchResult:
    """Best candidate with its score and the evidence of every scorer."""

    candidate_id: str | int
    score: float
    scorer: str
    components: dict[str, float]
    profile: dict[str, str]


def _usable(query: str, min_token_length: int) -> bool:
    return bool(query) and any(len(t) >= min_token_length for t in query.split())


def best_match(
    query: str,
    candidates: Sequence[Candidate],
    profile: Profile,
    *,
    min_score: float,
) -> MatchResult | None:
    """Highest-scoring candidate at or above ``min_score`` or ``None``.

    ``min_score`` is mandatory; the source used 75 for entity resolution
    (``profile.resolution.fuzzy_threshold``), which remains a named setting.
    """
    rules = profile.resolution
    if rules is None:
        raise ProfileError(f"Profil {profile.id} enthält keine Auswahlregeln.")
    if not _usable(query, rules.min_token_length) or not candidates:
        return None
    fuzz, process = _rapidfuzz()
    strings = [c.normalized or "" for c in candidates]
    best_index: int | None = None
    best_score = 0.0
    best_scorer = ""
    for name in rules.scorers:
        hits = process.extract(
            query,
            strings,
            scorer=getattr(fuzz, name),
            limit=rules.per_scorer_limit,
            score_cutoff=min_score,
        )
        for _value, score, index in hits:
            if score > best_score:
                best_score, best_index, best_scorer = float(score), int(index), name
    if best_index is None or best_score < min_score:
        return None
    chosen = strings[best_index]
    components = {name: float(getattr(fuzz, name)(query, chosen)) for name in rules.scorers}
    return MatchResult(
        candidates[best_index].id, round(best_score, 1), best_scorer, components, profile.reference
    )


def classify(
    score: float,
    profile: Profile,
    query_normalized: str | None = None,
    matched_normalized: str | None = None,
) -> str:
    """Score class ``exact``/``high``/``medium``/``low`` of a screening profile.

    A token subset (100 by ``token_set_ratio``) is only ``exact`` if the token
    counts agree or the ``token_sort_ratio`` reaches the profile limit.
    """
    rules = profile.classification
    if rules is None:
        raise ProfileError(f"Profil {profile.id} enthält keine Klassengrenzen.")
    if score >= rules.exact_from:
        if query_normalized is not None and matched_normalized is not None:
            fuzz, _ = _rapidfuzz()
            same_count = len(query_normalized.split()) == len(matched_normalized.split())
            sort_ratio = fuzz.token_sort_ratio(query_normalized, matched_normalized)
            return "exact" if same_count or sort_ratio >= rules.exact_token_sort_from else "high"
        return "exact"
    if score >= rules.high_from:
        return "high"
    if score >= rules.medium_from:
        return "medium"
    return "low"
