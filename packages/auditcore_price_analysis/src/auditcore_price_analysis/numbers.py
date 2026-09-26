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

from auditcore_common.numbers_de import parse_number_result

from .errors import PriceAnalysisError, ProfileError

_PLAIN = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)")
ROUNDING_MODES = {
    "ROUND_HALF_UP": ROUND_HALF_UP,
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_DOWN": ROUND_DOWN,
    "ROUND_UP": ROUND_UP,
}


def _legacy_decimal_from_text(value: str, field: str) -> Decimal:
    """Plain decimal text with a point; commas and exponents are rejected (0.1.1)."""
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
        return Decimal(text)
    except InvalidOperation as exc:  # pragma: no cover - regex guards this
        raise PriceAnalysisError("invalid_number", f"{field} ist ungültig.", field=field) from exc


def _decimal_from_text(value: str, field: str) -> Decimal:
    """Point text as before; any other text in German notation (contract ``parse-number``).

    Plain point text (``"2.5"``, ``"1.234"``, ``".5"``) is the package's own
    text format and keeps its value. Everything else is read in mode ``de`` of
    ``auditcore_common.numbers_de``: ``"1.234,56"``, ``"1234,56"``, ``"1,5 €"``,
    ``"1.000.000"``. Ambiguous German text (``"1,234"``, ``"1.234 €"``) is
    rejected with ``ambiguous_number``; exponents stay invalid.
    """
    text = value.strip()
    if _PLAIN.fullmatch(text):
        return Decimal(text)
    parsed = parse_number_result(text, "de")
    if parsed.value is not None:
        return parsed.value
    if parsed.hint == "mehrdeutig":
        raise PriceAnalysisError(
            "ambiguous_number",
            f"{field}: „{text}“ ist mehrdeutig; Dezimalkomma mit höchstens zwei "
            "Nachkommastellen (1.234,56) oder Dezimalpunkt ohne Tausendertrenner "
            "(1234.567) angeben.",
            field=field,
        )
    raise PriceAnalysisError(
        "invalid_number", f"{field} ist keine gültige Dezimalzahl.", field=field
    )


def _exact_decimal(value: object, field: str, *, legacy: bool = False) -> Decimal:
    """Exact decimal of a supported type (booleans and ``None`` are handled by the caller)."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    if isinstance(value, str):
        reader = _legacy_decimal_from_text if legacy else _decimal_from_text
        return reader(value, field)
    raise PriceAnalysisError(
        "invalid_number", f"{field} hat den Typ {type(value).__name__}.", field=field
    )


def _checked_decimal(value: object, field: str, *, legacy: bool) -> Decimal:
    if value is None:
        raise PriceAnalysisError("missing_value", f"{field} fehlt.", field=field)
    if isinstance(value, bool):
        raise PriceAnalysisError(
            "invalid_number", f"{field} ist ein Wahrheitswert, keine Zahl.", field=field
        )
    result = _exact_decimal(value, field, legacy=legacy)
    if not result.is_finite():
        raise PriceAnalysisError("invalid_number", f"{field} muss endlich sein.", field=field)
    return result


def parse_decimal(value: object, *, field: str) -> Decimal:
    """Exact decimal from ``int``, ``Decimal``, finite ``float`` or number text.

    Text is plain point notation (``"2.5"``, unchanged) or German notation
    (``"1.234,56 €"``, ``"1234,56"``); ambiguous German text such as
    ``"1,234"`` is rejected with code ``ambiguous_number`` instead of being
    guessed (PA-C01). ``None`` is
    *missing*, never zero; booleans, exponents and non-finite values are
    rejected. The point-only reader of 0.1.1 is :func:`legacy_parse_decimal`.
    """
    return _checked_decimal(value, field, legacy=False)


def legacy_parse_decimal(value: object, *, field: str) -> Decimal:
    """Characterized 0.1.1 behaviour: point text only, every comma is rejected.

    ``"1.234"`` is 1.234 and ``"1.234,56"``/``"1234,56"`` raise
    ``invalid_number`` („Dezimalkomma wird nicht umgedeutet“).
    """
    return _checked_decimal(value, field, legacy=True)


def non_negative(value: object, *, field: str) -> Decimal:
    """Like :func:`parse_decimal` but rejects negative values."""
    result = parse_decimal(value, field=field)
    if result < 0:
        raise PriceAnalysisError("negative", f"{field} darf nicht negativ sein.", field=field)
    return result


def optional_non_negative(value: object, *, field: str) -> Decimal | None:
    """``None`` stays ``None`` (missing); anything else must be a valid non-negative number."""
    return None if value is None else non_negative(value, field=field)


def parse_day(value: object, *, field: str = "stichtag") -> date:
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
