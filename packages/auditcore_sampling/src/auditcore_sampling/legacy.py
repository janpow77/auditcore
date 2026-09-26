"""Behavior-compatible adapters for ``flowstat@d665ac2`` and ``audit-portal@d8eefa4``.

They reproduce the characterized results of the source functions exactly,
including silently defaulted confidence levels, the flowstat MUS formula and
NumPy/pandas float semantics. Random numbers are not drawn here: the caller
passes the start value its NumPy generator produced, so a consumer keeps its
own random behavior and the deterministic parts are shared.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from auditcore_common.numeric import numpy_round

from ._numeric import pandas_sum
from .selection import stratified_allocation, systematic_mus
from .sizes import MUS_POISSON, SRS_FLOWSTAT, SRS_PORTAL

_FLOWSTAT_Z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}


def _divide(numerator: float, denominator: float, numpy_scalars: bool) -> float:
    """Python raises on division by zero; NumPy float64 yields inf/nan."""
    if denominator == 0 and numpy_scalars:
        if numerator == 0 or math.isnan(numerator):
            return math.nan
        return math.copysign(math.inf, numerator) * math.copysign(1.0, denominator)
    return numerator / denominator


def flowstat_mus_size(
    population_value: float,
    materiality: float,
    expected_error_rate: float,
    confidence_level: float,
    *,
    numpy_scalars: bool = False,
) -> tuple[int, float]:
    """``flowstat._calculate_mus_sample_size``; ``numpy_scalars`` for pandas sums."""
    z = _FLOWSTAT_Z.get(confidence_level, 1.96)
    _divide(materiality, population_value, numpy_scalars)  # source computes, never uses
    numerator = population_value * (z**2) * (1 - expected_error_rate)
    denominator = (materiality**2) + (z**2) * (1 - expected_error_rate)
    size = int(math.ceil(_divide(numerator, denominator, numpy_scalars)))
    interval = population_value / size if size > 0 else 0
    return size, interval


def portal_mus_size_legacy(
    population_value: float,
    materiality: float,
    expected_error_rate: float,
    confidence_level: float,
) -> tuple[int, float]:
    """``audit-portal._calculate_mus_sample_size_legacy`` (deprecated there)."""
    z = _FLOWSTAT_Z.get(confidence_level, 1.96)
    numerator = population_value * (z**2) * (1 - expected_error_rate)
    denominator = (materiality**2) + (z**2) * (1 - expected_error_rate)
    size = int(math.ceil(numerator / denominator))
    interval = population_value / size if size > 0 else 0
    return size, interval


def portal_mus_size(
    population_value: float,
    materiality: float,
    expected_error_rate: float,
    confidence_level: float,
) -> tuple[int, float]:
    """``audit-portal._calculate_mus_sample_size`` (Poisson reliability factors)."""
    if materiality <= 0:
        raise ValueError("Materiality muss > 0 sein")
    if population_value <= 0:
        return 0, 0.0
    if expected_error_rate < 0 or expected_error_rate >= 1:
        raise ValueError("expected_error_rate muss in [0, 1) liegen")
    factors = dict(MUS_POISSON.factors)
    rf = factors.get(confidence_level)
    if rf is None:
        raise ValueError(
            f"Konfidenzniveau {confidence_level} nicht unterstützt; erlaubt: {sorted(factors)}"
        )
    precision = max(materiality - population_value * expected_error_rate, materiality * 0.5)
    size = int(math.ceil(rf * population_value / precision))
    interval = population_value / size if size > 0 else 0.0
    return size, interval


def _srs(population_size: int, z: float, margin_of_error: float, proportion: float) -> int:
    n = (z**2) * proportion * (1 - proportion) / (margin_of_error**2)
    adjusted = n / (1 + (n - 1) / population_size)
    return int(math.ceil(adjusted))


def flowstat_srs_size(
    population_size: int,
    confidence_level: float,
    margin_of_error: float,
    expected_proportion: float = 0.5,
) -> int:
    """``flowstat._calculate_srs_sample_size`` (unknown levels silently 1.96)."""
    z = dict(SRS_FLOWSTAT.factors).get(confidence_level, 1.96)
    return _srs(population_size, z, margin_of_error, expected_proportion)


def portal_srs_size(
    population_size: int,
    confidence_level: float,
    margin_of_error: float,
    expected_proportion: float = 0.5,
) -> int:
    """``audit-portal._calculate_srs_sample_size`` (larger table, default 1.96)."""
    z = dict(SRS_PORTAL.factors).get(confidence_level, 1.96)
    return _srs(population_size, z, margin_of_error, expected_proportion)


def _round2(value: float | int, numpy_value: bool) -> float | int:
    if isinstance(value, int) and not isinstance(value, bool):
        return round(value, 2)
    return numpy_round(value, 2) if numpy_value else round(value, 2)


_TEMPLATES = {"run_mus_standard": "MUS Standard", "run_mus_conservative": "MUS Conservative"}


def flowstat_mus(
    values: Sequence[float | int | None],
    *,
    template: str,
    materiality: float,
    confidence_level: float,
    expected_error_rate: float,
    start: float | None,
) -> tuple[dict[str, Any], list[int]]:
    """Summary row and selected positions of ``run_mus_standard/conservative``.

    ``values`` are the ``pd.to_numeric(..., errors="coerce")`` values; ``start``
    is what ``np.random.uniform(0, interval)`` returned (``None`` if interval 0).
    """
    population_value = pandas_sum(values)
    size, interval = flowstat_mus_size(
        population_value, materiality, expected_error_rate, confidence_level, numpy_scalars=True
    )
    begin = start if (interval > 0 and start is not None) else 0.0
    selection = systematic_mus(
        values, sample_size=max(size, 0), interval=float(interval), start=begin, variant="flowstat"
    )
    summary = {
        "Template": _TEMPLATES[template],
        "Grundgesamtheit_Anzahl": len(values),
        "Grundgesamtheit_Wert": _round2(population_value, True),
        "Wesentlichkeit": round(materiality, 2),
        "Konfidenzniveau": confidence_level,
        "Erwartete_Fehlerrate": expected_error_rate,
        "Stichprobenumfang": size,
        "Auswahlintervall": _round2(interval, isinstance(interval, float) and size > 0),
        "Ausgewählte_Anzahl": len(selection.positions),
    }
    return summary, list(selection.positions)


def portal_mus(
    values: Sequence[float | int | None],
    *,
    template: str,
    materiality: float,
    confidence_level: float,
    expected_error_rate: float,
    start: float | None,
) -> tuple[dict[str, Any], list[int], list[int], list[int]]:
    """``audit-portal`` run_mus_standard/conservative: summary, positions, negatives, zero/NaN."""
    positive = [
        v
        for v in values
        if v is not None and not (isinstance(v, float) and math.isnan(v)) and v > 0
    ]
    population_value = float(pandas_sum(positive))
    size, interval = portal_mus_size(
        population_value, materiality, expected_error_rate, confidence_level
    )
    begin = start if (interval > 0 and start is not None) else 0.0
    selection = systematic_mus(
        values, sample_size=size, interval=float(interval), start=begin, variant="portal"
    )
    summary = {
        "Template": _TEMPLATES[template],
        "Grundgesamtheit_Anzahl": len(positive),
        "Grundgesamtheit_Wert": round(population_value, 2),
        "Wesentlichkeit": round(materiality, 2),
        "Konfidenzniveau": confidence_level,
        "Erwartete_Fehlerrate": expected_error_rate,
        "Stichprobenumfang": size,
        "Auswahlintervall": round(interval, 2),
        "Ausgewählte_Anzahl": len(selection.positions),
    }
    return (
        summary,
        list(selection.positions),
        list(selection.excluded_negative),
        list(selection.excluded_zero_or_missing),
    )


def flowstat_mus_stratified(
    values: Sequence[float | int | None],
    strata: Sequence[Any],
    *,
    materiality: float,
    confidence_level: float,
    expected_error_rate: float,
    starts: Sequence[float | None],
) -> tuple[list[dict[str, Any]], list[int], float | int]:
    """``run_mus_stratified``: per-stratum rows, positions (global) and total value.

    ``strata`` gives the stratum key per value; groups follow sorted key order
    (pandas ``groupby``); missing keys are dropped like pandas does.
    """
    total = pandas_sum(values)
    keys = sorted(
        {k for k in strata if k is not None and not (isinstance(k, float) and math.isnan(k))}
    )
    if len(starts) != len(keys):
        raise ValueError("Für jede Schicht ist genau ein Startwert anzugeben.")
    rows: list[dict[str, object]] = []
    selected: list[int] = []
    for key, start in zip(keys, starts, strict=True):
        members = [i for i, k in enumerate(strata) if k == key]
        row, local = _flowstat_stratum(
            key,
            [values[i] for i in members],
            total,
            start,
            materiality=materiality,
            confidence_level=confidence_level,
            expected_error_rate=expected_error_rate,
        )
        selected.extend(members[i] for i in local)
        rows.append(row)
    return rows, selected, total


def _flowstat_stratum(
    key: object,
    group: list[float | int | None],
    total: float | int,
    start: float | None,
    *,
    materiality: float,
    confidence_level: float,
    expected_error_rate: float,
) -> tuple[dict[str, object], tuple[int, ...]]:
    """One stratum of ``run_mus_stratified``: summary row and group-local positions."""
    stratum_value = pandas_sum(group)
    share = _divide(stratum_value, total, True)
    stratum_materiality = materiality * share
    size, interval = flowstat_mus_size(
        stratum_value,
        stratum_materiality,
        expected_error_rate,
        confidence_level,
        numpy_scalars=True,
    )
    begin = start if (interval > 0 and start is not None) else 0.0
    local = systematic_mus(
        group,
        sample_size=max(size, 0),
        interval=float(interval),
        start=begin,
        variant="flowstat",
    ).positions
    row: dict[str, object] = {
        "Stratum": str(key),
        "Anzahl": len(group),
        "Wert": _round2(stratum_value, True),
        "Anteil_Prozent": _round2(share * 100, True),
        "Stichprobenumfang": size,
        "Ausgewählte": len(local),
    }
    return row, local


def flowstat_srs_stratified_sizes(
    strata: Sequence[Any],
    *,
    confidence_level: float,
    margin_of_error: float,
    allocation_method: str,
) -> list[dict[str, Any]]:
    """Per-stratum rows of ``run_srs_stratified`` (the random draw stays with NumPy)."""
    population = len(strata)
    total = flowstat_srs_size(population, confidence_level, margin_of_error)
    keys = sorted({k for k in strata if k is not None})
    sizes = {k: sum(1 for s in strata if s == k) for k in keys}
    method = "proportional" if allocation_method == "proportional" else "equal"
    allocation = stratified_allocation(total, sizes, method)
    return [
        {
            "Stratum": str(k),
            "Anzahl": sizes[k],
            "Anteil_Prozent": round(sizes[k] / population * 100, 2),
            "Stichprobenumfang": allocation[k],
            "Ausgewählte": allocation[k],
        }
        for k in keys
    ]
