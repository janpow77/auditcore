"""Adaptive dispatch and rate caching must preserve exact reference results."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import numpy as np
import pytest
from conftest import requires_numba

from auditcore_compute import DISABLE_ENV, _engine, accelerate, use_python
from auditcore_compute._quotas import _cached_rate, share_cents, share_kernel


@pytest.fixture(autouse=True)
def engine_path() -> str:
    return "engine"


@requires_numba
def test_serial_parallel_and_python_have_identical_cents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    amounts = np.resize(np.array([-(10**12), -5, -1, 0, 1, 5, 10**12], dtype=np.int64), 100_000)
    large = share_cents(amounts, "0.5")
    assert share_kernel.info().parallel and share_kernel.info().compiled
    small = share_cents(amounts[:7], "0.5")
    assert not share_kernel.info().parallel and share_kernel.info().compiled
    with use_python():
        reference = share_cents(amounts, "0.5")
    np.testing.assert_array_equal(large, reference)
    np.testing.assert_array_equal(small, reference[:7])
    serial = share_kernel._serial
    assert serial is not None
    parallel_dispatch = share_kernel._compiled
    serial_dispatch = serial._compiled
    signature = parallel_dispatch.signatures[0]
    parallel_key = parallel_dispatch._cache._index_key(
        signature, parallel_dispatch.targetctx.codegen()
    )
    serial_key = serial_dispatch._cache._index_key(signature, serial_dispatch.targetctx.codegen())
    assert parallel_key != serial_key


def test_fallback_is_observable_and_python_context_keeps_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(_engine, "_NUMBA", None)
    calls = []

    def original(value: int) -> int:
        calls.append("reference")
        return value * 2

    def vectorized(value: int) -> int:
        calls.append("numpy")
        return value * 2

    kernel = accelerate(original, fallback=vectorized)
    assert kernel(2) == 4 and kernel.info().mode == "numpy"
    with use_python():
        assert kernel(2) == 4
    assert calls == ["numpy", "reference"]


def test_cached_rates_keep_types_distinct_and_bound_memory() -> None:
    _cached_rate.cache_clear()
    valid = [1, 1.0, Decimal("1"), Fraction(1), "1"]
    assert share_cents([9] * 5, valid).tolist() == [9] * 5
    with pytest.raises(TypeError, match="keine Quote"):
        share_cents([9], [True])
    with pytest.raises(ValueError):
        share_cents([9], [float("nan")])
    for i in range(1100):
        _cached_rate(Fraction(i, 1100))
    assert _cached_rate.cache_info().currsize == 1024


@pytest.mark.parametrize("value", [-1, True, 1.5])
def test_invalid_parallel_threshold(value: object) -> None:
    with pytest.raises((TypeError, ValueError), match="min_parallel_size"):
        accelerate(min_parallel_size=value)


def test_small_threshold_uses_numpy_without_compiling(monkeypatch: pytest.MonkeyPatch) -> None:
    from auditcore_compute._outliers import threshold_kernel
    from auditcore_compute._vectorized import threshold

    kernel = accelerate(
        threshold_kernel.py_func, parallel=True, fallback=threshold, min_jit_size=250_000
    )

    def unexpected_compile() -> None:
        raise AssertionError("small mask must not initialize the compiler")

    monkeypatch.setattr(kernel, "_dispatcher", unexpected_compile)
    data = np.array([-100, 0, 100], dtype=np.int64)
    out = np.zeros(3, dtype=bool)
    kernel(data, 50, True, out)
    assert out.tolist() == [True, False, True]
    assert kernel.info().mode == "numpy" and not kernel.info().compiled
    with use_python():
        kernel(data, 50, True, out)
    assert out.tolist() == [True, False, True]


def test_numpy_threshold_requires_fallback() -> None:
    with pytest.raises(ValueError, match="NumPy"):
        accelerate(min_jit_size=1)
