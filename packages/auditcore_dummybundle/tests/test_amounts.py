"""Betragsverteilung mit Restausgleich: centgenau, deterministisch, in Dezimalrechnung."""

from __future__ import annotations

from decimal import Decimal
from random import Random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_dummybundle import allocate, quantize, share, split_random

EXAMPLES = settings(max_examples=200, deadline=None)
CENTS = st.integers(min_value=0, max_value=10**12)


def test_allocate_remainder_goes_to_last_part() -> None:
    parts = allocate(Decimal("100.00"), [1, 1, 1])
    assert parts == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]


def test_allocate_follows_weights() -> None:
    assert allocate(Decimal("10.00"), [3, 1]) == [Decimal("7.50"), Decimal("2.50")]
    assert allocate(Decimal("0.01"), [1, 1, 1]) == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.01"),
    ]


@pytest.mark.parametrize(
    ("total", "weights"),
    [
        (Decimal("-1.00"), [1]),
        (Decimal("1.005"), [1]),
        (Decimal("1.00"), []),
        (Decimal("1.00"), [0, 0]),
        (Decimal("1.00"), [1, -1]),
    ],
)
def test_allocate_rejects_invalid_input(total: Decimal, weights: list[int]) -> None:
    with pytest.raises(ValueError):
        allocate(total, weights)


@EXAMPLES
@given(cents=CENTS, weights=st.lists(st.integers(0, 10**6), min_size=1, max_size=40))
def test_allocate_always_adds_up(cents: int, weights: list[int]) -> None:
    if sum(weights) == 0:
        weights = [*weights, 1]
    total = Decimal(cents) / 100
    parts = allocate(total, weights)
    assert sum(parts) == total
    assert len(parts) == len(weights)
    assert all(part >= 0 and part == part.quantize(Decimal("0.01")) for part in parts)


@EXAMPLES
@given(cents=st.integers(1_000, 10**11), parts=st.integers(1, 60), seed=st.integers(0, 2**31))
def test_split_random_adds_up_and_respects_minimum(cents: int, parts: int, seed: int) -> None:
    total = Decimal(cents) / 100
    minimum = Decimal("0.10")
    result = split_random(total, parts, Random(seed), minimum=minimum)
    assert sum(result) == total
    assert min(result) >= minimum
    assert result == split_random(total, parts, Random(seed), minimum=minimum)


def test_split_random_rejects_total_below_minimums() -> None:
    with pytest.raises(ValueError):
        split_random(Decimal("1.00"), 3, Random(1), minimum=Decimal("0.50"))
    with pytest.raises(ValueError):
        split_random(Decimal("1.00"), 0, Random(1))


def test_rounding_is_commercial() -> None:
    assert quantize(Decimal("0.005")) == Decimal("0.01")
    assert quantize(Decimal("2.675")) == Decimal("2.68")
    assert share(Decimal("100.10"), Decimal("0.75")) == Decimal("75.08")
