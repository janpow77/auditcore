"""Equal-probability projection: mean-per-unit, ratio and difference estimation.

Formulas of the guidance, sections 6.1.1 (simple random sampling), 6.1.2
(stratified), 6.2 (difference estimation) and Appendix 1 sections 2 and 3
(systemic errors). The same projections serve non-statistical samples with
equal probability selection (section 6.4.5.1/6.4.5.2), then without precision.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType

from .design import Stratum
from .errors import ExtrapolationInputError
from .projection import StratumResult, exhaustive_random_error
from .sources import DELVO, Step, guidance
from .units import sample_covariance, sample_sd, sample_variance

MEAN_PER_UNIT = "mean_per_unit"
RATIO = "ratio"


def mean_per_unit_error(population_size: float, error_total: float, sample_size: int) -> float:
    """EE₁ = N × ΣE_i / n (section 6.1.1.3, also 6.2.1.3 and 6.4.5.1)."""
    return population_size * error_total / sample_size


def ratio_error(book_value: float, error_total: float, sample_book_value: float) -> float:
    """EE₂ = BV × ΣE_i / ΣBV_i (section 6.1.1.3; Appendix 1, 2.3 with BV′)."""
    return book_value * error_total / sample_book_value


def ratio_q_values(errors: Sequence[float], book_values: Sequence[float]) -> list[float]:
    """q_i = E_i − (ΣE / ΣBV) × BV_i (section 6.1.1.4)."""
    rate = math.fsum(errors) / math.fsum(book_values)
    return [e - rate * b for e, b in zip(errors, book_values, strict=True)]


def precision(population_size: float, z: float, sd: float, sample_size: int) -> float:
    """SE = N × z × s / √n (sections 6.1.1.4 and 6.2.1.4)."""
    return population_size * z * sd / math.sqrt(sample_size)


def stratified_precision(z: float, strata: Sequence[tuple[float, float, int]]) -> float:
    """SE = N × z × s_w / √n with s_w² = Σ N_h/N × s_h² (sections 6.1.2.4, 6.2.2.4).

    ``strata`` holds (N_h, s_h, n_h) of the sampling strata; N = ΣN_h, n = Σn_h.
    The formula of Annex II of Delegated Regulation (EU) 2023/67 and of the
    guidance; it equals :func:`general_stratified_precision` only under
    proportional allocation n_h = n × N_h / N.
    """
    total = math.fsum(n for n, _, _ in strata)
    size = sum(n for _, _, n in strata)
    weighted = math.fsum(n / total * sd**2 for n, sd, _ in strata)
    return total * z * math.sqrt(weighted) / math.sqrt(size)


def general_stratified_precision(z: float, strata: Sequence[tuple[float, float, int]]) -> float:
    """SE = z × √(Σ N_h² × s_h² / n_h) for any allocation (no finite population correction).

    Variance of the stratified estimator Σ N_h × ē_h (Cochran 1977, *Sampling
    Techniques*, eq. 5.6, without the factor 1 − n_h/N_h, as the unstratified
    formula of section 6.1.1.4). With n_h = n × N_h / N it reduces to
    :func:`stratified_precision`.
    """
    return z * math.sqrt(math.fsum(size**2 * sd**2 / n for size, sd, n in strata))


def is_proportional(strata: Sequence[tuple[float, float, int]]) -> bool:
    """True if every n_h is within one unit of n × N_h / N (allocation up to rounding).

    The allocation assumed by the stratified formula of Annex II of Delegated
    Regulation (EU) 2023/67 and guidance section 6.1.2.4.
    """
    total = math.fsum(size for size, _, _ in strata)
    sample = sum(n for _, _, n in strata)
    return all(abs(n - sample * size / total) < 1 for size, _, n in strata)


def _precision_step(
    z: float, sampled: Sequence[tuple[float, float, int]]
) -> tuple[float, Step, list[str]]:
    """Precision with the Annex II formula, or the general one if allocation is not proportional."""
    if len(sampled) == 1 or is_proportional(sampled):
        se = stratified_precision(z, sampled)
        section = "6.1.1.4" if len(sampled) == 1 else "6.1.2.4"
        return se, Step("Präzision", "SE = N × z × s_w / √n", se, guidance(section)), []
    se = general_stratified_precision(z, sampled)
    annex = stratified_precision(z, sampled)
    warning = (
        "Aufteilung der Stichprobe auf die Schichten nicht proportional (n_h ≠ n × N_h / N): "
        "Die Präzision ist mit der allgemeinen Formel z × √(Σ N_h² × s_h² / n_h) berechnet "
        f"({_euro(se)}); die Formel N × z × s_w / √n aus Anhang II der {DELVO} und dem "
        f"Leitfaden (Abschn. 6.1.2.4) setzt proportionale Aufteilung voraus und ergäbe "
        f"{_euro(annex)}."
    )
    step = Step(
        "Präzision (nicht proportionale Aufteilung)",
        "SE = z × √(Σ N_h² × s_h² / n_h)",
        se,
        guidance("6.1.2.4"),
    )
    return se, step, [warning]


def _euro(amount: float) -> str:
    """German amount notation, whole euros."""
    return f"{amount:,.0f} €".replace(",", ".")


@dataclass(frozen=True)
class EstimatorCheck:
    """Rule of section 6.1.1.3: ratio estimation if COV(E,BV)/VAR(BV) > ER/2."""

    covariance_ratio: float
    half_error_rate: float
    recommended: str

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible check."""
        return {
            "covariance_ratio": self.covariance_ratio,
            "half_error_rate": self.half_error_rate,
            "recommended": self.recommended,
        }


