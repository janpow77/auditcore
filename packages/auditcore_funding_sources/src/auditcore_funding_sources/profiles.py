"""Packaged, versioned data profiles; every result names the profile it used."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from importlib import resources
from typing import Any

from .errors import ProfileError

PROFILE_VERSION = "2026.09.1"


def fingerprint(data: Any) -> str:
    """SHA-256 of the canonical JSON representation."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def available_profiles() -> tuple[tuple[str, str], ...]:
    """``(id, version)`` of every packaged profile."""
    found = []
    for entry in resources.files("auditcore_funding_sources.data").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


@lru_cache(maxsize=None)
def load_profile(profile_id: str, version: str = PROFILE_VERSION) -> dict[str, Any]:
    """Load an explicitly named profile; adds ``fingerprint``.

    Raises:
        ProfileError: unknown id/version or mismatching content.
    """
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name or name.startswith("."):
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files("auditcore_funding_sources.data").joinpath(name)
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    data = json.loads(entry.read_text(encoding="utf-8"))
    if (data.get("id"), data.get("version")) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return {**data, "fingerprint": fingerprint(data)}


def reference(profile: dict[str, Any]) -> dict[str, str]:
    """Identity recorded with every result."""
    return {"id": profile["id"], "version": profile["version"], "fingerprint": profile["fingerprint"]}
