"""Floating-point helpers: known reference values and invariants."""

from __future__ import annotations

import math
import random

import pytest

from auditcore_statistics.numeric import (
    chi2_survival,
    numpy_pairwise_sum,
    numpy_round,
    regularized_upper_gamma,
)


@pytest.mark.parametrize(
    ("statistic", "dof", "expected"),
    [
        (3.841458820694124, 1, 0.05),
        (15.507313055865453, 8, 0.05),
        (20.090235029663233, 8, 0.01),
        (112.02198574980785, 89, 0.05),
        (0.0, 8, 1.0),
    ],
)
def test_chi2_quantiles(statistic: float, dof: int, expected: float) -> None:
    assert math.isclose(chi2_survival(statistic, dof), expected, rel_tol=1e-9)


def test_gamma_and_survival_edge_cases() -> None:
    assert regularized_upper_gamma(2.0, 0.0) == 1.0
    assert math.isnan(chi2_survival(math.nan, 3))
    for bad in ((0.0, 1.0), (1.0, -1.0)):
        with pytest.raises(ValueError):
            regularized_upper_gamma(*bad)
    with pytest.raises(ValueError):
        chi2_survival(1.0, 0)
    assert chi2_survival(10_000.0, 8) == 0.0 or chi2_survival(10_000.0, 8) < 1e-300


def test_pairwise_sum_is_close_to_exact_sum() -> None:
    rng = random.Random(4)
    for size in (0, 1, 7, 8, 9, 127, 128, 129, 1000, 5000):
        values = [rng.uniform(-1e6, 1e6) for _ in range(size)]
        assert math.isclose(numpy_pairwise_sum(values), math.fsum(values), abs_tol=1e-6)


def test_numpy_round_is_half_even_after_scaling() -> None:
    assert numpy_round(0.125, 2) == 0.12
    assert numpy_round(0.135, 2) == 0.14
    assert numpy_round(2.675, 2) == 2.68  # 2.675 * 100 == 267.5 exactly; NumPy 1.26.2 agrees
    assert numpy_round(-1.005, 2) == -1.0
