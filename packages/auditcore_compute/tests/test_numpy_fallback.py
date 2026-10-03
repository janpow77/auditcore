"""Every NumPy fallback matches the original kernel, including boundary statuses."""

from __future__ import annotations

import numpy as np
import pytest

from auditcore_compute import _engine, accelerate
from auditcore_compute import _vectorized as vector
from auditcore_compute._duplicates import reconcile_kernel
from auditcore_compute._outliers import band_kernel
from auditcore_compute._quotas import quota_kernel, share_kernel


@pytest.fixture(autouse=True)
def engine_path() -> str:
    return "engine"


def compare(monkeypatch: pytest.MonkeyPatch, original, fallback, inputs, outputs) -> None:
    monkeypatch.setattr(_engine, "_NUMBA", None)
    expected = [np.zeros_like(out) for out in outputs]
    original.py_func(*inputs, *expected)
    kernel = accelerate(original.py_func, fallback=fallback)
    kernel(*inputs, *outputs)
    for actual, reference in zip(outputs, expected, strict=True):
        np.testing.assert_array_equal(actual, reference)
    assert kernel.info().mode == "numpy"


def test_share_fallback_at_money_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    amounts = np.array([-(10**12), -1, 0, 1, 10**12], dtype=np.int64)
    numerators = np.array([999999, 1, 0, 1, 1], dtype=np.int64)
    denominators = np.array([1000000, 2, 1, 2, 3], dtype=np.int64)
    compare(
        monkeypatch,
        share_kernel,
        vector.share,
        [amounts, numerators, denominators],
        [np.zeros(5, dtype=np.int64)],
    )


@pytest.mark.parametrize("bounds", [[1, 2, 5, 1, 3, 4], [0, 0, 1, 0, 1, 1]])
def test_quota_fallback_status_and_undefined_totals(
    monkeypatch: pytest.MonkeyPatch, bounds
) -> None:
    parts = np.array([-1, 0, 4, 8, 10**12, 1], dtype=np.int64)
    totals = np.array([0, -1, 10, 10, 10**12, 2], dtype=np.int64)
    compare(
        monkeypatch,
        quota_kernel,
        vector.quota,
        [parts, totals, np.array(bounds)],
        [np.zeros(6, dtype=np.int64), np.zeros(6, dtype=np.int8)],
    )


def test_reconcile_fallback_tolerances_and_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = np.array([100, -100, 0, 10**12, -(10**12)], dtype=np.int64)
    actual = np.array([100, -99, 2, -(10**12), 10**12], dtype=np.int64)
    missing = np.array([False, False, False, True, False])
    compare(
        monkeypatch,
        reconcile_kernel,
        vector.reconcile,
        [expected, actual, missing, 1],
        [np.zeros(5, dtype=np.int64), np.zeros(5, dtype=np.int8)],
    )


def test_band_fallback_preserves_boundary_inclusion(monkeypatch: pytest.MonkeyPatch) -> None:
    values = np.array([-2.0, -1.0, -0.0, 0.0, 1.0, 2.0])
    compare(monkeypatch, band_kernel, vector.band, [values, -1.0, 1.0], [np.zeros(6, dtype=bool)])
