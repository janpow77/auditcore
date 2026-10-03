"""Conversion of lists, NumPy arrays and pandas/polars series into kernel buffers.

Kernels only see C-contiguous NumPy arrays of a fixed dtype. Missing values
(``None``, NaN, pandas ``NA``/``NaT``, polars ``null``) are never turned into
0 silently: the default raises, ``nulls="mask"`` returns the values together
with an explicit mask.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Generic, Literal, TypeVar, cast, overload

import numpy as np
import numpy.typing as npt

from ._intmath import MAX_ABS_CENTS

S = TypeVar("S", np.int64, np.float64, np.bool_)
Nulls = Literal["raise", "mask"]
_EPOCH_ORDINAL = dt.date(1970, 1, 1).toordinal()
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class MaskedBuffer(Generic[S]):
    """Values with an explicit missing-value mask (masked positions hold 0)."""

    values: npt.NDArray[S]
    missing: npt.NDArray[np.bool_]

    @property
    def any_missing(self) -> bool:
        """True when at least one position is missing."""
        return bool(self.missing.any())


def _is_series(values: object) -> bool:
    return hasattr(values, "to_numpy") and not isinstance(values, np.ndarray)


def series_items(values: object) -> object:
    """Python list of an ndarray or pandas/polars series; other inputs unchanged."""
    if isinstance(values, np.ndarray):
        return values.tolist()
    method = getattr(values, "to_numpy", None)
    if callable(method):
        return np.asarray(method()).tolist()
    return values


def _series_missing(values: object) -> npt.NDArray[np.bool_]:
    for name in ("isna", "is_null"):
        method = getattr(values, name, None)
        if callable(method):
            return np.ascontiguousarray(np.asarray(method().to_numpy(), dtype=np.bool_))
    raise TypeError("Serie ohne isna()/is_null() wird nicht unterstützt.")


_Raw = tuple[npt.NDArray[np.generic], npt.NDArray[np.bool_]]


def _from_series(values: object, dtype: np.dtype[np.generic]) -> _Raw:
    missing = _series_missing(values)
    if missing.any():
        zero = False if dtype == np.bool_ else 0
        filled = values.fillna(zero) if hasattr(values, "fillna") else values.fill_null(zero)  # type: ignore[attr-defined]
        values = filled
    raw = np.asarray(values.to_numpy())  # type: ignore[attr-defined]
    # Older pandas return object arrays for nullable integers even without NA.
    array = _from_iterable(raw.tolist(), dtype)[0] if raw.dtype == np.object_ else _cast(raw, dtype)
    if array.dtype.kind == "f":
        missing = missing | np.isnan(array)
        array = np.where(missing, 0.0, array) if missing.any() else array
    return np.ascontiguousarray(array), missing


def _cast(array: npt.NDArray[np.generic], dtype: np.dtype[np.generic]) -> npt.NDArray[np.generic]:
    if array.dtype == dtype:
        return array
    if array.dtype == np.object_ or not np.can_cast(array.dtype, dtype, casting="safe"):
        raise TypeError(f"Datentyp {array.dtype} lässt sich nicht verlustfrei in {dtype} wandeln.")
    return array.astype(dtype)


def _python_value(value: object, dtype: np.dtype[np.generic], index: int) -> object:
    if dtype == np.bool_:
        allowed: bool = isinstance(value, (bool, np.bool_))
    elif dtype == np.int64:
        allowed = isinstance(value, (int, np.integer)) and not isinstance(value, bool)
    else:
        allowed = isinstance(value, (int, float, np.integer, np.floating))
        allowed = allowed and not isinstance(value, bool)
    if not allowed:
        raise TypeError(f"Position {index}: {type(value).__name__} ist kein Wert für {dtype}.")
    return value


def _is_null(value: object) -> bool:
    return value is None or (isinstance(value, (float, np.floating)) and math.isnan(value))


def _from_iterable(values: Iterable[object], dtype: np.dtype[np.generic]) -> _Raw:
    items = list(values)
    missing = np.fromiter((_is_null(v) for v in items), dtype=np.bool_, count=len(items))
    zero = False if dtype == np.bool_ else 0
    filled = [
        zero if m else _python_value(v, dtype, i)
        for i, (v, m) in enumerate(zip(items, missing, strict=True))
    ]
    return np.array(filled, dtype=dtype), missing


def _from_array(values: npt.NDArray[np.generic], dtype: np.dtype[np.generic]) -> _Raw:
    if values.ndim != 1:
        raise ValueError("Es werden nur eindimensionale Arrays verarbeitet.")
    if values.dtype == np.object_:
        return _from_iterable(values.tolist(), dtype)
    array = _cast(values, dtype)
    missing = np.isnan(array) if array.dtype.kind == "f" else np.zeros(array.shape, np.bool_)
    if missing.any():
        array = np.where(missing, 0.0, array)
    return np.ascontiguousarray(array), missing


def _masked(values: object, dtype: type[np.generic]) -> _Raw:
    if dtype not in (np.int64, np.float64, np.bool_):
        raise ValueError("Unterstützte Datentypen: np.int64, np.float64, np.bool_.")
    target = np.dtype(dtype)
    if isinstance(values, (str, bytes)):
        raise TypeError("Eine Zeichenkette ist keine Wertefolge.")
    if isinstance(values, np.ndarray):
        return _from_array(values, target)
    if _is_series(values):
        return _from_series(values, target)
    if isinstance(values, Iterable):
        return _from_iterable(values, target)
    raise TypeError(f"{type(values).__name__} ist keine Wertefolge.")


@overload
def to_buffer(values: object, dtype: type[S], *, nulls: Literal["raise"] = ...) -> npt.NDArray[S]:
    """Convert values into a C-contiguous NumPy buffer of ``dtype`` (nulls raise)."""


@overload
def to_buffer(values: object, dtype: type[S], *, nulls: Literal["mask"]) -> MaskedBuffer[S]:
    """Convert values into a buffer plus an explicit missing-value mask."""


def to_buffer(
    values: object, dtype: type[S], *, nulls: Nulls = "raise"
) -> npt.NDArray[S] | MaskedBuffer[S]:
    """Convert a list, ndarray, pandas or polars series into a C-contiguous buffer.

    ``dtype`` is ``np.int64``, ``np.float64`` or ``np.bool_``. A matching
    C-contiguous ndarray is returned without copying; otherwise exactly one
    converted array is produced. Only lossless (``safe``) casts are performed.
    Missing values raise ``ValueError`` unless ``nulls="mask"``.
    """
    raw, missing = _masked(values, dtype)
    array = cast("npt.NDArray[S]", raw)
    if nulls == "mask":
        return MaskedBuffer(array, missing)
    if bool(missing.any()):
        first = int(np.flatnonzero(missing)[0])
        raise ValueError(
            f"Fehlender Wert an Position {first}; nulls='mask' wählen oder bereinigen."
        )
    return array


def to_cents(value: Decimal | str | int | float) -> int:
    """Euro amount as integer cents, commercially rounded (ROUND_HALF_UP).

    ``int`` means whole euros; ``float`` goes through ``Decimal(str(value))`` so
    that ``0.1`` stays 10 cents; strings use a decimal point (``"1234.56"``).
    """
    if isinstance(value, bool) or not isinstance(value, (Decimal, str, int, float)):
        raise TypeError(f"{type(value).__name__} ist kein Betrag.")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError(f"Kein gültiger Betrag: {value!r}") from None
    if not number.is_finite():
        raise ValueError(f"Kein endlicher Betrag: {value!r}")
    return int(number.quantize(_CENT, rounding=ROUND_HALF_UP).scaleb(2))


def to_cents_buffer(values: object) -> npt.NDArray[np.int64]:
    """Euro amounts (sequence or series) as an int64 cent buffer; missing values raise."""
    items = series_items(values)
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes)):
        raise TypeError("Erwartet wird eine Folge von Beträgen.")
    cents = []
    for index, value in enumerate(items):
        if _is_null(value):
            raise ValueError(f"Fehlender Betrag an Position {index}.")
        cents.append(to_cents(value))
    return np.array(cents, dtype=np.int64)


def cents_input(values: object, label: str) -> npt.NDArray[np.int64]:
    """Integer cent buffer within ±10 billion euros per row (int64-safe kernels)."""
    array = to_buffer(values, np.int64)
    if array.size and (int(np.min(array)) < -MAX_ABS_CENTS or int(np.max(array)) > MAX_ABS_CENTS):
        raise ValueError(f"{label}: Betrag über 10 Mrd. € je Zeile wird nicht unterstützt.")
    return array


def from_cents(cents: int) -> Decimal:
    """Integer cents back to a Decimal euro amount with two places."""
    return Decimal(int(cents)).scaleb(-2)


def _day_number(value: object, index: int) -> int:
    if isinstance(value, dt.datetime) or not isinstance(value, dt.date):
        raise TypeError(f"Position {index}: {type(value).__name__} ist kein Datum (date).")
    return value.toordinal() - _EPOCH_ORDINAL


def to_days(values: object) -> npt.NDArray[np.int64]:
    """Dates (``date`` objects or ``datetime64``) as int64 days since 1970-01-01."""
    raw = values.to_numpy() if _is_series(values) else values  # type: ignore[attr-defined]
    if isinstance(raw, np.ndarray) and raw.dtype.kind == "M":
        if np.isnat(raw).any():
            raise ValueError("Fehlendes Datum (NaT).")
        return np.ascontiguousarray(raw.astype("datetime64[D]").astype(np.int64))
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
        raise TypeError("Erwartet wird eine Folge von Daten.")
    return np.array([_day_number(v, i) for i, v in enumerate(raw)], dtype=np.int64)
