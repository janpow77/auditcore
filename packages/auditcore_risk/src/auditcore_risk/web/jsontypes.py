"""JSON value types of the web API and the conversion of library results into them."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import TypeAlias

JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
JsonObject: TypeAlias = "dict[str, JsonValue]"


def _number(value: float) -> JsonValue:
    if math.isfinite(value):
        return value
    if math.isnan(value):
        return "NaN"
    return "Infinity" if value > 0 else "-Infinity"


def json_safe(value: object) -> JsonValue:
    """JSON without NaN/Infinity: non-finite numbers as text, dates ISO, Decimal as float.

    Mapping proxies become objects, tuples lists; any other object its ``str``.
    """
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, Decimal):
        return _number(float(value))
    if isinstance(value, float):
        return _number(value)
    if isinstance(value, date):
        return value.isoformat()
    if value is None or isinstance(value, str | int | bool):
        return value
    return str(value)


def json_object(value: object) -> JsonObject:
    """:func:`json_safe` of a mapping (``{}`` for anything else)."""
    safe = json_safe(value)
    return safe if isinstance(safe, dict) else {}
