"""Published reference values with their sources (docs/test-vectors.md)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import auditcore_identifiers as ai

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from samples import IBAN_EXAMPLES, LEI_EXAMPLES  # noqa: E402

#: GLEIF record names, fetched from api.gleif.org/api/v1/lei-records/<LEI> on 2026-09-25.
GLEIF = {
    "7LTWFZYICNSX8D621K86": "DEUTSCHE BANK AKTIENGESELLSCHAFT",
    "529900T8BM49AURSDO55": "Ubisecure Oy",
    "5493001KJTIIGC8Y1R12": "Bloomberg Finance L.P.",
    "529900W18LQJJN6SJ336": "Société Générale Effekten GmbH",
}


@pytest.mark.parametrize("iban", IBAN_EXAMPLES)
def test_swift_registry_examples_are_valid(iban: str) -> None:
    """SWIFT IBAN Registry, example IBAN per country (electronic format)."""
    result = ai.check_iban(iban)
    assert result.valid, result
    assert ai.check_iban(ai.format_iban(iban)).normalized == iban
    assert ai.iban_check_digits(iban[:2], iban[4:]) == iban[2:4]


def test_ecbs_paper_format() -> None:
    """EBS204 / ISO 13616-1: paper form in groups of four with optional "IBAN" prefix."""
    assert ai.format_iban("DE89370400440532013000") == "DE89 3704 0044 0532 0130 00"
    assert ai.check_iban("IBAN DE89 3704 0044 0532 0130 00").normalized == (
        "DE89370400440532013000")
    assert ai.check_iban("DE88370400440532013000").reason is ai.Reason.INVALID_CHECKSUM


@pytest.mark.parametrize("lei", sorted(GLEIF))
def test_gleif_records_are_valid(lei: str) -> None:
    assert lei in LEI_EXAMPLES
    assert ai.check_lei(lei).valid
    assert ai.lei_check_digits(lei[:18]) == lei[18:]
    assert ai.extract_lei(f"LEI: {lei} ({GLEIF[lei]})") == lei


def test_iso_7064_mod_11_10_examples() -> None:
    """BZSt procedure (ISO 7064 MOD 11,10) for USt-IdNr. and Steuer-IdNr.

    Values from the python-stdnum doctests (independent implementation):
    ``DE136695976`` (stdnum.de.vat) and ``36574261809`` (stdnum.de.idnr).
    """
    assert ai.de_vat_check_digit("13669597") == 6
    assert ai.check_vat_id("DE136695976").valid
    assert ai.check_vat_id("DE136695978").reason is ai.Reason.INVALID_CHECKSUM
    assert ai.check_tax_id("36 574 261 809").normalized == "36574261809"
    assert ai.check_tax_id("36574261890").reason is ai.Reason.INVALID_CHECKSUM
    assert ai.check_tax_id("36554266806").reason is ai.Reason.INVALID_FORMAT


def test_austrian_uid_example() -> None:
    """BMF procedure; ``ATU13585627`` from the python-stdnum doctest (stdnum.at.uid)."""
    assert ai.at_uid_check_digit("1358562") == 7
    assert ai.check_vat_id("ATU13585627").valid
    assert ai.check_vat_id("ATU13585626").reason is ai.Reason.INVALID_CHECKSUM


def test_federal_tax_number_layout() -> None:
    """ELSTER 13-digit layout; examples from the python-stdnum doctest (stdnum.de.stnr)."""
    assert ai.check_tax_number("4151081508156").details["land"] == "Thüringen"
    assert ai.check_tax_number("4151181508156").reason is ai.Reason.INVALID_FORMAT
    assert ai.check_tax_number(" 181/815/0815 5").details["format"] == "land"
