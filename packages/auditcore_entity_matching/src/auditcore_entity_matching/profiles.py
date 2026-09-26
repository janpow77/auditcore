"""Versioned, source-bound normalisation, classification and resolution profiles.

Each profile reproduces one characterized source variant. Variants that behave
differently (for example ``ä → ae`` versus ``ä → a``) stay separate profiles;
nothing here chooses or harmonises one of them.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import (
    load_packaged_profile,
    packaged_profile_ids,
    recommended_profile_id,
)

from .errors import ProfileError

_RESOURCES = "auditcore_entity_matching.profile_data"

SCHEMA = "auditcore_entity_matching.profile/1"
ALGORITHMS = frozenset(
    {
        "translate_then_casefold",
        "casefold_fold_nfkd",
        "casefold_nfc_fold_nfkd",
        "lower_nfkd_ascii",
        "nfkd_lower_regex",
    }
)

#: A profile document as read from JSON. Values are validated field by field
#: while the profile is built, so the raw form stays untyped at this boundary.
_RawDocument = Mapping[str, Any]


@dataclass(frozen=True)
class Normalization:
    """Steps of one normalisation variant."""

    algorithm: str
    translation: Mapping[str, str]
    fold_map: Mapping[str, str]
    ampersand: str | None
    legal_suffixes: frozenset[str]
    filler_words: frozenset[str]
    compact_tokens: bool
    #: Only ``nfkd_lower_regex``: characters replaced by a space after NFKD/lower().
    nonword_pattern: str | None = None
    #: Optional ``"NFC"``: compose decomposed characters first (decision R2 of
    #: 23.09.2026). Absent in all source-characterized profiles.
    compose: str | None = None
    #: Only ``nfkd_lower_regex``: legal-form/generic tokens replaced by a space.
    removal_pattern: str | None = None


@dataclass(frozen=True)
class Classification:
    """Score classes of a screening variant (fachliche Schwellen, source-characterized)."""

    exact_from: float
    high_from: float
    medium_from: float
    exact_token_sort_from: float
    minimum_score: float | None


@dataclass(frozen=True)
class Resolution:
    """Candidate selection of an entity-resolution variant."""

    normalization_profile: str
    scorers: tuple[str, ...]
    min_token_length: int
    per_scorer_limit: int
    fuzzy_threshold: float
    lei_pattern: str
    lei_checksum: bool
    confidence: Mapping[str, float]


@dataclass(frozen=True)
class Profile:
    """Immutable profile with identity, source and fingerprint."""

    id: str
    version: str
    kind: str
    status: str
    legal_status: str
    source: Mapping[str, Any]
    fingerprint: str
    normalization: Normalization | None = None
    classification: Classification | None = None
    resolution: Resolution | None = None

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result that used this profile."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}


def fingerprint(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    return canonical_sha256(data)


def _strings(values: object, label: str) -> frozenset[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ProfileError(f"{label} muss eine Liste von Texten sein.")
    return frozenset(values)


def _mapping(values: object, label: str) -> Mapping[str, str]:
    if not isinstance(values, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in values.items()
    ):
        raise ProfileError(f"{label} muss eine Zuordnung Text → Text sein.")
    return MappingProxyType(dict(values))


def _check_patterns(rules: Normalization) -> None:
    """``nfkd_lower_regex`` needs both compilable patterns; other algorithms none."""
    patterns = (rules.nonword_pattern, rules.removal_pattern)
    if rules.algorithm != "nfkd_lower_regex":
        if any(p is not None for p in patterns):
            raise ProfileError("Muster sind nur für nfkd_lower_regex zulässig.")
        return
    if not all(isinstance(p, str) and p for p in patterns):
        raise ProfileError("nfkd_lower_regex verlangt nonword_pattern und removal_pattern.")
    for pattern in patterns:
        try:
            re.compile(str(pattern))
        except re.error as exc:
            raise ProfileError(f"Ungültiges Muster {pattern!r}: {exc}") from exc


def _normalization(n: _RawDocument) -> Normalization:
    if n["algorithm"] not in ALGORITHMS:
        raise ProfileError(f"Unbekannter Algorithmus {n['algorithm']!r}.")
    normalization = Normalization(
        algorithm=n["algorithm"],
        translation=_mapping(n.get("translation", {}), "translation"),
        fold_map=_mapping(n.get("fold_map", {}), "fold_map"),
        ampersand=n["ampersand"],
        legal_suffixes=_strings(n["legal_suffixes"], "legal_suffixes"),
        filler_words=_strings(n["filler_words"], "filler_words"),
        compact_tokens=bool(n["compact_tokens"]),
        nonword_pattern=n.get("nonword_pattern"),
        compose=n.get("compose"),
        removal_pattern=n.get("removal_pattern"),
    )
    _check_patterns(normalization)
    if normalization.compose not in (None, "NFC"):
        raise ProfileError("compose kennt nur 'NFC'.")
    return normalization


def _classification(c: _RawDocument) -> Classification:
    classification = Classification(
        exact_from=float(c["exact_from"]),
        high_from=float(c["high_from"]),
        medium_from=float(c["medium_from"]),
        exact_token_sort_from=float(c["exact_token_sort_from"]),
        minimum_score=None if c.get("minimum_score") is None else float(c["minimum_score"]),
    )
    if not classification.medium_from < classification.high_from <= classification.exact_from:
        raise ProfileError("Klassengrenzen sind nicht aufsteigend.")
    return classification


def _resolution(r: _RawDocument) -> Resolution:
    resolution = Resolution(
        normalization_profile=r["normalization_profile"],
        scorers=tuple(r["scorers"]),
        min_token_length=int(r["min_token_length"]),
        per_scorer_limit=int(r["per_scorer_limit"]),
        fuzzy_threshold=float(r["fuzzy_threshold"]),
        lei_pattern=r["lei_pattern"],
        lei_checksum=bool(r["lei_checksum"]),
        confidence=MappingProxyType({k: float(v) for k, v in r["confidence"].items()}),
    )
    if not set(resolution.scorers) <= {"token_set_ratio", "WRatio"}:
        raise ProfileError("Unbekannter Scorer im Profil.")
    return resolution


def profile_from_dict(data: _RawDocument) -> Profile:
    """Validate a profile document; nothing is defaulted silently."""
    try:
        if data["schema"] != SCHEMA:
            raise ProfileError("Unbekanntes Profilschema.")
        normalization = _normalization(data["normalization"]) if "normalization" in data else None
        classification = (
            _classification(data["classification"]) if "classification" in data else None
        )
        resolution = _resolution(data["resolution"]) if "resolution" in data else None
        if normalization is None and resolution is None:
            raise ProfileError("Profil enthält weder Normalisierung noch Auflösung.")
        return Profile(
            id=data["id"],
            version=data["version"],
            kind=data["kind"],
            status=data["status"],
            legal_status=data["legal_status"],
            source=MappingProxyType(dict(data["source"])),
            fingerprint=fingerprint(data),
            normalization=normalization,
            classification=classification,
            resolution=resolution,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def recommended_profile(purpose: str) -> Profile:
    """The profile marked as recommended for ``purpose`` (user decisions of 23.09.2026).

    Purposes: ``entity_normalization``, ``sanctions_screening``,
    ``pep_screening``, ``payee``. Exactly one packaged profile carries each
    purpose; the recommendation never changes a result of a named profile.
    """
    return load_profile(*recommended_profile_id(_RESOURCES, purpose, ProfileError))


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; no profile is an implicit default."""
    return packaged_profile_ids(_RESOURCES)


def load_profile(profile_id: str, version: str) -> Profile:
    """Load an explicitly named packaged profile version."""
    return load_packaged_profile(
        _RESOURCES,
        profile_id,
        version,
        parse=profile_from_dict,
        identity=lambda profile: (profile.id, profile.version),
        error=ProfileError,
        require_text=True,
        invalid_name="missing",
    )
