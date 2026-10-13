"""Strict readers for configuration and recipe values (German error messages)."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation

from auditcore_dummybundle.errors import BundleError


def as_object(value: object, path: str, allowed: Collection[str]) -> Mapping[str, object]:
    """``value`` as JSON object whose keys are all in ``allowed``."""
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise BundleError(f"'{path}' muss ein Objekt sein.", path=path)
    unknown = sorted(key for key in value if key not in allowed)
    if unknown:
        raise BundleError(
            f"'{path}' enthält unbekannte Angaben: {', '.join(unknown)}.",
            code="unknown_key",
            path=path,
        )
    return value


def as_text(value: object, path: str, *, max_length: int = 200, empty: bool = False) -> str:
    """Text of at most ``max_length`` characters without control characters."""
    if not isinstance(value, str):
        raise BundleError(f"'{path}' muss Text sein.", path=path)
    if len(value) > max_length:
        raise BundleError(f"'{path}' ist länger als {max_length} Zeichen.", path=path)
    if any(ord(char) < 32 for char in value):
        raise BundleError(f"'{path}' enthält Steuerzeichen.", path=path)
    if not empty and not value.strip():
        raise BundleError(f"'{path}' darf nicht leer sein.", path=path)
    return value


def as_int(value: object, path: str, low: int, high: int) -> int:
    """Integer within the inclusive range."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise BundleError(f"'{path}' muss eine ganze Zahl sein.", path=path)
    if not low <= value <= high:
        raise BundleError(f"'{path}' muss zwischen {low} und {high} liegen.", path=path)
    return value


def as_decimal(value: object, path: str, low: Decimal, high: Decimal) -> Decimal:
    """Finite decimal within the inclusive range; text, integers and floats are read exactly."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise BundleError(f"'{path}' muss eine Zahl sein.", path=path)
    try:
        number = Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation as exc:
        raise BundleError(f"'{path}' muss eine Zahl sein.", path=path) from exc
    if not number.is_finite() or not low <= number <= high:
        raise BundleError(f"'{path}' muss zwischen {low} und {high} liegen.", path=path)
    return number


def as_bool(value: object, path: str) -> bool:
    """JSON boolean."""
    if not isinstance(value, bool):
        raise BundleError(f"'{path}' muss wahr oder falsch sein.", path=path)
    return value


def as_date(value: object, path: str) -> date:
    """ISO date ``JJJJ-MM-TT`` between 1990 and 2100."""
    if not isinstance(value, str):
        raise BundleError(f"'{path}' muss ein Datum der Form JJJJ-MM-TT sein.", path=path)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise BundleError(f"'{path}' muss ein Datum der Form JJJJ-MM-TT sein.", path=path) from exc
    if not 1990 <= parsed.year <= 2100:
        raise BundleError(f"'{path}' muss zwischen 1990 und 2100 liegen.", path=path)
    return parsed


def as_choice(value: object, path: str, allowed: Collection[str]) -> str:
    """One of the explicitly allowed values."""
    if not isinstance(value, str) or value not in allowed:
        raise BundleError(
            f"'{path}' muss einer der Werte {', '.join(sorted(allowed))} sein.",
            code="unknown_value",
            path=path,
        )
    return value


def as_list(value: object, path: str, maximum: int, *, minimum: int = 0) -> list[object]:
    """JSON list with ``minimum`` to ``maximum`` entries."""
    if not isinstance(value, list):
        raise BundleError(f"'{path}' muss eine Liste sein.", path=path)
    if not minimum <= len(value) <= maximum:
        raise BundleError(
            f"'{path}' muss {minimum} bis {maximum} Einträge haben.", code="too_large", path=path
        )
    return value
