"""German amount display after the shared contract ``format-money``.

Python counterpart of ``formatEur`` in ``@auditcore/common``
(``contracts/common-cases/format-money.json``): two decimals, decimal comma,
thousands dots, a no-break space (U+00A0) before "€", commercial rounding
(half-up, away from zero) on the decimal value, and the shared empty value
"—" for missing or invalid input. Floats are read by their shortest decimal
form (``repr``), as JavaScript's ``String(number)`` does, so 0.125 and 1.005
round up like in the TypeScript implementation.

The catalogue target of this contract is ``auditcore_common.format_de``; the
function lives here until the next ``auditcore_common`` release, which needs
new exact pins in every package.
"""

from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

#: Shared empty value (``contracts/common-cases/decisions.json``, ``empty_value``).
EMPTY_VALUE = "—"
#: No-break space between amount and currency symbol (U+00A0).
NBSP = chr(0xA0)
_PLAIN = re.compile(r"-?\d+(?:\.\d+)?")


def _decimal_of_float(value: float) -> Decimal | None:
    if not math.isfinite(value):
        return None
    if abs(value) >= 1e21:
        # JavaScript: BigInt(Math.round(value)) – the exact integer of the double.
        return Decimal(int(value))
    return Decimal(repr(value))


def plain_decimal(value: object) -> Decimal | None:
    """Decimal value of a number or a plain decimal string; ``None`` if empty or invalid.

    Strings are trimmed and may start with ``+``; exponents, thousands
    separators and decimal commas are invalid (use ``numbers_de`` to parse
    user input). ``bool`` is not a number.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return _decimal_of_float(value)
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, str):
        text = value.strip().removeprefix("+")
        return Decimal(text) if _PLAIN.fullmatch(text) else None
    return None


def _grouped(digits: str) -> str:
    head = len(digits) % 3 or 3
    groups = [digits[:head]] + [digits[i : i + 3] for i in range(head, len(digits), 3)]
    return ".".join(groups)


def format_eur(value: object, *, empty: str = EMPTY_VALUE, digits: int = 2) -> str:
    """``1.234,50 €`` (U+00A0 before "€"), half-up rounded; ``empty`` for empty/invalid input.

    >>> format_eur(1234.5)
    '1.234,50\\xa0€'
    >>> format_eur(None)
    '—'
    """
    if not 0 <= digits <= 20:
        raise ValueError("digits: 0 bis 20 Nachkommastellen.")
    amount = plain_decimal(value)
    if amount is None:
        return empty
    try:
        rounded = amount.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    except InvalidOperation:  # more digits than the decimal context holds
        return empty
    sign = "-" if rounded < 0 else ""
    whole, _, fraction = f"{abs(rounded):f}".partition(".")
    text = _grouped(whole) + ("," + fraction if digits else "")
    return f"{sign}{text}{NBSP}€"
