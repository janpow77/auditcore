"""Monetary unit sampling (MUS), standard approach, also stratified.

Formulas of the guidance, sections 6.3.1.4/6.3.1.5 (standard approach),
6.3.2.4/6.3.2.5 (stratified MUS) and Appendix 1 section 4 (systemic errors:
4.1 standard approach, 4.2 ratio estimation). The projection of the
exhaustive (high-value) part is the sum of its errors and carries no sampling
error. The same projection serves non-statistical samples selected with
probability proportional to size (section 6.4.5.3/6.4.5.4), then without
precision.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from types import MappingProxyType

from .design import Stratum
from .errors import ExtrapolationInputError
from .projection import StratumResult, exhaustive_random_error
from .sources import Step, guidance
from .units import sample_sd


def tainting_projection(interval: float, tainting_sum: float) -> float:
    """EE_s = SI × Σ E_i / BV_i with SI = BV_s / n_s (section 6.3.1.4)."""
    return interval * tainting_sum


def mus_precision(z: float, strata: Sequence[tuple[float, int, float]]) -> float:
    """SE = z × √(Σ BV_hs² / n_hs × s_rh²) (section 6.3.2.5; H = 1: 6.3.1.5).

    ``strata`` holds (BV_hs, n_hs, s_rh) of the sampling parts.
    """
    return z * math.sqrt(math.fsum(book**2 / size * sd**2 for book, size, sd in strata))


def _part(
    stratum: Stratum, statistical: bool
) -> tuple[StratumResult, tuple[float, int, float] | None]:
    exhaustive = exhaustive_random_error(stratum)
    units = stratum.units
    if not units:
        return StratumResult(stratum.name, exhaustive, exhaustive, 0, 0.0), None
    book = stratum.sampling_book_value
    interval = book / len(units)
    rates = [u.random_rate for u in units]
    projected = tainting_projection(interval, math.fsum(rates))
    figures = {"interval": interval, "tainting_sum": math.fsum(rates)}
    spread = None
    if statistical:
        sd = sample_sd(rates)
        figures["sd_rates"] = sd
        spread = (book, len(units), sd)
    result = StratumResult(
        stratum.name,
        projected + exhaustive,
        exhaustive,
        len(units),
        book,
        MappingProxyType(figures),
    )
    return result, spread


def project_standard(
    strata: Sequence[Stratum], z: float | None
) -> tuple[tuple[StratumResult, ...], float, float | None, list[Step]]:
    """MUS standard approach over all strata; ``z`` None = non-statistical PPS."""
    parts = [_part(s, z is not None) for s in strata]
    results = tuple(r for r, _ in parts)
    stratified = sum(1 for r in results if r.sample_size) > 1
    section = "6.3.2.4" if stratified else "6.3.1.4"
    steps = [
        Step(
            f"Hochgerechneter Fehler Schicht {r.name}",
            "EE_e + BV_s / n_s × Σ E_i / BV_i",
            r.projected_error,
            guidance(section),
        )
        for r in results
    ]
    projected = math.fsum(r.projected_error for r in results)
    if z is None:
        return results, projected, None, steps
    spreads = [s for _, s in parts if s is not None]
    se = mus_precision(z, spreads)
    steps.append(Step("z-Wert", "z", z, guidance("5.3")))
    steps.append(
        Step(
            "Präzision",
            "SE = z × √(Σ BV_hs² / n_hs × s_rh²)",
            se,
            guidance("6.3.2.5" if stratified else "6.3.1.5"),
        )
    )
    return results, projected, se, steps


def ratio_components(
    errors: Sequence[float], books: Sequence[float], adjusted: Sequence[float]
) -> tuple[float, list[float]]:
    """Rate Σ(E_i/BV_i) / Σ(BV′_i/BV_i) and transformed rates q′_i/BV_i (Appendix 1, 4.2)."""
    rate = math.fsum(e / b for e, b in zip(errors, books, strict=True)) / math.fsum(
        a / b for a, b in zip(adjusted, books, strict=True)
    )
    transformed = [(e - rate * a) / b for e, a, b in zip(errors, adjusted, books, strict=True)]
    return rate, transformed


def project_ratio(
    strata: Sequence[Stratum], z: float
) -> tuple[tuple[StratumResult, ...], float, float, list[Step]]:
    """MUS ratio estimation in the presence of systemic errors (Appendix 1, 4.2).

    Defined in the guidance for one sampling stratum only.
    """
    sampled = [s for s in strata if s.units]
    if len(sampled) != 1:
        raise ExtrapolationInputError(
            "Die MUS-Verhältnisschätzung (Leitfaden, Anhang 1, 4.2) ist nur für eine "
            "Stichprobenschicht definiert."
        )
    stratum = sampled[0]
    units = stratum.units
    books = [u.book_value for u in units]
    adjusted = [u.book_value - u.systemic_error for u in units]
    rate, transformed = ratio_components([u.random_error for u in units], books, adjusted)
    adjusted_total = stratum.sampling_book_value - stratum.systemic_error
    projected_s = adjusted_total * rate
    sd = sample_sd(transformed)
    se = z * stratum.sampling_book_value / math.sqrt(len(units)) * sd
    source = guidance("Anhang 1, 4.2")
    results = []
    for s in strata:
        exhaustive = exhaustive_random_error(s)
        own = projected_s if s is stratum else 0.0
        figures = (
            {"book_value_adjusted": adjusted_total, "rate": rate, "sd_rates": sd} if own else {}
        )
        results.append(
            StratumResult(
                s.name,
                own + exhaustive,
                exhaustive,
                len(s.units),
                s.sampling_book_value,
                MappingProxyType(figures),
            )
        )
    steps = [
        Step("Fehlerquote (Verhältnis)", "Σ(E_i/BV_i) / Σ(BV′_i/BV_i)", rate, source),
        Step(
            "Hochgerechneter Fehler Stichprobenschicht", "EE_s = BV′_s × Quote", projected_s, source
        ),
        Step("z-Wert", "z", z, guidance("5.3")),
        Step("Präzision", "SE = z × BV_s / √n_s × s_rq", se, source),
    ]
    total = math.fsum(r.projected_error for r in results)
    return tuple(results), total, se, steps
