"""VAT identification numbers (USt-IdNr.): formats of all EU member states.

Formats follow the structure published by the European Commission for VIES
(``EL`` for Greece, ``XI`` for Northern Ireland). Check digits are verified for
Germany (ISO 7064 MOD 11,10, BZSt procedure) and Austria (BMF procedure); for
the other states the format is checked and ``details["checksum"]`` says
``"not_checked"``. ``GB`` is supported as non-EU format (``details["eu"]``).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from types import MappingProxyType

from auditcore_identifiers.checksums import is_ascii_alnum, mod_11_10_check_digit, prepare
from auditcore_identifiers.registry import COUNTRY_CODES
from auditcore_identifiers.result import CheckResult, IdentifierKind, Reason, invalid, valid

_KIND = IdentifierKind.VAT_ID
_UK = r"[0-9]{9}|[0-9]{12}|GD[0-4][0-9]{2}|HA[5-9][0-9]{2}"

#: Number part (without the prefix) per VAT prefix, EU member states and XI.
EU_VAT_FORMATS: Mapping[str, str] = MappingProxyType({
    "AT": r"U[0-9]{8}",
    "BE": r"[01][0-9]{9}",
    "BG": r"[0-9]{9,10}",
    "CY": r"[0-9]{8}[A-Z]",
    "CZ": r"[0-9]{8,10}",
    "DE": r"[1-9][0-9]{8}",
    "DK": r"[0-9]{8}",
    "EE": r"[0-9]{9}",
    "EL": r"[0-9]{9}",
    "ES": r"[A-Z0-9][0-9]{7}[A-Z0-9]",
    "FI": r"[0-9]{8}",
    "FR": r"[A-HJ-NP-Z0-9]{2}[0-9]{9}",
    "HR": r"[0-9]{11}",
    "HU": r"[0-9]{8}",
    "IE": r"[0-9]{7}[A-W][A-I]?|[0-9][A-Z+*][0-9]{5}[A-W]",
    "IT": r"[0-9]{11}",
    "LT": r"[0-9]{9}|[0-9]{12}",
    "LU": r"[0-9]{8}",
    "LV": r"[0-9]{11}",
    "MT": r"[0-9]{8}",
    "NL": r"[0-9]{9}B[0-9]{2}",
    "PL": r"[0-9]{10}",
    "PT": r"[0-9]{9}",
    "RO": r"[1-9][0-9]{1,9}",
    "SE": r"[0-9]{10}01",
    "SI": r"[1-9][0-9]{7}",
    "SK": r"[1-9][0-9]{9}",
    "XI": _UK,
})
#: Non-EU VAT formats the strict profile knows.
OTHER_VAT_FORMATS: Mapping[str, str] = MappingProxyType({"GB": _UK})

_PATTERNS = {
    prefix: re.compile(pattern, re.ASCII)
    for prefix, pattern in {**EU_VAT_FORMATS, **OTHER_VAT_FORMATS}.items()
}
#: Characters removed before the check (as in flowinvoice ``_normalize_vat_id``).
VAT_SEPARATORS = ".-/\\"


def de_vat_check_digit(first_eight: str) -> int:
    """Check digit of the German USt-IdNr. (ISO 7064 MOD 11,10)."""
    return mod_11_10_check_digit(first_eight)


def at_uid_check_digit(first_seven: str) -> int:
    """Check digit of the Austrian UID (``ATU`` + 8 digits, BMF procedure)."""
    digits = [int(char) for char in first_seven]
    total = sum(d if i % 2 == 0 else (2 * d) // 10 + (2 * d) % 10 for i, d in enumerate(digits))
    return (10 - (total + 4) % 10) % 10


def _de_ok(number: str) -> bool:
    return de_vat_check_digit(number[:8]) == int(number[8])


def _at_ok(number: str) -> bool:
    return at_uid_check_digit(number[1:8]) == int(number[8])


_CHECK_DIGITS: Mapping[str, Callable[[str], bool]] = MappingProxyType(
    {"DE": _de_ok, "AT": _at_ok}
)


def normalize_vat_id(value: str) -> str:
    """Upper case without whitespace and separators ``. - / \\`` (no validation)."""
    text = "".join(value.split()).upper()
    for separator in VAT_SEPARATORS:
        text = text.replace(separator, "")
    return text


def _split(value: object, text: str, country: str | None) -> tuple[str, str] | CheckResult:
    head = text[:2]
    has_prefix = head.isalpha() and (head in _PATTERNS or head in COUNTRY_CODES or head == "EL")
    if country is None:
        if not has_prefix:
            return invalid(_KIND, value, Reason.INVALID_FORMAT,
                           "USt-IdNr. ohne Länderpräfix (z. B. DE)")
        return head, text[2:]
    wanted = "EL" if country.upper() == "GR" else country.upper()
    if not has_prefix:
        return wanted, text
    if head != wanted:
        return invalid(_KIND, value, Reason.COUNTRY_MISMATCH,
                       f"USt-IdNr. beginnt mit {head}, erwartet wurde {wanted}", country=head)
    return head, text[2:]


def _unknown(value: object, prefix: str) -> CheckResult:
    hint = " (Griechenland verwendet EL)" if prefix == "GR" else ""
    return invalid(_KIND, value, Reason.UNKNOWN_COUNTRY,
                   f"Für {prefix} ist kein USt-IdNr.-Format bekannt{hint}", country=prefix)


def check_vat_id(value: object, country: str | None = None) -> CheckResult:
    """Strict check of a VAT identification number.

    ``country`` (e.g. ``"DE"``) restricts the accepted prefix; a number given
    without prefix is then checked for that country.
    """
    text = prepare(_KIND, value, separators=VAT_SEPARATORS)
    if isinstance(text, CheckResult):
        return text
    if not is_ascii_alnum(text.replace("+", "").replace("*", "")):
        return invalid(_KIND, value, Reason.INVALID_CHARACTERS,
                       "USt-IdNr. enthält unzulässige Zeichen")
    split = _split(value, text, country)
    if isinstance(split, CheckResult):
        return split
    prefix, number = split
    pattern = _PATTERNS.get(prefix)
    if pattern is None:
        return _unknown(value, prefix)
    if pattern.fullmatch(number) is None:
        return invalid(_KIND, value, Reason.INVALID_FORMAT,
                       f"USt-IdNr. entspricht nicht dem Format für {prefix}", country=prefix)
    checker = _CHECK_DIGITS.get(prefix)
    if checker is not None and not checker(number):
        return invalid(_KIND, value, Reason.INVALID_CHECKSUM,
                       "Prüfziffer der USt-IdNr. ist falsch", country=prefix)
    return valid(_KIND, value, prefix + number, country=prefix,
                 details={"eu": prefix in EU_VAT_FORMATS,
                          "checksum": "verified" if checker else "not_checked"})
