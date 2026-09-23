"""Shared helpers: decode the type-preserving fixture encoding of the capture tool."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def revive(value: Any) -> Any:
    """Inverse of ``tools/capture_legacy.jsonable`` (dataclasses stay as field dicts)."""
    if isinstance(value, list):
        return [revive(v) for v in value]
    if not isinstance(value, dict):
        return value
    if "$float" in value:
        return float(value["$float"])
    if "$decimal" in value:
        return Decimal(value["$decimal"])
    if "$datetime" in value:
        return datetime.fromisoformat(value["$datetime"])
    if "$date" in value:
        return date.fromisoformat(value["$date"])
    if "$dict" in value:
        return {revive(k): revive(v) for k, v in value["$dict"]}
    if "$tuple" in value:
        return tuple(revive(v) for v in value["$tuple"])
    if "$dataclass" in value:
        return {"$dataclass": value["$dataclass"], **revive(value["fields"])}
    return {k: revive(v) for k, v in value.items()}


def load(variant: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{variant}_observed.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


def encode(value: Any) -> Any:
    """Same type-preserving encoding as ``tools/capture_legacy.jsonable``."""
    import hashlib
    from dataclasses import asdict, is_dataclass

    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return {"$float": "nan"} if value != value else {"$float": repr(value)}
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, bytes):
        return {"$bytes_sha256": hashlib.sha256(value).hexdigest(), "length": len(value)}
    if is_dataclass(value) and not isinstance(value, type):
        return {"$dataclass": type(value).__name__, "fields": encode(asdict(value))}
    if isinstance(value, dict):
        return {"$dict": [[encode(k), encode(v)] for k, v in value.items()]}
    if isinstance(value, tuple):
        return {"$tuple": [encode(v) for v in value]}
    if isinstance(value, (list, set, frozenset)):
        items = list(value) if isinstance(value, list) else sorted(value, key=repr)
        return [encode(v) for v in items]
    return {"$repr": repr(value), "type": type(value).__name__}
