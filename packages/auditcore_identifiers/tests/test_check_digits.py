"""Check-digit status, verdict and the corrections of 0.3.0 (sources: docs/test-vectors.md)."""

from __future__ import annotations

import pytest

import auditcore_identifiers as ai
from auditcore_identifiers import CheckDigit, Reason, Verdict
from auditcore_identifiers.web import contract

#: Synthetic numbers with a valid national check digit: drawn at random by
#: ``tools/crosscheck_stdnum.py`` (``vat_valid_by_country`` in
#: ``tests/fixtures/stdnum_crosscheck.json``) and accepted there by python-stdnum 2.2.
#: Not taken from any register; tests use synthetic data only (AGENTS.md).
SYNTHETIC_VALID = (
    "BG662404571",
    "CZ67267068",
    "CZ8746084468",
    "DE801752040",
    "DK54958498",
    "EL062125293",
    "ESB37172087",
    "FI29604457",
    "FR16796035319",
    "FR09751916354",
    "HR21619732144",
    "HU14772667",
    "IE5365209J",
    "IT23086660679",
    "IT89139130747",
    "LT508608012",
    "LU62423174",
    "NL000001545B35",
    "NL000009350B57",
    "PL7539778793",
    "PT566879344",
    "SE330585586201",
    "SI60576235",
)


@pytest.mark.parametrize(
    "iban",
    # MOD 97 remainder 1, but ISO 7064 MOD 97-10 only produces check digits 02–98.
    ["DE01370400441000000008", "DE00370400441000000026", "DE99370400441000000087"],
)
def test_iban_check_digits_outside_02_to_98_are_invalid(iban: str) -> None:
    result = ai.check_iban(iban)
    assert result.reason is Reason.INVALID_CHECKSUM and result.check_digit is CheckDigit.FAILED
    assert iban[2:4] in result.message


def test_lei_check_digits_outside_02_to_98_are_invalid() -> None:
    # ISO 17442 uses ISO 7064 MOD 97-10 as IBAN does; remainder 1 with "01" is impossible.
    assert ai.check_lei("549300ABCDEFGHIAIH01").reason is Reason.INVALID_CHECKSUM
    assert ai.check_lei("7LTWFZYICNSX8D621K86").verdict is Verdict.VALID


@pytest.mark.parametrize("value", SYNTHETIC_VALID)
def test_synthetic_valid_numbers_have_a_verified_check_digit(value: str) -> None:
    result = ai.check_vat_id(value)
    assert result.check_digit is CheckDigit.VERIFIED and result.verdict is Verdict.VALID


@pytest.mark.parametrize(
    "value",
    # Last digit of a synthetic valid number changed (``vat_mutated`` in the stdnum
    # fixture, rejected there as well): the national check digit no longer matches.
    ["FR16796035310", "IT23086660670", "BE0239792909", "PL7539778794", "DK54958499"],
)
def test_wrong_national_check_digit_is_invalid(value: str) -> None:
    result = ai.check_vat_id(value)
    assert result.reason is Reason.INVALID_CHECKSUM and result.check_digit is CheckDigit.FAILED


def test_vat_without_verifiable_check_digit_is_only_format_valid() -> None:
    gb = ai.check_vat_id("GB123456789")
    assert gb.valid and gb.check_digit is CheckDigit.NOT_CHECKED
    assert gb.verdict is Verdict.FORMAT_VALID and "nicht prüfbar" in gb.message
    assert ai.check_vat_id("GBGD001").check_digit is CheckDigit.NONE
    letter_key = ai.check_vat_id("FRK7399859412")  # alphanumeric key, SIREN passes Luhn
    assert letter_key.check_digit is CheckDigit.NOT_CHECKED
    assert letter_key.verdict is Verdict.FORMAT_VALID


def test_structural_rules_of_the_national_numbers() -> None:
    assert ai.check_vat_id("IT2308666" + "3009").reason is Reason.INVALID_FORMAT  # office 300
    assert ai.check_vat_id("NL000001545B00").reason is Reason.INVALID_FORMAT
    assert ai.check_vat_id("PT000000000").reason is Reason.INVALID_FORMAT
    assert ai.check_vat_id("CZ5602301234").reason is Reason.INVALID_FORMAT  # 30 Feb


def test_bic_has_no_check_digit_and_is_never_fully_valid() -> None:
    # "DEUTSCHLAND" is structurally a BIC (bank DEUT, country SC, location HL, branch AND);
    # ISO 9362 defines no check digit, so the verdict stays "format_valid".
    for value in ("DEUTDEFF", "DEUTSCHLAND"):
        result = ai.check_bic(value)
        assert result.valid and result.check_digit is CheckDigit.NONE
        assert result.verdict is Verdict.FORMAT_VALID


@pytest.mark.parametrize("value", ["HRB 0", "HRB 012", "HRA 0000"])
def test_register_number_zero_or_leading_zero_is_invalid(value: str) -> None:
    assert ai.check_register_number(value).reason is Reason.INVALID_FORMAT


@pytest.mark.parametrize(
    ("value", "number", "court"),
    [
        ("Amtsgericht Frankfurt am Main HRB 12345", "HRB 12345", "Frankfurt am Main"),
        ("AG Charlottenburg HRB 123456 B", "HRB 123456 B", "Charlottenburg"),
        ("HRB 123, Amtsgericht Köln", "HRB 123", "Köln"),
        ("HRB 123 (AG Köln)", "HRB 123", "Köln"),
        ("Registergericht: Amtsgericht München, Registernummer: HRB 12345", "HRB 12345", "München"),
        ("GsR 17", "GsR 17", None),
    ],
)
def test_register_number_with_court(value: str, number: str, court: str | None) -> None:
    result = ai.check_register_number(value)
    assert result.valid and result.normalized == number
    assert result.details.get("court") == court
    assert result.check_digit is CheckDigit.NONE and result.verdict is Verdict.FORMAT_VALID


def test_check_digit_and_verdict_in_dict_labels_and_summary() -> None:
    data = ai.check_tax_id("36574261809").to_dict()
    assert data["check_digit"] == "verified" and data["verdict"] == "valid"
    assert ai.check_tax_number("4151081508156").check_digit is CheckDigit.NOT_CHECKED
    row = contract.result_dict(ai.check_vat_id("GB123456789"))
    assert row["check_digit_label"] == "nicht prüfbar"
    assert row["verdict_label"] == "Format gültig, Prüfziffer nicht geprüft"
    assert contract.result_dict(ai.check_lei("")).get("check_digit_label") is None
    legacy = ai.check_iban("DE89370400440532013000", profile="flowinvoice.legacy")
    assert legacy.check_digit is None and legacy.verdict is Verdict.FORMAT_VALID
