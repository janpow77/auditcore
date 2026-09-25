"""Execute a run request with the library and turn results into review views.

Sanctions runs use :func:`auditcore_registry_sources.screen` (rapidfuzz
profiles), PEP runs use :func:`auditcore_registry_sources.pep_bulk_screen`
(token profiles). Both yield the same per-subject view: every requested list
has a finding with its state; a list without inventory is *not searched*.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

from auditcore_entity_matching import Profile as NormalizationProfile
from auditcore_entity_matching import load_profile as load_normalization
from auditcore_entity_matching import normalize

from ..bulk_screening import BulkHit, pep_bulk_screen
from ..errors import ProfileError, QueryError
from ..model import ListSnapshot
from ..profiles import RegistryProfile, available_profiles, load_profile, recommended_profile
from ..screening import NOT_SEARCHED_NOTE, ScreeningHit, ScreeningSettings, screen
from .breakdown import entry_view, pep_breakdown, sanctions_breakdown
from .contract import KIND_PEP, KIND_SANCTIONS, RunRequest, Subject, invalid

ALGORITHMS = {"rapidfuzz_token_set": KIND_SANCTIONS, "token_f1": KIND_PEP}
PURPOSES = {KIND_SANCTIONS: "sanctions_screening", KIND_PEP: "pep_bulk"}
PEP_NOTICE = (
    "Ein Treffer ist ein Prüfhinweis auf eine möglicherweise politisch exponierte Person, "
    "keine Feststellung. Identität, Funktion und Zeitraum sind am Vorgang zu verifizieren."
)
NO_HIT_LIMITATION = (
    "Ein Ergebnis ohne Treffer belegt keine Unbedenklichkeit; es bezieht sich nur auf die "
    "abgefragten Listen in ihrem angegebenen Stand."
)


def hit_id(subject_id: str, list_key: str, entry_id: str) -> str:
    """Stable, URL-safe id of a hit within a run."""
    digest = hashlib.sha256(f"{subject_id}\x1f{list_key}\x1f{entry_id}".encode()).hexdigest()
    return f"h{digest[:16]}"


def _recommended(kind: str) -> tuple[str, str] | None:
    try:
        profile = recommended_profile(PURPOSES[kind])
    except ProfileError:
        return None
    return profile.id, profile.version


def profile_views() -> list[dict[str, Any]]:
    """Screening profiles usable by the review API, with the recommendation flag."""
    recommended = {_recommended(kind) for kind in PURPOSES}
    views = []
    for profile_id, version in available_profiles():
        profile = load_profile(profile_id, version)
        kind = ALGORITHMS.get(str(profile.settings.get("algorithm")))
        if profile.kind != "screening" or kind is None:
            continue
        views.append(
            {
                **profile.reference,
                "kind": kind,
                "legal_status": profile.legal_status,
                "default_min_score": float(profile.setting("default_min_score")),
                "scale": {"min": 0.0, "max": 1.0 if kind == KIND_PEP else 100.0},
                "recommended": (profile.id, profile.version) in recommended,
            }
        )
    return views


def resolve_profile(request: RunRequest) -> RegistryProfile:
    """Load the explicitly named profile and check it fits the run kind."""
    try:
        profile = load_profile(request.profile_id, request.profile_version)
    except ProfileError as exc:
        raise invalid(str(exc), field="profile") from exc
    kind = ALGORITHMS.get(str(profile.settings.get("algorithm")))
    if profile.kind != "screening" or kind != request.kind:
        raise invalid(
            f"Profil {profile.id} {profile.version} passt nicht zur Prüfart „{request.kind}“.",
            field="profile",
        )
    return profile


def _finding(snapshot: ListSnapshot, searched: bool, hit_count: int) -> dict[str, Any]:
    return {
        "list_key": snapshot.list.key,
        "list_name": snapshot.list.name,
        "source_key": snapshot.list.source_key,
        "searched": searched,
        "entry_count": len(snapshot.entries),
        "as_of": snapshot.as_of,
        "retrieved_at": snapshot.retrieved_at,
        "hit_count": hit_count,
        "note": snapshot.note if searched else (snapshot.note or NOT_SEARCHED_NOTE),
    }


def _status(hit_count: int, findings: Sequence[dict[str, Any]]) -> str:
    searched = [f for f in findings if f["searched"]]
    if hit_count:
        return "HITS"
    if not searched:
        return "NOT_SEARCHED"
    return "INCOMPLETE" if len(searched) < len(findings) else "NO_HITS"


def _subject_view(subject: Subject, **values: Any) -> dict[str, Any]:
    return {"subject_id": subject.subject_id, "input": subject.to_dict(), **values}


def _sanctions_hit(
    hit: ScreeningHit,
    subject: Subject,
    settings: ScreeningSettings,
    normalized_query: str,
    min_score: float,
) -> dict[str, Any]:
    return {
        "hit_id": hit_id(subject.subject_id, hit.list_key, hit.entry.entry_id),
        "subject_id": subject.subject_id,
        "list_key": hit.list_key,
        "list_name": hit.list_name,
        "source_key": hit.source_key,
        "entry": entry_view(hit.entry),
        "matched_name": hit.matched_name,
        "matched_field": hit.matched_field,
        "raw_score": hit.raw_score,
        "score": hit.score,
        "confidence": hit.confidence,
        "dob_conflict": hit.dob_conflict,
        "country_conflict": hit.country_conflict,
        "below_min_score": hit.below_min_score,
        "indicators": list(hit.indicators),
        "breakdown": sanctions_breakdown(
            hit, settings, normalized_query=normalized_query, min_score=min_score
        ),
    }


def _sanctions_subject(
    subject: Subject,
    snapshots: Sequence[ListSnapshot],
    profile: RegistryProfile,
    settings: ScreeningSettings,
    request: RunRequest,
) -> dict[str, Any]:
    try:
        result = screen(
            subject.name,
            snapshots,
            profile,
            limit=request.limit,
            min_score=request.min_score,
            schema=subject.schema,
            birth_date=subject.birth_date,
            country=subject.country,
        )
    except QueryError as exc:
        raise invalid(f"{subject.subject_id}: {exc}", subject=subject.subject_id) from exc
    hits = [
        _sanctions_hit(hit, subject, settings, result.normalized_query, result.min_score)
        for hit in result.hits
    ]
    return _subject_view(
        subject,
        status=result.status,
        normalized_query=result.normalized_query,
        min_score=result.min_score,
        findings=[f.to_dict() for f in result.findings],
        hits=hits,
        total_hits=result.total_hits,
        truncated=result.truncated,
        notice=result.notice,
        limitations=list(result.limitations),
    )


def _pep_threshold(request: RunRequest, profile: RegistryProfile) -> float:
    value = request.min_score
    if value is None:
        return float(profile.setting("default_min_score"))
    if not 0 < value <= 1:
        raise invalid("Der Mindestwert der PEP-Prüfung liegt über 0 und höchstens bei 1.")
    return value


def _pep_hit(
    hit: BulkHit,
    subject: Subject,
    snapshot: ListSnapshot,
    profile: RegistryProfile,
    normalization: NormalizationProfile,
    threshold: float,
) -> dict[str, Any]:
    return {
        "hit_id": hit_id(subject.subject_id, snapshot.list.key, hit.entry.entry_id),
        "subject_id": subject.subject_id,
        "list_key": snapshot.list.key,
        "list_name": snapshot.list.name,
        "source_key": snapshot.list.source_key,
        "entry": entry_view(hit.entry),
        "matched_name": hit.matched_name,
        "matched_field": "alias" if hit.via_alias else "name",
        "raw_score": hit.score,
        "score": hit.score,
        "confidence": hit.method,
        "dob_conflict": False,
        "country_conflict": False,
        "below_min_score": False,
        "indicators": ["alias_match"] if hit.via_alias else [],
        "breakdown": pep_breakdown(
            hit,
            profile,
            normalization,
            query=subject.name,
            country=subject.country,
            min_score=threshold,
        ),
    }


def _pep_subject(
    subject: Subject,
    snapshots: Sequence[ListSnapshot],
    profile: RegistryProfile,
    request: RunRequest,
) -> dict[str, Any]:
    ref = profile.setting("normalization")
    normalization = load_normalization(ref["id"], ref["version"])
    threshold = _pep_threshold(request, profile)
    findings: list[dict[str, Any]] = []
    hits: list[dict[str, Any]] = []
    for snapshot in snapshots:
        if not snapshot.entries:
            findings.append(_finding(snapshot, False, 0))
            continue
        result = pep_bulk_screen(
            subject.name,
            snapshot.entries,
            profile,
            country=subject.country,
            min_score=threshold,
            as_of=snapshot.as_of,
        )
        findings.append(_finding(snapshot, True, len(result.hits)))
        hits.extend(
            _pep_hit(hit, subject, snapshot, profile, normalization, threshold)
            for hit in result.hits
        )
    hits.sort(key=lambda h: h["score"], reverse=True)
    status = _status(len(hits), findings)
    limitations = [NO_HIT_LIMITATION] if status in ("NO_HITS", "INCOMPLETE") else []
    return _subject_view(
        subject,
        status=status,
        normalized_query=normalize(subject.name, normalization),
        min_score=threshold,
        findings=findings,
        hits=hits[: request.limit],
        total_hits=len(hits),
        truncated=len(hits) > request.limit,
        notice=PEP_NOTICE,
        limitations=limitations,
    )


def execute(
    request: RunRequest, profile: RegistryProfile, snapshots: Sequence[ListSnapshot]
) -> list[dict[str, Any]]:
    """Screen every subject of the request; one view per subject."""
    if request.kind == KIND_PEP:
        return [_pep_subject(s, snapshots, profile, request) for s in request.subjects]
    settings = ScreeningSettings.from_profile(profile)
    return [_sanctions_subject(s, snapshots, profile, settings, request) for s in request.subjects]
