"""Versioned source catalog: origin, planned consumer, semantics and access status.

The catalog records what was actually checked: robots.txt was read once on
2026-09-23 (snapshots in the test fixtures); terms of use were **not**
reviewed (``REVIEW_REQUIRED``); live tests carry their executed status.
"""

from __future__ import annotations

import copy
import json
from functools import cache
from importlib import resources
from typing import Any

SCHEMA = "auditcore_property_sources.catalog/1"


@cache
def _load() -> dict[str, Any]:
    text = (
        resources.files("auditcore_property_sources")
        .joinpath("catalog.json")
        .read_text(encoding="utf-8")
    )
    data: dict[str, Any] = json.loads(text)
    if data.get("schema") != SCHEMA:
        raise ValueError("Unbekanntes Katalogschema.")
    return data


def catalog() -> dict[str, Any]:
    """Deep copy of the whole catalog document."""
    return copy.deepcopy(_load())


def source_entry(source_id: str) -> dict[str, Any]:
    """Catalog entry of one source profile (``KeyError`` if unknown)."""
    for entry in _load()["sources"]:
        if entry["source_id"] == source_id:
            return copy.deepcopy(dict(entry))
    raise KeyError(source_id)
