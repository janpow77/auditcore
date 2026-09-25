"""Versioned, source-bound profiles of the registry sources.

A profile holds the professional settings of one characterized source
variant: list catalogues, screening thresholds, date-of-birth/country
weights, PEP risk rules, UBO and SME rules, company verification weights.
Variants that behave differently stay separate profiles; no profile is an
implicit default and nothing here harmonises them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from auditcore_common.frozen import freeze
from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import (
    load_packaged_profile,
    packaged_profile_ids,
    recommended_profile_id,
)

from ._types import JsonValue
from .errors import ProfileError

SCHEMA = "auditcore_registry_sources.profile/1"
_RESOURCES = "auditcore_registry_sources.profile_data"
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
    return canonical_sha256(data)


def _freeze(value: Any) -> Any:
    """:func:`auditcore_common.frozen.freeze`, typed ``Any`` for the dataclass fields."""
    return freeze(value)


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
    return load_profile(*recommended_profile_id(_RESOURCES, purpose, ProfileError))


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; no profile is an implicit default."""
    return packaged_profile_ids(_RESOURCES)


def load_profile(profile_id: str, version: str) -> RegistryProfile:
    """Load an explicitly named packaged profile version."""
    return load_packaged_profile(
        _RESOURCES,
        profile_id,
        version,
        parse=profile_from_dict,
        identity=lambda profile: (profile.id, profile.version),
        error=ProfileError,
        require_text=True,
        invalid_name="invalid",
    )
