"""Plausibility checks against the list-based reference; bit-identical engines."""

from __future__ import annotations

import math

import _reference as ref
import numpy as np
import pytest
from conftest import bits, both_paths
from hypothesis import given
from hypothesis import strategies as st

from auditcore_compute.validation import (
    DEVIATION,
    MATCH,
    MISSING,
    WITHIN_TOLERANCE,
    double_funding,
    exceeds_threshold,
    factorize,
    iqr_outliers,
    mad_outliers,
    reconcile,
)

cents = st.integers(min_value=-(10**12), max_value=10**12)
maybe_cents = st.none() | cents
floats = st.floats(min_value=-1e12, max_value=1e12, allow_nan=False)


@given(
    rows=st.lists(st.tuples(maybe_cents, maybe_cents), max_size=60),
    tolerance=st.integers(min_value=0, max_value=1000),
)
def test_reconcile_matches_reference(
    rows: list[tuple[int | None, int | None]], tolerance: int
) -> None:
    expected = [e for e, _ in rows]
    actual = [a for _, a in rows]
    jit, python = both_paths(
        lambda: reconcile(expected, actual, tolerance_cents=tolerance, nulls="mask")
    )
    assert bits(jit.difference) == bits(python.difference)
    assert bits(jit.status) == bits(python.status)
    reference = [ref.reconcile(e, a, tolerance) for e, a in rows]
    assert list(zip(jit.difference.tolist(), jit.status.tolist(), strict=True)) == reference


def test_reconcile_status_codes_and_errors() -> None:
    result = reconcile([100, 100, 100], [100, 101, 150], tolerance_cents=1)
    assert result.status.tolist() == [MATCH, WITHIN_TOLERANCE, DEVIATION]
    assert result.difference.tolist() == [0, 1, 50]
    masked = reconcile([1, None], [None, 2], nulls="mask")
    assert masked.status.tolist() == [MISSING, MISSING]
    with pytest.raises(ValueError, match="Position 1"):
        reconcile([1, None], [1, 2])
    with pytest.raises(ValueError, match="gleich lang"):
        reconcile([1], [1, 2])
    with pytest.raises(ValueError, match="gleich lang"):
        reconcile([1], [1, 2], nulls="mask")
    with pytest.raises(ValueError, match="negativ"):
        reconcile([1], [1], tolerance_cents=-1)
    with pytest.raises(ValueError, match="10 Mrd"):
        reconcile([10**13], [1], nulls="mask")
    assert reconcile([], []).status.shape == (0,)


@given(st.lists(cents, max_size=60), cents, st.booleans())
def test_threshold(amounts: list[int], threshold: int, absolute: bool) -> None:
    threshold = abs(threshold)
    jit, python = both_paths(lambda: exceeds_threshold(amounts, threshold, absolute=absolute))
    assert bits(jit) == bits(python)
    assert jit.tolist() == [(abs(a) if absolute else a) > threshold for a in amounts]


@given(
    values=st.lists(floats, min_size=1, max_size=80),
    factor=st.floats(min_value=0.5, max_value=6),
)
def test_mad_matches_reference(values: list[float], factor: float) -> None:
    jit, python = both_paths(lambda: mad_outliers(values, factor))
    assert bits(jit.mask) == bits(python.mask)
    assert (jit.center, jit.spread, jit.lower, jit.upper) == (
        python.center,
        python.spread,
        python.lower,
        python.upper,
    )
    center, spread, lower, upper = ref.mad_bounds(values, factor)
    assert (jit.center, jit.spread, jit.lower, jit.upper) == (center, spread, lower, upper)
    assert jit.mask.tolist() == [v < lower or v > upper for v in values]


@given(
    values=st.lists(floats, min_size=1, max_size=80),
    factor=st.floats(min_value=0.5, max_value=6),
)
def test_iqr_matches_reference(values: list[float], factor: float) -> None:
    jit, python = both_paths(lambda: iqr_outliers(values, factor))
    assert bits(jit.mask) == bits(python.mask)
    center, spread, lower, upper = ref.iqr_bounds(values, factor)
    assert (jit.center, jit.spread, jit.lower, jit.upper) == (center, spread, lower, upper)
    assert jit.mask.tolist() == [v < lower or v > upper for v in values]


def test_outlier_examples_and_errors() -> None:
    result = mad_outliers([10.0, 11, 12, 13, 1000], 3.5)
    assert result.mask.tolist() == [False, False, False, False, True]
    assert result.center == 12.0 and result.spread == 1.0
    flat = mad_outliers([5.0, 5, 5, 6], 3.5)  # MAD = 0: every deviation counts
    assert flat.spread == 0.0 and flat.mask.tolist() == [False, False, False, True]
    tukey = iqr_outliers([1.0, 2, 3, 4, 100], 1.5)
    assert (tukey.lower, tukey.upper) == (-1.0, 7.0)
    for bad in ([], [1.0, math.nan], [math.inf]):
        with pytest.raises(ValueError):
            mad_outliers(bad, 3.5)
    with pytest.raises(ValueError, match="Faktor"):
        iqr_outliers([1.0], 0)


keys = st.sampled_from(["R-1", "R-2", "R-3", "R-4"])
projects = st.sampled_from(["P-A", "P-B", "P-C"])
small_amounts = st.integers(min_value=-3, max_value=3)


@given(
    rows=st.lists(st.tuples(keys, small_amounts, projects), max_size=60),
    match_amount=st.booleans(),
)
def test_double_funding_matches_reference(
    rows: list[tuple[str, int, str]], match_amount: bool
) -> None:
    key_list = [r[0] for r in rows]
    amounts = [r[1] for r in rows]
    project_list = [r[2] for r in rows]
    jit, python = both_paths(
        lambda: double_funding(key_list, amounts, project_list, match_amount=match_amount)
    )
    assert bits(jit.group) == bits(python.group) and jit.groups == python.groups
    expected = ref.double_funding(key_list, amounts, project_list, match_amount)
    assert jit.flagged.tolist() == expected
    assert jit.groups == len({g for g in jit.group.tolist() if g >= 0})


def test_double_funding_example() -> None:
    result = double_funding(
        np.array(["RE-7", "RE-7", "RE-8", "RE-7"], dtype=object),
        [125_000, 125_000, 99, 125_001],
        np.array([11, 12, 11, 11], dtype=np.int64),
    )
    assert result.flagged.tolist() == [True, True, False, False]
    assert result.group.tolist() == [0, 0, -1, -1]
    loose = double_funding(["RE-7", "RE-7"], [1, 2], ["A", "B"], match_amount=False)
    assert loose.groups == 1
    with pytest.raises(ValueError, match="gleich lang"):
        double_funding(["a"], [1, 2], ["x"])


def test_factorize() -> None:
    codes, uniques = factorize(["b", "a", "b", "c"])
    assert codes.tolist() == [0, 1, 0, 2] and uniques == ("b", "a", "c")
    assert factorize(np.array([3, 3, 1]))[0].tolist() == [0, 0, 1]
    with pytest.raises(ValueError, match="Position 1"):
        factorize(["a", None])
    with pytest.raises(ValueError, match="Position 0"):
        factorize([math.nan])
    with pytest.raises(TypeError):
        factorize("abc")
