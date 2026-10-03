"""Columns of the vectorised evaluation: input check, NumPy views, record values.

A column is a list, a one-dimensional ndarray or a pandas/polars series. The
vectorised rule kinds read NumPy views where the dtype allows it and fall back
to the record values (``items``) everywhere else; ``items`` yields the values
``DataFrame.to_dict("records")`` would yield, so both paths decide alike.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import TypeAlias

import numpy as np
import numpy.typing as npt
from auditcore_compute import to_cents_buffer
from auditcore_compute.validation import factorize, first_occurrence_codes

from .base import CENT_LIMIT, CENT_LIMIT_EUROS, MISSING_KEY, Table
from .errors import InputError
from .values import coerce_number, is_missing, strict_amount, text

Bools: TypeAlias = npt.NDArray[np.bool_]
Floats: TypeAlias = npt.NDArray[np.float64]
Ints: TypeAlias = npt.NDArray[np.int64]
#: ``None`` as a 0-d object array (element-wise comparison with an object column).
_NONE = np.array(None, dtype=object)
#: Dtype kinds read as numbers without a per-value loop.
NUMERIC_KINDS = "fiu"


def _is_series(values: object) -> bool:
    return hasattr(values, "to_numpy") and not isinstance(values, np.ndarray)


def _length(name: str, values: object) -> int:
    if isinstance(values, np.ndarray):
        if values.ndim != 1:
            raise InputError(f"Spalte {name!r}: nur eindimensionale Arrays.")
        return int(values.shape[0])
    if _is_series(values) or isinstance(values, list | tuple):
        return len(values)  # type: ignore[arg-type]
    raise InputError(f"Spalte {name!r}: Liste, Array oder Serie erwartet.")


class ColumnData:
    """Named columns of equal length with cached NumPy views and record values."""

    def __init__(self, columns: Mapping[str, object]) -> None:
        if not all(isinstance(name, str) for name in columns):
            raise InputError("Spaltennamen müssen Text sein.")
        lengths = {name: _length(name, values) for name, values in columns.items()}
        if len(set(lengths.values())) > 1:
            raise InputError(f"Spalten unterschiedlich lang: {lengths}.")
        self._raw = dict(columns)
        self._items: dict[str, list[object]] = {}
        self._arrays: dict[str, npt.NDArray[np.generic] | None] = {}
        self.missing: dict[str, Bools] = {}
        self.codes: dict[str, tuple[Ints, tuple[object, ...]]] = {}
        self.names = tuple(columns)
        self.size = next(iter(lengths.values()), 0)

    def has(self, *names: str) -> bool:
        """Whether every named column is present."""
        return all(name in self._raw for name in names)

    def array(self, name: str) -> npt.NDArray[np.generic] | None:
        """NumPy view of an ndarray or series column (``None`` for lists and absent columns)."""
        if name not in self._arrays:
            raw = self._raw.get(name)
            view: npt.NDArray[np.generic] | None = None
            if isinstance(raw, np.ndarray):
                view = raw.astype("datetime64[us]") if raw.dtype.kind == "M" else raw
            elif raw is not None and _is_series(raw):
                view = np.asarray(raw.to_numpy())  # type: ignore[attr-defined]
            self._arrays[name] = view
        return self._arrays[name]

    def items(self, name: str) -> list[object]:
        """Record values of a column (``to_dict("records")`` semantics), cached."""
        if name not in self._items:
            raw = self._raw[name]
            if isinstance(raw, np.ndarray):
                array = raw.astype("datetime64[us]") if raw.dtype.kind == "M" else raw
                values: list[object] = array.astype(object).tolist()
            elif _is_series(raw):
                values = list(raw.tolist())  # type: ignore[attr-defined]
            else:
                values = list(raw)  # type: ignore[call-overload]
            self._items[name] = values
        return self._items[name]


class ColumnTable(Table):
    """:class:`Table` over :class:`ColumnData` for the record-wise rule kinds."""

    def __init__(self, data: ColumnData) -> None:
        super().__init__((), data.names)
        self.data = data

    def __len__(self) -> int:
        return self.data.size

    def value(self, index: int, name: str) -> object:
        """Cell value; an absent column reads as ``None`` (missing)."""
        return self.data.items(name)[index] if self.data.has(name) else None


def _object_missing(array: npt.NDArray[np.generic]) -> Bools | None:
    """``value != value`` or ``value is None`` element-wise; ``None`` if a value objects."""
    try:
        nan_like = np.not_equal(array, array)
        none = np.equal(array, _NONE)
    except (TypeError, ValueError):  # e.g. pandas.NA: comparison is ambiguous
        return None
    mask: Bools = nan_like | none
    return mask


def _missing(data: ColumnData, name: str) -> Bools:
    array = data.array(name)
    if array is not None and array.dtype.kind in "fc":
        return np.isnan(array)
    if array is not None and array.dtype.kind in "Mm":
        return np.isnat(array)
    if array is not None and array.dtype.kind in "biuUS":
        return np.zeros(data.size, dtype=np.bool_)
    if array is not None and array.dtype.kind == "O":
        fast = _object_missing(array)
        if fast is not None:
            return fast
    return np.fromiter((is_missing(v) for v in data.items(name)), np.bool_, data.size)


def missing_mask(data: ColumnData, name: str) -> Bools:
    """Missing values (``None``, NaN, ``NA``, ``NaT``) of a column; absent = all missing.

    Same rule as :func:`auditcore_risk.values.is_missing` (``None`` or
    ``value != value``); cached per column.
    """
    if not data.has(name):
        return np.ones(data.size, dtype=np.bool_)
    if name not in data.missing:
        data.missing[name] = _missing(data, name)
    return data.missing[name]


def numbers(data: ColumnData, name: str, parse: str) -> tuple[Floats, Bools]:
    """Amounts by ``parse`` (``strict``/``coerce``) as float64 plus the missing mask."""
    array = data.array(name)
    if array is not None and array.dtype.kind in NUMERIC_KINDS:
        values = array.astype(np.float64)
        return values, np.isnan(values)
    convert = coerce_number if parse == "coerce" else _strict
    parsed = [convert(v, name) for v in data.items(name)]
    missing = np.fromiter((v is None for v in parsed), np.bool_, data.size)
    filled = [0.0 if v is None else v for v in parsed]
    return np.array(filled, dtype=np.float64).reshape(data.size), missing


def _strict(value: object, name: str) -> float | None:
    return strict_amount(value, name, None)


def amounts(data: ColumnData, name: str, parse: str, substitute: float) -> Floats:
    """Amounts with ``substitute`` for missing values and for an absent column."""
    if not data.has(name):
        return np.full(data.size, float(substitute), dtype=np.float64)
    values, missing = numbers(data, name, parse)
    return np.where(missing, float(substitute), values)


def cents(values: Floats) -> tuple[Ints, Bools]:
    """Whole cents (``to_cents_buffer``) and which values are convertible.

    Same bound as :func:`auditcore_risk.base.amount_cents`: finite and at most
    10 Mrd. € in magnitude after rounding; other positions hold 0.
    """
    candidate = np.isfinite(values) & (np.abs(values) <= 10 * CENT_LIMIT_EUROS)
    converted = to_cents_buffer(np.where(candidate, values, 0.0))
    ok = candidate & (np.abs(converted) <= CENT_LIMIT)
    return np.where(ok, converted, 0), ok


def _object_keys(data: ColumnData, name: str, missing: Bools) -> list[object]:
    values = data.items(name)
    return [MISSING_KEY if absent else values[i] for i, absent in enumerate(missing.tolist())]


def _numeric_codes(
    array: npt.NDArray[np.generic], missing: Bools
) -> tuple[Ints, tuple[object, ...]]:
    present, uniques = factorize(array[~missing])
    codes = np.full(array.shape[0], len(uniques), dtype=np.int64)
    codes[~missing] = present
    keys: list[object] = [*uniques, MISSING_KEY]
    relabelled = first_occurrence_codes(codes, len(keys))
    order = np.empty(len(keys), dtype=np.int64)
    order[relabelled] = codes  # new label -> old code
    used = int(relabelled.max()) + 1 if array.shape[0] else 0
    return relabelled, tuple(keys[i] for i in order[:used].tolist())


def _codes(data: ColumnData, name: str) -> tuple[Ints, tuple[object, ...]]:
    missing = missing_mask(data, name)
    array = data.array(name) if data.has(name) else None
    if array is not None and array.dtype.kind in "biuf":
        return _numeric_codes(array, missing)
    labels = _object_keys(data, name, missing) if data.has(name) else [MISSING_KEY] * data.size
    try:
        return factorize(labels)
    except TypeError as exc:
        raise InputError(f"Feld {name!r}: Wert ist nicht als Schlüssel nutzbar.") from exc


def key_codes(data: ColumnData, name: str) -> tuple[Ints, tuple[object, ...]]:
    """Group code per record in order of first occurrence; missing values form one group.

    The keys follow the codes; the missing group is :data:`MISSING_KEY`.
    Unhashable values raise ``InputError`` like the record path. Cached per column.
    """
    if name not in data.codes:
        data.codes[name] = _codes(data, name)
    return data.codes[name]


def _text_keys(data: ColumnData, name: str) -> tuple[Ints, tuple[str | None, ...]] | None:
    """Codes and texts per group when every present key is a ``str`` (else ``None``).

    A value equal to a ``str`` key is itself a ``str`` with the same content, so
    ``str(value)`` is the same for the whole group.
    """
    try:
        codes, keys = key_codes(data, name)
    except InputError:
        return None
    if not all(k is MISSING_KEY or type(k) is str for k in keys):
        return None
    return codes, tuple(None if k is MISSING_KEY else str(k) for k in keys)


def text_flags(
    data: ColumnData, name: str, rows: Ints, decide: Callable[[str | None], bool]
) -> Bools:
    """``decide(text(value))`` for the given rows, evaluated once per distinct text."""
    if data.has(name):
        grouped = _text_keys(data, name)
        if grouped is not None:
            codes, keys = grouped
            per_key = np.array([decide(k) for k in keys], dtype=np.bool_)
            selected: Bools = per_key[codes[rows]]
            return selected
    found = texts(data, name, rows.tolist())
    return np.array([decide(t) for t in found], dtype=np.bool_).reshape(rows.shape[0])


def texts(data: ColumnData, name: str, rows: Iterable[int]) -> list[str | None]:
    """``str(value)`` of the given rows, ``None`` where missing or the column is absent."""
    if not data.has(name):
        return [None for _ in rows]
    values = data.items(name)
    return [text(values[i]) for i in rows]
