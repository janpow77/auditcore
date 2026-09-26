"""Named projection methods and the single entry point :func:`project`.

Every method is chosen explicitly by its id; stratification follows from the
number of sampled strata. Statistical methods need a confidence level and a
factor profile, non-statistical methods have no precision (section 6.4.5).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType

from . import conservative, equal_probability, mus
from .design import Stratum, check_strata
from .errors import ExtrapolationInputError
from .factors import basic_reliability_factor, profile, z_value
from .projection import (
    Projection,
    StratumResult,
    anomaly_warnings,
    error_classes,
    systemic_population,
)
from .sources import Step, cpr, guidance


@dataclass(frozen=True)
class Method:
    """A projection method of the guidance."""

    id: str
    label: str
    statistical: bool
    selection: str
    stratification: bool
    source: str
    formula: str

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible description."""
        return {
            "id": self.id,
            "label": self.label,
            "statistical": self.statistical,
            "selection": self.selection,
            "stratification": self.stratification,
            "source": self.source,
            "formula": self.formula,
            "needs_population_size": self.selection == "equal_probability" or not self.statistical,
            "needs_sample_size": self.id == "mus.conservative",
        }


_EQ, _PPS = "equal_probability", "pps"
METHODS = MappingProxyType(
    {
        m.id: m
        for m in (
            Method(
                "srs.mean_per_unit",
                "Einfache Zufallsstichprobe – Mittelwertschätzung",
                True,
                _EQ,
                True,
                guidance("6.1.1, 6.1.2"),
                "EE = Σ N_h × ΣE_h / n_h",
            ),
            Method(
                "srs.ratio",
                "Einfache Zufallsstichprobe – Verhältnisschätzung",
                True,
                _EQ,
                True,
                guidance("6.1.1, 6.1.2; Anhang 1, 2.3"),
                "EE = Σ BV′_h × ΣE_h / ΣBV′_h",
            ),
            Method(
                "difference",
                "Differenzenschätzung",
                True,
                _EQ,
                True,
                guidance("6.2.1, 6.2.2; Anhang 1, 3"),
                "EE = Σ N_h × ΣE_h / n_h, CBV = BV − TER",
            ),
            Method(
                "mus.standard",
                "MUS – Standardansatz",
                True,
                _PPS,
                True,
                guidance("6.3.1, 6.3.2; Anhang 1, 4.1"),
                "EE = EE_e + Σ BV_hs / n_hs × ΣE/BV",
            ),
            Method(
                "mus.ratio",
                "MUS – Verhältnisschätzung bei systemischen Fehlern",
                True,
                _PPS,
                False,
                guidance("Anhang 1, 4.2"),
                "EE_s = BV′_s × Σ(E/BV) / Σ(BV′/BV)",
            ),
            Method(
                "mus.conservative",
                "MUS – konservativer Ansatz",
                True,
                _PPS,
                False,
                guidance("6.3.5"),
                "SE = SI × RF + Σ (RF(i) − RF(i−1) − 1) × SI × E/BV",
            ),
            Method(
                "nonstatistical.mean_per_unit",
                "Nicht-statistisch, gleiche Wahrscheinlichkeit – Mittelwertschätzung",
                False,
                _EQ,
                True,
                guidance("6.4.5.1, 6.4.5.2"),
                "EE = Σ N_h × ΣE_h / n_h",
            ),
            Method(
                "nonstatistical.ratio",
                "Nicht-statistisch, gleiche Wahrscheinlichkeit – Verhältnisschätzung",
                False,
                _EQ,
                True,
                guidance("6.4.5.1, 6.4.5.2"),
                "EE = Σ BV_h × ΣE_h / ΣBV_h",
            ),
            Method(
                "nonstatistical.pps",
                "Nicht-statistisch, wertproportionale Auswahl",
                False,
                _PPS,
                True,
                guidance("6.4.5.3, 6.4.5.4"),
                "EE = EE_e + Σ BV_hs / n_hs × ΣE/BV",
            ),
        )
    }
)
NON_STATISTICAL_MAX_UNITS = 300
NON_STATISTICAL_MIN_COVERAGE = 0.10


def method(method_id: str) -> Method:
    """The explicitly named method."""
    found = METHODS.get(method_id)
    if found is None:
        raise ExtrapolationInputError(
            f"Unbekannte Methode '{method_id}'. Zulässig: {', '.join(METHODS)}."
        )
    return found


def _coverage(strata: Sequence[Stratum]) -> tuple[dict[str, object], list[str]]:
    population = sum(s.population_size or 0 for s in strata)
    audited = sum(len(s.units) + len(s.exhaustive_units) for s in strata)
    share = audited / population if population else 0.0
    warnings = []
    if population >= NON_STATISTICAL_MAX_UNITS:
        warnings.append(
            f"Grundgesamtheit mit {population} Einheiten: nicht-statistische Verfahren nur unter "
            f"{NON_STATISTICAL_MAX_UNITS} Einheiten ({cpr('79 Abs. 2')})."
        )
    if share < NON_STATISTICAL_MIN_COVERAGE:
        warnings.append(
            f"Abdeckung {share:.1%} der Einheiten liegt unter 10 % ({cpr('79 Abs. 2')})."
        )
    return {"population_units": population, "audited_units": audited, "coverage": share}, warnings


