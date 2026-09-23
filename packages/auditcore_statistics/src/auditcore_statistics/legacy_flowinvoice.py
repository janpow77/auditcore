"""Exact legacy variant of flowinvoice ``BenfordsLawAnalyzer.analyze`` (fraud detection).

Method profile ``flowinvoice.fraud_benford`` (flowinvoice@fb2d185,
``backend/app/services/fraud_detection/benfords_law.py``). It differs from
:func:`auditcore_statistics.benford_test` and is kept separate:

* expected shares rounded to three decimals (0.301 … 0.046), not ``log10(1+1/d)``;
* first digit by repeated ``*10``/``/10`` on ``float``; zero, ``None``, NaN and
  non-numeric text are dropped silently, numeric text is accepted;
* no test below 50 digits (``p = 1.0``, not anomalous);
* decision ``χ² > 15.507`` (fixed critical value, α = 0.05, df = 8) while the
  reported p-value is a step function; ``significance_level`` is only echoed;
* per-digit z-test without continuity correction, ``z > 2.576``;
* χ², p and observed shares rounded to four decimals.

The only deliberate deviation: ``±inf`` raises ``ValueError`` — the source loops
forever. Results are the source's own statements, not a validated method.
"""

from __future__ import annotations

import math
from collections import Counter
from decimal import Decimal
from typing import Any

PROFILE = "flowinvoice.fraud_benford"
EXPECTED: dict[int, float] = {
    1: 0.301,
    2: 0.176,
    3: 0.125,
    4: 0.097,
    5: 0.079,
    6: 0.067,
    7: 0.058,
    8: 0.051,
    9: 0.046,
}
CHI_SQUARE_CRITICAL = 15.507
MIN_SAMPLE_SIZE = 50
Z_LIMIT = 2.576
P_STEPS = ((10.0, 0.8), (13.36, 0.15), (15.51, 0.08), (20.09, 0.03), (26.12, 0.005))
P_FLOOR = 0.001


def _first_digit(value: Any) -> int | None:
    try:
        number = abs(float(value))
    except (ValueError, TypeError):
        return None
    if math.isinf(number):
        raise ValueError("Unendliche Beträge sind nicht auswertbar (Quelle: Endlosschleife).")
    if number == 0 or math.isnan(number):
        return None
    while number < 1:
        number *= 10
    while number >= 10:
        number /= 10
    return int(number)


def _p_value(chi_square: float) -> float:
    for limit, p in P_STEPS:
        if chi_square < limit:
            return p
    return P_FLOOR


def legacy_flowinvoice_benford(
    amounts: list[Decimal | float | int | str | None], significance_level: float = 0.05
) -> dict[str, Any]:
    """Result fields of the source ``BenfordResult`` as a dictionary (same values)."""
    digits = [d for d in (_first_digit(a) for a in amounts) if d]
    size = len(digits)
    counts = Counter(digits)
    base = {
        "profile": PROFILE,
        "critical_value": CHI_SQUARE_CRITICAL,
        "expected_distribution": dict(EXPECTED),
        "sample_size": size,
        "degrees_of_freedom": 8,
    }
    if size < MIN_SAMPLE_SIZE:
        return {
            **base,
            "is_anomalous": False,
            "chi_square_statistic": 0.0,
            "p_value": 1.0,
            "observed_distribution": (
                {d: counts.get(d, 0) / size for d in range(1, 10)} if size > 0 else {}
            ),
            "anomalous_digits": [],
            "interpretation": (
                f"HINWEIS: Stichprobe zu klein ({size} von "
                f"mindestens {MIN_SAMPLE_SIZE} erforderlichen Datenpunkten). "
                f"Die statistische Aussagekraft ist erheblich eingeschraenkt. "
                f"Der Chi-Quadrat-Test wurde nicht durchgefuehrt."
            ),
            "significance_level": 0.05,
            "null_hypothesis_rejected": False,
            "sample_size_sufficient": False,
        }
    observed = {d: counts.get(d, 0) / size for d in range(1, 10)}
    chi_square = 0.0
    anomalous: list[int] = []
    for digit in range(1, 10):
        expected_count = EXPECTED[digit] * size
        if expected_count > 0:
            chi_square += (counts.get(digit, 0) - expected_count) ** 2 / expected_count
        expected_p = EXPECTED[digit]
        variance = expected_p * (1 - expected_p) / size
        if variance > 0 and abs(observed[digit] - expected_p) / math.sqrt(variance) > Z_LIMIT:
            anomalous.append(digit)
    p_value = _p_value(chi_square)
    is_anomalous = chi_square > CHI_SQUARE_CRITICAL
    head = (
        f"Chi-Quadrat-Statistik: χ²={chi_square:.2f} "
        f"(kritischer Wert bei α=0,05: {CHI_SQUARE_CRITICAL:.2f}, "
        f"df=8). p-Wert: {p_value:.4f}. "
    )
    if is_anomalous:
        interpretation = (
            "WARNUNG: Signifikante Abweichung von Benford's Law. "
            + head
            + "Die Nullhypothese (Verteilung entspricht Benford) wird verworfen. "
            + f"Auffaellige Ziffern: [{', '.join(str(d) for d in anomalous)}]. "
            + "Dies kann auf Datenmanipulation hindeuten."
        )
    else:
        interpretation = (
            "Verteilung entspricht Benford's Law. "
            + head
            + "Die Nullhypothese wird nicht verworfen. "
            + "Keine Auffaelligkeiten erkannt."
        )
    return {
        **base,
        "is_anomalous": is_anomalous,
        "chi_square_statistic": round(chi_square, 4),
        "p_value": round(p_value, 4),
        "observed_distribution": {k: round(v, 4) for k, v in observed.items()},
        "anomalous_digits": anomalous,
        "interpretation": interpretation,
        "significance_level": significance_level,
        "null_hypothesis_rejected": is_anomalous,
        "sample_size_sufficient": True,
    }


#: Recommended method for the flowinvoice fraud check (user decision K10,
#: 23.09.2026, "alle empfehlungen"): the standard :func:`benford_test` with
#: exact expected shares, exact chi-square p-value and an explicit α of 0.05.
RECOMMENDED_PROFILE = "flowinvoice.fraud_benford.recommended"
RECOMMENDED_PARAMETERS: dict[str, Any] = {"digits": 1, "significance_level": 0.05}


def recommended_flowinvoice_benford(values: list[Any]) -> Any:
    """``benford_test`` with the decided parameters (replaces the legacy variant)."""
    from .benford import benford_test

    return benford_test(values, **RECOMMENDED_PARAMETERS)
