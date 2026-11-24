"""Independent cross-check against python-stdnum verdicts (recorded offline as data)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import auditcore_identifiers as ai

DATA: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "stdnum_crosscheck.json").read_text("utf-8")
)
#: stdnum also verifies national account check digits for these IBAN countries.
NATIONAL_BBAN_CHECKS = {"BE", "ES", "FI", "FR", "IT", "ME", "MK", "NO", "PT", "SI", "SM"}


def _disagreements(kind: str, key: str | None = None) -> list[tuple[str, bool, ai.CheckResult]]:
    result = []
    for entry in DATA[key or kind]:
        checked = ai.check(kind, entry["value"])
        if checked.valid is not entry["stdnum_valid"]:
            result.append((entry["value"], entry["stdnum_valid"], checked))
    return result


def test_recorded_stdnum_version() -> None:
    assert DATA["stdnum_version"] == "2.2"


def test_strict_accepts_every_number_stdnum_accepts_per_eu_country() -> None:
    numbers = DATA["vat_valid_by_country"]
    assert len(numbers) == 27 and sum(map(len, numbers.values())) > 190
    for country, values in numbers.items():
        for value in values:
            result = ai.check_vat_id(value)
            assert result.valid and result.country == country, value
            if country == "FR" and not value[2:4].isdigit():  # letter key: no published procedure
                assert result.check_digit is ai.CheckDigit.NOT_CHECKED, value
            elif country == "CZ" and len(value) == 11:  # birth number until 1953: no check digit
                assert result.check_digit is ai.CheckDigit.NONE, value
            else:
                assert result.check_digit is ai.CheckDigit.VERIFIED, value
                assert result.verdict is ai.Verdict.VALID, value


def test_one_wrong_check_character_is_rejected_like_stdnum() -> None:
    """Last character of every number above changed: same verdict as stdnum, except where
    strict cannot verify (FR letter keys) – those are VALID but only ``format_valid``."""
    assert len(DATA["vat_mutated"]) > 190
    for value, stdnum_valid, result in _disagreements("vat_id", "vat_mutated"):
        assert not stdnum_valid and result.verdict is ai.Verdict.FORMAT_VALID, value


def test_iban_differences_are_prefix_or_national_checks() -> None:
    for value, stdnum_valid, result in _disagreements("iban"):
        assert not stdnum_valid and result.valid, value
        assert value.strip().upper().startswith("IBAN") or result.country in NATIONAL_BBAN_CHECKS


def test_bic_and_lei_differences_are_documented() -> None:
    for value, stdnum_valid, result in _disagreements("bic"):
        if stdnum_valid:  # stdnum removes hyphens
            assert "-" in value and not result.valid
        else:  # ISO 9362:2014 allows digits in the party prefix
            assert any(c.isdigit() for c in result.normalized or "")
    for value, stdnum_valid, _ in _disagreements("lei"):
        assert stdnum_valid and "-" in value


def test_vat_differences_only_where_strict_cannot_verify_the_check_digit() -> None:
    for value, stdnum_valid, result in _disagreements("vat_id"):
        assert not stdnum_valid and result.valid, value
        assert result.check_digit in (ai.CheckDigit.NOT_CHECKED, ai.CheckDigit.NONE), value
        assert result.verdict is ai.Verdict.FORMAT_VALID, value


def test_tax_id_differences_are_the_three_in_a_row_rule() -> None:
    rows = _disagreements("tax_id")
    assert rows
    for value, stdnum_valid, result in rows:
        first_ten = value[:10]
        assert stdnum_valid and any(d * 3 in first_ten for d in "0123456789"), value
        assert result.reason is ai.Reason.INVALID_FORMAT


def test_tax_number_agrees() -> None:
    assert _disagreements("tax_number") == []
