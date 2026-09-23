"""Versioned, source-bound normalisation, classification and resolution profiles.

Each profile reproduces one characterized source variant. Variants that behave
differently (for example ``ä → ae`` versus ``ä → a``) stay separate profiles;
nothing here chooses or harmonises one of them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

from .errors import ProfileError

SCHEMA = "auditcore_entity_matching.profile/1"
ALGORITHMS = frozenset(
    {"translate_then_casefold", "casefold_fold_nfkd", "casefold_nfc_fold_nfkd", "lower_nfkd_ascii"}
)


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


def fingerprint(data: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _strings(values: Any, label: str) -> frozenset[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ProfileError(f"{label} muss eine Liste von Texten sein.")
    return frozenset(values)


def _mapping(values: Any, label: str) -> Mapping[str, str]:
    if not isinstance(values, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in values.items()
    ):
        raise ProfileError(f"{label} muss eine Zuordnung Text → Text sein.")
    return MappingProxyType(dict(values))


def profile_from_dict(data: Mapping[str, Any]) -> Profile:
    """Validate a profile document; nothing is defaulted silently."""
    try:
        if data["schema"] != SCHEMA:
            raise ProfileError("Unbekanntes Profilschema.")
        normalization = classification = resolution = None
        if "normalization" in data:
            n = data["normalization"]
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
            )
        if "classification" in data:
            c = data["classification"]
            classification = Classification(
                exact_from=float(c["exact_from"]),
                high_from=float(c["high_from"]),
                medium_from=float(c["medium_from"]),
                exact_token_sort_from=float(c["exact_token_sort_from"]),
                minimum_score=None if c.get("minimum_score") is None else float(c["minimum_score"]),
            )
            if (
                not classification.medium_from
                < classification.high_from
                <= classification.exact_from
            ):
                raise ProfileError("Klassengrenzen sind nicht aufsteigend.")
        if "resolution" in data:
            r = data["resolution"]
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


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; no profile is an implicit default."""
    found = []
    for entry in resources.files("auditcore_entity_matching.profile_data").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


def load_profile(profile_id: str, version: str) -> Profile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    entry = resources.files("auditcore_entity_matching.profile_data").joinpath(name)
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile
