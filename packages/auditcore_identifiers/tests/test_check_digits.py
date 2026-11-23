"""Check-digit status, verdict and the corrections of 0.3.0 (sources: docs/test-vectors.md)."""

from __future__ import annotations

import pytest

import auditcore_identifiers as ai
from auditcore_identifiers import CheckDigit, Reason, Verdict
from auditcore_identifiers.web import contract

#: Confirmed as valid and registered by the VIES REST service of the European Commission
#: (``/taxation_customs/vies/rest-api/ms/{CC}/vat/{number}``) on 23.11.2026.
VIES_CONFIRMED = (
    "BG175074752",
    "CZ25123891",
    "CZ00006947",
    "DE811569869",
    "DK13585628",
    "EL094259216",
    "ESA28015865",
    "FI20774740",
    "FR40303265045",
    "FR61954506077",
    "HR33392005961",
    "HU12892312",
    "IE6433435F",
    "IT00743110157",
    "IT00488410010",
    "LT119511515",
    "LU15027442",
    "NL004495445B01",
    "NL001545668B01",
    "PL5260250995",
    "PT500100144",
    "SE556464687401",
    "SI50223054",
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


@pytest.mark.parametrize("value", VIES_CONFIRMED)
def test_vies_confirmed_numbers_have_a_verified_check_digit(value: str) -> None:
    result = ai.check_vat_id(value)
    assert result.check_digit is CheckDigit.VERIFIED and result.verdict is Verdict.VALID


@pytest.mark.parametrize(
    "value",
    # One digit changed in a VIES-confirmed number (FR, IT) or in the Belgian and Polish
    # numbers of the task description: the national check digit no longer matches.
    ["FR41303265045", "IT00743110158", "BE0403170702", "PL5260001247", "DK13585629"],
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
    assert ai.check_vat_id("IT0074311" + "3007").reason is Reason.INVALID_FORMAT  # office 300
    assert ai.check_vat_id("NL004495445B00").reason is Reason.INVALID_FORMAT
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
