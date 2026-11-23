"""Legacy adapter: ``flowstat@d665ac2`` ``analysis_core_service.run_benford``.

Reproduces the source exactly, including the behavior that
:func:`auditcore_statistics.benford_test` corrects (see
``docs/behavior-changes.md``).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Literal

from .numeric import chi2_survival, numpy_pairwise_sum, numpy_round

LEGACY_METHOD = "flowstat.run_benford@d665ac221f50ba1f465b7337bdd4aa218d78ec8a"

LegacyDtype = Literal["int", "float", "bool"]
_TOLERANCE = 1e-8


def _legacy_text(value: int | float | bool, dtype: LegacyDtype) -> str:
    if dtype == "bool":
        return str(bool(value))
    if dtype == "int":
        return str(int(value))
    return repr(float(value))


def _legacy_positive(values: Sequence[int | float | bool | None]) -> list[int | float]:
    """Absolute values above zero; ``None`` and NaN are dropped like ``dropna``."""
    positive = []
    for value in values:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        absolute = abs(value)
        if absolute > 0:
            positive.append(absolute)
    if not positive:
        raise ValueError("Keine positiven Werte in der Spalte gefunden.")
    return positive


def _legacy_leading(positive: list[int | float], dtype: LegacyDtype, digit: object) -> list[int]:
    """Leading digit (group) from the source's string form; 0 for a short value."""
    leading: list[int] = []
    for value in positive:
        text = _legacy_text(value, dtype).replace(".", "").lstrip("0")
        if digit == 1:
            leading.append(int(text[0]))
        else:
            leading.append(int(text[:2]) if len(text) >= 2 else 0)
    return leading


def _legacy_row(d: int, count: int, total: int) -> tuple[dict[str, object], float]:
    """Table row of one digit and its expected count (pandas/NumPy rounding paths)."""
    expected_percent = math.log10(1 + 1 / d) * 100
    if count:
        observed_percent = count / total * 100
        observed_rounded = numpy_round(observed_percent, 2)
        deviation = numpy_round(observed_percent - expected_percent, 2)
    else:
        observed_percent = 0 / total * 100
        observed_rounded = round(observed_percent, 2)
        deviation = round(observed_percent - expected_percent, 2)
    row = {
        "digit": str(d),
        "observed_count": count,
        "observed_percent": observed_rounded,
        "expected_percent": round(expected_percent, 2),
        "deviation": deviation,
    }
    return row, (expected_percent / 100) * total


def _legacy_check_sums(observed: list[float], expected: list[float]) -> None:
    """SciPy 1.11 ``chisquare`` frequency-sum check with its original message."""
    observed_sum = numpy_pairwise_sum(observed)
    expected_sum = numpy_pairwise_sum(expected)
    relative = abs(observed_sum - expected_sum) / min(observed_sum, expected_sum)
    if relative > _TOLERANCE:
        raise ValueError(
            "For each axis slice, the sum of the observed frequencies must agree with the "
            f"sum of the expected frequencies to a relative tolerance of {_TOLERANCE}, but the "
            "percent differences are:"
            f"\n{relative!r}"
        )


def legacy_run_benford(
    values: Sequence[int | float | bool | None],
    *,
    dtype: LegacyDtype,
    digit: object,
    column: str,
) -> dict[str, Any]:
    """Exact ``run_benford`` result for values already coerced by ``pd.to_numeric``.

    ``dtype`` is the pandas dtype family of the coerced column (``int64``,
    ``float64`` or ``bool``); it determines the string form the source uses
    for digit extraction. Column/parameter checks stay with the caller.

    Raises:
        ValueError: with the source application's messages, including the
            chi-square frequency-sum error of SciPy 1.11.
    """
    if digit not in [1, 2]:
        raise ValueError("Parameter 'digit' muss 1 oder 2 sein.")
    leading = _legacy_leading(_legacy_positive(values), dtype, digit)
    domain = range(1, 10) if digit == 1 else range(10, 100)
    total = len(leading)
    counts: dict[int, int] = {}
    for d in leading:
        counts[d] = counts.get(d, 0) + 1
    rows: list[dict[str, object]] = []
    observed: list[float] = []
    expected: list[float] = []
    for d in domain:
        count = counts.get(d, 0)
        row, expected_count = _legacy_row(d, count, total)
        rows.append(row)
        observed.append(float(count))
        expected.append(expected_count)
    _legacy_check_sums(observed, expected)
    statistic = numpy_pairwise_sum(
        [(o - e) ** 2 / e for o, e in zip(observed, expected, strict=True)]
    )
    p_value = chi2_survival(statistic, len(observed) - 1)
    return {
        "type": "table",
        "columns": ["digit", "observed_count", "observed_percent", "expected_percent", "deviation"],
        "rows": rows,
        "meta": {
            "analysis": "core_benford",
            "column": column,
            "digit": digit,
            "chi2_statistic": numpy_round(statistic, 4),
            "p_value": numpy_round(p_value, 4),
            "significant": p_value < 0.05,
            "sample_size": total,
        },
    }
