"""to_buffer, to_cents and to_days: zero-copy where possible, explicit nulls, exact cents."""

from __future__ import annotations

import datetime as dt
import math
from decimal import Decimal

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditcore_compute import (
    MaskedBuffer,
    from_cents,
    to_buffer,
    to_cents,
    to_cents_buffer,
    to_days,
)

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")


def test_matching_ndarray_is_not_copied() -> None:
    data = np.arange(5, dtype=np.int64)
    assert to_buffer(data, np.int64) is data
    strided = np.arange(10, dtype=np.int64)[slice(None, None, 2)]  # every second value
    contiguous = to_buffer(strided, np.int64)
    assert contiguous.flags.c_contiguous and contiguous.tolist() == [0, 2, 4, 6, 8]
    widened = to_buffer(np.array([1, 2], dtype=np.int32), np.int64)
    assert widened.dtype == np.int64


def test_pandas_and_polars_without_nulls_are_zero_copy() -> None:
    series = pd.Series(np.arange(4, dtype=np.int64))
    assert np.shares_memory(to_buffer(series, np.int64), series.to_numpy())
    floats = pl.Series([1.5, 2.5])
    assert to_buffer(floats, np.float64).tolist() == [1.5, 2.5]
    assert to_buffer(pl.Series([1, 2]), np.int64).dtype == np.int64


def test_nulls_raise_or_mask_never_zero_silently() -> None:
    cases = [
        [1, None, 3],
        np.array([1.0, np.nan, 3.0]),
        pd.Series([1, None, 3], dtype="Int64"),
        pd.Series([1.0, np.nan, 3.0]),
        pl.Series([1, None, 3]),
        pl.Series([1.0, float("nan"), 3.0]),
    ]
    for values in cases:
        dtype = np.float64 if "float" in str(getattr(values, "dtype", "")).lower() else np.int64
        with pytest.raises(ValueError, match="Position 1"):
            to_buffer(values, dtype)
        masked = to_buffer(values, dtype, nulls="mask")
        assert isinstance(masked, MaskedBuffer)
        assert masked.missing.tolist() == [False, True, False]
        assert masked.any_missing
        assert masked.values.tolist() == [1, 0, 3]
    flags = to_buffer(pd.Series([True, None], dtype="boolean"), np.bool_, nulls="mask")
    assert flags.missing.tolist() == [False, True] and flags.values.tolist() == [True, False]


def test_lists_are_type_checked() -> None:
    assert to_buffer([1, 2], np.float64).tolist() == [1.0, 2.0]
    assert to_buffer([True, False], np.bool_).tolist() == [True, False]
    assert to_buffer(np.array([1, 2], dtype=object), np.int64).tolist() == [1, 2]
    assert to_buffer((x for x in [3]), np.int64).tolist() == [3]
    for values, dtype in (
        ([1.5], np.int64),
        ([True], np.int64),
        ([1], np.bool_),
        (["1"], np.float64),
    ):
        with pytest.raises(TypeError):
            to_buffer(values, dtype)
    with pytest.raises(TypeError, match="verlustfrei"):
        to_buffer(np.array([1.5]), np.int64)
    with pytest.raises(ValueError, match="eindimensional"):
        to_buffer(np.zeros((2, 2)), np.float64)
    with pytest.raises(ValueError, match="Datentypen"):
        to_buffer([1], np.int32)  # type: ignore[type-var]
    for bad in ("123", 5):
        with pytest.raises(TypeError):
            to_buffer(bad, np.int64)


class _NoNullApi:
    def to_numpy(self) -> np.ndarray:  # pragma: no cover - never reached
        return np.zeros(1)


def test_series_needs_null_api() -> None:
    with pytest.raises(TypeError, match="isna"):
        to_buffer(_NoNullApi(), np.float64)


def test_empty_inputs() -> None:
    assert to_buffer([], np.int64).shape == (0,)
    assert to_cents_buffer([]).shape == (0,)
    assert to_days([]).shape == (0,)


@pytest.mark.parametrize(
    ("value", "cents"),
    [
        (Decimal("1234.565"), 123457),
        (Decimal("-0.005"), -1),
        ("0.105", 11),
        (" 2.5 ", 250),
        (7, 700),
        (0.1, 10),
        (1.005, 101),  # Decimal(str(1.005)) = 1.005, not the binary 1.00499…
        (-2.675, -268),
    ],
)
def test_to_cents_half_up(value: Decimal | str | int | float, cents: int) -> None:
    assert to_cents(value) == cents


def test_to_cents_errors() -> None:
    for bad in ("1,5", "abc"):
        with pytest.raises(ValueError, match="gültiger"):
            to_cents(bad)
    for bad_value in (math.nan, math.inf, Decimal("NaN")):
        with pytest.raises(ValueError, match="endlicher"):
            to_cents(bad_value)
    with pytest.raises(TypeError):
        to_cents(True)
    with pytest.raises(TypeError):
        to_cents(None)  # type: ignore[arg-type]


@given(st.decimals(min_value=-(10**9), max_value=10**9, places=2))
def test_cents_roundtrip(value: Decimal) -> None:
    assert from_cents(to_cents(value)) == value


def test_cents_buffer_from_all_inputs() -> None:
    expected = [10, 1050, -1]
    for values in (
        [0.1, "10.50", Decimal("-0.005")],
        np.array([0.1, 10.5, -0.005]),
        pd.Series([0.1, 10.5, -0.005]),
        pl.Series([0.1, 10.5, -0.005]),
    ):
        assert to_cents_buffer(values).tolist() == expected
    with pytest.raises(ValueError, match="Position 1"):
        to_cents_buffer([1, None])
    with pytest.raises(TypeError):
        to_cents_buffer("12")


def test_days() -> None:
    days = [dt.date(1970, 1, 1), dt.date(2024, 2, 29), dt.date(1900, 3, 1)]
    expected = [0, 19782, -25508]
    assert to_days(days).tolist() == expected
    assert to_days(np.array(days, dtype="datetime64[D]")).tolist() == expected
    assert to_days(pd.Series(pd.to_datetime(days))).tolist() == expected
    with pytest.raises(ValueError, match="NaT"):
        to_days(np.array(["2024-01-01", "NaT"], dtype="datetime64[D]"))
    with pytest.raises(TypeError, match="kein Datum"):
        to_days([dt.datetime(2024, 1, 1)])
    with pytest.raises(TypeError):
        to_days("2024-01-01")
