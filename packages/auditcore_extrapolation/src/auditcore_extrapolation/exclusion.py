"""Units excluded under proportional control: extension to the original population.

Guidance section 7.10.2 (Art. 148(1) Regulation (EU) No 1303/2013; for
2021–2027 the single-audit rule of Art. 80 Regulation (EU) 2021/1060): units
may be excluded from the population to be sampled (or replaced after
selection). The audit opinion still concerns the whole declared expenditure,
so the projection of the reduced population is extended per stratum:

* sampling part: EE_s × f_s and SE × f_s with f_s = BV_s,original / BV_s,reduced
  (MUS, ratio estimation, PPS, conservative approach) or
  N_s,original / N_s,reduced (mean-per-unit and difference estimation);
* high-value (exhaustive) part: EE_e × BV_e,original / BV_e,reduced, for
  mean-per-unit estimation N_e,original / N_e,reduced (7.10.2 tables,
  examples 7.10.3.1 b, 7.10.3.2–7.10.3.4).

For mean-per-unit estimation the result equals the direct projection with
the original N (footnotes 69/70); for ratio estimation the precision must be
computed for the reduced population and then extended (7.10.2 c). The
stratified MUS precision is recomputed with the extended book values of the
sampling parts; other stratified precisions with exclusions in more than one
sampling stratum are not described in the guidance and are rejected.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace
from types import MappingProxyType

from .design import Stratum
from .errors import ExtrapolationInputError
from .mus import mus_precision
from .projection import Projection, StratumResult
from .sources import Step, guidance

#: Methods whose projection is based on the number of units (N ratio).
COUNT_BASED = frozenset({"srs.mean_per_unit", "difference", "nonstatistical.mean_per_unit"})


def extension_factor(original: float, reduced: float) -> float:
    """f = original / reduced (book values or numbers of units, guidance section 7.10.2)."""
    if (
        not math.isfinite(original)
        or not math.isfinite(reduced)
        or reduced <= 0
        or original < reduced
    ):
        raise ExtrapolationInputError(
            "Die ursprüngliche Grundgesamtheit muss mindestens so groß sein wie die "
            "reduzierte (> 0)."
        )
    return original / reduced


def _factors(stratum: Stratum, by_count: bool) -> tuple[float, float]:
    label = f"Schicht '{stratum.name}'"
    sampling = 1.0
    if stratum.excluded_book_value or stratum.excluded_units:
        if not stratum.units:
            raise ExtrapolationInputError(
                f"{label}: Ausschluss in der Stichprobenschicht ohne Stichprobe "
                "(Leitfaden, Abschn. 7.10.2)."
            )
        if by_count:
            size = stratum.sampling_population_size or 0
            sampling = extension_factor(size + stratum.excluded_units, size)
        else:
            book = stratum.sampling_book_value
            sampling = extension_factor(book + stratum.excluded_book_value, book)
    exhaustive = 1.0
    if stratum.excluded_exhaustive_book_value or stratum.excluded_exhaustive_units:
        if by_count:
            count = len(stratum.exhaustive_units)
            exhaustive = extension_factor(count + stratum.excluded_exhaustive_units, count)
        else:
            book = stratum.exhaustive_book_value
            exhaustive = extension_factor(book + stratum.excluded_exhaustive_book_value, book)
    return sampling, exhaustive


def _extended(result: StratumResult, sampling: float, exhaustive: float) -> StratumResult:
    random_part = result.projected_error - result.exhaustive_error
    figures = dict(result.figures) | {
        "extension_factor": sampling,
        "exhaustive_extension_factor": exhaustive,
    }
    return replace(
        result,
        projected_error=random_part * sampling + result.exhaustive_error * exhaustive,
        exhaustive_error=result.exhaustive_error * exhaustive,
        figures=MappingProxyType(figures),
    )


def _precision(
    method: str,
    projection: Projection,
    strata: Sequence[Stratum],
    factors: list[tuple[float, float]],
) -> float | None:
    if projection.precision is None:
        return None
    sampled = [
        (s, r, f)
        for s, r, (f, _) in zip(strata, projection.strata, factors, strict=True)
        if s.units
    ]
    if method == "mus.standard" and projection.coefficient is not None:
        return mus_precision(
            projection.coefficient,
            [
                (r.sampling_book_value * f, r.sample_size, r.figures.get("sd_rates", 0.0))
                for _, r, f in sampled
            ],
        )
    extended = [f for _, _, f in sampled if f != 1.0]
    if len(sampled) > 1 and extended:
        raise ExtrapolationInputError(
            "Ausschluss nach Abschn. 7.10 bei mehreren Stichprobenschichten beschreibt der "
            "Leitfaden nur für den MUS-Standardansatz; die Schichten bitte getrennt auswerten."
        )
    return projection.precision * (extended[0] if extended else 1.0)


def extend_to_original(
    method: str, strata: Sequence[Stratum], projection: Projection
) -> Projection:
    """Projection and precision of the original population (guidance section 7.10.2)."""
    by_count = method in COUNT_BASED
    factors = [_factors(s, by_count) for s in strata]
    results = tuple(
        _extended(r, f, e) for r, (f, e) in zip(projection.strata, factors, strict=True)
    )
    precision = _precision(method, projection, strata, factors)
    basis = "N_original / N_reduziert" if by_count else "BV_original / BV_reduziert"
    steps = [
        Step(
            f"Ausweitung auf die ursprüngliche Grundgesamtheit, Schicht {s.name}",
            f"EE_s × f (f = {basis})",
            f,
            guidance("7.10.2"),
        )
        for s, (f, _) in zip(strata, factors, strict=True)
        if f != 1.0
    ] + [
        Step(f"Ausweitung der Hochwertschicht {s.name}", f"EE_e × ({basis})", e, guidance("7.10.2"))
        for s, (_, e) in zip(strata, factors, strict=True)
        if e != 1.0
    ]
    projected = math.fsum(r.projected_error for r in results)
    steps.append(
        Step(
            "Hochgerechneter Fehler (ursprüngliche Grundgesamtheit)",
            "Σ EE_h",
            projected,
            guidance("7.10.2"),
        )
    )
    if precision is not None:
        steps.append(
            Step(
                "Präzision (ursprüngliche Grundgesamtheit)", "SE × f", precision, guidance("7.10.2")
            )
        )
    return replace(
        projection,
        projected_random_error=projected,
        precision=precision,
        strata=results,
        steps=projection.steps + tuple(steps),
    )
