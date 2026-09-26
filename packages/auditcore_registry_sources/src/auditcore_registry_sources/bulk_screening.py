"""flowinvoice screening variants: local ``difflib`` list check and PEP bulk token matching.

Both are separate profiles because they differ from the rapidfuzz method of
audit_designer/flowworkshop in scale (0–1), normalisation and thresholds
(``HUMAN_DECISION_REQUIRED`` in the profiles). They need only the standard
library.

Deliberate differences to the originals: an unavailable data set yields
status ``NOT_SEARCHED`` instead of ``is_clean=True``; the data state is the
state stated by the caller (for example the list's ``last_change``), never
the time of loading.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher

from auditcore_entity_matching import Profile as NormalizationProfile
from auditcore_entity_matching import load_profile as load_normalization
from auditcore_entity_matching import normalize

from ._types import JsonObject
from .errors import ProfileError, QueryError
from .model import ListEntry
from .profiles import RegistryProfile


@dataclass(frozen=True)
class BulkHit:
    """A hit of a bulk variant (score 0–1)."""

    list_key: str
    entry: ListEntry
    matched_name: str
    via_alias: bool
    score: float
    method: str

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "list_key": self.list_key,
            "entry": self.entry.to_dict(),
            "matched_name": self.matched_name,
            "via_alias": self.via_alias,
            "score": self.score,
            "method": self.method,
        }


@dataclass(frozen=True)
class BulkResult:
    """Result of a bulk variant with explicit status and data state."""

    status: str
    query: str
    min_score: float
    hits: tuple[BulkHit, ...]
    entries_checked: int
    as_of: str | None
    profile: Mapping[str, str]
    note: str | None = None

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "status": self.status,
            "query": self.query,
            "min_score": self.min_score,
            "hits": [h.to_dict() for h in self.hits],
            "entries_checked": self.entries_checked,
            "as_of": self.as_of,
            "profile": dict(self.profile),
            "note": self.note,
        }


def _check_query(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise QueryError("Pflichtangabe fehlt: Name.")
    return name


def _not_searched(
    profile: RegistryProfile, query: str, min_score: float, as_of: str | None
) -> BulkResult:
    return BulkResult(
        status="NOT_SEARCHED",
        query=query,
        min_score=min_score,
        hits=(),
        entries_checked=0,
        as_of=as_of,
        profile=profile.reference,
        note="Kein Datenbestand übergeben; es wurde nichts geprüft.",
    )


def difflib_score(query: str, candidate: str) -> float:
    """``SequenceMatcher`` ratio of the lower-cased, stripped strings (flowinvoice)."""
    return SequenceMatcher(None, query.lower().strip(), candidate.lower().strip()).ratio()


def local_screen(
    name: str,
    entries: Sequence[ListEntry],
    profile: RegistryProfile,
    *,
    min_score: float | None = None,
    as_of: str | None = None,
) -> BulkResult:
    """``check_entity_local``: best ratio over name and aliases per entry, at/above the minimum."""
    profile.require_kind("screening")
    if profile.setting("algorithm") != "difflib_ratio":
        raise ProfileError(f"Profil {profile.id} ist kein difflib-Profil.")
    query = _check_query(name)
    threshold = float(profile.setting("default_min_score") if min_score is None else min_score)
    if not entries:
        return _not_searched(profile, query, threshold, as_of)
    exact_from = float(profile.setting("exact_from"))
    digits = int(profile.setting("score_digits"))
    hits = []
    for entry in entries:
        best, best_name = 0.0, entry.name
        for candidate in (entry.name, *entry.aliases):
            if not candidate:
                continue
            value = difflib_score(query, candidate)
            if value > best:
                best, best_name = value, candidate
        if best >= threshold:
            hits.append(
                BulkHit(
                    list_key=entry.list_key,
                    entry=entry,
                    matched_name=best_name,
                    via_alias=best_name != entry.name,
                    score=round(best, digits),
                    method="exact" if best >= exact_from else "fuzzy",
                )
            )
    return BulkResult(
        status="HITS" if hits else "NO_HITS",
        query=query,
        min_score=threshold,
        hits=tuple(hits),
        entries_checked=len(entries),
        as_of=as_of,
        profile=profile.reference,
    )


def _pep_settings(profile: RegistryProfile) -> NormalizationProfile:
    profile.require_kind("screening")
    if profile.setting("algorithm") != "token_f1":
        raise ProfileError(f"Profil {profile.id} ist kein Token-Profil.")
    ref = profile.setting("normalization")
    return load_normalization(ref["id"], ref["version"])


def pep_score(
    query_form: str,
    candidate_form: str,
    profile: RegistryProfile,
    *,
    country: str | None,
    entry_countries: str,
) -> float:
    """``_match_name``: exact 1.0, else token F1 + substring bonus + country bonus, capped at 1."""
    if not query_form or not candidate_form:
        return 0.0
    if query_form == candidate_form:
        return 1.0
    query_tokens, candidate_tokens = set(query_form.split()), set(candidate_form.split())
    if not query_tokens or not candidate_tokens:
        return 0.0
    common = query_tokens & candidate_tokens
    if not common:
        return 0.0
    q_cov, c_cov = len(common) / len(query_tokens), len(common) / len(candidate_tokens)
    token_score = 2 * (q_cov * c_cov) / (q_cov + c_cov)
    bonus = 0.0
    if query_form in candidate_form or candidate_form in query_form:
        bonus += float(profile.setting("substring_bonus"))
    if country and entry_countries and country.lower() in entry_countries.lower():
        bonus += float(profile.setting("country_bonus"))
    return min(1.0, token_score + bonus)


def pep_bulk_screen(
    name: str,
    entries: Sequence[ListEntry],
    profile: RegistryProfile,
    *,
    country: str | None = None,
    min_score: float | None = None,
    as_of: str | None = None,
) -> BulkResult:
    """PEP bulk screening of flowinvoice against parsed ``peps`` list entries."""
    normalization = _pep_settings(profile)
    query = _check_query(name)
    threshold = float(profile.setting("default_min_score") if min_score is None else min_score)
    if not entries:
        return _not_searched(profile, query, threshold, as_of)
    query_form = normalize(query, normalization)
    exact_from = float(profile.setting("exact_from"))
    digits = int(profile.setting("score_digits"))
    hits = []
    for entry in entries:
        best, best_method, best_name = 0.0, "fuzzy", ""
        for display in (entry.name, *entry.aliases):
            form = normalize(display, normalization)
            if not form:
                continue
            value = pep_score(
                query_form, form, profile, country=country, entry_countries=entry.countries
            )
            if value > best:
                best, best_name = value, display
                best_method = "exact" if value >= exact_from else "fuzzy"
        if best >= threshold:
            hits.append(
                BulkHit(
                    list_key=entry.list_key,
                    entry=entry,
                    matched_name=best_name,
                    via_alias=bool(best_name and best_name != entry.name),
                    score=round(best, digits),
                    method=best_method,
                )
            )
    hits.sort(key=lambda h: h.score, reverse=True)
    return BulkResult(
        status="HITS" if hits else "NO_HITS",
        query=query,
        min_score=threshold,
        hits=tuple(hits[: int(profile.setting("max_hits"))]),
        entries_checked=len(entries),
        as_of=as_of,
        profile=profile.reference,
    )
