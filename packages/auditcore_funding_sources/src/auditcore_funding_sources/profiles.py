"""Packaged, versioned data profiles; every result names the profile it used."""

from __future__ import annotations

from collections.abc import Mapping
from functools import cache
from typing import Any

from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import load_packaged_profile, packaged_profile_ids

from .errors import ProfileError

PROFILE_VERSION = "2026.09.1"
_RESOURCES = "auditcore_funding_sources.data"


def fingerprint(data: object) -> str:
    """SHA-256 of the canonical JSON representation."""
    return canonical_sha256(data)


def available_profiles() -> tuple[tuple[str, str], ...]:
    """``(id, version)`` of every packaged profile."""
    return packaged_profile_ids(_RESOURCES)


@cache
def load_profile(profile_id: str, version: str = PROFILE_VERSION) -> dict[str, Any]:
    """Load an explicitly named profile; adds ``fingerprint``.

    Raises:
        ProfileError: unknown id/version or mismatching content.
    """
    data = load_packaged_profile(
        _RESOURCES,
        profile_id,
        version,
        parse=_raw,
        identity=lambda raw: (raw.get("id"), raw.get("version")),
        error=ProfileError,
        invalid_name="invalid_or_hidden",
    )
    return {**data, "fingerprint": fingerprint(data)}


def _raw(data: dict[str, object]) -> dict[str, object]:
    """The profile document as read; checked by the identity comparison only."""
    return data


def reference(profile: Mapping[str, Any]) -> dict[str, str]:
    """Identity recorded with every result."""
    return {
        "id": profile["id"],
        "version": profile["version"],
        "fingerprint": profile["fingerprint"],
    }
