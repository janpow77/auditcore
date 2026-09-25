"""Strict profile: reasons, normalisation and the no-exception contract."""

from __future__ import annotations

import random
import string

import pytest

import auditcore_identifiers as ai
from auditcore_identifiers import IdentifierKind, Reason, Status

R = Reason


@pytest.mark.parametrize("value,reason", [
    (None, R.MISSING), ("", R.MISSING), (" \t", R.MISSING), (12.5, R.INVALID_TYPE),
    (True, R.INVALID_TYPE), ("DE89 3704 0044 0532 0130 0ä", R.INVALID_CHARACTERS),
    ("DE89370400440532013000ß", R.INVALID_CHARACTERS), ("89DE370400440532013000", R.INVALID_FORMAT),
    ("DZ580002100001113000000570", R.UNKNOWN_COUNTRY), ("DE8937040044053201300", R.INVALID_LENGTH),
    ("GB29NWBK6016133192681A", R.INVALID_FORMAT), ("DE89370400440532013001", R.INVALID_CHECKSUM),
    ("DE89370400440532013@00", R.INVALID_CHARACTERS),
])
def test_iban_reasons(value: object, reason: Reason) -> None:
    result = ai.check_iban(value)
    assert result.reason is reason and not result.valid and result.message


def test_iban_normalisation_and_details() -> None:
    result = ai.check_iban(" de89-3704-0044-0532-0130-00\n")
    assert result.status is Status.VALID and result.normalized == "DE89370400440532013000"
    assert result.details["bban"] == "370400440532013000" and result.country == "DE"
    assert ai.check_iban("DE8937040044053201300").details["expected_length"] == 22
    with pytest.raises(ValueError):
        ai.iban_check_digits("D1", "123")


@pytest.mark.parametrize("value,reason", [
    ("DEUTDEF", R.INVALID_LENGTH), ("DEUTDEFF50", R.INVALID_LENGTH),
    ("DEUT1EFF", R.INVALID_FORMAT), ("DEUTXXFF", R.UNKNOWN_COUNTRY),
    ("DEUT-DEFF", R.INVALID_CHARACTERS),
])
def test_bic_reasons(value: str, reason: Reason) -> None:
    assert ai.check_bic(value).reason is reason


def test_bic_details() -> None:
    assert dict(ai.check_bic("deut de ff").details) == {
        "institution": "DEUT", "location": "FF", "branch": "XXX", "test_bic": False}
    assert ai.check_bic("DEUTDE00").details["test_bic"] is True
    assert ai.check_bic("1234DEFF").valid  # ISO 9362:2014 party prefix is alphanumeric
    assert ai.check_bic("DEUTXKFF").valid  # Kosovo


@pytest.mark.parametrize("value,country,reason", [
    ("136695976", None, R.INVALID_FORMAT), ("US123456789", None, R.UNKNOWN_COUNTRY),
    ("GR123456789", None, R.UNKNOWN_COUNTRY), ("DE136695976", "AT", R.COUNTRY_MISMATCH),
    ("DE036695976", None, R.INVALID_FORMAT), ("BE903955048", None, R.INVALID_FORMAT),
    ("DE13669597", None, R.INVALID_FORMAT), ("DE 136 695 978", None, R.INVALID_CHECKSUM),
    ("DE1366959#6", None, R.INVALID_CHARACTERS),
])
def test_vat_reasons(value: str, country: str | None, reason: Reason) -> None:
    assert ai.check_vat_id(value, country=country).reason is reason


def test_vat_normalisation_and_country_argument() -> None:
    assert ai.check_vat_id("de 136.695-976").normalized == "DE136695976"
    assert ai.check_vat_id("136695976", country="de").normalized == "DE136695976"
    assert ai.check_vat_id("U13585627", country="AT").normalized == "ATU13585627"
    assert ai.check_vat_id("123456789", country="GR").normalized == "EL123456789"
    assert "EL" in ai.check_vat_id("GR123456789").message
    gb = ai.check_vat_id("GB 123 4567 89")
    assert gb.valid and gb.details["eu"] is False and gb.details["checksum"] == "not_checked"
    assert ai.check_vat_id("XI123456789").details["eu"] is True
    assert ai.check_vat_id("IE1234567WA").valid and ai.check_vat_id("IE1+23456W").valid
    assert ai.check_vat_id("SE123456789001").valid
    assert ai.normalize_vat_id(" de-136.695/976 ") == "DE136695976"


