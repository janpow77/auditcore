"""Check and normalise IBAN, BIC, VAT IDs, German tax identifiers and LEI.

Every check returns a :class:`CheckResult` (status, reason, German message,
normalised value) and never raises for invalid input. ``profile`` selects the
rule set: ``strict`` (default) or a legacy profile reproducing an application.
"""

from __future__ import annotations

from auditcore_identifiers.iban import format_iban, iban_check_digits
from auditcore_identifiers.lei import extract_lei, lei_check_digits
from auditcore_identifiers.profiles import (
    PROFILES,
    STRICT,
    Profile,
    UnknownProfileError,
    UnsupportedKindError,
    get_profile,
    profile_names,
)
from auditcore_identifiers.result import CheckResult, IdentifierKind, Reason, Status
from auditcore_identifiers.tax_de import format_tax_id
from auditcore_identifiers.vat import at_uid_check_digit, de_vat_check_digit, normalize_vat_id

__version__ = "0.2.0"


def check(
    kind: IdentifierKind | str,
    value: object,
    *,
    profile: str | Profile = STRICT,
    country: str | None = None,
) -> CheckResult:
    """Check ``value`` as identifier ``kind`` under ``profile``."""
    return get_profile(profile).check(kind, value, country)


def check_iban(value: object, *, profile: str | Profile = STRICT) -> CheckResult:
    """IBAN (ISO 13616): register length, BBAN structure, MOD 97-10 (strict)."""
    return check(IdentifierKind.IBAN, value, profile=profile)


def check_bic(value: object, *, profile: str | Profile = STRICT) -> CheckResult:
    """BIC (ISO 9362): 8/11 characters, ISO 3166 country code (strict)."""
    return check(IdentifierKind.BIC, value, profile=profile)


def check_vat_id(
    value: object, *, country: str | None = None, profile: str | Profile = STRICT
) -> CheckResult:
    """USt-IdNr./VAT ID: EU formats, check digits DE and AT (strict)."""
    return check(IdentifierKind.VAT_ID, value, profile=profile, country=country)


def check_tax_id(value: object, *, profile: str | Profile = STRICT) -> CheckResult:
    """Steuerliche Identifikationsnummer (11 digits, MOD 11,10)."""
    return check(IdentifierKind.TAX_ID, value, profile=profile)


def check_tax_number(value: object, *, profile: str | Profile = STRICT) -> CheckResult:
    """Steuernummer (coarse: Land format 10/11 digits, federal format 13 digits)."""
    return check(IdentifierKind.TAX_NUMBER, value, profile=profile)


def check_lei(value: object, *, profile: str | Profile = STRICT) -> CheckResult:
    """LEI (ISO 17442): 20 characters, MOD 97-10 (strict)."""
    return check(IdentifierKind.LEI, value, profile=profile)


def check_register_number(value: object, *, profile: str | Profile = STRICT) -> CheckResult:
    """Handelsregisternummer (format only)."""
    return check(IdentifierKind.REGISTER_NUMBER, value, profile=profile)


__all__ = [
    "PROFILES",
    "STRICT",
    "CheckResult",
    "IdentifierKind",
    "Profile",
    "Reason",
    "Status",
    "UnknownProfileError",
    "UnsupportedKindError",
    "__version__",
    "at_uid_check_digit",
    "check",
    "check_bic",
    "check_iban",
    "check_lei",
    "check_register_number",
    "check_tax_id",
    "check_tax_number",
    "check_vat_id",
    "de_vat_check_digit",
    "extract_lei",
    "format_iban",
    "format_tax_id",
    "get_profile",
    "iban_check_digits",
    "lei_check_digits",
    "normalize_vat_id",
    "profile_names",
]
