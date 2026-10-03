"""Overflow-free integer helpers against exact Fractions, in both engines."""

from __future__ import annotations

from fractions import Fraction

import _reference as ref
from hypothesis import assume, given
from hypothesis import strategies as st

from auditcore_compute import accelerate
from auditcore_compute._intmath import div_round, mul_div_round


@accelerate(cache=False)
def _mul_div_round(value: int, factor: int, divisor: int) -> int:
    return mul_div_round(value, factor, divisor)


@given(
    value=st.integers(min_value=-(10**12), max_value=10**12),
    factor=st.integers(min_value=-(5 * 10**11), max_value=5 * 10**11),
    divisor=st.integers(min_value=1, max_value=3 * 10**9),
)
def test_mul_div_round_is_exact(value: int, factor: int, divisor: int) -> None:
    # Documented domain: the quotient itself must fit into int64 with headroom.
    assume(abs(value * factor) // divisor < 2**61)
    expected = ref.round_half_up(Fraction(value * factor, divisor))
    assert _mul_div_round(value, factor, divisor) == expected


def test_large_products_round_half_away_from_zero() -> None:
    # Products above 4e18 take the split path; remainders exactly at and above one half.
    divisor = 1_335_900_000
    for value, factor in ((10**12, 4 * 10**11 + 1), (999_999_999_999, 433_590_000_001)):
        for sign in (1, -1):
            expected = ref.round_half_up(Fraction(sign * value * factor, divisor))
            assert _mul_div_round(sign * value, factor, divisor) == expected
    half = 2 * 10**9
    value = 3 * 10**9 + 1  # (value * factor) mod divisor == divisor / 2
    assert _mul_div_round(value, half + 1, half) == ref.round_half_up(
        Fraction(value * (half + 1), half)
    )


@given(st.integers(min_value=-(10**16), max_value=10**16), st.integers(1, 10**12))
def test_div_round(numerator: int, divisor: int) -> None:
    assert div_round(numerator, divisor) == ref.round_half_up(Fraction(numerator, divisor))
