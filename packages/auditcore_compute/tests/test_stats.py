"""Deterministic summation and weighted moments: bit-identical engines, ULP-close to exact."""

from __future__ import annotations

import math
from fractions import Fraction

import _reference as ref
import numpy as np
import pytest
from conftest import both_paths
from hypothesis import given
from hypothesis import strategies as st

from auditcore_compute.stats import (
    deterministic_sum,
    weighted_mean,
    weighted_std,
    weighted_variance,
)

# No values so small that products underflow (subnormal results lose relative accuracy).
values = st.floats(min_value=-1e9, max_value=1e9).filter(lambda v: v == 0 or abs(v) > 1e-100)
weights = st.floats(min_value=0.0, max_value=1e3).filter(lambda v: v == 0 or v > 1e-100)


def ulps(got: float, exact: Fraction) -> float:
    """Distance in units of the last place of the exactly rounded result."""
    nearest = float(exact)
    if got == nearest:
        return 0.0
    return float(abs(Fraction(got) - exact) / Fraction(math.ulp(nearest) or math.ulp(0.0)))


@given(st.lists(values, max_size=200))
def test_sum_is_bit_identical_and_nearly_exact(data: list[float]) -> None:
    jit, python = both_paths(lambda: deterministic_sum(data))
    assert math.copysign(1, jit) == math.copysign(1, python) and jit == python
    assert jit == ref.neumaier(data)
    exact = sum((Fraction(v) for v in data), Fraction(0))
    # Neumaier: |error| ≤ ulp(result) + 2·n·eps²·Σ|x| (eps = 2**-53).
    magnitude = sum((abs(Fraction(v)) for v in data), Fraction(0))
    bound = Fraction(math.ulp(float(exact))) + 2 * len(data) * magnitude / 2**106
    assert abs(Fraction(jit) - exact) <= bound


def test_sum_known_cancellation() -> None:
    assert deterministic_sum([1e16, 1.0, -1e16]) == 1.0
    assert deterministic_sum([0.1] * 10) == 1.0
    assert deterministic_sum([]) == 0.0
    with pytest.raises(ValueError, match="endlich"):
        deterministic_sum([math.inf])


@given(st.lists(st.tuples(values, weights), min_size=1, max_size=80))
def test_weighted_moments(rows: list[tuple[float, float]]) -> None:
    data = [v for v, _ in rows]
    weight = [w for _, w in rows]
    weight_sum, mean, squared, square_weights = ref.weighted_moments(data, weight)
    if weight_sum == 0:
        with pytest.raises(ValueError, match="positiv"):
            weighted_mean(data, weight)
        return
    jit, python = both_paths(lambda: weighted_mean(data, weight))
    assert jit == python
    # Rounding of each product w·x is amplified only by cancellation: bound by Σ|w·x|/Σw.
    spread = sum((abs(Fraction(w) * Fraction(x)) for x, w in rows), Fraction(0)) / weight_sum
    assert abs(Fraction(jit) - mean) <= 4 * spread / 2**53 + Fraction(math.ulp(float(mean)))
    if all(x >= 0 for x in data):
        assert ulps(jit, mean) <= 4
    jit_var, python_var = both_paths(lambda: weighted_variance(data, weight))
    assert jit_var == python_var
    exact = squared / weight_sum
    # Two-pass variance: the mean is rounded once; error bounded relative to Σw·x².
    scale = sum((Fraction(w) * Fraction(x) ** 2 for x, w in rows), Fraction(0)) / weight_sum
    assert abs(Fraction(jit_var) - exact) <= scale * Fraction(1, 2**40) + Fraction(math.ulp(0.0))


def test_variance_kinds() -> None:
    data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    assert weighted_mean(data) == 5.0
    assert weighted_variance(data) == 4.0
    assert weighted_std(data) == 2.0
    assert weighted_variance(data, kind="frequency") == 32.0 / 7.0
    counts = [1.0, 3.0, 2.0, 1.0]
    distinct = [2.0, 4.0, 5.0, 7.0]
    # Frequency weights reproduce the expanded sample variance exactly here.
    assert weighted_variance(distinct, counts, kind="frequency") == pytest.approx(
        weighted_variance([2.0, 4, 4, 4, 5, 5, 7], kind="frequency"), rel=1e-15
    )
    reliability = weighted_variance([1.0, 3.0], [0.5, 0.5], kind="reliability")
    assert reliability == 2.0
    assert weighted_std(np.array([1.0, 3.0]), kind="population") == 1.0


def test_stats_errors() -> None:
    with pytest.raises(ValueError, match="Keine Werte"):
        weighted_mean([])
    with pytest.raises(ValueError, match="gleich lang"):
        weighted_mean([1.0], [1.0, 2.0])
    with pytest.raises(ValueError, match="negativ"):
        weighted_mean([1.0], [-1.0])
    with pytest.raises(ValueError, match="Varianzart"):
        weighted_variance([1.0], kind="sample")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Zu wenige"):
        weighted_variance([1.0], kind="frequency")
    with pytest.raises(ValueError, match="Position 1"):
        weighted_mean([1.0, math.nan])


@given(
    st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=1e9).filter(lambda v: v == 0 or v > 1e-100),
            st.floats(min_value=1e-3, max_value=1e3),
        ),
        min_size=1,
        max_size=80,
    )
)
def test_weighted_mean_few_ulp_when_well_conditioned(rows: list[tuple[float, float]]) -> None:
    data = [v for v, _ in rows]
    weight = [w for _, w in rows]
    mean = ref.weighted_moments(data, weight)[1]
    assert ulps(weighted_mean(data, weight), mean) <= 4
