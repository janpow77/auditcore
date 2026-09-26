"""Summation orders with documented floating-point behavior.

``neumaier_sum`` is the algorithm of CPython's builtin ``sum()`` for floats
since Python 3.12 (Neumaier-compensated). krypto requires Python ≥ 3.12, so
its ``sum(window) / n`` start values are Neumaier sums; implementing the
algorithm here keeps legacy replays independent of the interpreter version
(Python 3.11 would sum without compensation).

The NumPy pairwise order (``ndarray.mean()`` before the division) is
``auditcore_common.numeric.numpy_pairwise_sum``.

Window statistics (SMA, rolling standard deviation …) use ``math.fsum`` —
correctly rounded and therefore independent of the summation order of any
data-frame library version.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def neumaier_sum(values: Sequence[float]) -> float:
    """CPython ≥ 3.12 ``sum()`` over floats (Neumaier compensation)."""
    if not values:
        return 0.0
    total = 0.0 + values[0]
    compensation = 0.0
    for value in values[1:]:
        t = total + value
        if abs(total) >= abs(value):
            compensation += (total - t) + value
        else:
            compensation += (value - t) + total
        total = t
    if compensation and math.isfinite(compensation):
        total += compensation
    return total


def window_mean(values: Sequence[float]) -> float:
    """Correctly rounded arithmetic mean of a non-empty window."""
    return math.fsum(values) / len(values)


def window_std(values: Sequence[float]) -> float:
    """Sample standard deviation (ddof = 1), two-pass with ``math.fsum``."""
    mean = window_mean(values)
    return math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1))
