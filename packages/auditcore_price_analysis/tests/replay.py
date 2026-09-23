"""Shared helpers: type-preserving JSON codec of the characterization fixture."""

from __future__ import annotations

import json
import math
import types
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

FIXTURE = Path(__file__).parent / "fixtures" / "regulierung_calculator_observed.json"


def load_fixture() -> dict[str, Any]:
    """The observed legacy cases."""
    data: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data


def decode(value: Any) -> Any:
    """Inverse of the capture tool's ``encode``."""
    if isinstance(value, list):
        return [decode(v) for v in value]
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
    if "$obj" in value:
        return types.SimpleNamespace(**{k: decode(v) for k, v in value["$obj"].items()})
    if "$set" in value:
        return {decode(v) for v in value["$set"]}
    return {k: decode(v) for k, v in value.items()}


def encode_result(value: Any) -> Any:
    """Same result encoding as the capture tool."""
    if isinstance(value, types.SimpleNamespace):
        return {"$ref": value.ref}
    if isinstance(value, tuple):
        return {"$tuple": [encode_result(v) for v in value]}
    if isinstance(value, float):
        if math.isnan(value):
            return {"$float": "nan"}
        if math.isinf(value):
            return {"$float": "inf" if value > 0 else "-inf"}
        return value
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, dict):
        return {k: encode_result(v) for k, v in value.items()}
    if isinstance(value, list):
        return [encode_result(v) for v in value]
    return value
