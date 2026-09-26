"""Parity old ↔ new: VAT check digits now come from ``auditcore_identifiers``.

The copies below are the 0.3.3 implementations of
``pipeline/stages/donut_values.py`` (verbatim). An exhaustive run over all
10**8 (DE) or 10**7 (AT) inputs is too slow for the suite; a seeded sample,
every combination of the digits 0/1/5/9, wrong lengths and invalid characters
are compared instead, plus ``vat_id_check`` on valid and invalid identifiers.
"""

from __future__ import annotations

import itertools
import random
import re

import pytest
from auditcore_identifiers import at_uid_check_digit as identifiers_at
from auditcore_identifiers import de_vat_check_digit as identifiers_de

from auditcore_documents.pipeline.stages import donut_merge, donut_values
from auditcore_documents.pipeline.stages.validation import VAT_ID_PATTERNS


# donut_values.py :: de_vat_check_digit (0.3.3, verbatim)
def legacy_de_vat_check_digit(first_eight: str) -> int:
    product = 10
    for char in first_eight:
        total = (int(char) + product) % 10 or 10
        product = (2 * total) % 11
    check = 11 - product
    return 0 if check == 10 else check


# donut_values.py :: at_uid_check_digit (0.3.3, verbatim)
def legacy_at_uid_check_digit(first_seven: str) -> int:
    digits = [int(c) for c in first_seven]
    total = sum(d if i % 2 == 0 else (2 * d) // 10 + (2 * d) % 10 for i, d in enumerate(digits))
    return (10 - (total + 4) % 10) % 10


def _inputs(length: int) -> list[str]:
    rng = random.Random(20260926 + length)
    sample = [f"{rng.randrange(10**length):0{length}d}" for _ in range(20_000)]
    patterns = ["".join(p) for p in itertools.product("0159", repeat=length)]
    return [*sample, *patterns, "", "1", "12345678901"]


def test_same_objects_are_reexported() -> None:
    assert donut_values.de_vat_check_digit is identifiers_de
    assert donut_values.at_uid_check_digit is identifiers_at
    assert donut_merge.de_vat_check_digit is identifiers_de
    assert donut_merge.at_uid_check_digit is identifiers_at


def test_de_check_digit_is_unchanged() -> None:
    for text in _inputs(8):
        assert donut_values.de_vat_check_digit(text) == legacy_de_vat_check_digit(text), text


def test_at_check_digit_is_unchanged() -> None:
    for text in _inputs(7):
        assert donut_values.at_uid_check_digit(text) == legacy_at_uid_check_digit(text), text


@pytest.mark.parametrize("text", ["12a45678", "1234 678", "-1234567", "１２３４５６７８", "²"])
def test_invalid_digits_fail_identically(text: str) -> None:
    for new, old in (
        (donut_values.de_vat_check_digit, legacy_de_vat_check_digit),
        (donut_values.at_uid_check_digit, legacy_at_uid_check_digit),
    ):
        try:
            expected: object = old(text)
        except ValueError as exc:
            expected = ("ValueError", str(exc))
        try:
            actual: object = new(text)
        except ValueError as exc:
            actual = ("ValueError", str(exc))
        assert actual == expected


# donut_values.py :: vat_id_check (0.3.3, verbatim, with the legacy check digits)
def legacy_vat_id_check(vat_id: str) -> str | None:
    country = vat_id[:2]
    pattern = VAT_ID_PATTERNS.get(country)
    if pattern is None:
        return f"USt-IdNr.-Land unbekannt: {country}"
    if not re.match(pattern, vat_id):
        return "USt-IdNr.-Format ungültig"
    if country == "DE" and legacy_de_vat_check_digit(vat_id[2:10]) != int(vat_id[10]):
        return "USt-IdNr.-Prüfziffer ungültig"
    if country == "AT" and legacy_at_uid_check_digit(vat_id[3:10]) != int(vat_id[10]):
        return "UID-Prüfziffer ungültig"
    return None


def test_vat_id_check_is_unchanged() -> None:
    rng = random.Random(7)
    ids = ["FR12345678901", "XX1", "DE1", "ATU1", ""]
    ids += [f"DE{rng.randrange(10**9):09d}" for _ in range(3000)]
    ids += [f"ATU{rng.randrange(10**8):08d}" for _ in range(3000)]
    for vat_id in ids:
        assert donut_values.vat_id_check(vat_id) == legacy_vat_id_check(vat_id), vat_id
