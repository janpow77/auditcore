"""Check digit algorithms (ISO 7064) and input preparation shared by all checks."""

from __future__ import annotations

import re

from auditcore_identifiers.result import CheckResult, IdentifierKind, Reason, invalid

_ALNUM = re.compile(r"[A-Z0-9]*", re.ASCII)
_DIGITS = re.compile(r"[0-9]+", re.ASCII)
_WHITESPACE = re.compile(r"\s+")


def is_ascii_alnum(text: str) -> bool:
    """Only ASCII capital letters and digits (``str.isalnum`` also accepts ``ä`` or ``٣``)."""
    return _ALNUM.fullmatch(text) is not None


def is_ascii_digits(text: str) -> bool:
    """Only ASCII digits 0–9 (``str.isdigit`` also accepts ``²`` or ``٣``)."""
    return _DIGITS.fullmatch(text) is not None


def alnum_to_digits(text: str) -> str:
    """Replace letters by two digits (A=10 … Z=35), ISO 7064 MOD 97-10 convention."""
    return "".join(str(int(char, 36)) for char in text)


def mod97(text: str) -> int:
    """Remainder modulo 97 of the alphanumeric string (ASCII A–Z, 0–9)."""
    return int(alnum_to_digits(text)) % 97


def mod97_check_digits(body: str) -> str:
    """Two check digits so that ``body + digits`` has remainder 1 (ISO 7064 MOD 97-10)."""
    return f"{98 - mod97(body + '00'):02d}"


def mod_11_10_check_digit(digits: str) -> int:
    """ISO 7064 MOD 11,10 check digit (German USt-IdNr. and Steuer-IdNr.)."""
    product = 10
    for char in digits:
        total = (int(char) + product) % 10 or 10
        product = (2 * total) % 11
    check = 11 - product
    return 0 if check == 10 else check


def prepare(
    kind: IdentifierKind, value: object, separators: str = ""
) -> str | CheckResult:
    """Normalise the raw input or return the MISSING/INVALID_TYPE result.

    Integers are accepted and converted (tax identifiers often arrive as numbers);
    whitespace of any kind and the given separators are removed, letters upper-cased.
    """
    if value is None:
        return invalid(kind, value, Reason.MISSING, "Wert fehlt")
    if isinstance(value, bool) or not isinstance(value, str | int):
        return invalid(kind, value, Reason.INVALID_TYPE, "Wert ist keine Zeichenkette")
    text = _WHITESPACE.sub("", str(value))
    for separator in separators:
        text = text.replace(separator, "")
    if not text:
        return invalid(kind, value, Reason.MISSING, "Wert fehlt")
    if not text.isascii():
        # Before upper-casing: "ß".upper() would become "SS" and look valid.
        return invalid(kind, value, Reason.INVALID_CHARACTERS, "Unzulässige Zeichen (nur A–Z, 0–9)")
    return text.upper()
