"""Legacy profiles of the document pipeline and the auditcore-internal copies.

* ``flowinvoice.pipeline.legacy`` (= ``audit_portal.pipeline.legacy``, carried on in
  ``auditcore_documents.pipeline.stages.validation_base``): ``_validate_iban`` of the
  ``IbanChecksumRule`` (MOD 97, lengths for nine countries, English messages) and the
  decision of ``VatIdFormatRule.evaluate`` (eight countries, format only).
* ``documents.donut``: ``auditcore_documents`` Donut check – values compacted,
  then ``validate_iban`` and ``vat_id_check`` (DE/AT check digits, German messages).
* ``invoicesynth.legacy``: ``iban_valid``/``vat_id_valid`` (booleans).
* ``flowworkshop.legacy``: ``is_valid_lei`` (format only, no check digits).

Characterised in ``tests/fixtures/*_observed.json``; see ``docs/profiles.md``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from auditcore_identifiers.result import CheckResult, IdentifierKind, Reason, invalid, valid
from auditcore_identifiers.vat import at_uid_check_digit, de_vat_check_digit

PIPELINE = "flowinvoice.pipeline.legacy"
DONUT = "documents.donut"
INVOICESYNTH = "invoicesynth.legacy"
FLOWWORKSHOP = "flowworkshop.legacy"

PIPELINE_IBAN_LENGTHS: Mapping[str, int] = {
    "DE": 22, "AT": 20, "CH": 21, "FR": 27, "IT": 27, "ES": 24, "NL": 18, "BE": 16, "GB": 22,
}
PIPELINE_VAT_PATTERNS: Mapping[str, str] = {
    "DE": r"^DE\d{9}$",
    "AT": r"^ATU\d{8}$",
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "IT": r"^IT\d{11}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "NL": r"^NL\d{9}B\d{2}$",
    "BE": r"^BE0?\d{9,10}$",
    "GB": r"^GB\d{9}$|^GB\d{12}$|^GBGD\d{3}$|^GBHA\d{3}$",
}
_LEI = re.compile(r"^[A-Z0-9]{18}\d{2}$")


def _type_error(kind: IdentifierKind, value: object, profile: str) -> CheckResult | None:
    if not value or isinstance(value, str):
        return None
    return invalid(kind, value, Reason.INVALID_TYPE, "Wert ist keine Zeichenkette",
                   profile=profile)


def _pipeline_iban_numeric(rearranged: str) -> str:
    return "".join(char if char.isdigit() else str(ord(char) - 55) for char in rearranged)


def pipeline_validate_iban(value: object, profile: str = PIPELINE) -> CheckResult:
    """``IbanChecksumRule._validate_iban``; ``None`` (original: AttributeError) → MISSING."""
    kind = IdentifierKind.IBAN
    if value is None:
        return invalid(kind, value, Reason.MISSING, "No IBAN found", profile=profile)
    if not isinstance(value, str):
        return invalid(kind, value, Reason.INVALID_TYPE, "Wert ist keine Zeichenkette",
                       profile=profile)
    iban = value.replace(" ", "").upper()
    if len(iban) < 15 or len(iban) > 34:
        return invalid(kind, value, Reason.INVALID_LENGTH, f"Invalid IBAN length: {len(iban)}",
                       profile=profile)
    country = iban[:2]
    expected = PIPELINE_IBAN_LENGTHS.get(country)
    if expected is not None and len(iban) != expected:
        return invalid(kind, value, Reason.INVALID_LENGTH,
                       f"Invalid IBAN length for {country}: expected {expected}, got {len(iban)}",
                       country=country, profile=profile)
    try:
        if int(_pipeline_iban_numeric(iban[4:] + iban[:4])) % 97 != 1:
            return invalid(kind, value, Reason.INVALID_CHECKSUM, "IBAN checksum invalid",
                           country=country, profile=profile)
    except ValueError:
        return invalid(kind, value, Reason.INVALID_CHARACTERS, "IBAN contains invalid characters",
                       country=country, profile=profile)
    return valid(kind, value, iban, country=country, profile=profile)


def pipeline_vat_id_format(value: object, profile: str = PIPELINE) -> CheckResult:
    """Decision of ``VatIdFormatRule.evaluate`` (outcome in ``details["outcome"]``).

    Only the prefix is upper-cased; the pattern is matched against the raw value.
    PASS on an empty value (skipped) → MISSING, REVIEW (unknown country) → INVALID.
    """
    kind = IdentifierKind.VAT_ID
    problem = _type_error(kind, value, profile)
    if problem is not None:
        return problem
    if not value or not isinstance(value, str):
        return invalid(kind, value, Reason.MISSING, "No VAT ID found, skipping validation",
                       profile=profile, details={"outcome": "PASS", "severity": "INFO"})
    country = value[:2].upper()
    pattern = PIPELINE_VAT_PATTERNS.get(country)
    if not pattern:
        return invalid(kind, value, Reason.UNKNOWN_COUNTRY, f"Unknown VAT ID country: {country}",
                       country=country, profile=profile,
                       details={"outcome": "REVIEW", "severity": "INFO"})
    if re.match(pattern, value):
        return valid(kind, value, value, country=country, profile=profile,
                     message=f"VAT ID format valid: {value}",
                     details={"outcome": "PASS", "severity": "WARN"})
    return invalid(kind, value, Reason.INVALID_FORMAT,
                   f"VAT ID format invalid for country {country}", country=country,
                   profile=profile, details={"outcome": "FAIL", "severity": "WARN"})


def donut_compact(raw: str) -> str:
    """``compact`` of the Donut stage: whitespace removed, upper case."""
    return "".join(raw.split()).upper()


def donut_validate_iban(value: object) -> CheckResult:
    """Donut stage: compacted value through ``validate_iban`` (pipeline semantics)."""
    if isinstance(value, str) and value:
        value = donut_compact(value)
    return pipeline_validate_iban(value, profile=DONUT)


def _donut_problem(vat_id: str) -> tuple[Reason, str] | None:
    country = vat_id[:2]
    pattern = PIPELINE_VAT_PATTERNS.get(country)
    if pattern is None:
        return Reason.UNKNOWN_COUNTRY, f"USt-IdNr.-Land unbekannt: {country}"
    if not re.match(pattern, vat_id):
        return Reason.INVALID_FORMAT, "USt-IdNr.-Format ungültig"
    if country == "DE" and de_vat_check_digit(vat_id[2:10]) != int(vat_id[10]):
        return Reason.INVALID_CHECKSUM, "USt-IdNr.-Prüfziffer ungültig"
    if country == "AT" and at_uid_check_digit(vat_id[3:10]) != int(vat_id[10]):
        return Reason.INVALID_CHECKSUM, "UID-Prüfziffer ungültig"
    return None


def donut_vat_id_check(value: object) -> CheckResult:
    """Donut stage: ``compact`` then ``vat_id_check`` (format, DE/AT check digits)."""
    kind = IdentifierKind.VAT_ID
    problem = _type_error(kind, value, DONUT)
    if problem is not None:
        return problem
    if not value or not isinstance(value, str):
        return invalid(kind, value, Reason.MISSING, "Wert fehlt", profile=DONUT)
    text = donut_compact(value)
    found = _donut_problem(text)
    if found is not None:
        return invalid(kind, value, found[0], found[1], country=text[:2], profile=DONUT)
    return valid(kind, value, text, country=text[:2], profile=DONUT)


def _base36_mod97(text: str) -> int:
    """``int(char, 36)`` per character; the original raised ValueError for e.g. ``ä``."""
    try:
        return int("".join(str(int(c, 36)) for c in text)) % 97
    except ValueError:
        return -1


def invoicesynth_iban_valid(value: object) -> CheckResult:
    """``iban_valid``: length 15–34 (DE 22, AT 20), alphanumeric, MOD 97."""
    kind = IdentifierKind.IBAN
    if not isinstance(value, str):
        return invalid(kind, value, Reason.INVALID_TYPE, "Wert ist keine Zeichenkette",
                       profile=INVOICESYNTH)
    text = value.replace(" ", "").upper()
    expected = {"DE": 22, "AT": 20}.get(text[:2])
    ok = (
        15 <= len(text) <= 34 and text.isalnum() and text[:2].isalpha()
        and (expected is None or len(text) == expected) and text[2:4].isdigit()
        and _base36_mod97(text[4:] + text[:4]) == 1
    )
    if ok:
        return valid(kind, value, text, country=text[:2], profile=INVOICESYNTH)
    return invalid(kind, value, Reason.INVALID_FORMAT, "IBAN ungültig", profile=INVOICESYNTH)


def _invoicesynth_vat_ok(text: str) -> bool:
    """``int()`` of digits like ``²`` raised ValueError in the original; here: invalid."""
    try:
        if text.startswith("DE") and len(text) == 11 and text[2:].isdigit() and text[2] != "0":
            return de_vat_check_digit(text[2:10]) == int(text[10])
        if text.startswith("ATU") and len(text) == 11 and text[3:].isdigit():
            return at_uid_check_digit(text[3:10]) == int(text[10])
    except ValueError:
        pass
    return False


def invoicesynth_vat_id_valid(value: object) -> CheckResult:
    """``vat_id_valid``: only DE and ATU with check digit; every other country is invalid."""
    kind = IdentifierKind.VAT_ID
    if not isinstance(value, str):
        return invalid(kind, value, Reason.INVALID_TYPE, "Wert ist keine Zeichenkette",
                       profile=INVOICESYNTH)
    text = value.replace(" ", "").upper()
    if _invoicesynth_vat_ok(text):
        return valid(kind, value, text, country=text[:2], profile=INVOICESYNTH)
    return invalid(kind, value, Reason.INVALID_FORMAT, "USt-IdNr. ungültig",
                   profile=INVOICESYNTH)


def flowworkshop_is_valid_lei(value: object) -> CheckResult:
    """``is_valid_lei``: strip, upper case, format only (no check digits)."""
    kind = IdentifierKind.LEI
    if not value:
        return invalid(kind, value, Reason.MISSING, "Wert fehlt", profile=FLOWWORKSHOP)
    text = str(value).strip().upper()
    if _LEI.match(text):
        return valid(kind, value, text, profile=FLOWWORKSHOP)
    return invalid(kind, value, Reason.INVALID_FORMAT, "Kein LEI-Format", profile=FLOWWORKSHOP)


def flowworkshop_extract_lei_from_text(value: object) -> str | None:
    """``extract_lei_from_text``: whole value or first ``\\b``-delimited token, no check digits."""
    if not value:
        return None
    text = str(value).strip().upper()
    if _LEI.match(text):
        return text
    match = re.search(r"\b([A-Z0-9]{18}\d{2})\b", text)
    return match.group(1) if match else None
