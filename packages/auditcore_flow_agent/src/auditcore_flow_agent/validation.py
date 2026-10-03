"""Validierung der technischen Auftragsverträge."""

from __future__ import annotations

from auditcore_common.numeric import require_finite


def number(value: object, name: str, *, minimum: float = 0) -> float:
    result = require_finite(
        value,
        not_number=lambda: ValueError(f"{name}: Zahl erforderlich."),
        not_finite=lambda: ValueError(f"{name}: endliche Zahl erforderlich."),
    )
    if result < minimum:
        raise ValueError(f"{name}: mindestens {minimum} erforderlich.")
    return result


def positive(value: object, name: str) -> float:
    result = number(value, name)
    if result == 0:
        raise ValueError(f"{name}: muss positiv sein.")
    return result


def integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name}: ganze Zahl ab {minimum} erforderlich.")
    return value


def identifier(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200 or "\x00" in value:
        raise ValueError("Kennung muss 1 bis 200 Zeichen enthalten.")
    return value


def names(values: tuple[str, ...]) -> None:
    if not isinstance(values, tuple) or len(set(values)) != len(values):
        raise ValueError("Kennungen müssen als Tupel ohne Duplikate vorliegen.")
    for value in values:
        identifier(value)
