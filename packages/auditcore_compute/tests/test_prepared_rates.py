"""Prepared rates keep cent-exact behavior across independent evaluations."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import numpy as np
import pytest

from auditcore_compute.finance import PreparedRates, apply_reduction, cofinancing, share_cents


def test_prepared_rates_match_input_and_keep_snapshot() -> None:
    rates = ["0.5", Decimal("0.4"), Fraction(1, 3), 0.75, 1, 0]
    prepared = PreparedRates(rates)
    amounts = np.array([-1, 5, 10**12, -(10**12), 5, 7], dtype=np.int64)
    expected = share_cents(amounts, rates)
    rates[:] = [0] * len(rates)
    assert len(prepared) == len(amounts)
    for factor in [1, -1]:
        actual = share_cents(amounts * factor, prepared)
        np.testing.assert_array_equal(actual, expected * factor)
        split = cofinancing(amounts * factor, prepared)
        np.testing.assert_array_equal(split.share + split.rest, amounts * factor)
        np.testing.assert_array_equal(apply_reduction(amounts * factor, prepared).share, actual)


@pytest.mark.parametrize("rates", [[True], ["2"], ["nan"], [Fraction(1, 1_000_001)], "0.5"])
def test_invalid_prepared_rates_are_rejected(rates: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        PreparedRates(rates)


def test_prepared_size_and_empty_input() -> None:
    assert share_cents([], PreparedRates([])).tolist() == []
    with pytest.raises(ValueError, match="genau eine Quote"):
        share_cents([1, 2], PreparedRates(["0.5"]))
