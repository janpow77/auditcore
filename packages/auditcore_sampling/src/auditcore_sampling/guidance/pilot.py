"""Standard deviations for the size formulas from a pilot or previous-period sample.

σ_e (errors, guidance 6.1.1.2) and σ_r (error rates of a MUS sample,
6.3.1.2) are sample standard deviations with divisor n − 1 (MS Excel
``STDEV.S``). For MUS, units above the cut-off BV/n contribute E_i / (BV/n)
instead of E_i / BV_i (footnote 27; worked example 6.3.1.7).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from ..sizes import SamplingInputError
from .plan import finite, whole


def _sample_sd(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise SamplingInputError("Für eine Standardabweichung sind mindestens 2 Werte nötig.")
    mean = math.fsum(values) / len(values)
    return math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1))


def _amount(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SamplingInputError("Fehlerbeträge müssen endliche Zahlen sein.")
    return float(value)


def error_sd(errors: Sequence[float]) -> float:
    """σ_e = √(Σ (E_i − Ē)² / (n_p − 1)) of the pilot errors (guidance 6.1.1.2)."""
    return _sample_sd([_amount(e) for e in errors])


def error_rates(
    errors: Sequence[float],
    book_values: Sequence[float],
    *,
    population_book_value: float,
    pilot_sample_size: int,
) -> list[float]:
    """r_i = E_i / BV_i, above the cut-off BV/n: E_i / (BV/n) (guidance 6.3.1.2, footnote 27).

    ``population_book_value`` and ``pilot_sample_size`` are BV and n of the
    population the pilot (or previous-period) sample was drawn from.
    """
    if len(errors) != len(book_values):
        raise SamplingInputError("Fehler und Buchwerte müssen gleich viele Einträge haben.")
    cut_off = finite(population_book_value, "population_book_value", positive=True) / whole(
        pilot_sample_size, "pilot_sample_size"
    )
    rates = []
    for error, book in zip(errors, book_values, strict=True):
        value = finite(book, "book_values", positive=True)
        rates.append(_amount(error) / (cut_off if value > cut_off else value))
    return rates


def error_rate_sd(
    errors: Sequence[float],
    book_values: Sequence[float],
    *,
    population_book_value: float,
    pilot_sample_size: int,
) -> float:
    """σ_r of the error rates of a MUS pilot sample (guidance 6.3.1.2, 6.3.2.2)."""
    return _sample_sd(
        error_rates(
            errors,
            book_values,
            population_book_value=population_book_value,
            pilot_sample_size=pilot_sample_size,
        )
    )
