"""Reconciliation of expected and actual amounts and double-funding detection."""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

from ._buffers import MaskedBuffer, cents_input, numeric_array, series_items, to_buffer
from ._engine import accelerate, prange

#: Status codes of ``reconcile``.
MATCH = 0
WITHIN_TOLERANCE = 1
DEVIATION = 2
MISSING = 3


@dataclass(frozen=True)
class Reconciliation:
    """Difference ``actual − expected`` in cents and a status code per row."""

    difference: npt.NDArray[np.int64]
    status: npt.NDArray[np.int8]


@accelerate(parallel=True)
def reconcile_kernel(
    expected: npt.NDArray[np.int64],
    actual: npt.NDArray[np.int64],
    missing: npt.NDArray[np.bool_],
    tolerance: int,
    difference: npt.NDArray[np.int64],
    status: npt.NDArray[np.int8],
) -> None:
    """Element-wise difference and status (0 match, 1 tolerated, 2 deviation, 3 missing)."""
    for i in prange(expected.shape[0]):
        if missing[i]:
            difference[i] = 0
            status[i] = 3
            continue
        delta = actual[i] - expected[i]
        difference[i] = delta
        if delta == 0:
            status[i] = 0
        elif abs(delta) <= tolerance:
            status[i] = 1
        else:
            status[i] = 2


def _masked_cents(values: object, label: str) -> MaskedBuffer[np.int64]:
    buffer = to_buffer(values, np.int64, nulls="mask")
    cents_input(buffer.values, label)
    return buffer


def reconcile(
    expected_cents: object,
    actual_cents: object,
    *,
    tolerance_cents: int = 0,
    nulls: Literal["raise", "mask"] = "raise",
) -> Reconciliation:
    """Row-wise target/actual comparison with a tolerance in cents (caller's input).

    With ``nulls="mask"`` a missing value on either side yields status
    ``MISSING`` and difference 0 instead of an error.
    """
    if tolerance_cents < 0:
        raise ValueError("Die Toleranz darf nicht negativ sein.")
    if nulls == "raise":
        expected = cents_input(expected_cents, "Soll")
        actual = cents_input(actual_cents, "Ist")
        missing = np.zeros(expected.shape, dtype=np.bool_)
    else:
        left, right = _masked_cents(expected_cents, "Soll"), _masked_cents(actual_cents, "Ist")
        expected, actual = left.values, right.values
        missing = left.missing
        if expected.shape == actual.shape:
            missing = left.missing | right.missing
    if expected.shape != actual.shape:
        raise ValueError("Soll und Ist müssen gleich lang sein.")
    difference = np.zeros(expected.shape, dtype=np.int64)
    status = np.zeros(expected.shape, dtype=np.int8)
    reconcile_kernel(expected, actual, missing, tolerance_cents, difference, status)
    return Reconciliation(difference, status)


def first_occurrence_codes(codes: npt.NDArray[np.int64], count: int) -> npt.NDArray[np.int64]:
    """Relabel codes ``0 … count−1`` so that they number groups by first occurrence."""
    first = np.full(count, codes.shape[0], dtype=np.int64)
    np.minimum.at(first, codes, np.arange(codes.shape[0], dtype=np.int64))
    rank = np.empty(count, dtype=np.int64)
    rank[np.argsort(first, kind="stable")] = np.arange(count, dtype=np.int64)
    relabelled: npt.NDArray[np.int64] = rank[codes]
    return relabelled


def _factorize_array(
    array: npt.NDArray[np.generic],
) -> tuple[npt.NDArray[np.int64], tuple[Hashable, ...]]:
    """Vectorised ``factorize`` of a bool, integer or float array (same codes and keys).

    Text keys stay in the dict loop: sorting strings is slower than hashing them.
    """
    if array.dtype.kind == "f":
        nan = np.isnan(array)
        if bool(nan.any()):
            raise ValueError(f"Fehlender Schlüssel an Position {int(np.flatnonzero(nan)[0])}.")
    # Stable sort: ``first`` holds the first position of every distinct value.
    _, first, inverse = np.unique(array, return_index=True, return_inverse=True)
    order = np.argsort(first, kind="stable")
    rank = np.empty(order.shape[0], dtype=np.int64)
    rank[order] = np.arange(order.shape[0], dtype=np.int64)
    codes = np.ascontiguousarray(rank[inverse.reshape(-1)])
    keys: list[Hashable] = array[first[order]].tolist()
    return codes, tuple(keys)


def factorize(values: object) -> tuple[npt.NDArray[np.int64], tuple[Hashable, ...]]:
    """Integer codes in order of first occurrence and the distinct values.

    Accepts lists, ndarrays and pandas/polars series of hashable keys
    (receipt numbers, project IDs). Missing keys raise ``ValueError``.
    """
    array = numeric_array(values, "biuf")
    if array is not None:
        return _factorize_array(array)
    raw = series_items(values)
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
        raise TypeError("Erwartet wird eine Folge von Schlüsseln.")
    items = list(raw)
    seen: dict[Hashable, int] = {}
    codes = np.empty(len(items), dtype=np.int64)
    for index, item in enumerate(items):
        if item is None or (isinstance(item, float) and item != item):
            raise ValueError(f"Fehlender Schlüssel an Position {index}.")
        codes[index] = seen.setdefault(item, len(seen))
    return codes, tuple(seen)


@dataclass(frozen=True)
class DoubleFunding:
    """Rows whose key (and amount) recurs in at least two different projects."""

    flagged: npt.NDArray[np.bool_]
    group: npt.NDArray[np.int64]
    groups: int


@accelerate
def duplicate_scan_kernel(
    order: npt.NDArray[np.int64],
    keys: npt.NDArray[np.int64],
    amounts: npt.NDArray[np.int64],
    projects: npt.NDArray[np.int64],
    group: npt.NDArray[np.int64],
) -> int:
    """Scan rows sorted by (key, amount, project); number runs spanning ≥ 2 projects."""
    count = order.shape[0]
    groups = 0
    start = 0
    while start < count:
        head = order[start]
        stop = start + 1
        distinct = 1
        while (
            stop < count
            and keys[order[stop]] == keys[head]
            and amounts[order[stop]] == amounts[head]
        ):
            if projects[order[stop]] != projects[order[stop - 1]]:
                distinct += 1
            stop += 1
        if distinct >= 2:
            for position in range(start, stop):
                group[order[position]] = groups
            groups += 1
        start = stop
    return groups


def _codes(values: object) -> npt.NDArray[np.int64]:
    if isinstance(values, np.ndarray) and values.dtype == np.int64:
        return to_buffer(values, np.int64)
    return factorize(values)[0]


def double_funding(
    keys: object, amounts_cents: object, projects: object, *, match_amount: bool = True
) -> DoubleFunding:
    """Double-dip detection: the same receipt key (and amount) in different projects.

    Keys and projects may be any hashable values; they are factorised to
    int64 codes first. Group numbers follow the sorted code order.
    """
    key_codes, project_codes = _codes(keys), _codes(projects)
    amounts = cents_input(amounts_cents, "Betrag")
    if not key_codes.shape == amounts.shape == project_codes.shape:
        raise ValueError("Schlüssel, Beträge und Vorhaben müssen gleich lang sein.")
    compared = amounts if match_amount else np.zeros(amounts.shape, dtype=np.int64)
    order = np.lexsort((project_codes, compared, key_codes)).astype(np.int64)
    group = np.full(amounts.shape, -1, dtype=np.int64)
    groups = int(duplicate_scan_kernel(order, key_codes, compared, project_codes, group))
    return DoubleFunding(group >= 0, group, groups)
