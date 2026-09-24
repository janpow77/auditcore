from __future__ import annotations

from random import Random

import pytest

from auditcore_invoicesynth.identifiers import (
    FICTIONAL_BANKS_AT,
    FICTIONAL_BANKS_DE,
    at_uid_check_digit,
    de_vat_check_digit,
    fictional_bank_account,
    fictional_vat_id,
    format_iban,
    iban_check_digits,
    iban_valid,
    vat_id_valid,
)


def test_known_public_examples() -> None:
    # Öffentlich dokumentierte Beispielnummern (Prüfziffernverfahren).
    assert iban_valid("DE89 3704 0044 0532 0130 00")
    assert iban_valid("AT611904300234573201")
    assert not iban_valid("DE89370400440532013001")
    assert iban_check_digits("DE", "370400440532013000") == "89"
    assert de_vat_check_digit("13669597") == 6
    assert vat_id_valid("DE136695976")
    assert not vat_id_valid("DE136695975")
    assert at_uid_check_digit("1358562") == 7
    assert vat_id_valid("ATU13585627")
    assert not vat_id_valid("ATU13585626")
    assert not vat_id_valid("FR12345678901")


@pytest.mark.parametrize("country", ["DE", "AT"])
def test_generated_identifiers_are_valid_and_fictional(country: str) -> None:
    rng = Random(1)
    banks = {b[1] for b in (FICTIONAL_BANKS_DE if country == "DE" else FICTIONAL_BANKS_AT)}
    for _ in range(300):
        account = fictional_bank_account(rng, country)
        assert iban_valid(account.iban) and account.iban.startswith(country)
        assert account.iban[4 : 4 + (8 if country == "DE" else 5)] in banks
        assert account.bic.startswith("SYNT")
        assert vat_id_valid(fictional_vat_id(rng, country))
    if country == "DE":
        assert all(b.startswith("9") for b in banks)  # kein Clearinggebiet 1–8


def test_format_iban_and_errors() -> None:
    assert format_iban("DE89370400440532013000", grouped=True) == "DE89 3704 0044 0532 0130 00"
    with pytest.raises(ValueError):
        fictional_vat_id(Random(0), "FR")
    with pytest.raises(ValueError):
        de_vat_check_digit("01234567")
    with pytest.raises(ValueError):
        iban_check_digits("de", "123")