def test_tax_id_rules() -> None:
    assert ai.check_tax_id(36574261809).valid  # integers are accepted
    assert ai.check_tax_id("3657426180").reason is R.INVALID_LENGTH
    assert ai.check_tax_id("0657426180 9").reason is R.INVALID_FORMAT
    assert ai.check_tax_id("3657426180x").reason is R.INVALID_CHARACTERS
    assert ai.format_tax_id("36574261809") == "36 574 261 809"


def test_tax_number_and_register_number() -> None:
    assert ai.check_tax_number("2893081508152").details["land"] == "Baden-Württemberg"
    assert ai.check_tax_number("9181081508155").details["land"] == "Bayern"
    assert ai.check_tax_number("2893181508152").reason is R.INVALID_FORMAT
    assert ai.check_tax_number("123456789").reason is R.INVALID_LENGTH
    assert ai.check_tax_number("12/345/6789A").reason is R.INVALID_CHARACTERS
    assert ai.check_register_number("hrb 12345 b").normalized == "HRB 12345 B"
    assert ai.check_register_number("GnR 17").details["register"] == "GnR"
    assert ai.check_register_number("HRC 1").reason is R.INVALID_FORMAT


def test_lei_reasons_and_extraction() -> None:
    assert ai.check_lei("7LTWFZYICNSX8D621K8").reason is R.INVALID_LENGTH
    assert ai.check_lei("7LTWFZYICNSX8D621KA6").reason is R.INVALID_FORMAT
    assert ai.check_lei("7LTWFZYICNSX8D621K87").reason is R.INVALID_CHECKSUM
    assert ai.check_lei("7ltw fzyi cnsx 8d62 1k86").normalized == "7LTWFZYICNSX8D621K86"
    assert ai.extract_lei("x 7LTWFZYICNSX8D621K87 / 7LTWFZYICNSX8D621K86") == (
        "7LTWFZYICNSX8D621K86")
    assert ai.extract_lei(None) is None and ai.extract_lei("nichts") is None
    with pytest.raises(ValueError):
        ai.lei_check_digits("zu kurz")


def test_result_object() -> None:
    result = ai.check_iban("DE89370400440532013000")
    assert bool(result) and result.to_dict()["details"]["check_digits"] == "89"
    with pytest.raises(TypeError):
        result.details["x"] = 1  # type: ignore[index]
    missing = ai.check_iban(None).to_dict()
    assert missing["status"] == "MISSING" and missing["raw"] is None


def test_profiles_api() -> None:
    names = ai.profile_names()
    assert names[0] == "strict" and "flowinvoice.legacy" in names and len(names) == 8
    assert all(ai.get_profile(n).legacy for n in names[1:])
    assert all(ai.get_profile(n).rationale for n in names)
    assert ai.get_profile(ai.PROFILES["strict"]) is ai.PROFILES["strict"]
    with pytest.raises(ai.UnknownProfileError):
        ai.check_iban("x", profile="unbekannt")
    with pytest.raises(ai.UnsupportedKindError):
        ai.check_tax_id("x", profile="flowinvoice.legacy")
    legacy = ai.check_iban("DE89370400440532013001", profile="flowinvoice.legacy")
    assert legacy.valid and legacy.profile == "flowinvoice.legacy"
    assert ai.check_vat_id("DE136695976", country="DE", profile="flowinvoice.legacy").valid


_GARBAGE: list[object] = [None, "", " ", 0, 1, -5, 3.5, b"DE89", ["DE"], {"a": 1}, object(),
                          "\x00", "ÄÖÜ", "٣٣٣", "IBAN", "-" * 40, "9" * 5000]


def test_no_profile_raises_for_any_input() -> None:
    rng = random.Random(7)
    values = _GARBAGE + ["".join(rng.choice(string.printable + "ßä٣²@") for _ in range(
        rng.randrange(0, 40))) for _ in range(400)]
    for name in ai.profile_names():
        profile = ai.get_profile(name)
        for kind in profile.checkers:
            for value in values:
                result = profile.check(kind, value, "DE")
                assert isinstance(result.status, Status)
                assert result.kind is IdentifierKind(kind)
