"""Behavior-compatible functions of the source applications.

Each function reproduces one characterized original exactly (see
``tests/fixtures/legacy_observed.json``) so that a consumer can switch to the
installed package without changing results. Differences to the library
contract are documented in ``docs/behavior-changes.md``.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache

from .lei import extract_lei, is_lei_format
from .matching import Candidate, best_match, classify
from .normalize import normalize
from .profiles import Profile, load_profile

PROFILE_VERSION = "2026.09.1"
#: Sanctions normalisation after the decision of 23.09.2026 („mueller wenn es
#: kein umlaut gibt“): audit_designer@1254591 (PR #380), flowworkshop@3d1cb40 (PR #49).
TRANSLITERATION_VERSION = "2026.09.2"


@cache
def _profile(profile_id: str, version: str = PROFILE_VERSION) -> Profile:
    return load_profile(profile_id, version)


def flowworkshop_normalize_company_name(text: str | None, *, drop_filler: bool = False) -> str:
    """``state_aid_service.normalize_company_name`` (flowworkshop@a05bb21)."""
    return normalize(text, _profile("flowworkshop.state_aid"), drop_filler=drop_filler)


def flowworkshop_normalize_name(text: str) -> str:
    """``sanctions_service.normalize_name`` (flowworkshop@a05bb21)."""
    return normalize(text, _profile("flowworkshop.sanctions"))


def designer_normalisiere_name(text: str) -> str:
    """``register.sanctions.normalisiere_name`` (audit_designer@030a71e)."""
    return normalize(text, _profile("audit_designer.sanctions"))


def designer_normalisiere_name_umschrift(text: str) -> str:
    """``register.sanctions.normalisiere_name`` (audit_designer@1254591, ``Müller → mueller``)."""
    return normalize(text, _profile("audit_designer.sanctions", TRANSLITERATION_VERSION))


def flowworkshop_normalize_name_umschrift(text: str) -> str:
    """``sanctions_service.normalize_name`` (flowworkshop@3d1cb40, ``Müller → mueller``)."""
    return normalize(text, _profile("flowworkshop.sanctions", TRANSLITERATION_VERSION))


def flowinvoice_pep_normalize_name(name: str) -> str:
    """``PEPChecker._normalize_name`` (flowinvoice@fb2d185, ``Straße → stra e``)."""
    return normalize(name, _profile("flowinvoice.pep"))


def flowworkshop_is_valid_lei(value: str | None) -> bool:
    """``entity_resolution.is_valid_lei``: format only, check digits not verified."""
    return is_lei_format(value)


def flowworkshop_extract_lei_from_text(value: str | None) -> str | None:
    """``entity_resolution.extract_lei_from_text``: first token of LEI format."""
    return extract_lei(value, require_checksum=False)


def flowworkshop_classify(
    score: float, q_norm: str | None = None, matched_norm: str | None = None
) -> str:
    """``sanctions_service._classify``."""
    return classify(score, _profile("flowworkshop.sanctions"), q_norm, matched_norm)


def designer_klassifiziere(
    wert: float, anfrage_norm: str | None = None, treffer_norm: str | None = None
) -> str:
    """``register.sanctions.klassifiziere``."""
    return classify(wert, _profile("audit_designer.sanctions"), anfrage_norm, treffer_norm)


def flowworkshop_fuzzy_best(
    name_normalized: str,
    candidates: Sequence[tuple[int, str]],
    *,
    min_score: float | None = None,
) -> tuple[int, float] | None:
    """Scoring part of ``entity_resolution._find_by_name_fuzzy`` for prefiltered rows.

    ``candidates`` are ``(id, canonical_name_normalized)`` in database order; the
    SQL prefilter (ILIKE on the first tokens, trigram ordering, limit 200)
    stays in the application. ``min_score`` defaults to the source threshold.
    """
    profile = _profile("flowworkshop.entity_resolution")
    assert profile.resolution is not None
    threshold = profile.resolution.fuzzy_threshold if min_score is None else min_score
    result = best_match(
        name_normalized,
        [Candidate(i, n) for i, n in candidates],
        profile,
        min_score=threshold,
    )
    return None if result is None else (int(result.candidate_id), result.score)
