"""The JSON-safe variant of the harvest records (``auditcore_common.json_values``).

Decimal and dates become text, NaN becomes ``None``; values of other types
are passed on unchanged, as in the source.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar, cast

from auditcore_common.json_values import jsonable

K = TypeVar("K")


def json_safe(value: object) -> object:
    """JSON-safe copy: ``jsonable(value, decimals=True, nan_as_none=True)``."""
    return jsonable(value, decimals=True, nan_as_none=True)


def json_safe_mapping(value: Mapping[K, object]) -> dict[str, object]:
    """:func:`json_safe` of a mapping; keys become text."""
    return cast(dict[str, object], json_safe(value))
