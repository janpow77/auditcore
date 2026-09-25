"""Versioned, source-bound profiles of the registry sources.

A profile holds the professional settings of one characterized source
variant: list catalogues, screening thresholds, date-of-birth/country
weights, PEP risk rules, UBO and SME rules, company verification weights.
Variants that behave differently stay separate profiles; no profile is an
implicit default and nothing here harmonises them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

from ._types import JsonValue
from .errors import ProfileError

SCHEMA = "auditcore_registry_sources.profile/1"
KINDS = frozenset(
    {
        "list_catalog",
        "screening",
        "match_api",
        "ownership",
        "sme",
        "company_verification",
    }
)
STATUSES = frozenset(
    {"SOURCE_CHARACTERIZED", "HUMAN_DECISION_REQUIRED", "LEGACY_ONLY", "USER_DECIDED"}
)


def fingerprint(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class RegistryProfile:
    """Immutable profile with identity, origin, status and fingerprint."""

    id: str
    version: str
    kind: str
    status: str
    legal_status: str
    source: Mapping[str, Any]
    settings: Mapping[str, Any]
    fingerprint: str
    decisions: tuple[Mapping[str, JsonValue], ...] = ()

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result that used this profile."""
        return {
            "id": self.id,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "status": self.status,
        }

    def setting(self, name: str) -> Any:
        """Required setting; a missing key is a profile error, never a default."""
        try:
            return self.settings[name]
        except KeyError as exc:
            raise ProfileError(f"Profil {self.id} {self.version}: Wert '{name}' fehlt.") from exc

    def require_kind(self, kind: str) -> RegistryProfile:
        """Return ``self`` if the profile has the expected kind."""
        if self.kind != kind:
            raise ProfileError(f"Profil {self.id} ist vom Typ {self.kind}, erwartet {kind}.")
        return self


def profile_from_dict(data: Mapping[str, Any]) -> RegistryProfile:
    """Validate a profile document; nothing is defaulted silently."""
    try:
        if data["schema"] != SCHEMA:
            raise ProfileError("Unbekanntes Profilschema.")
        if data["kind"] not in KINDS:
            raise ProfileError(f"Unbekannter Profiltyp {data['kind']!r}.")
        if data["status"] not in STATUSES:
            raise ProfileError(f"Unbekannter Profilstatus {data['status']!r}.")
        source = data["source"]
        if not source.get("repository") or not source.get("commit") or not source.get("path"):
            raise ProfileError("Profil ohne gebundene Quelle.")
        settings = data["settings"]
        if not isinstance(settings, dict) or not settings:
            raise ProfileError("Profil ohne Einstellungen.")
        return RegistryProfile(
            id=str(data["id"]),
            version=str(data["version"]),
            kind=str(data["kind"]),
            status=str(data["status"]),
            legal_status=str(data["legal_status"]),
            source=_freeze(dict(source)),
            settings=_freeze(dict(settings)),
            fingerprint=fingerprint(data),
            decisions=tuple(_freeze(d) for d in data.get("decisions", [])),
        )
    except (KeyError, TypeError, AttributeError) as exc:
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def recommended_profile(purpose: str) -> RegistryProfile:
    """The profile recommended for ``purpose`` after the user decisions of 23.09.2026.

    Purposes: ``sanctions_screening``, ``pep_bulk``, ``pep_risk``, ``ubo``,
    ``sme``, ``company_verification``. Named profiles keep their results; the
    recommendation only says which one to choose.
    """
    found = []
    for entry in resources.files("auditcore_registry_sources.profile_data").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            if purpose in data.get("recommended_for", []):
                found.append((str(data["id"]), str(data["version"])))
    if len(found) != 1:
        raise ProfileError(f"Für '{purpose}' ist kein eindeutiges empfohlenes Profil hinterlegt.")
    return load_profile(*found[0])


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; no profile is an implicit default."""
    found = []
    for entry in resources.files("auditcore_registry_sources.profile_data").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


def load_profile(profile_id: str, version: str) -> RegistryProfile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name:
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files("auditcore_registry_sources.profile_data").joinpath(name)
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile
