"""Recorded flowstat/audit-portal behavior (gzip-compressed JSON)."""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sampling_legacy_observed.json.gz"
LEGACY: dict[str, Any] = json.loads(gzip.decompress(FIXTURE_PATH.read_bytes()))


def revive(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"$float"}:
        return float(value["$float"])
    if isinstance(value, list):
        return [revive(v) for v in value]
    return value


def column(frame: str, name: str) -> list[Any]:
    values = [revive(v) for v in LEGACY["frames"][frame][name]]
    return [None if isinstance(v, float) and math.isnan(v) else v for v in values]
