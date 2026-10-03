"""Deterministic summation and weighted moments on float64 buffers.

Every reduction runs strictly sequentially in input order with Neumaier
compensation, in the compiled and the Python path alike, so results are
bit-identical across runs, thread counts and engines. Floating point is used
only for statistics, never for money (see ``auditcore_compute.finance``).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import numpy.typing as npt

from ._buffers import to_buffer
from ._engine import accelerate, jitable

VarianceKind = Literal["population", "frequency", "reliability"]
_KINDS = ("population", "frequency", "reliability")


@jitable
def _compensated_sum(values: npt.NDArray[np.float64]) -> float:
    """Neumaier's compensated sum, strictly in input order."""
    total = 0.0
    compensation = 0.0
    for i in range(values.shape[0]):
        value = values[i]
        candidate = total + value
        if abs(total) >= abs(value):
            compensation += (total - candidate) + value
        else:
            compensation += (value - candidate) + total
        total = candidate
    return total + compensation


@accelerate
def sum_kernel(values: npt.NDArray[np.float64]) -> float:
    """Sequential compensated sum of a float64 buffer."""
    return _compensated_sum(values)


@accelerate
def moments_kernel(
    values: npt.NDArray[np.float64],
    weights: npt.NDArray[np.float64],
    out: npt.NDArray[np.float64],
) -> None:
    """Weight sum, weighted mean, Σ w·(x−mean)² and Σ w² (two passes, sequential)."""
    count = values.shape[0]
    products = np.empty(count, dtype=np.float64)
    squares = np.empty(count, dtype=np.float64)
    for i in range(count):
        products[i] = weights[i] * values[i]
        squares[i] = weights[i] * weights[i]
    weight_sum = _compensated_sum(weights)
    out[0] = weight_sum
    if not weight_sum > 0:
        return
    mean = _compensated_sum(products) / weight_sum
    for i in range(count):
        deviation = values[i] - mean
        products[i] = weights[i] * deviation * deviation
    out[1] = mean
    out[2] = _compensated_sum(products)
    out[3] = _compensated_sum(squares)


def _finite(values: object, label: str) -> npt.NDArray[np.float64]:
    array = to_buffer(values, np.float64)
    if not bool(np.isfinite(array).all()):
        raise ValueError(f"{label}: nur endliche Werte (kein inf).")
    return array


def deterministic_sum(values: object) -> float:
    """Compensated sum in input order; NaN raises (use ``to_buffer(..., nulls="mask")``)."""
    return float(sum_kernel(_finite(values, "Werte")))


def _moments(values: object, weights: object | None) -> npt.NDArray[np.float64]:
    data = _finite(values, "Werte")
    if data.size == 0:
        raise ValueError("Keine Werte.")
    if weights is None:
        weight = np.ones(data.shape, dtype=np.float64)
    else:
        weight = _finite(weights, "Gewichte")
        if weight.shape != data.shape:
            raise ValueError("Werte und Gewichte müssen gleich lang sein.")
        if bool((weight < 0).any()):
            raise ValueError("Gewichte dürfen nicht negativ sein.")
    out = np.zeros(4, dtype=np.float64)
    moments_kernel(data, weight, out)
    if not out[0] > 0:
        raise ValueError("Die Summe der Gewichte muss positiv sein.")
    return out


def weighted_mean(values: object, weights: object | None = None) -> float:
    """Σ w·x / Σ w with compensated sums (unweighted when ``weights`` is None)."""
    return float(_moments(values, weights)[1])


def weighted_variance(
    values: object, weights: object | None = None, *, kind: VarianceKind = "population"
) -> float:
    """Weighted variance around the weighted mean.

    ``population`` divides by Σw, ``frequency`` by Σw − 1 (weights are counts,
    the sample variance for unit weights), ``reliability`` by Σw − Σw²/Σw.
    """
    if kind not in _KINDS:
        raise ValueError(f"Unbekannte Varianzart {kind!r}; erlaubt: {list(_KINDS)}")
    weight_sum, _mean, squared, square_weights = (float(v) for v in _moments(values, weights))
    if kind == "population":
        divisor = weight_sum
    elif kind == "frequency":
        divisor = weight_sum - 1.0
    else:
        divisor = weight_sum - square_weights / weight_sum
    if not divisor > 0:
        raise ValueError("Zu wenige Beobachtungen für diese Varianzart.")
    return squared / divisor


def weighted_std(
    values: object, weights: object | None = None, *, kind: VarianceKind = "population"
) -> float:
    """Square root of ``weighted_variance``."""
    return float(np.sqrt(weighted_variance(values, weights, kind=kind)))
