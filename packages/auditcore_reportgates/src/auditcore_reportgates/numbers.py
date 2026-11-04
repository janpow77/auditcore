"""Printed German numbers with their precision; true zero versus missing value.

A report cell is one of three things: a number (``0,00`` is a number), a
missing-value marker (``k. A.``, ``–``, ``n. v.``) or text. These are never
mixed up: a missing value is not zero and zero is never printed as ``k. A.``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import (
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Decimal,
)
from enum import Enum

from auditcore_common.numbers_de import parse_number
from auditcore_common.text import group_thousands_de

MISSING_MARKERS = frozenset(
    {"k. a.", "k.a.", "-", "–", "—", "n. v.", "n.v.", "x. x.", ".", ":", "..."}
)
"""Markers that stand for a missing value (compared case-insensitively).

``.`` (Zahlenwert unbekannt) and ``:`` (Eurostat: not available) included.
"""

ZERO_DASHES = frozenset({"-", "–", "—"})
"""Destatis notation: a dash means "genau null". Used when ``dash_is_zero``."""

MISSING_TEXT = "k. A."
"""Printed form of a missing value."""

ROUNDING_MODES = frozenset(
    {
        ROUND_05UP,
        ROUND_CEILING,
        ROUND_DOWN,
        ROUND_FLOOR,
        ROUND_HALF_DOWN,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_UP,
    }
)
"""Rounding modes of :mod:`decimal` accepted by :func:`format_de`."""

_THOUSANDS_ONLY = re.compile(r"-?\d{1,3}(?:\.\d{3})+")
_FOOTNOTE = re.compile(r"\*+$")
_DASHES = str.maketrans({"–": "-", "−": "-", "—": "-"})


class Missing(Enum):
    """The single missing-value marker."""

    VALUE = "missing"


MISSING = Missing.VALUE


@dataclass(frozen=True)
class PrintedNumber:
    """A number as printed: exact value and printed decimals.

    ``decimals`` is ``None`` for an exact (computed, unrounded) value.
    """

    value: Decimal
    decimals: int | None
    text: str = ""


Cell = PrintedNumber | Missing | str


def _decimals(text: str) -> int:
    return len(text.split(",", 1)[1]) if "," in text else 0


def read_number(text: str) -> PrintedNumber | None:
    """German printed number (``"1.234,50"``, ``"2,2 %"``, ``"– 5,1"``) or ``None``.

    The point is a thousands separator only in groups of three; anything
    ambiguous (``"2.5"``) is not read.
    """
    cleaned = _FOOTNOTE.sub("", text.translate(_DASHES).replace("%", "").strip())
    cleaned = re.sub(r"(?<=-)\s+", "", cleaned)
    if _THOUSANDS_ONLY.fullmatch(cleaned):
        cleaned = cleaned.replace(".", "")
    value = parse_number(cleaned, "de", max_fraction_digits=None)
    if value is None or not value.is_finite():
        return None
    return PrintedNumber(value, _decimals(cleaned), text.strip())


def _finite(value: int | float | Decimal) -> Decimal:
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError(f"Kein endlicher Zahlwert: {value!r}")
    return number


def exact(value: int | float | Decimal) -> PrintedNumber:
    """A computed value without printed rounding; NaN and infinity are rejected."""
    if isinstance(value, bool):
        raise TypeError("Wahrheitswerte sind keine Zahlen.")
    return PrintedNumber(_finite(value), None, str(value))


def read_cell(
    raw: object,
    *,
    missing_markers: Iterable[str] = MISSING_MARKERS,
    dash_is_zero: bool = False,
) -> Cell:
    """Classify a cell: number, ``MISSING`` or text (returned stripped).

    ``None`` and empty text are missing. Numbers from a computation are exact;
    NaN and infinity raise ``ValueError``. ``missing_markers`` replaces the
    default markers; with ``dash_is_zero`` a lone dash is exactly zero
    (Destatis) instead of missing.
    """
    if raw is None:
        return MISSING
    if isinstance(raw, int | float | Decimal) and not isinstance(raw, bool):
        return exact(raw)
    text = str(raw).strip()
    if dash_is_zero and text in ZERO_DASHES:
        return PrintedNumber(Decimal(0), None, text)
    markers = {marker.lower() for marker in missing_markers}
    if not text or text.lower() in markers:
        return MISSING
    number = read_number(text)
    return number if number is not None else text


def _epsilon(epsilon: Decimal | int | float) -> Decimal:
    if isinstance(epsilon, bool):
        raise ValueError(f"epsilon muss eine endliche Zahl sein: {epsilon!r}")
    number = _finite(epsilon)
    if number < 0:
        raise ValueError(f"epsilon darf nicht negativ sein: {epsilon!r}")
    return number


def tolerance(
    left: PrintedNumber, right: PrintedNumber, *, epsilon: Decimal | int | float = 0
) -> Decimal:
    """Half a unit of the coarser printed side plus ``epsilon``.

    Zero (plus ``epsilon``) when both sides are exact. ``epsilon`` is an
    absolute buffer for values that went through binary floating point
    (``15.850000000000001`` against a printed ``15,8``); the default ``0``
    compares strictly. A negative or non-finite ``epsilon`` raises ``ValueError``.
    """
    buffer = _epsilon(epsilon)
    printed = [n.decimals for n in (left, right) if n.decimals is not None]
    if not printed:
        return buffer
    return Decimal(5) * Decimal(10) ** -(min(printed) + 1) + buffer


def same_value(
    left: PrintedNumber, right: PrintedNumber, *, epsilon: Decimal | int | float = 0
) -> bool:
    """Equal within the printed rounding of the coarser side (plus ``epsilon``)."""
    return abs(left.value - right.value) <= tolerance(left, right, epsilon=epsilon)


def relative_deviation(actual: Decimal, expected: Decimal) -> Decimal | None:
    """``|actual - expected| / |expected|``; ``None`` for an expected zero."""
    if expected == 0:
        return None
    return abs(actual - expected) / abs(expected)


def format_de(
    value: Decimal | int | float | Missing | None,
    decimals: int = 2,
    *,
    rounding: str = ROUND_HALF_UP,
) -> str:
    """Print a value German style; ``None``/``MISSING`` become ``k. A.``, zero stays ``0,00``.

    ``rounding`` is a :mod:`decimal` mode, by default ``ROUND_HALF_UP``
    (kaufmännisch); ``ROUND_HALF_EVEN`` rounds half to even. A float is taken
    by its shortest representation (``str``): ``2.675`` is the tie 2,675. Pass
    ``Decimal(x)`` to round the exact binary value as Python's ``format`` does.
    A negative zero prints without sign. ``decimals`` must be a non-negative
    integer; rounding to tens is not offered (``ValueError``), scale the value
    first. An unknown ``rounding`` and NaN or infinity raise ``ValueError``.
    """
    if value is None or value is MISSING:
        return MISSING_TEXT
    if isinstance(value, Missing):  # pragma: no cover - single member
        return MISSING_TEXT
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        raise ValueError(
            f"decimals muss eine nichtnegative ganze Zahl sein, erhalten: {decimals!r}; "
            "für Rundung auf Zehner den Wert vorher durch 10 teilen."
        )
    if rounding not in ROUNDING_MODES:
        raise ValueError(f"Unbekannte Rundungsart: {rounding!r}")
    quantum = Decimal(1).scaleb(-decimals)
    rounded = _finite(value).quantize(quantum, rounding=rounding)
    if rounded.is_zero():
        rounded = abs(rounded)
    sign = "-" if rounded < 0 else ""
    integer, _, fraction = f"{abs(rounded):f}".partition(".")
    body = group_thousands_de(int(integer))
    return f"{sign}{body},{fraction}" if decimals else f"{sign}{body}"
