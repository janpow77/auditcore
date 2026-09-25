"""JSON-safe copies of parsed values for harvest records."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import TypeVar

K = TypeVar("K")


def json_safe(value: object) -> object:
    """JSON-safe copy (Decimal/date as text, NaN as ``None``).

    Values of other types are passed on unchanged, as in the source.
    """
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, Mapping):
        return json_safe_mapping(value)
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def json_safe_mapping(value: Mapping[K, object]) -> dict[str, object]:
    """:func:`json_safe` of a mapping; keys become text."""
    return {str(k): json_safe(v) for k, v in value.items()}
