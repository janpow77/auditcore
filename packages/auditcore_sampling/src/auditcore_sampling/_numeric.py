"""Internal float helpers reproducing pandas results without NumPy.

The NumPy-compatible pairwise sum and ``numpy_round`` come from
``auditcore_common.numeric`` (proven bitwise equal to the former copies here).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from auditcore_common.numeric import numpy_pairwise_sum


def is_missing(value: float | int | None) -> bool:
    """None or NaN."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def pandas_sum(values: Sequence[float | int | None]) -> float | int:
    """``Series.sum()`` (skipna): integers exactly, floats pairwise with NaN as 0."""
    if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        return sum(values)  # type: ignore[arg-type]
    floats = [0.0 if is_missing(v) else float(v) for v in values]  # type: ignore[arg-type]
    return numpy_pairwise_sum(floats)


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
