"""Exact number parsing and explicit rounding (no binary floating point in results)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import (
    ROUND_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Decimal,
    InvalidOperation,
)
from typing import Any

from .errors import PriceAnalysisError, ProfileError

_PLAIN = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)")
ROUNDING_MODES = {
    "ROUND_HALF_UP": ROUND_HALF_UP,
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_DOWN": ROUND_DOWN,
    "ROUND_UP": ROUND_UP,
}


def parse_decimal(value: Any, *, field: str) -> Decimal:
    """Exact decimal from ``int``, ``Decimal``, finite ``float`` or plain decimal text.

    ``None`` is *missing*, never zero; callers decide whether a value may be
    absent. Booleans, German decimal commas, exponents and non-finite values
    are rejected so that no number is silently reinterpreted.
    """
    if value is None:
        raise PriceAnalysisError("missing_value", f"{field} fehlt.", field=field)
    if isinstance(value, bool):
        raise PriceAnalysisError(
            "invalid_number", f"{field} ist ein Wahrheitswert, keine Zahl.", field=field
        )
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        result = Decimal(repr(value))
    elif isinstance(value, str):
        text = value.strip()
        if "," in text:
            raise PriceAnalysisError(
                "invalid_number",
                f"{field}: Dezimalkomma wird nicht umgedeutet; Punkt verwenden.",
                field=field,
            )
        if not _PLAIN.fullmatch(text):
            raise PriceAnalysisError(
                "invalid_number", f"{field} ist keine einfache Dezimalzahl.", field=field
            )
        try:
            result = Decimal(text)
        except InvalidOperation as exc:  # pragma: no cover - regex guards this
            raise PriceAnalysisError(
                "invalid_number", f"{field} ist ungültig.", field=field
            ) from exc
    else:
        raise PriceAnalysisError(
            "invalid_number", f"{field} hat den Typ {type(value).__name__}.", field=field
        )
    if not result.is_finite():
        raise PriceAnalysisError("invalid_number", f"{field} muss endlich sein.", field=field)
    return result


def non_negative(value: Any, *, field: str) -> Decimal:
    """Like :func:`parse_decimal` but rejects negative values."""
    result = parse_decimal(value, field=field)
    if result < 0:
        raise PriceAnalysisError("negative", f"{field} darf nicht negativ sein.", field=field)
    return result


def optional_non_negative(value: Any, *, field: str) -> Decimal | None:
    """``None`` stays ``None`` (missing); anything else must be a valid non-negative number."""
    return None if value is None else non_negative(value, field=field)


def parse_day(value: Any, *, field: str = "stichtag") -> date:
    """A calendar day from ``date`` or ISO text ``YYYY-MM-DD``; datetimes are rejected."""
    if isinstance(value, datetime):
        raise PriceAnalysisError(
            "invalid_date",
            f"{field} muss ein Kalendertag sein, kein Zeitpunkt.",
            field=field,
        )
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            if len(value) != 10:
                raise ValueError(value)
            return date.fromisoformat(value)
        except ValueError as exc:
            raise PriceAnalysisError(
                "invalid_date", f"{field} muss im Format JJJJ-MM-TT angegeben sein.", field=field
            ) from exc
    raise PriceAnalysisError("invalid_date", f"{field} fehlt oder ist kein Datum.", field=field)


@dataclass(frozen=True)
class Rounding:
    """A named rounding rule: quantum and mode (for example 0.01, ROUND_HALF_UP)."""

    places: Decimal
    mode: str

    def __post_init__(self) -> None:
        if self.mode not in ROUNDING_MODES:
            raise ProfileError(f"Unbekannter Rundungsmodus {self.mode}.")
        if not self.places.is_finite() or self.places <= 0:
            raise ProfileError("Rundungsschritt muss positiv sein.")

    def apply(self, value: Decimal) -> Decimal:
        """Round ``value`` exactly once with this rule."""
        return value.quantize(self.places, rounding=ROUNDING_MODES[self.mode])

    def to_dict(self) -> dict[str, str]:
        """JSON view."""
        return {"places": str(self.places), "mode": self.mode}


def text(value: Decimal | None) -> str | None:
    """JSON-safe text form of an exact value."""
    return None if value is None else str(value)
