"""Printed German numbers with their precision; true zero versus missing value.

A report cell is one of three things: a number (``0,00`` is a number), a
missing-value marker (``k. A.``, ``–``, ``n. v.``) or text. These are never
mixed up: a missing value is not zero and zero is never printed as ``k. A.``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from auditcore_common.numbers_de import parse_number
from auditcore_common.text import group_thousands_de

MISSING_MARKERS = frozenset({"k. a.", "k.a.", "-", "–", "—", "n. v.", "n.v.", "x. x."})
"""Markers that stand for a missing value (compared case-insensitively)."""

MISSING_TEXT = "k. A."
"""Printed form of a missing value."""

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
    if value is None:
        return None
    return PrintedNumber(value, _decimals(cleaned), text.strip())


def exact(value: int | float | Decimal) -> PrintedNumber:
    """A computed value without printed rounding."""
    if isinstance(value, bool):
        raise TypeError("Wahrheitswerte sind keine Zahlen.")
    return PrintedNumber(Decimal(str(value)), None, str(value))


def read_cell(raw: object) -> Cell:
    """Classify a cell: number, ``MISSING`` or text (returned stripped).

    ``None`` and empty text are missing. Numbers from a computation are exact.
    """
    if raw is None:
        return MISSING
    if isinstance(raw, int | float | Decimal) and not isinstance(raw, bool):
        return exact(raw)
    text = str(raw).strip()
    if not text or text.lower() in MISSING_MARKERS:
        return MISSING
    number = read_number(text)
    return number if number is not None else text


def tolerance(left: PrintedNumber, right: PrintedNumber) -> Decimal:
    """Half a unit of the coarser printed side; zero when both are exact."""
    printed = [n.decimals for n in (left, right) if n.decimals is not None]
    if not printed:
        return Decimal(0)
    return Decimal(5) * Decimal(10) ** -(min(printed) + 1)


def same_value(left: PrintedNumber, right: PrintedNumber) -> bool:
    """Equal within the printed rounding of the coarser side."""
    return abs(left.value - right.value) <= tolerance(left, right)


def relative_deviation(actual: Decimal, expected: Decimal) -> Decimal | None:
    """``|actual - expected| / |expected|``; ``None`` for an expected zero."""
    if expected == 0:
        return None
    return abs(actual - expected) / abs(expected)


def format_de(value: Decimal | int | float | Missing | None, decimals: int = 2) -> str:
    """Print a value German style; ``None``/``MISSING`` become ``k. A.``, zero stays ``0,00``."""
    if value is None or value is MISSING:
        return MISSING_TEXT
    if isinstance(value, Missing):  # pragma: no cover - single member
        return MISSING_TEXT
    if decimals < 0:
        raise ValueError("decimals darf nicht negativ sein.")
    quantum = Decimal(1).scaleb(-decimals)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    if rounded.is_zero():
        rounded = abs(rounded)
    sign = "-" if rounded < 0 else ""
    integer, _, fraction = f"{abs(rounded):f}".partition(".")
    body = group_thousands_de(int(integer))
    return f"{sign}{body},{fraction}" if decimals else f"{sign}{body}"
