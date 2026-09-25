"""Canonical JSON digests that bind results to exact profile and register content."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping


def canonical_sha256(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON form (sorted keys, no whitespace, UTF-8)."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
