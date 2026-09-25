"""IBAN (ISO 13616) and BIC (ISO 9362) – strict checks."""

from __future__ import annotations

import re

from auditcore_identifiers.checksums import is_ascii_alnum, mod97, mod97_check_digits, prepare
from auditcore_identifiers.registry import (
    BBAN_PATTERNS,
    COUNTRY_CODES,
    IBAN_LENGTHS,
    IBAN_REGISTRY_RELEASE,
)
from auditcore_identifiers.result import CheckResult, IdentifierKind, Reason, invalid, valid

_KIND = IdentifierKind.IBAN
_HEAD = re.compile(r"[A-Z]{2}[0-9]{2}", re.ASCII)
_BIC = re.compile(r"[A-Z0-9]{4}([A-Z]{2})[A-Z0-9]{2}(?:[A-Z0-9]{3})?", re.ASCII)
#: Paper form may carry the literal "IBAN" in front (ISO 13616-1, 5.3).
_PAPER_PREFIX = "IBAN"


def _iban_text(value: object) -> str | CheckResult:
    text = prepare(_KIND, value, separators="-")
    if isinstance(text, str) and text.startswith(_PAPER_PREFIX):
        text = text[len(_PAPER_PREFIX) :] or text
    return text


def _iban_structure(value: object, text: str) -> CheckResult | None:
    if not is_ascii_alnum(text):
        return invalid(_KIND, value, Reason.INVALID_CHARACTERS,
                       "IBAN enthält unzulässige Zeichen (nur A–Z, 0–9)")
    if _HEAD.match(text) is None:
        return invalid(_KIND, value, Reason.INVALID_FORMAT,
                       "IBAN muss mit Ländercode und zwei Prüfziffern beginnen")
    country = text[:2]
    expected = IBAN_LENGTHS.get(country)
    if expected is None:
        return invalid(_KIND, value, Reason.UNKNOWN_COUNTRY,
                       f"Land {country} ist im IBAN-Register nicht verzeichnet", country=country)
    if len(text) != expected:
        return invalid(_KIND, value, Reason.INVALID_LENGTH,
                       f"IBAN für {country} muss {expected} Zeichen haben, nicht {len(text)}",
                       country=country, details={"expected_length": expected,
                                                 "length": len(text)})
    if BBAN_PATTERNS[country].fullmatch(text[4:]) is None:
        return invalid(_KIND, value, Reason.INVALID_FORMAT,
                       f"Kontoteil (BBAN) entspricht nicht dem Aufbau für {country}",
                       country=country)
    return None


def check_iban(value: object) -> CheckResult:
    """Strict IBAN check: characters, country, length, BBAN structure, MOD 97-10.

    Accepts the paper form (groups of four, optional ``IBAN`` prefix, hyphens) and
    returns the electronic form in ``normalized``.
    """
    text = _iban_text(value)
    if isinstance(text, CheckResult):
        return text
    problem = _iban_structure(value, text)
    if problem is not None:
        return problem
    country = text[:2]
    if mod97(text[4:] + text[:4]) != 1:
        return invalid(_KIND, value, Reason.INVALID_CHECKSUM, "IBAN-Prüfziffer ist falsch",
                       country=country)
    return valid(_KIND, value, text, country=country,
                 details={"bban": text[4:], "check_digits": text[2:4],
                          "registry": IBAN_REGISTRY_RELEASE})


def iban_check_digits(country: str, bban: str) -> str:
    """Two ISO 13616 check digits for ``country`` + ``bban`` (for test data)."""
    if not (len(country) == 2 and is_ascii_alnum(country) and country.isalpha()):
        raise ValueError("Ländercode aus zwei Großbuchstaben erwartet")
    if not bban or not is_ascii_alnum(bban):
        raise ValueError("BBAN aus Ziffern und Großbuchstaben erwartet")
    return mod97_check_digits(bban + country)


def format_iban(value: str, *, grouped: bool = True) -> str:
    """Paper form in groups of four (``grouped``) or the electronic form."""
    text = "".join(value.split()).upper()
    return " ".join(text[i : i + 4] for i in range(0, len(text), 4)) if grouped else text


def check_bic(value: object) -> CheckResult:
    """Strict BIC check (ISO 9362:2014): 8 or 11 characters, ISO 3166 country code.

    The business party prefix may be alphanumeric since ISO 9362:2014; a ``0`` as
    second location character marks a test BIC (``details["test_bic"]``).
    """
    kind = IdentifierKind.BIC
    text = prepare(kind, value)
    if isinstance(text, CheckResult):
        return text
    if not is_ascii_alnum(text):
        return invalid(kind, value, Reason.INVALID_CHARACTERS,
                       "BIC enthält unzulässige Zeichen (nur A–Z, 0–9)")
    if len(text) not in (8, 11):
        return invalid(kind, value, Reason.INVALID_LENGTH,
                       f"BIC muss 8 oder 11 Zeichen haben, nicht {len(text)}",
                       details={"length": len(text)})
    match = _BIC.fullmatch(text)
    if match is None:
        return invalid(kind, value, Reason.INVALID_FORMAT,
                       "BIC-Aufbau ungültig (Stellen 5–6 müssen ein Ländercode sein)")
    country = match.group(1)
    if country not in COUNTRY_CODES:
        return invalid(kind, value, Reason.UNKNOWN_COUNTRY,
                       f"Ländercode {country} ist nicht nach ISO 3166 vergeben",
                       country=country)
    return valid(kind, value, text, country=country,
                 details={"institution": text[:4], "location": text[6:8],
                          "branch": text[8:] or "XXX", "test_bic": text[7] == "0"})
