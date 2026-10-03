"""Threshold, MAD and IQR outlier rules on sorted copies (deterministic)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ._buffers import cents_input, to_buffer
from ._engine import accelerate, jitable, prange

#: Iglewicz/Hoaglin constant: 0.6745 ≈ Φ⁻¹(0.75), makes the MAD comparable to σ.
MAD_CONSTANT = 0.6745


@dataclass(frozen=True)
class OutlierResult:
    """Outlier mask with the centre, spread and bounds that produced it."""

    mask: npt.NDArray[np.bool_]
    center: float
    spread: float
    lower: float
    upper: float


@accelerate(parallel=True)
def threshold_kernel(
    amounts: npt.NDArray[np.int64], threshold: int, absolute: bool, out: npt.NDArray[np.bool_]
) -> None:
    """Element-wise ``amount > threshold`` (or ``|amount| > threshold``)."""
    for i in prange(amounts.shape[0]):
        value = abs(amounts[i]) if absolute else amounts[i]
        out[i] = value > threshold


def exceeds_threshold(
    amounts_cents: object, threshold_cents: int, *, absolute: bool = False
) -> npt.NDArray[np.bool_]:
    """Rows above a fixed threshold in cents (the threshold is the caller's input)."""
    amounts = cents_input(amounts_cents, "Betrag")
    limit = int(cents_input([threshold_cents], "Schwelle")[0])
    out = np.zeros(amounts.shape, dtype=np.bool_)
    threshold_kernel(amounts, limit, absolute, out)
    return out


@jitable
def quantile_sorted(ordered: npt.NDArray[np.float64], probability: float) -> float:
    """Linear interpolation between order statistics (Hyndman/Fan type 7)."""
    position = (ordered.shape[0] - 1) * probability
    lower = int(math.floor(position))
    upper = min(lower + 1, ordered.shape[0] - 1)
    return float(ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower]))


@accelerate(parallel=True)
def band_kernel(
    values: npt.NDArray[np.float64], lower: float, upper: float, out: npt.NDArray[np.bool_]
) -> None:
    """Element-wise ``value < lower or value > upper``."""
    for i in prange(values.shape[0]):
        out[i] = values[i] < lower or values[i] > upper


@accelerate
def median_deviation_kernel(values: npt.NDArray[np.float64], center: float) -> float:
    """Median of ``|value − center|`` on a sorted copy."""
    deviations = np.empty(values.shape[0], dtype=np.float64)
    for i in range(values.shape[0]):
        deviations[i] = abs(values[i] - center)
    return quantile_sorted(np.sort(deviations), 0.5)


def _sample(values: object, factor: float) -> npt.NDArray[np.float64]:
    data = to_buffer(values, np.float64)
    if data.size == 0:
        raise ValueError("Keine Werte.")
    if not bool(np.isfinite(data).all()):
        raise ValueError("Nur endliche Werte (NaN mit to_buffer(..., nulls='mask') ausfiltern).")
    if not (math.isfinite(factor) and factor > 0):
        raise ValueError("Der Faktor muss positiv sein.")
    return data


def _band(
    data: npt.NDArray[np.float64], center: float, spread: float, low: float, high: float
) -> OutlierResult:
    mask = np.zeros(data.shape, dtype=np.bool_)
    band_kernel(data, low, high, mask)
    return OutlierResult(mask, center, spread, low, high)


def mad_outliers(values: object, factor: float) -> OutlierResult:
    """Robust MAD rule (modified z-score of Iglewicz/Hoaglin).

    Flags values outside ``median ± factor · MAD / 0.6745``, i.e. a modified
    z-score ``0.6745·|x − median| / MAD`` above ``factor``. The factor is the
    caller's choice (Iglewicz/Hoaglin recommend 3.5). When the MAD is 0 every
    value different from the median is flagged.
    """
    data = _sample(values, factor)
    center = float(quantile_sorted(np.sort(data), 0.5))
    spread = float(median_deviation_kernel(data, center))
    reach = factor * spread / MAD_CONSTANT
    return _band(data, center, spread, center - reach, center + reach)


def iqr_outliers(values: object, factor: float) -> OutlierResult:
    """Tukey fences: outside ``[Q1 − factor·IQR, Q3 + factor·IQR]`` (quantiles type 7).

    The factor is the caller's choice (Tukey: 1.5 for outliers, 3 for far out).
    """
    data = _sample(values, factor)
    ordered = np.sort(data)
    first = float(quantile_sorted(ordered, 0.25))
    third = float(quantile_sorted(ordered, 0.75))
    spread = third - first
    return _band(
        data, (first + third) / 2.0, spread, first - factor * spread, third + factor * spread
    )
