"""Sample size for equal-probability methods: simple random sampling and difference estimation.

Guidance EGESIF_16-0014-01, sections 6.1.1.2 and 6.2.1.2 (standard approach)
and 6.1.2.2 and 6.2.2.2 (stratified): n = (N × z × σ / (TE − AE))², with the
weighted variance σ_w² = Σ N_h/N × σ_h² and the proportional allocation
n_h = N_h/N × n. Difference estimation uses exactly the formulas of simple
random sampling (6.2.1.2). The optional finite population correction is the
exact formula of footnote 25.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from ..sizes import SamplingInputError
from .factors import z_value
from .plan import (
    GuidancePlan,
    StratumAllocation,
    StratumInput,
    Tolerance,
    finite,
    frozen,
    largest_remainder,
    round_up,
    tolerance,
    whole,
)
from .sources import Step, guidance

SRS = "guidance.srs"
DIFFERENCE = "guidance.difference"
#: Section of the sample-size formula per method: (standard, stratified).
SECTIONS = {SRS: ("6.1.1.2", "6.1.2.2"), DIFFERENCE: ("6.2.1.2", "6.2.2.2")}
#: Rule of thumb of the guidance (footnote 37): at least 30 units for statistical sampling.
MINIMUM_STATISTICAL = 30
#: Advisable minimum per stratum to estimate its standard deviation (6.1.2.2).
MINIMUM_PER_STRATUM = 3


@dataclass(frozen=True)
class _Core:
    raw: float
    size: int
    steps: list[Step]
    warnings: list[str]


def _section(method: str, stratified: bool) -> str:
    if method not in SECTIONS:
        raise SamplingInputError(f"Unbekannte Methode '{method}'. Zulässig: {', '.join(SECTIONS)}.")
    return SECTIONS[method][1 if stratified else 0]


def _core(n_units: int, z: float, sd: float, limits: Tolerance, fpc: bool, section: str) -> _Core:
    """n = (N z σ / (TE − AE))², optionally n / (1 + n/N) (footnote 25), capped at N."""
    source = guidance(section)
    raw = (n_units * z * sd / (limits.tolerable_error - limits.anticipated_error)) ** 2
    steps = [Step("Stichprobenumfang", "n = (N × z × σ / (TE − AE))²", raw, source)]
    warnings: list[str] = []
    if fpc:
        raw = raw / (1 + raw / n_units)
        steps.append(
            Step("Endlichkeitskorrektur", "n′ = n / (1 + n / N)", raw, f"{source}, Fußnote 25")
        )
    elif raw > 0.1 * n_units:
        warnings.append(
            "Der Umfang übersteigt 10 % der Grundgesamtheit; die Endlichkeitskorrektur "
            "(Leitfaden, Fußnote 25) kann ihn verringern."
        )
    size = min(round_up(raw), n_units)
    if size == n_units:
        warnings.append("Der Umfang erreicht die Grundgesamtheit: Vollerhebung.")
    return _Core(raw, size, steps, warnings)


def _minimum_warning(size: int) -> list[str]:
    if size >= MINIMUM_STATISTICAL:
        return []
    return [
        f"Umfang unter {MINIMUM_STATISTICAL} Einheiten, der Faustregel des Leitfadens für "
        "statistische Stichproben (Fußnote 37)."
    ]


def equal_probability_size(
    method: str,
    *,
    population_size: int,
    book_value: float,
    error_sd: float,
    confidence_level: float,
    factor_profile: str,
    anticipated_error_rate: float,
    materiality_rate: float = 0.02,
    finite_population_correction: bool = False,
) -> GuidancePlan:
    """Sample size of simple random sampling (6.1.1.2) or difference estimation (6.2.1.2).

    ``error_sd`` is σ_e, the standard deviation of the errors from historical
    data or a pilot sample (:func:`auditcore_sampling.guidance.error_sd`).
    """
    section = _section(method, stratified=False)
    units = whole(population_size, "population_size")
    sd = finite(error_sd, "error_sd", positive=True)
    limits = tolerance(book_value, materiality_rate, anticipated_error_rate)
    z = z_value(confidence_level, factor_profile)
    core = _core(units, z, sd, limits, finite_population_correction, section)
    steps = [Step("z-Wert", "z", z, guidance("5.3")), *limits.steps(), *core.steps]
    inputs = {
        **limits.inputs(),
        "population_size": units,
        "error_sd": sd,
        "confidence_level": confidence_level,
        "factor_profile": factor_profile,
        "z": z,
        "finite_population_correction": finite_population_correction,
    }
    warnings = core.warnings + _minimum_warning(core.size)
    return GuidancePlan(
        method, core.size, core.raw, frozen(inputs), tuple(steps), warnings=tuple(warnings)
    )


def _checked_strata(
    strata: Sequence[StratumInput],
) -> tuple[list[StratumInput], list[StratumInput]]:
    if not strata or len({s.name for s in strata}) != len(strata):
        raise SamplingInputError("Mindestens eine Schicht mit eindeutigem Namen ist erforderlich.")
    for stratum in strata:
        if not stratum.name.strip():
            raise SamplingInputError("Jede Schicht braucht einen Namen.")
        whole(stratum.population_size, f"Schicht '{stratum.name}': population_size")
        if not stratum.exhaustive:
            finite(stratum.sd, f"Schicht '{stratum.name}': sd", positive=True)
    sampled = [s for s in strata if not s.exhaustive]
    if not sampled:
        raise SamplingInputError("Mindestens eine Schicht muss eine Stichprobenschicht sein.")
    return sampled, [s for s in strata if s.exhaustive]


def _allocate(size: int, sampled: list[StratumInput]) -> tuple[list[int], list[str]]:
    sizes = [s.population_size or 0 for s in sampled]
    shares = largest_remainder(size, [float(n) for n in sizes])
    raised = [max(n, min(MINIMUM_PER_STRATUM, cap)) for n, cap in zip(shares, sizes, strict=True)]
    capped = [min(n, cap) for n, cap in zip(raised, sizes, strict=True)]
    warnings = []
    if raised != shares:
        warnings.append(
            f"Mindestens {MINIMUM_PER_STRATUM} Einheiten je Schicht, damit die "
            "Standardabweichung schätzbar ist (Leitfaden, Abschn. 6.1.2.2)."
        )
    return capped, warnings


def _rows(
    sampled: list[StratumInput], shares: list[int], exhaustive: list[StratumInput], units: int
) -> list[StratumAllocation]:
    rows = [
        StratumAllocation(
            s.name, n, False, s.population_size, s.book_value, (s.population_size or 0) / units
        )
        for s, n in zip(sampled, shares, strict=True)
    ]
    return rows + [
        StratumAllocation(s.name, s.population_size or 0, True, s.population_size, s.book_value)
        for s in exhaustive
    ]


def stratified_equal_probability_size(
    method: str,
    *,
    strata: Sequence[StratumInput],
    book_value: float,
    confidence_level: float,
    factor_profile: str,
    anticipated_error_rate: float,
    materiality_rate: float = 0.02,
    finite_population_correction: bool = False,
) -> GuidancePlan:
    """Stratified simple random sampling (6.1.2.2) or difference estimation (6.2.2.2).

    ``book_value`` is the total expenditure BV including exhaustive strata
    (TE and AE refer to it); N is the number of units outside the exhaustive
    strata. Exhaustive strata are added with n_h = N_h.
    """
    section = _section(method, stratified=True)
    sampled, exhaustive = _checked_strata(strata)
    limits = tolerance(book_value, materiality_rate, anticipated_error_rate)
    z = z_value(confidence_level, factor_profile)
    units = sum(s.population_size or 0 for s in sampled)
    variance = math.fsum((s.population_size or 0) / units * (s.sd or 0.0) ** 2 for s in sampled)
    core = _core(units, z, math.sqrt(variance), limits, finite_population_correction, section)
    shares, allocation_warnings = _allocate(core.size, sampled)
    rows = _rows(sampled, shares, exhaustive, units)
    total = sum(r.sample_size for r in rows)
    steps = [
        Step("z-Wert", "z", z, guidance("5.3")),
        *limits.steps(),
        Step("Gewichtete Varianz", "σ_w² = Σ N_h / N × σ_h²", variance, guidance(section)),
        *core.steps,
        Step(
            "Aufteilung", "n_h = N_h / N × n (größter Rest)", float(sum(shares)), guidance(section)
        ),
        Step("Gesamtumfang", "Σ n_h + Einheiten der Vollerhebung", float(total), guidance(section)),
    ]
    inputs = {
        **limits.inputs(),
        "population_size": units,
        "confidence_level": confidence_level,
        "factor_profile": factor_profile,
        "z": z,
        "weighted_variance": variance,
        "finite_population_correction": finite_population_correction,
    }
    warnings = core.warnings + allocation_warnings + _minimum_warning(sum(shares))
    stratified = f"{method}_stratified"
    return GuidancePlan(
        stratified,
        total,
        core.raw,
        frozen(inputs),
        tuple(steps),
        tuple(rows),
        warnings=tuple(warnings),
    )
