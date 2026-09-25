"""Value semantics of the characterized sources, expressed without pandas.

The legacy engines work on pandas frames. Their scalar semantics are
reproduced here and pinned by the recorded fixtures:

* *missing* is ``None``, a float ``NaN``, ``pandas.NA`` or ``NaT``;
* ``strict`` amounts accept numbers only (strings raise ``InputError`` — the
  source raises ``TypeError`` as well);
* ``coerce`` numbers follow ``pandas.to_numeric(errors="coerce")``: numbers,
  and decimal strings with optional sign, exponent and surrounding whitespace;
  everything else (``"6,0"``, ``"0x10"``, ``"6_0"``, ``"abc"``) is missing.
"""

from __future__ import annotations

import math
import numbers
import re
from collections.abc import Hashable
from datetime import date, datetime
from decimal import Decimal

from .errors import InputError

_DECIMAL = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_INFINITY = re.compile(r"[+-]?(?:inf|infinity)", re.IGNORECASE)


def is_missing(value: object) -> bool:
    """``None``, NaN, ``pandas.NA`` and ``NaT`` are missing; everything else is a value."""
    if value is None:
        return True
    if isinstance(value, str | bool | int):
        return False
    try:
        return bool(value != value)
    except TypeError:  # pandas.NA: comparison is ambiguous
        return True


def strict_amount(value: object, field: str, missing_value: float | None) -> float | None:
    """Number or ``missing_value``; strings and booleans violate the contract."""
    if is_missing(value):
        return missing_value
    if isinstance(value, bool) or not isinstance(value, numbers.Real | Decimal):
        raise InputError(f"Feld {field!r} erwartet einen Betrag, erhalten: {value!r}.")
    return float(value)


def coerce_number(value: object, field: str) -> float | None:
    """``pandas.to_numeric(errors="coerce")`` for one scalar; ``None`` = missing."""
    if is_missing(value):
        return None
    if isinstance(value, bool):
        raise InputError(f"Feld {field!r}: Wahrheitswerte sind keine Zahlen ({value!r}).")
    if isinstance(value, numbers.Real | Decimal):
        number = float(value)
        return None if math.isnan(number) else number
    if isinstance(value, str):
        text = value.strip()
        if _DECIMAL.fullmatch(text):
            return float(text)
        if _INFINITY.fullmatch(text):
            return float(text)
        return None
    return None


def text(value: object) -> str | None:
    """``str(value)`` for present values (``astype(str)``), ``None`` when missing."""
    return None if is_missing(value) else str(value)


def as_date(value: object, field: str) -> date | None:
    """Calendar date of a ``date``/``datetime``/ISO string; ``None`` when missing."""
    if is_missing(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError as exc:
            raise InputError(f"Feld {field!r}: kein ISO-Datum {value!r}.") from exc
    raise InputError(f"Feld {field!r}: kein Datum {value!r}.")


def hashable(value: object, field: str) -> Hashable:
    """Grouping key; unhashable values violate the contract."""
    if not isinstance(value, Hashable):
        raise InputError(f"Feld {field!r}: Wert ist nicht als Schlüssel nutzbar.")
    try:
        hash(value)
    except TypeError as exc:
        raise InputError(f"Feld {field!r}: Wert ist nicht als Schlüssel nutzbar.") from exc
    return value


def fmt(number: float) -> str:
    """German number format for reasons (two decimals, dot as thousands separator)."""
    if math.isinf(number) or math.isnan(number):
        return str(number)
    raw = f"{number:,.2f}"
    return raw.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
