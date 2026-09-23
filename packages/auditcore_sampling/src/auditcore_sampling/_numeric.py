"""Internal float helpers reproducing NumPy/pandas results without NumPy."""

from __future__ import annotations

import math
from collections.abc import Sequence

_BLOCK = 128


def pairwise_sum(values: Sequence[float]) -> float:
    """NumPy ``add.reduce`` order for contiguous float64 data."""
    count = len(values)
    if count < 8:
        result = 0.0
        for value in values:
            result += value
        return result
    if count <= _BLOCK:
        acc = [float(v) for v in values[:8]]
        index = 8
        limit = count - (count % 8)
        while index < limit:
            for lane in range(8):
                acc[lane] += values[index + lane]
            index += 8
        result = ((acc[0] + acc[1]) + (acc[2] + acc[3])) + ((acc[4] + acc[5]) + (acc[6] + acc[7]))
        while index < count:
            result += values[index]
            index += 1
        return result
    half = count // 2
    half -= half % 8
    return pairwise_sum(values[:half]) + pairwise_sum(values[half:])


def is_missing(value: float | int | None) -> bool:
    """None or NaN."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def pandas_sum(values: Sequence[float | int | None]) -> float | int:
    """``Series.sum()`` (skipna): integers exactly, floats pairwise with NaN as 0."""
    if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        return sum(values)  # type: ignore[arg-type]
    return pairwise_sum([0.0 if is_missing(v) else float(v) for v in values])  # type: ignore[arg-type]


def pandas_cumsum(values: Sequence[float | int | None]) -> list[float | None]:
    """``Series.cumsum()`` (skipna): missing positions stay missing, sum continues."""
    result: list[float | None] = []
    running = 0.0
    for value in values:
        if is_missing(value):
            result.append(None)
            continue
        running += value  # type: ignore[operator]
        result.append(running)
    return result


def numpy_round(value: float, decimals: int) -> float:
    """``numpy.round`` for float64."""
    factor = 10.0**decimals
    return round(value * factor) / factor