def _estimator_extra(strata: Sequence[Stratum], chosen: str) -> tuple[dict[str, object], list[str]]:
    units = [u for s in strata for u in s.units]
    try:
        check = equal_probability.estimator_check(
            [u.random_error for u in units], [u.book_value for u in units]
        )
    except ExtrapolationInputError as exc:
        return {}, [f"Schätzerwahl nicht prüfbar: {exc}"]
    warnings = []
    if check.recommended != chosen:
        warnings.append(
            "Nach der Kovarianzregel (Leitfaden, Abschn. 6.1.1.3) wäre "
            f"'{check.recommended}' vorzuziehen."
        )
    return {"estimator_check": check.to_dict()}, warnings


@dataclass(frozen=True)
class _Outcome:
    strata: tuple[StratumResult, ...]
    projected: float
    precision: float | None
    steps: list[Step]
    warnings: list[str]
    extra: dict[str, object]


def _run_statistical_mus(
    chosen: Method, strata: tuple[Stratum, ...], level: float, profile_id: str, sample_size: int
) -> _Outcome:
    if chosen.id == "mus.conservative":
        res, ee, se, steps, warns, rows = conservative.project_conservative(
            strata, sample_size, level, profile_id
        )
        return _Outcome(res, ee, se, steps, warns, {"allowances": [r.to_dict() for r in rows]})
    res, ee, se_ratio, steps = mus.project_ratio(strata, z_value(level, profile_id))
    return _Outcome(res, ee, se_ratio, steps, [], {})


def _run(
    chosen: Method,
    strata: tuple[Stratum, ...],
    level: float | None,
    profile_id: str | None,
    sample_size: int | None,
) -> _Outcome:
    statistical = chosen.statistical and level is not None and profile_id is not None
    z = z_value(level, profile_id) if statistical and level is not None and profile_id else None
    kind = chosen.id.split(".")[-1]
    if chosen.id in ("mus.conservative", "mus.ratio") and level is not None and profile_id:
        return _run_statistical_mus(chosen, strata, level, profile_id, sample_size or 0)
    if chosen.selection == "pps":
        res, ee, se_mus, steps = mus.project_standard(strata, z)
        return _Outcome(res, ee, se_mus, steps, [], {})
    estimator = equal_probability.RATIO if kind == "ratio" else equal_probability.MEAN_PER_UNIT
    res, ee, se_eq, steps, warns = equal_probability.project(strata, estimator, z)
    extra: dict[str, object] = {}
    if chosen.id in ("srs.mean_per_unit", "srs.ratio"):
        extra, more = _estimator_extra(strata, estimator)
        warns += more
    return _Outcome(res, ee, se_eq, steps, warns, extra)


def _check_parameters(chosen: Method, level: float | None, profile_id: str | None) -> None:
    if chosen.statistical and (level is None or profile_id is None):
        raise ExtrapolationInputError(
            "Statistische Verfahren brauchen Konfidenzniveau und Faktorprofil."
        )
    if profile_id is not None:
        profile(profile_id)


def project(
    method_id: str,
    strata: Sequence[Stratum],
    *,
    confidence_level: float | None = None,
    factor_profile: str | None = None,
    sample_size: int | None = None,
) -> Projection:
    """Project the random errors of an audited sample to the population.

    Raises:
        ExtrapolationInputError: unknown method or profile, invalid strata or
            units, missing confidence level for a statistical method.
    """
    chosen = method(method_id)
    _check_parameters(chosen, confidence_level, factor_profile)
    needs_n = chosen.selection == "equal_probability" or not chosen.statistical
    checked = check_strata(strata, needs_population_size=needs_n)
    if not chosen.stratification and sum(1 for s in checked if s.units) > 1:
        raise ExtrapolationInputError(f"'{chosen.label}' lässt keine Schichtung zu.")
    outcome = _run(chosen, checked, confidence_level, factor_profile, sample_size)
    warnings = list(anomaly_warnings(checked)) + outcome.warnings
    extra = dict(outcome.extra)
    if not chosen.statistical:
        coverage, more = _coverage(checked)
        extra["coverage"] = coverage
        warnings += more
    statistical = chosen.statistical
    return Projection(
        method=chosen.id,
        projected_random_error=outcome.projected,
        precision=outcome.precision,
        confidence_level=confidence_level if statistical else None,
        factor_profile=factor_profile if statistical else None,
        coefficient=_coefficient(chosen, confidence_level, factor_profile),
        strata=outcome.strata,
        error_classes=error_classes(checked),
        systemic_population=systemic_population(checked),
        steps=tuple(outcome.steps),
        warnings=tuple(warnings),
        extra=MappingProxyType(extra),
    )


def _coefficient(chosen: Method, level: float | None, profile_id: str | None) -> float | None:
    if not chosen.statistical or level is None or profile_id is None:
        return None
    if chosen.id == "mus.conservative":
        return basic_reliability_factor(level, profile_id)
    return z_value(level, profile_id)
