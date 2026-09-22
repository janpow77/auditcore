"""Version and fingerprint references for the shipped synthetic-data profiles."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from typing import Any


def _content_hash(content: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def list_profiles() -> tuple[dict[str, Any], ...]:
    """Read independently owned metadata; reject altered content or implementation hashes.

    Returns:
        Fresh profile dictionaries with stable IDs, versions and provenance.
    Raises:
        ValueError: Registry content differs from its declared fingerprints.
    """
    resources = files("auditcore_dummygenerator")
    registry = json.loads(resources.joinpath("profiles.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(resources.joinpath("generator.py").read_bytes()).hexdigest()
    profiles: list[dict[str, Any]] = registry["profiles"]
    seen: set[str] = set()
    for profile in profiles:
        identifier = profile["artifact_id"]
        if identifier in seen:
            raise ValueError("Duplicate profile identifier")
        seen.add(identifier)
        if profile["content_hash"] != _content_hash(profile["content"]):
            raise ValueError(f"Profile content fingerprint mismatch: {identifier}")
        if profile["content"]["implementation_sha256"] != source_hash:
            raise ValueError(f"Profile implementation fingerprint mismatch: {identifier}")
    return tuple(profiles)


def profile_reference(artifact_id: str) -> dict[str, str]:
    """Return an exact ID/version/hash reference for a caller-owned run manifest.

    Args:
        artifact_id: Stable ID from list_profiles().
    Returns:
        Profile identity, draft status and content/implementation fingerprints.
    Raises:
        KeyError: artifact_id is not a shipped profile.
        ValueError: Registry fingerprints are invalid.
    """
    for profile in list_profiles():
        if profile["artifact_id"] == artifact_id:
            return {
                "artifact_id": profile["artifact_id"],
                "version": profile["version"],
                "status": profile["status"],
                "content_hash": profile["content_hash"],
                "implementation_sha256": profile["content"]["implementation_sha256"],
            }
    raise KeyError(artifact_id)
