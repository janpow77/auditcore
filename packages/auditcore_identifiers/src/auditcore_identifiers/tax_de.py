"""German tax identifiers: Steuer-IdNr. (§ 139b AO), Steuernummer, Handelsregisternummer."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from types import MappingProxyType

from auditcore_identifiers.checksums import is_ascii_digits, mod_11_10_check_digit, prepare
from auditcore_identifiers.result import (
    CheckDigit,
    CheckResult,
    IdentifierKind,
    Reason,
    invalid,
    valid,
)

#: First digits of the 13-digit federal Steuernummer (ELSTER) per Land.
#: Layout ``FFFF0BBBUUUUP``; NRW uses ``FFFF0BBBBUUUP`` (same length and position of the 0).
FEDERAL_TAX_NUMBER_PREFIXES: Mapping[str, str] = MappingProxyType(
    {
        "10": "Saarland",
        "11": "Berlin",
        "21": "Schleswig-Holstein",
        "22": "Hamburg",
        "23": "Niedersachsen",
        "24": "Bremen",
        "26": "Hessen",
        "27": "Rheinland-Pfalz",
        "28": "Baden-Württemberg",
        "30": "Brandenburg",
        "31": "Sachsen-Anhalt",
        "32": "Sachsen",
        "40": "Mecklenburg-Vorpommern",
        "41": "Thüringen",
        "5": "Nordrhein-Westfalen",
        "9": "Bayern",
    }
)
_TAX_NUMBER_SEPARATORS = "/-."
_REGISTER = re.compile(r"(HRA|HRB|GNR|GSR|PR|VR)([1-9][0-9]{0,5})([A-Z]{1,2})?", re.ASCII)
_REGISTER_WORD = r"(?:HRA|HRB|GnR|GsR|PR|VR)"
#: ``Amtsgericht Köln HRB 123`` / ``AG Köln, HRB 123`` (court in front).
_COURT_FIRST = re.compile(
    rf"\s*(?:Registergericht\s*:?\s*)?(?:Amtsgericht|AG)\s+(?P<court>[^,;:()]+?)\s*[,;:]?\s*"
    rf"(?:Registernummer\s*:?\s*)?(?P<number>{_REGISTER_WORD}\b.*?)\s*",
    re.IGNORECASE,
)
#: ``HRB 123, Amtsgericht Köln`` / ``HRB 123 (AG Köln)`` (court behind).
_COURT_LAST = re.compile(
    rf"\s*(?P<number>{_REGISTER_WORD}\b[^,;(]*?)\s*[,;]?\s*\(?\s*"
    rf"(?:Registergericht\s*:?\s*)?(?:Amtsgericht|AG)\s+(?P<court>[^,;:()]+?)\s*\)?\s*",
    re.IGNORECASE,
)
_REGISTER_TYPES = {"HRA": "HRA", "HRB": "HRB", "GNR": "GnR", "GSR": "GsR", "PR": "PR", "VR": "VR"}


def _digit_distribution_ok(first_ten: str) -> bool:
    """Exactly one digit twice or three times (not three in a row), the others once."""
    repeated = [(digit, n) for digit, n in Counter(first_ten).items() if n > 1]
    if len(repeated) != 1 or repeated[0][1] not in (2, 3):
        return False
    return repeated[0][0] * 3 not in first_ten


def check_tax_id(value: object) -> CheckResult:
    """Steuerliche Identifikationsnummer (IdNr): 11 digits, first digit not 0, digit
    distribution of the first ten digits and ISO 7064 MOD 11,10 check digit."""
    kind = IdentifierKind.TAX_ID
    text = prepare(kind, value, separators="/-.")
    if isinstance(text, CheckResult):
        return text
    if not is_ascii_digits(text):
        return invalid(kind, value, Reason.INVALID_CHARACTERS, "Steuer-ID besteht nur aus Ziffern")
    if len(text) != 11:
        return invalid(
            kind,
            value,
            Reason.INVALID_LENGTH,
            f"Steuer-ID muss 11 Ziffern haben, nicht {len(text)}",
            details={"length": len(text)},
        )
    if text[0] == "0" or not _digit_distribution_ok(text[:10]):
        return invalid(
            kind,
            value,
            Reason.INVALID_FORMAT,
            "Steuer-ID verletzt die Aufbauregeln (erste Ziffer, Ziffernverteilung)",
        )
    if mod_11_10_check_digit(text[:10]) != int(text[10]):
        return invalid(kind, value, Reason.INVALID_CHECKSUM, "Prüfziffer der Steuer-ID ist falsch")
    return valid(kind, value, text, country="DE", check_digit=CheckDigit.VERIFIED)


def format_tax_id(value: str) -> str:
    """Presentation form ``12 345 678 901``."""
    text = "".join(value.split())
    return " ".join((text[:2], text[2:5], text[5:8], text[8:]))


def _federal_land(text: str) -> str | None:
    for prefix in (text[:2], text[:1]):
        land = FEDERAL_TAX_NUMBER_PREFIXES.get(prefix)
        if land is not None:
            return land
    return None


def check_tax_number(value: object) -> CheckResult:
    """Steuernummer, coarse check without the Land-specific check digit.

    13 digits: federal format (known Land prefix, 5th digit ``0``); 10 or 11 digits:
    Land format (only length and digits). ``details["format"]`` names the variant.
    """
    kind = IdentifierKind.TAX_NUMBER
    text = prepare(kind, value, separators=_TAX_NUMBER_SEPARATORS)
    if isinstance(text, CheckResult):
        return text
    if not is_ascii_digits(text):
        return invalid(
            kind,
            value,
            Reason.INVALID_CHARACTERS,
            "Steuernummer besteht nur aus Ziffern und Trennzeichen",
        )
    if len(text) in (10, 11):
        return valid(
            kind,
            value,
            text,
            country="DE",
            details={"format": "land", "checksum": "not_checked"},
            check_digit=CheckDigit.NOT_CHECKED,
        )
    if len(text) != 13:
        return invalid(
            kind,
            value,
            Reason.INVALID_LENGTH,
            f"Steuernummer hat 10, 11 oder 13 Ziffern, nicht {len(text)}",
        )
    land = _federal_land(text)
    if land is None or text[4] != "0":
        return invalid(
            kind,
            value,
            Reason.INVALID_FORMAT,
            "13-stellige Steuernummer passt nicht zum Bundesschema",
        )
    return valid(
        kind,
        value,
        text,
        country="DE",
        details={"format": "federal", "land": land, "checksum": "not_checked"},
        check_digit=CheckDigit.NOT_CHECKED,
    )


def _split_court(value: object) -> tuple[object, str | None]:
    """Separate a register court given in front of or behind the number."""
    if not isinstance(value, str):
        return value, None
    for pattern in (_COURT_FIRST, _COURT_LAST):
        match = pattern.fullmatch(value)
        if match is not None:
            return match.group("number"), " ".join(match.group("court").split())
    return value, None


def check_register_number(value: object) -> CheckResult:
    """Handelsregisternummer (format only): ``HRA``/``HRB``/``GnR``/``GsR``/``PR``/``VR``
    plus a number from 1 to 999999 without leading zero and an optional suffix of one or
    two letters (e.g. ``HRB 12345 B``).

    A register court in front of or behind the number (``Amtsgericht Köln HRB 123``,
    ``HRB 123, AG Köln``) is separated and reported in ``details["court"]``; the court
    name itself is taken over as written and not checked against a list of courts.
    Whether the number is registered is not checked either (no check digit).
    """
    kind = IdentifierKind.REGISTER_NUMBER
    number_part, court = _split_court(value)
    text = prepare(kind, number_part, separators=".")
    if isinstance(text, CheckResult):
        return text
    match = _REGISTER.fullmatch(text)
    if match is None:
        return invalid(
            kind,
            value,
            Reason.INVALID_FORMAT,
            "Registernummer: Registerart (HRA, HRB, GnR, GsR, PR, VR) und Nummer ab 1 "
            "ohne führende Null",
        )
    register, number, suffix = match.group(1), match.group(2), match.group(3)
    normalized = f"{_REGISTER_TYPES[register]} {number}" + (f" {suffix}" if suffix else "")
    return valid(
        kind,
        value,
        normalized,
        country="DE",
        details={
            "register": _REGISTER_TYPES[register],
            "number": number,
            "suffix": suffix,
            "court": court,
        },
        check_digit=CheckDigit.NONE,
    )
