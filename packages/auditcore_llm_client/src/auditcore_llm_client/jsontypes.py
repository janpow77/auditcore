"""JSON value types and tolerant readers for router responses (stdlib only)."""

from __future__ import annotations

from typing import TypeAlias

JsonValue: TypeAlias = "str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]"
JsonObject: TypeAlias = "dict[str, JsonValue]"


def as_object(value: object) -> JsonObject:
    """Return ``value`` if it is a JSON object, otherwise an empty object."""
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def as_list(value: object) -> list[JsonValue]:
    """Return ``value`` if it is a JSON array, otherwise an empty list."""
    return list(value) if isinstance(value, list) else []


def as_text(value: object, default: str = "") -> str:
    """``str(value)`` with a default for ``None`` (legacy ``str(d.get(k, x))``)."""
    return default if value is None else str(value)


def as_int(value: object) -> int:
    """Legacy ``int(value or 0)``; non-numeric values count as 0."""
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return 0
    try:
        return int(value or 0)
    except ValueError:
        return 0


def as_optional_float(value: object) -> float | None:
    """A number or ``None``; strings and other types are not numbers."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def first_text(*values: object) -> str:
    """First non-empty value as text (legacy ``a or b or c``)."""
    for value in values:
        if value:
            return str(value)
    return ""


def strict_number(value: object) -> float:
    """``float(value)`` for numbers and numeric strings; ``ValueError`` otherwise."""
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise ValueError("not a number")
    return float(value)
