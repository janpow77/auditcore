"""Legacy profile ``flowinvoice.legacy`` (= ``audit_portal.legacy``).

Re-implementation of ``backend/app/services/validators.py`` of janpow77/flowinvoice
(byte-identical in janpow77/audit-portal), characterised in
``tests/fixtures/flowinvoice_observed.json``. Patterns, normalisation and German
messages are kept exactly, including the weaknesses documented in
``docs/profiles.md``: **no MOD 97 check of the IBAN**, IBAN lengths only for ten
countries, ``\\d`` also matches non-ASCII digits, the German USt-IdNr. is checked
by pattern only. On success ``normalized`` is the value the original returned.

Only difference: inputs that are neither ``str`` nor falsy made the original
raise ``AttributeError``; here they yield ``INVALID_TYPE``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from auditcore_identifiers.result import (
    CheckResult,
    DetailValue,
    IdentifierKind,
    Reason,
    invalid,
    valid,
)

FLOWINVOICE = "flowinvoice.legacy"

GERMAN_TAX_ID_PATTERNS = (
    r"^\d{2}/\d{3}/\d{5}$",
    r"^\d{3}/\d{3}/\d{5}$",
    r"^\d{3}/\d{4}/\d{4}$",
    r"^\d{2}\s?\d{3}\s?\d{5}$",
    r"^\d{10,11}$",
)
GERMAN_VAT_ID_PATTERN = r"^DE\d{9}$"
EU_VAT_ID_PATTERNS: Mapping[str, str] = {
    "AT": r"^ATU\d{8}$", "BE": r"^BE0?\d{9,10}$", "BG": r"^BG\d{9,10}$",
    "CY": r"^CY\d{8}[A-Z]$", "CZ": r"^CZ\d{8,10}$", "DE": r"^DE\d{9}$",
    "DK": r"^DK\d{8}$", "EE": r"^EE\d{9}$", "EL": r"^EL\d{9}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$", "FI": r"^FI\d{8}$", "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "HR": r"^HR\d{11}$", "HU": r"^HU\d{8}$", "IE": r"^IE\d{7}[A-Z]{1,2}$",
    "IT": r"^IT\d{11}$", "LT": r"^LT(\d{9}|\d{12})$", "LU": r"^LU\d{8}$",
    "LV": r"^LV\d{11}$", "MT": r"^MT\d{8}$", "NL": r"^NL\d{9}B\d{2}$",
    "PL": r"^PL\d{10}$", "PT": r"^PT\d{9}$", "RO": r"^RO\d{2,10}$",
    "SE": r"^SE\d{12}$", "SI": r"^SI\d{8}$", "SK": r"^SK\d{10}$",
}
UK_VAT_PATTERNS = (r"^GB\d{9}$", r"^GB\d{12}$")
IBAN_LENGTHS: Mapping[str, int] = {
    "DE": 22, "AT": 20, "CH": 21, "FR": 27, "IT": 27,
    "ES": 24, "NL": 18, "BE": 16, "PL": 28, "GB": 22,
}
BIC_PATTERN = r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$"


def _text(kind: IdentifierKind, value: object, missing: str, profile: str) -> str | CheckResult:
    if not value:
        return invalid(kind, value, Reason.MISSING, missing, profile=profile)
    if not isinstance(value, str):
        return invalid(kind, value, Reason.INVALID_TYPE, "Wert ist keine Zeichenkette",
                       profile=profile)
    return value


def _ok(kind: IdentifierKind, value: object, normalized: str, profile: str,
        details: Mapping[str, DetailValue] | None = None) -> CheckResult:
    country = None if details is None else str(details["country"])
    return valid(kind, value, normalized, country=country, profile=profile, details=details)


def validate_german_tax_id(value: object, profile: str = FLOWINVOICE) -> CheckResult:
    """``validate_german_tax_id`` (Steuernummer, five format patterns)."""
    kind = IdentifierKind.TAX_NUMBER
    text = _text(kind, value, "Steuernummer fehlt", profile)
    if isinstance(text, CheckResult):
        return text
    normalized = text.strip()
    if any(re.match(pattern, normalized) for pattern in GERMAN_TAX_ID_PATTERNS):
        return _ok(kind, value, normalized, profile)
    return invalid(kind, value, Reason.INVALID_FORMAT,
                   f"Ungültiges Format für deutsche Steuernummer: {text}", profile=profile)


def validate_german_vat_id(value: object, profile: str = FLOWINVOICE) -> CheckResult:
    """``validate_german_vat_id`` (``DE`` + 9 digits, no check digit)."""
    kind = IdentifierKind.VAT_ID
    text = _text(kind, value, "USt-ID fehlt", profile)
    if isinstance(text, CheckResult):
        return text
    normalized = text.strip().upper().replace(" ", "")
    if re.match(GERMAN_VAT_ID_PATTERN, normalized):
        return _ok(kind, value, normalized, profile)
    return invalid(kind, value, Reason.INVALID_FORMAT,
                   f"Ungültige deutsche USt-ID: {text} (erwartet: DE + 9 Ziffern)",
                   profile=profile)


def validate_eu_vat_id(
    value: object, country_code: str | None = None, profile: str = FLOWINVOICE
) -> CheckResult:
    """``validate_eu_vat_id`` (27 patterns, optional country restriction)."""
    kind = IdentifierKind.VAT_ID
    text = _text(kind, value, "EU-USt-ID fehlt", profile)
    if isinstance(text, CheckResult):
        return text
    normalized = text.strip().upper().replace(" ", "").replace("-", "")
    if country_code:
        pattern = EU_VAT_ID_PATTERNS.get(country_code)
        if pattern and re.match(pattern, normalized):
            return _ok(kind, value, normalized, profile, {"country": country_code})
        return invalid(kind, value, Reason.INVALID_FORMAT,
                       f"Ungültige USt-ID für {country_code}: {text}", profile=profile)
    if len(normalized) >= 2:
        prefix = normalized[:2]
        pattern = EU_VAT_ID_PATTERNS.get(prefix)
        if pattern and re.match(pattern, normalized):
            return _ok(kind, value, normalized, profile, {"country": prefix})
    return invalid(kind, value, Reason.INVALID_FORMAT, f"Ungültige EU-USt-ID: {text}",
                   profile=profile)


def validate_uk_vat_id(value: object, profile: str = FLOWINVOICE) -> CheckResult:
    """``validate_uk_vat_id`` (``GB`` + 9 or 12 digits)."""
    kind = IdentifierKind.VAT_ID
    text = _text(kind, value, "UK VAT-Nummer fehlt", profile)
    if isinstance(text, CheckResult):
        return text
    normalized = text.strip().upper().replace(" ", "").replace("-", "")
    if any(re.match(pattern, normalized) for pattern in UK_VAT_PATTERNS):
        return _ok(kind, value, normalized, profile)
    return invalid(kind, value, Reason.INVALID_FORMAT, f"Ungültige UK VAT-Nummer: {text}",
                   profile=profile)


def validate_iban(value: object, profile: str = FLOWINVOICE) -> CheckResult:
    """``validate_iban``: format and length for ten countries, **no MOD 97 check**."""
    kind = IdentifierKind.IBAN
    text = _text(kind, value, "IBAN fehlt", profile)
    if isinstance(text, CheckResult):
        return text
    normalized = text.strip().upper().replace(" ", "")
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$", normalized):
        return invalid(kind, value, Reason.INVALID_FORMAT, f"Ungültiges IBAN-Format: {text}",
                       profile=profile)
    country = normalized[:2]
    expected = IBAN_LENGTHS.get(country)
    if expected and len(normalized) != expected:
        return invalid(kind, value, Reason.INVALID_LENGTH,
                       f"IBAN hat falsche Länge für {country}: {len(normalized)} statt {expected}",
                       country=country, profile=profile)
    return _ok(kind, value, normalized, profile, {"country": country})


def validate_bic(value: object, profile: str = FLOWINVOICE) -> CheckResult:
    """``validate_bic`` (letters in the first six positions, no country list)."""
    kind = IdentifierKind.BIC
    text = _text(kind, value, "BIC fehlt", profile)
    if isinstance(text, CheckResult):
        return text
    normalized = text.strip().upper().replace(" ", "")
    if re.match(BIC_PATTERN, normalized):
        return _ok(kind, value, normalized, profile)
    return invalid(kind, value, Reason.INVALID_FORMAT, f"Ungültiger BIC: {text}",
                   profile=profile)


def normalize_vat_id(value: str) -> str:
    """``RiskChecker._normalize_vat_id`` of flowinvoice (comparison key, no validation)."""
    normalized = value.upper().strip()
    for char in [" ", ".", "-", "/", "\\"]:
        normalized = normalized.replace(char, "")
    return normalized
