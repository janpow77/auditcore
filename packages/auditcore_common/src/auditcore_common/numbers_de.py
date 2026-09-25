"""Number input after the shared contract ``parse-number`` (``contracts/common-cases``).

Three notations:

``de``
    Amount fields: decimal comma, the point only as thousands separator in
    groups of three, at most ``max_fraction_digits`` (default 2) decimals.
    ``"1.5"`` and ``"1.234"`` are ambiguous and rejected with hint
    ``"mehrdeutig"``; ``"1,234"`` is ambiguous while the two-digit limit
    applies (it could be an English thousands group).
``en``
    Decimal point, the comma only as thousands separator.
``auto``
    Imports from foreign files: the last separator decides; a single
    separator followed by exactly three digits after a one- to three-digit
    integer part (``"1.234"``, ``"1,234"``) is ambiguous and rejected.

Currency marks (``€``, ``EUR``) and white space (also U+00A0 and U+202F) are
removed, U+2212 counts as minus. Input made only of separators, signs or
currency counts as empty (hint ``"leer"``). Nothing ambiguous is guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Mode = Literal["de", "en", "auto"]
Hint = Literal["leer", "mehrdeutig", "ungültig"]

AMOUNT_FRACTION_DIGITS = 2
"""Decision ``amount_max_fraction_digits_de``: at most two decimals in amounts (de)."""

HINT_MESSAGES: dict[str, str] = {
    "leer": "Kein Wert angegeben.",
    "mehrdeutig": (
        "Mehrdeutige Schreibweise: Dezimalkomma verwenden, Punkte nur als "
        "Tausendertrenner in Dreiergruppen (z. B. 1.234,50)."
    ),
    "ungültig": "Keine gültige Zahl.",
}

_CURRENCY = re.compile(r"€|\bEUR\b", re.IGNORECASE)
_SPACES = re.compile("[  \t]")
_GROUP_SPACE = re.compile(r"(?<=\d) (?=\d{3}(?!\d))")
_LEADING_SIGN = re.compile(r"^-\s+")
_ONLY_MARKS = re.compile(r"[\s.,\-]*")
_DE = re.compile(r"-?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?")
_EN = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
_DOT_DECIMAL = re.compile(r"-?\d+\.\d+")
_SEPARATORS = {"de": (".", ","), "en": (",", ".")}


@dataclass(frozen=True)
class ParsedNumber:
    """Result of :func:`parse_number_result`: a value or a hint, never both."""

    value: Decimal | None
    hint: Hint | None = None

    @property
    def ok(self) -> bool:
        """``True`` when a value was read."""
        return self.value is not None

    @property
    def message(self) -> str | None:
        """German text for the hint (for a form or an import report)."""
        return None if self.hint is None else HINT_MESSAGES[self.hint]


_EMPTY = ParsedNumber(None, "leer")
_AMBIGUOUS = ParsedNumber(None, "mehrdeutig")
_INVALID = ParsedNumber(None, "ungültig")


def _clean(text: str) -> str:
    cleaned = _SPACES.sub(" ", _CURRENCY.sub("", text)).replace("−", "-").strip()
    cleaned = _LEADING_SIGN.sub("-", cleaned)
    return _GROUP_SPACE.sub("", cleaned)


def _decimal(text: str, group: str, decimal: str) -> ParsedNumber:
    value = Decimal(text.replace(group, "").replace(decimal, "."))
    return ParsedNumber(value.copy_abs() if value.is_zero() else value)


def _parse_de(text: str, max_fraction_digits: int | None) -> ParsedNumber:
    match = _DE.fullmatch(text)
    if match is None:
        return _AMBIGUOUS if _DOT_DECIMAL.fullmatch(text) else _INVALID
    fraction = match[1] or ""
    if "," not in text and text.count(".") == 1:
        return _AMBIGUOUS
    if max_fraction_digits is not None and len(fraction) > max_fraction_digits:
        three_digits_only = len(fraction) == 3 and "." not in text
        return _AMBIGUOUS if three_digits_only else _INVALID
    return _decimal(text, ".", ",")


def _parse_en(text: str) -> ParsedNumber:
    if _EN.fullmatch(text) is None:
        return _INVALID
    return _decimal(text, ",", ".")


def _auto_mode(text: str) -> str | None:
    """Notation of ``text`` from its separators; ``None`` when ambiguous."""
    last_dot, last_comma = text.rfind("."), text.rfind(",")
    if last_dot >= 0 and last_comma >= 0:
        return "de" if last_comma > last_dot else "en"
    separator = "." if last_dot >= 0 else "," if last_comma >= 0 else ""
    if not separator:
        return "de"
    if text.count(separator) > 1:
        return "de" if separator == "." else "en"
    integer, fraction = text.lstrip("-").split(separator)
    if len(fraction) == 3 and 1 <= len(integer) <= 3 and not integer.startswith("0"):
        return None
    return "en" if separator == "." else "de"


def parse_number_result(
    text: object,
    mode: Mode = "de",
    *,
    max_fraction_digits: int | None = AMOUNT_FRACTION_DIGITS,
) -> ParsedNumber:
    """Read ``text`` in notation ``mode``; the result carries a hint when nothing was read.

    ``max_fraction_digits`` limits the decimals in mode ``de`` (amounts);
    ``None`` lifts the limit for quantities and rates, then ``"1,234"`` is
    1.234. Non-text input is ``"ungültig"``.
    """
    if not isinstance(text, str):
        return _INVALID
    cleaned = _clean(text)
    if _ONLY_MARKS.fullmatch(cleaned):
        return _EMPTY
    if mode == "de":
        return _parse_de(cleaned, max_fraction_digits)
    if mode == "en":
        return _parse_en(cleaned)
    if mode != "auto":
        raise ValueError(f"Unknown notation {mode!r}")
    chosen = _auto_mode(cleaned)
    if chosen is None:
        return _AMBIGUOUS
    return _parse_de(cleaned, None) if chosen == "de" else _parse_en(cleaned)


def parse_number(
    text: object,
    mode: Mode = "de",
    *,
    max_fraction_digits: int | None = AMOUNT_FRACTION_DIGITS,
) -> Decimal | None:
    """Exact value of ``text`` or ``None`` (empty, ambiguous or invalid)."""
    return parse_number_result(text, mode, max_fraction_digits=max_fraction_digits).value


def parse_de_number(
    text: object, *, max_fraction_digits: int | None = AMOUNT_FRACTION_DIGITS
) -> Decimal | None:
    """German amount text (``"1.234,56 €"``) as ``Decimal``; ``None`` if not unambiguous."""
    return parse_number(text, "de", max_fraction_digits=max_fraction_digits)


__all__ = [
    "AMOUNT_FRACTION_DIGITS",
    "HINT_MESSAGES",
    "Hint",
    "Mode",
    "ParsedNumber",
    "parse_de_number",
    "parse_number",
    "parse_number_result",
]
