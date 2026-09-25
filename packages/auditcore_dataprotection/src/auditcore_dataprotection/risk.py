"""Risk assessment: gross risk, capped measure effects, explicit residual values.

Schema 1 profiles band the severity × likelihood product; schema 2 profiles
use the profile's risk matrix and severity floors (DSK-Kurzpapier Nr. 18,
EDPB template 2026).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .answers import Scenario, parse_scenarios
from .results import Issue, RiskResult, ScenarioResult
from .rules import RuleProfile


def _highest(profile: RuleProfile, bands: Sequence[str]) -> str:
    """Highest band of several scenarios; the lowest band when there is none."""
    if not bands:
        return profile.bands[0].label
    return max(bands, key=profile.band_rank)


def _bands(
    profile: RuleProfile,
    scenario: Scenario,
    gross: int,
    net: int,
    net_s: int,
    net_l: int,
    explicit_severity: bool,
) -> tuple[str, str, str | None]:
    """Gross band, net band and the reference of an applied severity floor.

    Schema 1: bands of the severity × likelihood product. Schema 2: bands from
    the profile's risk matrix (DSK-Kurzpapier Nr. 18, S. 5). A severity floor
    depends on the severity before measures, because a risk can be
    unacceptable when its potential impact is very severe even if it is
    unlikely (EDPB explainer, footnote 9). Measures do not remove the floor;
    only an explicit, justified residual severity does.
    """
    if not profile.edpb:
        return profile.band(gross), profile.band(net), None
    gross_band = profile.matrix_band(scenario.severity, scenario.likelihood)
    net_band = profile.matrix_band(net_s, net_l)
    floor = profile.severity_floor(scenario.severity)
    if floor is None:
        return gross_band, net_band, None
    if profile.band_rank(gross_band) < profile.band_rank(floor.min_band):
        gross_band = floor.min_band
    if explicit_severity or profile.band_rank(net_band) >= profile.band_rank(floor.min_band):
        return gross_band, net_band, None
    return gross_band, floor.min_band, floor.reference


def _residual_issues(
    index: int, scenario: Scenario, net_s: int, net_l: int, explicit: Sequence[str]
) -> list[Issue]:
    """Plausibility of explicit residual values."""
    issues: list[Issue] = []
    if explicit and not scenario.residual_justification:
        issues.append(
            Issue(
                "residual_without_justification",
                f"Szenario {index}: Der ausdrücklich gesetzte Restwert ist nicht begründet.",
                blocking=True,
                subject=str(index),
            )
        )
    if net_s > scenario.severity or net_l > scenario.likelihood:
        issues.append(
            Issue(
                "residual_above_gross",
                f"Szenario {index}: Der Restwert liegt über dem Wert vor Maßnahmen.",
                blocking=False,
                subject=str(index),
            )
        )
    return issues


def _edpb_details(
    profile: RuleProfile, scenario: Scenario, net_floor: str | None
) -> dict[str, object]:
    """Risk source, circumstances and acceptance of a schema 2 scenario."""
    if not profile.edpb:
        return {}
    titles = profile.acceptance_levels
    return {
        "net_floor": net_floor,
        "risk_source": scenario.risk_source,
        "modulating_factors": scenario.modulating_factors,
        "acceptance_inherent": scenario.acceptance_inherent,
        "acceptance_inherent_title": titles.get(scenario.acceptance_inherent or "", ""),
        "acceptance_residual": scenario.acceptance_residual,
        "acceptance_residual_title": titles.get(scenario.acceptance_residual or "", ""),
        "acceptance_note": scenario.acceptance_note,
    }


def _assess_scenario(
    profile: RuleProfile, index: int, scenario: Scenario
) -> tuple[ScenarioResult, list[Issue], str | None]:
    """Result, plausibility issues and applied severity floor of one scenario."""
    reduction_s = sum(profile.measure(m).reduces_severity for m in scenario.measures)
    reduction_l = sum(profile.measure(m).reduces_likelihood for m in scenario.measures)
    cap, floor = profile.mitigation_cap, profile.mitigation_floor
    net_s = max(floor, scenario.severity - min(cap, reduction_s))
    net_l = max(floor, scenario.likelihood - min(cap, reduction_l))
    explicit: list[str] = []
    if scenario.residual_severity is not None:
        net_s = scenario.residual_severity
        explicit.append("severity")
    if scenario.residual_likelihood is not None:
        net_l = scenario.residual_likelihood
        explicit.append("likelihood")
    issues = _residual_issues(index, scenario, net_s, net_l, explicit)
    gross = scenario.severity * scenario.likelihood
    net = net_s * net_l
    # Only a justified explicit residual severity lifts a severity floor.
    justified_severity = "severity" in explicit and bool(scenario.residual_justification)
    gross_band, net_band, net_floor = _bands(
        profile, scenario, gross, net, net_s, net_l, justified_severity
    )
    result = ScenarioResult(
        index=index,
        dimension=scenario.dimension,
        dimension_title=profile.dimensions[scenario.dimension],
        sdm=scenario.dimension in profile.sdm_dimensions,
        description=scenario.description,
        gross_severity=scenario.severity,
        gross_likelihood=scenario.likelihood,
        gross=gross,
        gross_band=gross_band,
        measures=scenario.measures,
        measure_titles=tuple(profile.measure(m).title for m in scenario.measures),
        reduction_severity=min(cap, reduction_s),
        reduction_likelihood=min(cap, reduction_l),
        net_severity=net_s,
        net_likelihood=net_l,
        net=net,
        net_band=net_band,
        explicit_residual=tuple(explicit),
        residual_justification=scenario.residual_justification,
        edpb=_edpb_details(profile, scenario, net_floor),
    )
    return result, issues, net_floor


def assess_risk(profile: RuleProfile, scenarios: Iterable[object]) -> RiskResult:
    """Gross = severity × likelihood; net after capped measure reductions or explicit values.

    Each distinct measure reduces an axis by its catalogue value; the sum per
    axis is capped by the profile and never goes below its floor. An explicit
    residual value replaces the computed value of that axis and is flagged.
    """
    results: list[ScenarioResult] = []
    issues: list[Issue] = []
    floored: list[int] = []
    for index, scenario in enumerate(parse_scenarios(scenarios, profile), start=1):
        result, found, net_floor = _assess_scenario(profile, index, scenario)
        results.append(result)
        issues.extend(found)
        if net_floor:
            floored.append(index)
    gross_max = max((r.gross for r in results), default=0)
    net_max = max((r.net for r in results), default=0)
    if not profile.edpb:
        return RiskResult(
            scenarios=tuple(results),
            gross_maximum=gross_max,
            net_maximum=net_max,
            net_band=profile.band(net_max),
            issues=tuple(issues),
        )
    return RiskResult(
        scenarios=tuple(results),
        gross_maximum=gross_max,
        net_maximum=net_max,
        net_band=_highest(profile, [r.net_band for r in results]),
        issues=tuple(issues),
        method="matrix",
        gross_band=_highest(profile, [r.gross_band for r in results]),
        floored=tuple(floored),
    )
