"""NumPy fallbacks for validated, bounded element-wise inputs.

Money stays in int64 throughout. The public API bounds amounts to ±10**12
cents and rate components to 10**6, so all intermediate products fit.
Reductions deliberately retain the original sequential reference order.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
import numpy.typing as npt

Ints: TypeAlias = npt.NDArray[np.int64]
Bools: TypeAlias = npt.NDArray[np.bool_]
Statuses: TypeAlias = npt.NDArray[np.int8]


def share(amounts: Ints, numerators: Ints, denominators: Ints, out: Ints) -> None:
    """Round exact rational shares half away from zero, including negative cents."""
    product = amounts * numerators
    magnitude = (2 * np.abs(product) + denominators) // (2 * denominators)
    out[:] = np.where(product < 0, -magnitude, magnitude)


def quota(parts: Ints, totals: Ints, bounds: Ints, basis_points: Ints, status: Statuses) -> None:
    """Exact quota comparisons; rounded basis points are display values only."""
    valid = totals > 0
    divisor = np.where(valid, totals, 1)
    product = parts * 10000
    magnitude = (2 * np.abs(product) + divisor) // (2 * divisor)
    basis_points[:] = np.where(valid, np.where(product < 0, -magnitude, magnitude), 0)
    status[:] = 0
    if bounds[3] == 1:
        status[parts * bounds[5] > totals * bounds[4]] = 2
    if bounds[0] == 1:
        status[parts * bounds[2] < totals * bounds[1]] = 1
    status[~valid] = 3


def reconcile(
    expected: Ints,
    actual: Ints,
    missing: Bools,
    tolerance: int,
    difference: Ints,
    status: Statuses,
) -> None:
    """Target/actual difference with the same missing-value and tolerance codes."""
    np.subtract(actual, expected, out=difference)
    status[:] = np.where(difference == 0, 0, np.where(np.abs(difference) <= tolerance, 1, 2))
    difference[missing] = 0
    status[missing] = 3


def threshold(amounts: Ints, threshold: int, absolute: bool, out: Bools) -> None:
    """Threshold mask without Python scalar iteration."""
    np.greater(np.abs(amounts) if absolute else amounts, threshold, out=out)


def band(values: npt.NDArray[np.float64], lower: float, upper: float, out: Bools) -> None:
    """Outside-band mask without changing floating point arithmetic."""
    np.logical_or(values < lower, values > upper, out=out)