def estimator_check(errors: Sequence[float], book_values: Sequence[float]) -> EstimatorCheck:
    """Recommend mean-per-unit or ratio estimation from the sample (section 6.1.1.3)."""
    variance = sample_variance(book_values)
    if variance == 0:
        raise ExtrapolationInputError("Alle Buchwerte gleich: Kovarianzregel nicht anwendbar.")
    ratio = sample_covariance(errors, book_values) / variance
    half = math.fsum(errors) / math.fsum(book_values) / 2
    return EstimatorCheck(ratio, half, RATIO if ratio > half else MEAN_PER_UNIT)


@dataclass(frozen=True)
class _Part:
    result: StratumResult
    population: int
    sd: float | None


def _stratum(stratum: Stratum, estimator: str, statistical: bool) -> _Part:
    units = stratum.units
    errors = [u.random_error for u in units]
    exhaustive = exhaustive_random_error(stratum)
    n_s = stratum.sampling_population_size or 0
    if not units:
        result = StratumResult(stratum.name, exhaustive, exhaustive, 0, 0.0)
        return _Part(result, 0, None)
    figures: dict[str, float] = {"population_size": n_s, "error_total": math.fsum(errors)}
    if estimator == RATIO:
        books = [u.book_value - u.systemic_error for u in units]
        adjusted = stratum.sampling_book_value - stratum.systemic_error
        if math.fsum(books) <= 0:
            raise ExtrapolationInputError(f"Schicht '{stratum.name}': Prüfvolumen ist 0.")
        projected = ratio_error(adjusted, math.fsum(errors), math.fsum(books))
        spread = ratio_q_values(errors, books)
        figures |= {"book_value_adjusted": adjusted, "sample_book_value": math.fsum(books)}
    else:
        projected = mean_per_unit_error(n_s, math.fsum(errors), len(units))
        spread = errors
    sd = sample_sd(spread) if statistical else None
    if sd is not None:
        figures["sd"] = sd
    result = StratumResult(
        stratum.name,
        projected + exhaustive,
        exhaustive,
        len(units),
        stratum.sampling_book_value,
        MappingProxyType(figures),
    )
    return _Part(result, n_s, sd)


def _steps(parts: Sequence[_Part], estimator: str, z: float | None) -> list[Step]:
    section = "6.1.1.3" if len(parts) == 1 else "6.1.2.3"
    formula = "N_h × ΣE / n_h" if estimator == MEAN_PER_UNIT else "BV′_h × ΣE / ΣBV′_i"
    steps = [
        Step(
            f"Hochgerechneter Fehler Schicht {p.result.name}",
            formula,
            p.result.projected_error,
            guidance(section),
        )
        for p in parts
    ]
    if z is not None:
        steps.append(Step("z-Wert", "z", z, guidance("5.3")))
    return steps


def project(
    strata: Sequence[Stratum], estimator: str, z: float | None
) -> tuple[tuple[StratumResult, ...], float, float | None, list[Step], list[str]]:
    """Projected random error and precision over all strata.

    ``z`` None means non-statistical: no precision. Exhaustive units add their
    random errors without sampling error.
    """
    if estimator not in (MEAN_PER_UNIT, RATIO):
        raise ExtrapolationInputError(f"Unbekannter Schätzer '{estimator}'.")
    parts = [_stratum(s, estimator, z is not None) for s in strata]
    warnings: list[str] = []
    projected = math.fsum(p.result.projected_error for p in parts)
    steps = _steps(parts, estimator, z)
    sampled = [
        (float(p.population), p.sd or 0.0, p.result.sample_size) for p in parts if p.sd is not None
    ]
    se = None
    if z is not None:
        se, step, more = _precision_step(z, sampled)
        steps.append(step)
        warnings += more
    return tuple(p.result for p in parts), projected, se, steps, warnings
