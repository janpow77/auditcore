"""Explicit format profiles; the original Flowlib selector remains unchanged."""

from __future__ import annotations

from typing import Any

from auditcore_reporting.formats import get_number_format

PROFILE_IDS = ("flowlib-legacy-v1", "plain-v1")


def get_profile_format(profile: str, column: str, value: Any = None) -> str:
    """Return a profile's format without modifying values or guessing locale.

    Args:
        profile: flowlib-legacy-v1 or plain-v1; unknown profiles are rejected.
        column: Header passed unchanged to the selected profile.
        value: Optional existing compatibility argument, unused by both profiles.
    Returns:
        Excel format string; plain-v1 always returns General.
    Raises:
        ValueError: Unknown profile.
        TypeError: Invalid column name in the Flowlib profile.
    """
    if profile == "flowlib-legacy-v1":
        return get_number_format(column, value)
    if profile == "plain-v1":
        return "General"
    raise ValueError(f"Unknown format profile: {profile}")


def get_profile_metadata(profile: str) -> dict[str, Any]:
    """Return versioned profile provenance after checking source and content hashes.

    Args:
        profile: One of PROFILE_IDS.
    Returns:
        Fresh metadata for exact profile references in caller-owned export manifests.
    Raises:
        ValueError: Unknown profile or modified profile/source fingerprints.
    """
    import hashlib
    import json
    from importlib.resources import files

    if profile not in PROFILE_IDS:
        raise ValueError(f"Unknown format profile: {profile}")
    package = files("auditcore_reporting")
    registry = json.loads(package.joinpath("profile-registry.json").read_text(encoding="utf-8"))
    entry: dict[str, Any] = registry["profiles"][profile]
    content = entry["content"]
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if hashlib.sha256(canonical.encode()).hexdigest() != entry["content_hash"]:
        raise ValueError("Profile content fingerprint mismatch")
    for filename in ("formats.py", "profiles.py"):
        actual = hashlib.sha256(package.joinpath(filename).read_bytes()).hexdigest()
        if actual != content["implementation_hashes"][filename]:
            raise ValueError("Profile implementation fingerprint mismatch")
    return entry
