"""Minimum sample sizes and the reliability of the precision of statistical samples.

* Art. 5 Abs. 5 of Delegated Regulation (EU) 2023/67: a statistical sample
  contains at least 30 units and every random stratum of a sampling period at
  least three units (guidance EGESIF_16-0014-01, sections 5.1 and 6.1.2.2).
  The formulas of Annex II rest on the normal approximation and therefore on
  this minimum. Below it the result keeps the prescribed z coefficient and
  states as a comparison the precision with Student's t quantile for n − 1
  degrees of freedom (one random stratum only; for several strata the degrees
  of freedom are not unique).
* A precision of 0 without any spread in the sample is no upper limit. For the
  MUS standard approach without errors in a sample with one random stratum
  the precision is the basic precision SI × RF(0) of the conservative
  approach (guidance section 6.3.5.5; the Poisson upper limit for zero
  errors). In all other cases, and for single strata without spread, the
  result states the limitation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType

from ._student_t import t_quantile
from .design import Stratum
from .factors import basic_reliability_factor
from .projection import Projection
from .sources import DELVO, Step, delegated, guidance

MINIMUM_SAMPLE_UNITS = 30
MINIMUM_STRATUM_UNITS = 3
#: Methods whose precision uses the z coefficient (normal approximation).
Z_METHODS = frozenset({"srs.mean_per_unit", "srs.ratio", "difference", "mus.standard", "mus.ratio"})


def _euro(amount: float) -> str:
    return f"{amount:,.0f} €".replace(",", ".")


def _decimal(value: float, places: int) -> str:
    """German decimal comma (2,31; 1,833)."""
    return f"{value:.{places}f}".replace(".", ",")


def stratum_minimum(strata: Sequence[Stratum]) -> list[str]:
    """Warnings for random strata with fewer than three sampled units."""
    return [
        f"Schicht '{s.name}': {len(s.units)} {'Einheit' if len(s.units) == 1 else 'Einheiten'} "
        f"in der Zufallsschicht, mindestens {MINIMUM_STRATUM_UNITS} vorgeschrieben "
        f"(Art. 5 Abs. 5 der {DELVO}; Leitfaden, Abschn. 6.1.2.2)."
        for s in strata
        if 0 < len(s.units) < MINIMUM_STRATUM_UNITS
    ]


def audited_units(strata: Sequence[Stratum]) -> int:
    """Units of the sample: random strata plus units audited at 100 %."""
    return sum(len(s.units) + len(s.exhaustive_units) for s in strata)


def sample_minimum_text(count: int, *, basic_precision: bool = False) -> str:
    """Limitation text for a sample below 30 units.

    ``basic_precision`` True when the precision is the Poisson basic precision
    SI × RF(0) (MUS without errors) rather than a z-based normal approximation.
    """
    basis = (
        "Die Präzision ist die Basispräzision SI × RF(0) und beruht auf dieser kleinen Stichprobe; "
        if basic_precision
        else "Die Präzision beruht auf der Normalverteilung und unterschätzt bei so kleinen "
        "Stichproben die Unsicherheit; "
    )
    return (
        f"Stichprobe mit {count} {'Einheit' if count == 1 else 'Einheiten'} unter dem "
        f"Mindestumfang von {MINIMUM_SAMPLE_UNITS} Einheiten (Art. 5 Abs. 5 der {DELVO}; "
        f"Leitfaden, Abschn. 5.1). {basis}Fehlerobergrenze und Schlussfolgerung sind nur "
        "eingeschränkt belastbar."
    )


@dataclass(frozen=True)
class TComparison:
    """Precision with Student's t for n − 1 degrees of freedom instead of z."""

    degrees_of_freedom: int
    t: float
    z: float
    precision_t: float

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible comparison."""
        return {
            "degrees_of_freedom": self.degrees_of_freedom,
            "t": self.t,
            "z": self.z,
            "precision_t": self.precision_t,
        }


def t_comparison(projection: Projection, strata: Sequence[Stratum]) -> TComparison | None:
    """Comparison value for one random stratum of a z-based method, else ``None``.

    ``None`` as well when the precision is the basic precision SI × RF(0) of a
    MUS sample without errors: it is a Poisson limit, not z-based.
    """
    sampled = [s for s in strata if s.units]
    level, z, se = projection.confidence_level, projection.coefficient, projection.precision
    if projection.method not in Z_METHODS or len(sampled) != 1:
        return None
    if "zero_errors" in projection.extra:
        return None
    if level is None or z is None or se is None or z <= 0 or len(sampled[0].units) < 2:
        return None
    df = len(sampled[0].units) - 1
    t = t_quantile(1 - (1 - level) / 2, df)
    return TComparison(df, t, z, se * t / z)


def _with_sample_minimum(projection: Projection, strata: Sequence[Stratum]) -> Projection:
    count = audited_units(strata)
    if count >= MINIMUM_SAMPLE_UNITS:
        return projection
    text = sample_minimum_text(count, basic_precision="zero_errors" in projection.extra)
    details: dict[str, object] = {"audited_units": count, "minimum": MINIMUM_SAMPLE_UNITS}
    steps = list(projection.steps)
    warnings = [*projection.warnings, text]
    comparison = t_comparison(projection, strata)
    if comparison is not None:
        details["t_comparison"] = comparison.to_dict()
        steps.append(
            Step(
                f"Vergleich: Präzision mit t ({comparison.degrees_of_freedom} FG)",
                "SE_t = SE × t / z",
                comparison.precision_t,
                delegated("Art. 5 Abs. 5"),
            )
        )
        warnings.append(
            f"Vergleichswert mit dem t-Quantil ({comparison.degrees_of_freedom} Freiheitsgrade, "
            f"t = {_decimal(comparison.t, 3)} statt z = {_decimal(comparison.z, 3)}): Präzision "
            f"{_euro(comparison.precision_t)} statt {_euro(projection.precision or 0.0)}. "
            "Maßgeblich bleibt nach Anhang II der z-Wert."
        )
    extra = {**projection.extra, "minimum_sample": details}
    return replace(
        projection,
        steps=tuple(steps),
        warnings=tuple(warnings),
        limitations=(*projection.limitations, text),
        extra=MappingProxyType(extra),
    )


def _mus_zero_errors(projection: Projection, strata: Sequence[Stratum]) -> Projection | None:
    """BP = SI × RF(0) for the MUS standard approach without sample errors.

    Also for MUS ratio estimation without any systemic error, which then equals
    the standard approach (Appendix 1, 4.2).
    """
    sampled = [s for s in strata if s.units]
    if projection.method not in ("mus.standard", "mus.ratio") or len(sampled) != 1:
        return None
    if projection.method == "mus.ratio" and projection.systemic_population:
        return None
    if any(u.random_rate != 0 for u in sampled[0].units) or any(s.has_exclusions for s in strata):
        return None
    level, profile_id = projection.confidence_level, projection.factor_profile
    if level is None or profile_id is None:
        return None
    interval = sampled[0].sampling_book_value / len(sampled[0].units)
    factor = basic_reliability_factor(level, profile_id)
    basic = interval * factor
    warning = (
        "Keine Fehler in der Stichprobe: Die Standardformel ergäbe die Präzision 0. Als "
        f"Präzision gilt die Basispräzision SI × RF(0) = {_euro(interval)} × "
        f"{_decimal(factor, 2)} = {_euro(basic)} (Leitfaden, Abschn. 6.3.5.5)."
    )
    steps = [
        *projection.steps,
        Step("Zuverlässigkeitsfaktor (0 Fehler)", "RF(0)", factor, guidance("6.3.5.2")),
        Step(
            "Präzision ohne Fehler (Basispräzision)", "SE = SI × RF(0)", basic, guidance("6.3.5.5")
        ),
    ]
    extra = {
        **projection.extra,
        "zero_errors": {
            "standard_precision": projection.precision,
            "interval": interval,
            "reliability_factor": factor,
            "basic_precision": basic,
        },
    }
    return replace(
        projection,
        precision=basic,
        steps=tuple(steps),
        warnings=(*projection.warnings, warning),
        extra=MappingProxyType(extra),
    )


def _without_spread(projection: Projection) -> list[str]:
    """Sampled strata whose sample standard deviation is 0 (no contribution to SE)."""
    return [
        r.name
        for r in projection.strata
        if r.sample_size and r.figures.get("sd", r.figures.get("sd_rates")) == 0
    ]


def _spread_text(names: Sequence[str], total_zero: bool) -> str:
    if total_zero:
        return (
            "Präzision 0, weil die Stichprobe keine Streuung der Fehler zeigt: Die "
            "Fehlerobergrenze entspricht dem hochgerechneten Fehler und ist keine belastbare "
            "Obergrenze. Stichprobe erweitern oder, beim MUS, den konservativen Ansatz "
            "verwenden (Leitfaden, Abschn. 6.3.5)."
        )
    listed = ", ".join(f"'{n}'" for n in names)
    return (
        f"{'Schicht' if len(names) == 1 else 'Schichten'} {listed} ohne Streuung der Fehler in "
        "der Stichprobe: Sie tragen 0 zur Präzision bei; die Präzision kann insoweit zu "
        "niedrig sein."
    )


def _with_zero_spread(
    projection: Projection, strata: Sequence[Stratum], *, complete: bool
) -> Projection:
    if projection.precision is None:
        return projection
    names = _without_spread(projection)
    if not names:
        return projection
    total_zero = projection.precision == 0
    if complete and total_zero:
        adjusted = _mus_zero_errors(projection, strata)
        if adjusted is not None:
            return adjusted
    text = _spread_text(names, total_zero)
    return replace(
        projection,
        warnings=(*projection.warnings, text),
        limitations=(*projection.limitations, text),
    )


def apply(projection: Projection, strata: Sequence[Stratum], *, complete: bool) -> Projection:
    """Checks of a statistical projection.

    ``complete`` True for a whole sample: 30-unit minimum and, for the MUS
    standard approach with one random stratum and no errors, the basic
    precision. False for one period of a multi-period sample: the minimum is
    checked over all periods (:func:`combine_periods`), and a precision of 0
    is only stated as a limitation, so that the periods keep matching the
    stratified formulas (guidance sections 6.3.3.4/6.3.3.5).
    """
    small = stratum_minimum(strata)
    checked = replace(
        projection,
        warnings=(*projection.warnings, *small),
        limitations=(*projection.limitations, *small),
    )
    checked = _with_zero_spread(checked, strata, complete=complete)
    return _with_sample_minimum(checked, strata) if complete else checked


def combine_periods(
    strata: Sequence[Stratum], limitations: Sequence[str]
) -> tuple[tuple[str, ...], list[str]]:
    """Limitations and extra warnings of a multi-period sample (30 units over all periods)."""
    count = audited_units(strata)
    if count >= MINIMUM_SAMPLE_UNITS:
        return tuple(limitations), []
    text = sample_minimum_text(count)
    return (*limitations, text), [text]
