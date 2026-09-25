"""Fraud-check mechanics of flowinvoice ``fraud_detection`` as profile-driven functions.

Three separate, versioned legacy profiles (schema ``auditcore_risk.fraud-profile/1``):

* ``signal_score`` — blockers, warnings, score and level from the results of the
  sub-checks (duplicates, sanctions, PEP, company, TED). Sanctions, PEP and
  company results are *consumed* as plain mappings (port contract); the
  screening itself belongs to the registry/screening libraries
  (:mod:`.fraud_signals`).
* ``ted_contractor`` — statistics, red flags and legitimacy score over the
  public contracts of one contractor, given as ``auditcore_procurement``
  ``notice/1`` records; :func:`select_contracts` reproduces the SQL selection
  (:mod:`.fraud_ted`).
* ``duplicates`` — exact and fuzzy invoice duplicates among candidate documents
  the application has already pre-selected (its SQL window/limit stay there)
  (:mod:`.fraud_duplicates`).

Every weight, threshold, text and format comes from the profile; the results
are this profile's legacy values only, never a combined score across profiles.
This module loads and validates the profiles and re-exports the mechanics.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from importlib import resources
from importlib.resources.abc import Traversable
from types import MappingProxyType

from .base import JsonObject
from .errors import ProfileError
from .fraud_duplicates import (
    DuplicateMatch,
    exact_duplicates,
    find_duplicates,
    fuzzy_duplicates,
    names_similar,
    parse_date,
    validate_duplicates,
)
from .fraud_profile import FRAUD_KINDS, SCHEMA, FraudProfile
from .fraud_signals import SignalAssessment, score_signals, validate_signal
from .fraud_ted import TedAssessment, assess_contractor, select_contracts, validate_ted
from .profiles import fingerprint

_TOP = frozenset(
    {
        "schema",
        "id",
        "version",
        "kind",
        "status",
        "legal_status",
        "source",
        "open_decisions",
        "parameters",
    }
)

_VALIDATORS: dict[str, Callable[[JsonObject], None]] = {
    "signal_score": validate_signal,
    "ted_contractor": validate_ted,
    "duplicates": validate_duplicates,
}


def fraud_profile_from_dict(data: JsonObject) -> FraudProfile:
    """Validate a fraud-check profile document."""
    if not isinstance(data, Mapping) or data.get("schema") != SCHEMA:
        raise ProfileError("Unbekanntes Schema für Betrugsprüfprofile.")
    unknown = set(data) - _TOP
    if unknown:
        raise ProfileError(f"Profil: unbekannte Felder {sorted(unknown)}.")
    if data.get("kind") not in FRAUD_KINDS:
        raise ProfileError(f"Unbekannte Profilart {data.get('kind')!r}.")
    for key in ("id", "version", "status", "legal_status"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ProfileError(f"Profil: {key!r} fehlt.")
    if not isinstance(data.get("source"), dict) or not isinstance(data.get("parameters"), dict):
        raise ProfileError("Profil: 'source' und 'parameters' sind Pflicht.")
    _VALIDATORS[data["kind"]](data["parameters"])
    return FraudProfile(
        id=data["id"],
        version=data["version"],
        kind=data["kind"],
        status=data["status"],
        legal_status=data["legal_status"],
        source=MappingProxyType(dict(data["source"])),
        parameters=MappingProxyType(json.loads(json.dumps(data["parameters"]))),
        open_decisions=tuple(data.get("open_decisions", [])),
        fingerprint=fingerprint(data),
    )


def _packaged() -> dict[tuple[str, str], Traversable]:
    found = {}
    for entry in resources.files("auditcore_risk.fraud_profiles").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found[(str(data["id"]), str(data["version"]))] = entry
    return found


def available_fraud_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs of fraud-check profiles."""
    return tuple(sorted(_packaged()))


def load_fraud_profile(profile_id: str, version: str, kind: str | None = None) -> FraudProfile:
    """Load an explicitly named packaged fraud-check profile (optionally of one kind)."""
    entry = _packaged().get((profile_id, version))
    if entry is None:
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = fraud_profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if kind is not None and profile.kind != kind:
        raise ProfileError(f"Profil {profile_id} ist kein {kind}-Profil.")
    return profile


__all__ = [
    "FRAUD_KINDS",
    "SCHEMA",
    "DuplicateMatch",
    "FraudProfile",
    "SignalAssessment",
    "TedAssessment",
    "assess_contractor",
    "available_fraud_profiles",
    "exact_duplicates",
    "find_duplicates",
    "fraud_profile_from_dict",
    "fuzzy_duplicates",
    "load_fraud_profile",
    "names_similar",
    "parse_date",
    "score_signals",
    "select_contracts",
]
