"""Groups of programmes and multi-fund programmes (guidance section 7.8).

A group of programmes (or funds) sharing one management and control system
may be audited with one sample stratified by programme ("top-down",
7.8.1): the conclusion is drawn for the group. Results per programme are
possible when each programme has at least 30 observations and its precision
is adequate for a conclusive result; otherwise an additional sample for that
programme (7.2.2) or the recalculation of the confidence level (7.7) may
follow. With separate samples per programme ("bottom-up") each programme is
evaluated on its own.

:func:`assess_groups` evaluates the whole group and, with the same method and
confidence level, each programme over its own strata (sampling part and its
share of the exhaustive units), as in the example of section 7.8.2.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .design import Stratum
from .errors import ExtrapolationInputError
from .evaluation import INCONCLUSIVE, MATERIALITY_RATE, Assessment, assess
from .periods import Period, assess_periods

#: Minimum observations per programme for a result per programme (section 7.8.1).
MIN_GROUP_OBSERVATIONS = 30


@dataclass(frozen=True)
class Group:
    """One programme or fund of the group with its strata."""

    name: str
    strata: tuple[Stratum, ...]


@dataclass(frozen=True)
class GroupResult:
    """Evaluation of one programme; ``observations`` = sampled units."""

    name: str
    observations: int
    assessment: Assessment
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {
            "name": self.name,
            "observations": self.observations,
            "warnings": list(self.warnings),
            **self.assessment.to_dict(),
        }


@dataclass(frozen=True)
class GroupsAssessment:
    """Evaluation of the whole group (top-down) and of each programme."""

    overall: Assessment
    groups: tuple[GroupResult, ...]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {"overall": self.overall.to_dict(), "groups": [g.to_dict() for g in self.groups]}


def _check(groups: Sequence[Group]) -> tuple[Group, ...]:
    checked = tuple(groups)
    if len(checked) < 2:
        raise ExtrapolationInputError(
            "Für eine Auswertung je Programm sind mindestens zwei Gruppen nötig (Leitfaden, "
            "Abschn. 7.8)."
        )
    names = [g.name.strip() for g in checked]
    if not all(names) or len(set(names)) != len(names):
        raise ExtrapolationInputError("Jede Gruppe braucht einen eindeutigen Namen.")
    if any(not g.strata for g in checked):
        raise ExtrapolationInputError("Jede Gruppe braucht mindestens eine Schicht.")
    return checked


def _warnings(name: str, observations: int, assessment: Assessment) -> tuple[str, ...]:
    found = []
    if observations < MIN_GROUP_OBSERVATIONS:
        found.append(
            f"Gruppe '{name}': {observations} Beobachtungen; ein Ergebnis je Programm setzt "
            f"mindestens {MIN_GROUP_OBSERVATIONS} voraus (Leitfaden, Abschn. 7.8.1)."
        )
    if assessment.total_error_rate.conclusion == INCONCLUSIVE:
        found.append(
            f"Gruppe '{name}': nicht schlüssig – zusätzliche Stichprobe (Abschn. 7.2.2) oder "
            "Neuberechnung des Konfidenzniveaus (Abschn. 7.7) möglich."
        )
    return tuple(found)


def assess_groups(
    method_id: str,
    groups: Sequence[Group],
    *,
    confidence_level: float | None = None,
    factor_profile: str | None = None,
    materiality_rate: float = MATERIALITY_RATE,
) -> GroupsAssessment:
    """Evaluate a group of programmes as a whole and per programme (guidance section 7.8).

    Stratum names must be unique across the groups. The overall evaluation
    uses all strata; each programme is evaluated over its own strata with
    the same method, confidence level and materiality.
    """
    checked = _check(groups)

    def run(strata: Sequence[Stratum]) -> Assessment:
        return assess(
            method_id,
            strata,
            confidence_level=confidence_level,
            factor_profile=factor_profile,
            materiality_rate=materiality_rate,
        )

    overall = run([s for g in checked for s in g.strata])
    results = []
    for group in checked:
        try:
            own = run(group.strata)
        except ExtrapolationInputError as exc:
            raise ExtrapolationInputError(f"Gruppe '{group.name}': {exc}") from exc
        observations = sum(len(s.units) for s in group.strata)
        results.append(
            GroupResult(group.name, observations, own, _warnings(group.name, observations, own))
        )
    return GroupsAssessment(overall, tuple(results))


def _group_periods(
    periods: Sequence[Period], labels: Mapping[tuple[str, str], str], name: str
) -> list[Period]:
    found = []
    for period in periods:
        own = tuple(s for s in period.strata if labels.get((period.name, s.name)) == name)
        if own:
            found.append(Period(period.name, own))
    return found


@dataclass(frozen=True)
class _Options:
    confidence_level: float | None
    factor_profile: str | None
    materiality_rate: float


def _period_group(method_id: str, own: list[Period], name: str, options: _Options) -> GroupResult:
    try:
        if len(own) > 1:
            assessment = assess_periods(
                method_id,
                own,
                confidence_level=options.confidence_level,
                factor_profile=options.factor_profile,
                materiality_rate=options.materiality_rate,
            )
        else:
            assessment = assess(
                method_id,
                own[0].strata,
                confidence_level=options.confidence_level,
                factor_profile=options.factor_profile,
                materiality_rate=options.materiality_rate,
            )
    except ExtrapolationInputError as exc:
        raise ExtrapolationInputError(f"Gruppe '{name}': {exc}") from exc
    observations = sum(len(s.units) for p in own for s in p.strata)
    return GroupResult(name, observations, assessment, _warnings(name, observations, assessment))


def assess_groups_over_periods(
    method_id: str,
    periods: Sequence[Period],
    labels: Mapping[tuple[str, str], str],
    *,
    confidence_level: float | None = None,
    factor_profile: str | None = None,
    population_units: int | None = None,
    materiality_rate: float = MATERIALITY_RATE,
) -> GroupsAssessment:
    """Group of programmes sampled in several periods (guidance sections 6.3.4, 7.3, 7.8).

    Section 6.3.4 stratifies each period by programme (example 6.3.4.7); the
    whole group is evaluated over all periods, each programme over its own
    strata of all periods. ``labels`` maps (period, stratum) to the programme.
    """
    missing = [
        (p.name, s.name) for p in periods for s in p.strata if not labels.get((p.name, s.name))
    ]
    if missing:
        period, stratum = missing[0]
        raise ExtrapolationInputError(f"Schicht '{stratum}' im Zeitraum '{period}' ohne Programm.")
    names = list(dict.fromkeys(labels[(p.name, s.name)] for p in periods for s in p.strata))
    if len(names) < 2:
        raise ExtrapolationInputError(
            "Für eine Auswertung je Programm sind mindestens zwei Programme nötig."
        )
    options = _Options(confidence_level, factor_profile, materiality_rate)
    overall = assess_periods(
        method_id,
        periods,
        confidence_level=confidence_level,
        factor_profile=factor_profile,
        population_units=population_units,
        materiality_rate=materiality_rate,
    )
    results = [
        _period_group(method_id, _group_periods(periods, labels, name), name, options)
        for name in names
    ]
    return GroupsAssessment(overall, tuple(results))
