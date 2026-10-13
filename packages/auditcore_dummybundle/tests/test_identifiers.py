"""Kennungen: standardmäßig garantiert formal ungültig, gültig nur auf ausdrückliche Wahl."""

from __future__ import annotations

from datetime import date
from random import Random

import pytest
from auditcore_identifiers import Status, check_bic, check_iban, check_vat_id
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_dummybundle import BundleConfig, bic, build_bundle, iban, vat_id

COUNTRIES = st.sampled_from(["DE", "AT"])
SEEDS = st.integers(0, 2**31 - 1)


def _mod97(value: str) -> int:
    digits = "".join(str(int(char, 36)) for char in value[4:] + value[:4])
    return int(digits) % 97


@settings(max_examples=500, deadline=None)
@given(seed=SEEDS, country=COUNTRIES)
def test_default_identifiers_never_pass_a_check(seed: int, country: str) -> None:
    rng = Random(seed)
    account, tax = iban(rng, country), vat_id(rng, country)
    assert check_iban(account).status is Status.INVALID
    assert _mod97(account) != 1
    assert check_vat_id(tax).status is Status.INVALID
    assert account.startswith(country) and tax.startswith(country)


@settings(max_examples=200, deadline=None)
@given(seed=SEEDS, country=COUNTRIES)
def test_valid_identifiers_only_on_explicit_choice(seed: int, country: str) -> None:
    rng = Random(seed)
    assert check_iban(iban(rng, country, valid=True)).status is Status.VALID
    assert check_vat_id(vat_id(rng, country, valid=True)).status is Status.VALID


@pytest.mark.parametrize("country", ["DE", "AT"])
def test_bank_parts_are_recognisably_synthetic(country: str) -> None:
    assert bic(country) == f"SYNT{country}X0"
    assert check_bic(bic(country)).status is Status.VALID  # nur Formprüfung, kein Verzeichnis
    assert iban(Random(1), country)[4] == "0"


@pytest.mark.parametrize("valid", [False, True], ids=["ungueltig", "gueltig"])
def test_bundle_identifiers_follow_the_choice(valid: bool) -> None:
    bundle = build_bundle(
        BundleConfig(seed=3, base_date=date(2026, 1, 1), country="DE+AT", identifiers_valid=valid)
    )
    expected = Status.VALID if valid else Status.INVALID
    for operation in bundle.table("operations"):
        assert check_iban(operation["beneficiary_iban"]).status is expected
        assert check_vat_id(operation["beneficiary_vat_id"]).status is expected
    for receipt in bundle.table("receipts"):
        assert check_vat_id(receipt["supplier_vat_id"]).status is expected
