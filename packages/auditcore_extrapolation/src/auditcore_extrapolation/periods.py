"""Sampling in several periods of the reference year (two-period and multi-period).

The year population is split into sub-populations, one per period (typically
two semesters); independent samples are drawn and evaluated per period with
the chosen method, possibly stratified (guidance sections 6.1.3, 6.2.3,
6.3.3, 6.3.4, 6.4.9 and 7.3; three and four periods: Appendix 2). The
projections add up and, the samples being independent, so do the variances:

* EE = Σ_t EE_t (6.1.3.3, 6.2.3.3, 6.3.3.4, 6.3.4.4, 6.4.9)
* SE = √(Σ_t SE_t²), e.g. z × √(Σ_t N_t² s_t² / n_t) for simple random
  sampling (6.1.3.4, 6.2.3.4) and z × √(Σ_t Σ_h BV_hts² / n_hts × s_rhts²)
  for MUS (6.3.3.5, 6.3.4.5).

The guidance describes no multi-period form of the MUS conservative approach
and of the MUS ratio estimation (Appendix 1, 4.2); both are rejected. The
evaluation (TER, upper limit, conclusion, corrected book value) is the usual
one over the book value of all periods.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType

from .design import Stratum
from .errors import ExtrapolationInputError
from .evaluation import MATERIALITY_RATE, Assessment, evaluate
from .methods import SINGLE_PERIOD_ONLY, Method, method, non_statistical_coverage, project_strata
from .projection import Projection, error_classes, systemic_population
from .sources import Step, guidance


@dataclass(frozen=True)
class Period:
    """One period of the reference year with its own strata and sample."""

    name: str
    strata: tuple[Stratum, ...]

    @property
    def book_value(self) -> float:
        """BV_t: declared expenditure of the period (all strata)."""
        return math.fsum(s.book_value for s in self.strata)


#: Methods without a multi-period form in the guidance.
NO_PERIODS = MappingProxyType(
    {
        "mus.conservative": "Der Leitfaden beschreibt den konservativen MUS-Ansatz nur für einen "
        "Zeitraum (Abschn. 6.3.5).",
        "mus.ratio": "Die MUS-Verhältnisschätzung ist nur für eine Stichprobenschicht eines "
        "Zeitraums definiert (Leitfaden, Anhang 1, 4.2).",
    }
)
_SOURCES = MappingProxyType(
    {
        "srs.mean_per_unit": ("6.1.3.3", "6.1.3.4"),
        "srs.ratio": ("6.1.3.3", "6.1.3.4"),
        "difference": ("6.2.3.3", "6.2.3.4"),
        "mus.standard": ("6.3.3.4, 6.3.4.4", "6.3.3.5, 6.3.4.5"),
    }
)


def _check_periods(chosen: Method, periods: Sequence[Period]) -> tuple[Period, ...]:
    if chosen.id in SINGLE_PERIOD_ONLY:
        raise ExtrapolationInputError(NO_PERIODS[chosen.id])
    checked = tuple(periods)
    if len(checked) < 2:
        raise ExtrapolationInputError(
            "Eine Stichprobe über mehrere Zeiträume braucht mindestens zwei Zeiträume "
            "(Leitfaden, Abschn. 7.3); für einen Zeitraum die einfache Hochrechnung verwenden."
        )
    names = [p.name.strip() for p in checked]
    if not all(names):
        raise ExtrapolationInputError("Jeder Zeitraum braucht einen Namen.")
    if len(set(names)) != len(names):
        raise ExtrapolationInputError("Die Namen der Zeiträume müssen eindeutig sein.")
    return checked


def _sources(chosen: Method) -> tuple[str, str]:
    if not chosen.statistical:
        return "6.4.9", "6.4.9"
    return _SOURCES[chosen.id]


def _prefixed(period: str, items: Sequence[Step]) -> list[Step]:
    return [replace(step, label=f"{period}: {step.label}") for step in items]


def _summary(period: Period, projection: Projection) -> dict[str, object]:
    return {
        "name": period.name,
        "book_value": period.book_value,
        "projected_random_error": projection.projected_random_error,
        "precision": projection.precision,
        "sample_size": sum(s.sample_size for s in projection.strata),
        "extra": dict(projection.extra),
    }


def combined_precision(precisions: Sequence[float]) -> float:
    """SE = √(Σ_t SE_t²) of independent period samples (sections 6.1.3.4, 6.3.3.5; Appendix 2)."""
    if not precisions or any(not math.isfinite(v) or v < 0 for v in precisions):
        raise ExtrapolationInputError("Präzisionen müssen endliche Zahlen ≥ 0 sein.")
    return math.sqrt(math.fsum(v * v for v in precisions))


def _combined_precision(parts: Sequence[Projection]) -> float | None:
    values = [p.precision for p in parts]
    if any(v is None for v in values):
        return None
    return combined_precision([v for v in values if v is not None])


def project_periods(
    method_id: str,
    periods: Sequence[Period],
    *,
    confidence_level: float | None = None,
    factor_profile: str | None = None,
    population_units: int | None = None,
) -> Projection:
    """Project a sample drawn in several periods (guidance sections 6.1.3–6.4.9, 7.3).

    Each period is projected with ``method_id`` over its own strata; EE is
    the sum and SE the root of the summed squared precisions (Appendix 2).
    ``population_units`` is the number of distinct units of the year for the
    coverage check of non-statistical samples (section 6.4.9), since the
    same operation may be active in several periods.

    Raises:
        ExtrapolationInputError: fewer than two periods, duplicate names, a
            method without multi-period form or invalid strata of a period.
    """
    chosen = method(method_id)
    checked = _check_periods(chosen, periods)
    parts = []
    for period in checked:
        try:
            parts.append(
                project_strata(
                    chosen, period.strata, confidence_level, factor_profile, None, coverage=False
                )
            )
        except ExtrapolationInputError as exc:
            raise ExtrapolationInputError(f"Zeitraum '{period.name}': {exc}") from exc
    return _combine(chosen, checked, parts, population_units)


def _combine(
    chosen: Method,
    periods: tuple[Period, ...],
    parts: list[Projection],
    population_units: int | None,
) -> Projection:
    projected = math.fsum(p.projected_random_error for p in parts)
    se = _combined_precision(parts)
    ee_source, se_source = _sources(chosen)
    steps = [
        s for period, p in zip(periods, parts, strict=True) for s in _prefixed(period.name, p.steps)
    ]
    steps.append(
        Step(
            "Hochgerechneter Fehler aller Zeiträume",
            "EE = Σ_t EE_t",
            projected,
            guidance(ee_source),
        )
    )
    if se is not None:
        steps.append(
            Step(
                "Präzision aller Zeiträume",
                "SE = √(Σ_t SE_t²)",
                se,
                guidance(f"{se_source}; Anhang 2"),
            )
        )
    warnings = [
        f"{period.name}: {w}" for period, p in zip(periods, parts, strict=True) for w in p.warnings
    ]
    extra: dict[str, object] = {
        "periods": [_summary(period, p) for period, p in zip(periods, parts, strict=True)]
    }
    all_strata = [s for period in periods for s in period.strata]
    if not chosen.statistical:
        coverage, more = non_statistical_coverage(all_strata, population_units)
        extra["coverage"] = coverage
        warnings += more
    first = parts[0]
    return Projection(
        method=chosen.id,
        projected_random_error=projected,
        precision=se,
        confidence_level=first.confidence_level,
        factor_profile=first.factor_profile,
        coefficient=first.coefficient,
        strata=tuple(
            replace(result, period=period.name)
            for period, p in zip(periods, parts, strict=True)
            for result in p.strata
        ),
        error_classes=error_classes(all_strata),
        systemic_population=systemic_population(all_strata),
        steps=tuple(steps),
        warnings=tuple(warnings),
        extra=MappingProxyType(extra),
    )


def assess_periods(
    method_id: str,
    periods: Sequence[Period],
    *,
    confidence_level: float | None = None,
    factor_profile: str | None = None,
    population_units: int | None = None,
    materiality_rate: float = MATERIALITY_RATE,
) -> Assessment:
    """:func:`project_periods` and the evaluation over BV = Σ_t BV_t (sections 6.1.3.5, 6.3.3.6)."""
    projection = project_periods(
        method_id,
        periods,
        confidence_level=confidence_level,
        factor_profile=factor_profile,
        population_units=population_units,
    )
    book_value = math.fsum(p.book_value for p in periods)
    return Assessment(projection, evaluate(projection, book_value, materiality_rate))
