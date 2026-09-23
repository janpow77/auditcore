"""DSFA calculation: threshold analysis, gross/net risk and a reasoned proposal.

Pure functions over an explicitly selected :class:`~auditcore_dataprotection.rules.RuleProfile`.
Unlike the source application, missing or unknown answers never count as
"no": they keep the result visibly ``unvollstaendig``. Input is validated at
the boundary; unknown keys, non-boolean answers, values outside the scale and
duplicate criteria or measures are rejected instead of being skipped.

The proposal is a recommendation for a human decision. It never releases
anything and always names the profile id, version and fingerprint it used.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .errors import ValidationError
from .rules import (
    EFFECT_FRIA,
    EFFECT_HARD,
    EFFECT_POINT,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_INCOMPLETE,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_SCREENING_ONLY,
    RuleProfile,
)

CALCULATION_VERSION = "auditcore_dataprotection.calculation/1"

SCREENING_REQUIRED = "pflicht"
SCREENING_NOT_REQUIRED = "keine_pflicht"
SCREENING_INCOMPLETE = "unvollstaendig"


class AnswerValue(StrEnum):
    """Explicit three-valued answer; ``UNKNOWN`` is never treated as ``NO``."""

    YES = "ja"
    NO = "nein"
    UNKNOWN = "unbekannt"


@dataclass(frozen=True)
class Answer:
    """Answer of the responsible department with its justification."""

    value: AnswerValue
    justification: str = ""

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form of the answer."""
        return {"value": self.value.value, "justification": self.justification}


@dataclass(frozen=True)
class Scenario:
    """Risk scenario of one protection dimension, gross and optionally explicit net."""

    dimension: str
    description: str
    severity: int
    likelihood: int
    measures: tuple[str, ...] = ()
    residual_severity: int | None = None
    residual_likelihood: int | None = None
    residual_justification: str = ""
    risk_source: str = ""
    modulating_factors: str = ""
    acceptance: str | None = None
    acceptance_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form of the scenario.

        The schema 2 fields (EDPB template 4.1) appear only when they are set,
        so schema 1 scenarios serialise exactly as before.
        """
        data: dict[str, Any] = {
            "dimension": self.dimension,
            "description": self.description,
            "severity": self.severity,
            "likelihood": self.likelihood,
            "measures": list(self.measures),
            "residual_severity": self.residual_severity,
            "residual_likelihood": self.residual_likelihood,
            "residual_justification": self.residual_justification,
        }
        for name in EDPB_SCENARIO_FIELDS:
            value = getattr(self, name)
            if value not in (None, ""):
                data[name] = value
        return data


#: Scenario fields that only schema 2 profiles accept (EDPB template, section 4).
EDPB_SCENARIO_FIELDS = ("risk_source", "modulating_factors", "acceptance", "acceptance_note")


@dataclass(frozen=True)
class Issue:
    """Completeness or plausibility note; ``blocking`` issues prevent a release."""

    code: str
    message: str
    blocking: bool
    subject: str = ""

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form of the issue."""
        return {
            "code": self.code,
            "message": self.message,
            "blocking": self.blocking,
            "subject": self.subject,
        }


@dataclass(frozen=True)
class ScreeningResult:
    """Result of the threshold analysis with open questions and trace."""

    outcome: str
    points: int
    points_threshold: int
    hard_triggers: tuple[str, ...]
    point_criteria: tuple[str, ...]
    fria_required: bool | None
    unanswered: tuple[str, ...]
    unknown: tuple[str, ...]
    reasoning: str
    trace: tuple[Mapping[str, Any], ...]

    @property
    def complete(self) -> bool:
        """True if every question has an explicit yes or no answer."""
        return not self.unanswered and not self.unknown


@dataclass(frozen=True)
class ScenarioResult:
    """Gross and net risk of one scenario with measure effects."""

    index: int
    dimension: str
    dimension_title: str
    sdm: bool
    description: str
    gross_severity: int
    gross_likelihood: int
    gross: int
    gross_band: str
    measures: tuple[str, ...]
    measure_titles: tuple[str, ...]
    reduction_severity: int
    reduction_likelihood: int
    net_severity: int
    net_likelihood: int
    net: int
    net_band: str
    explicit_residual: tuple[str, ...]
    residual_justification: str
    edpb: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskResult:
    """Risk of all scenarios with maxima and plausibility issues."""

    scenarios: tuple[ScenarioResult, ...]
    gross_maximum: int
    net_maximum: int
    net_band: str
    issues: tuple[Issue, ...]
    net_level_maximum: int | None = None

    @property
    def assessed(self) -> bool:
        """True if at least one scenario was assessed."""
        return bool(self.scenarios)


@dataclass(frozen=True)
class Proposal:
    """Reasoned recommendation; ``recommendation`` is one of the profile decisions
    or ``unvollstaendig``."""

    profile: Mapping[str, str]
    regime: str
    screening: ScreeningResult
    risk: RiskResult | None
    recommendation: str
    recommendation_text: str
    reasoning: str
    consultation_required: bool
    consultation_reference: str
    issues: tuple[Issue, ...]
    calculation: str = CALCULATION_VERSION
    trace: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    @property
    def blocking_issues(self) -> tuple[Issue, ...]:
        """Issues that prevent a release."""
        return tuple(i for i in self.issues if i.blocking)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable proposal including trace and profile identity."""
        return {
            "calculation": self.calculation,
            "profile": dict(self.profile),
            "regime": self.regime,
            "recommendation": self.recommendation,
            "recommendation_text": self.recommendation_text,
            "reasoning": self.reasoning,
            "consultation_required": self.consultation_required,
            "consultation_reference": self.consultation_reference,
            "issues": [i.to_dict() for i in self.issues],
            "screening": {
                "outcome": self.screening.outcome,
                "points": self.screening.points,
                "points_threshold": self.screening.points_threshold,
                "hard_triggers": list(self.screening.hard_triggers),
                "point_criteria": list(self.screening.point_criteria),
                "fria_required": self.screening.fria_required,
                "unanswered": list(self.screening.unanswered),
                "unknown": list(self.screening.unknown),
                "complete": self.screening.complete,
                "reasoning": self.screening.reasoning,
            },
            "risk": None
            if self.risk is None
            else {
                "gross_maximum": self.risk.gross_maximum,
                "net_maximum": self.risk.net_maximum,
                "net_band": self.risk.net_band,
                "scenarios": [
                    {
                        "index": s.index,
                        "dimension": s.dimension,
                        "dimension_title": s.dimension_title,
                        "sdm": s.sdm,
                        "description": s.description,
                        "gross_severity": s.gross_severity,
                        "gross_likelihood": s.gross_likelihood,
                        "gross": s.gross,
                        "gross_band": s.gross_band,
                        "measures": list(s.measures),
                        "measure_titles": list(s.measure_titles),
                        "reduction_severity": s.reduction_severity,
                        "reduction_likelihood": s.reduction_likelihood,
                        "net_severity": s.net_severity,
                        "net_likelihood": s.net_likelihood,
                        "net": s.net,
                        "net_band": s.net_band,
                        "explicit_residual": list(s.explicit_residual),
                        "residual_justification": s.residual_justification,
                        **dict(s.edpb),
                    }
                    for s in self.risk.scenarios
                ],
                **(
                    {}
                    if self.risk.net_level_maximum is None
                    else {"net_level_maximum": self.risk.net_level_maximum}
                ),
            },
            "trace": [dict(t) for t in self.trace],
        }


# ---------------------------------------------------------------------------
# Input boundary
# ---------------------------------------------------------------------------


def _answer(key: str, raw: Any) -> Answer:
    if isinstance(raw, Answer):
        return raw
    if isinstance(raw, AnswerValue):
        return Answer(raw)
    if raw is None:
        return Answer(AnswerValue.UNKNOWN)
    if isinstance(raw, bool):
        return Answer(AnswerValue.YES if raw else AnswerValue.NO)
    if isinstance(raw, str) and raw in {v.value for v in AnswerValue}:
        return Answer(AnswerValue(raw))
    if isinstance(raw, Mapping):
        unexpected = set(raw) - {"ja", "value", "begruendung", "justification"}
        if unexpected:
            raise ValidationError(
                f"Antwort zu '{key}' enthält unbekannte Felder: {', '.join(sorted(unexpected))}."
            )
        justification = raw.get("justification", raw.get("begruendung", "")) or ""
        if not isinstance(justification, str):
            raise ValidationError(f"Die Begründung zu '{key}' muss Text sein.")
        inner = _answer(key, raw["value"] if "value" in raw else raw.get("ja"))
        return Answer(inner.value, justification)
    raise ValidationError(
        f"Antwort zu '{key}' muss ja/nein (True/False) oder ausdrücklich unbekannt sein, "
        f"war: {raw!r}. Zeichenketten wie 'false' werden nicht umgedeutet."
    )


def parse_answers(raw: Mapping[str, Any], profile: RuleProfile) -> dict[str, Answer]:
    """Validate answers keyed by question.

    Accepted values: ``True``/``False``, ``None``/``"unbekannt"`` (explicit
    unknown), ``"ja"``/``"nein"``, :class:`Answer`, or a mapping with ``ja`` or
    ``value`` and an optional ``begruendung``/``justification``.

    Raises:
        ValidationError: not a mapping, unknown question keys or non-boolean values.
    """
    if not isinstance(raw, Mapping):
        raise ValidationError("Antworten sind als Zuordnung Frage → Antwort zu übergeben.")
    known = set(profile.question_keys)
    unknown_keys = sorted(str(k) for k in raw if k not in known)
    if unknown_keys:
        raise ValidationError(
            f"Unbekannte Fragen für Profil {profile.id} {profile.version}: "
            f"{', '.join(unknown_keys)}."
        )
    return {key: _answer(key, value) for key, value in raw.items()}


def parse_answer_list(items: Iterable[tuple[str, Any]], profile: RuleProfile) -> dict[str, Answer]:
    """Validate ``(key, answer)`` pairs; a criterion given twice is an error."""
    collected: dict[str, Any] = {}
    duplicates: list[str] = []
    for key, value in items:
        if key in collected:
            duplicates.append(key)
        collected[key] = value
    if duplicates:
        raise ValidationError(
            f"Kriterien sind mehrfach beantwortet: {', '.join(sorted(set(duplicates)))}. "
            "Jede Frage darf genau einmal beantwortet werden."
        )
    return parse_answers(collected, profile)


def _level(value: Any, label: str, profile: RuleProfile, *, optional: bool) -> int | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(
            f"{label} muss eine ganze Zahl von {profile.scale_min} bis {profile.scale_max} sein, "
            f"war: {value!r}."
        )
    if not profile.scale_min <= value <= profile.scale_max:
        raise ValidationError(
            f"{label} ist auf einer Skala von {profile.scale_min} bis {profile.scale_max} "
            f"einzustufen, war: {value}."
        )
    return value


def _scenario(index: int, raw: Any, profile: RuleProfile) -> Scenario:
    if isinstance(raw, Scenario):
        raw = raw.to_dict()
    if not isinstance(raw, Mapping):
        raise ValidationError(f"Risikoszenario {index} ist keine Zuordnung.")
    allowed = {
        "dimension",
        "description",
        "severity",
        "likelihood",
        "measures",
        "residual_severity",
        "residual_likelihood",
        "residual_justification",
        *EDPB_SCENARIO_FIELDS,
    }
    unexpected = set(raw) - allowed
    if unexpected:
        raise ValidationError(
            f"Risikoszenario {index} enthält unbekannte Felder: {', '.join(sorted(unexpected))}."
        )
    dimension = raw.get("dimension")
    if dimension not in profile.dimensions:
        raise ValidationError(f"Risikoszenario {index}: unbekanntes Schutzziel {dimension!r}.")
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValidationError(f"Risikoszenario {index} braucht eine Beschreibung.")
    measures = raw.get("measures") or ()
    if isinstance(measures, str) or not isinstance(measures, Sequence):
        raise ValidationError(f"Risikoszenario {index}: Maßnahmen sind als Liste anzugeben.")
    known = {m.key for m in profile.measures}
    unknown = sorted({str(m) for m in measures if m not in known})
    if unknown:
        raise ValidationError(f"Risikoszenario {index}: unbekannte Maßnahmen {', '.join(unknown)}.")
    if len(set(measures)) != len(measures):
        raise ValidationError(
            f"Risikoszenario {index}: eine Maßnahme ist mehrfach angegeben; sie wirkt nur einmal."
        )
    justification = raw.get("residual_justification") or ""
    if not isinstance(justification, str):
        raise ValidationError(f"Risikoszenario {index}: Begründung des Restwerts muss Text sein.")
    extra = _edpb_scenario_fields(index, raw, profile)
    severity = _level(raw.get("severity"), "Schwere", profile, optional=False)
    likelihood = _level(
        raw.get("likelihood"), "Eintrittswahrscheinlichkeit", profile, optional=False
    )
    assert severity is not None and likelihood is not None
    return Scenario(
        dimension=str(dimension),
        description=description.strip(),
        severity=severity,
        likelihood=likelihood,
        measures=tuple(str(m) for m in measures),
        residual_severity=_level(
            raw.get("residual_severity"), "Rest-Schwere", profile, optional=True
        ),
        residual_likelihood=_level(
            raw.get("residual_likelihood"), "Rest-Wahrscheinlichkeit", profile, optional=True
        ),
        residual_justification=justification.strip(),
        **extra,
    )


def _edpb_scenario_fields(
    index: int, raw: Mapping[str, Any], profile: RuleProfile
) -> dict[str, Any]:
    """Validate risk source, modulating factors and acceptance (schema 2 only)."""
    given = {
        name: raw.get(name) for name in EDPB_SCENARIO_FIELDS if raw.get(name) not in (None, "")
    }
    if given and not profile.edpb:
        raise ValidationError(
            f"Risikoszenario {index}: {', '.join(sorted(given))} kennt nur ein Profil nach "
            "der EDSA-Vorlage (Schema 2)."
        )
    result: dict[str, Any] = {}
    for name in ("risk_source", "modulating_factors", "acceptance_note"):
        value = given.get(name, "")
        if not isinstance(value, str):
            raise ValidationError(f"Risikoszenario {index}: '{name}' muss Text sein.")
        result[name] = value.strip()
    acceptance = given.get("acceptance")
    if acceptance is not None and acceptance not in profile.acceptance_levels:
        raise ValidationError(
            f"Risikoszenario {index}: unbekannte Bewertung {acceptance!r}. Zulässig sind: "
            f"{', '.join(profile.acceptance_levels)}."
        )
    result["acceptance"] = acceptance
    return result


def parse_scenarios(raw: Iterable[Any], profile: RuleProfile) -> tuple[Scenario, ...]:
    """Validate risk scenarios strictly against the profile scale and catalogues."""
    if isinstance(raw, (str, bytes, Mapping)):
        raise ValidationError("Risikoszenarien sind als Liste zu übergeben.")
    return tuple(_scenario(i, item, profile) for i, item in enumerate(raw, start=1))


# ---------------------------------------------------------------------------
# Threshold analysis
# ---------------------------------------------------------------------------


def _hard_trigger_reasoning(profile: RuleProfile, hard: Sequence[str]) -> str:
    """Reasoning when at least one hard trigger was answered with yes."""
    references = "; ".join(profile.question(k).reference for k in hard)
    if profile.regime == "hdsig_ji":
        return (
            f"Die Datenschutz-Folgenabschätzung ist durchzuführen "
            f"({profile.norm('pflicht')}). Erfüllt ist: {references}. "
            "Der Dritte Teil des HDSIG kennt die Regelbeispiele des Art. 35 "
            "Abs. 3 DSGVO und die Liste nach Abs. 4 nicht; sie werden hier "
            "als strengerer Maßstab angewandt, weil die Abgrenzung beider "
            "Rechtsakte auf europäischer Ebene nicht geklärt ist."
        )
    if len(hard) == 1:
        return (
            "Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
            f"1 Muss-Kriterium bejaht wurde: {references}."
        )
    return (
        "Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
        f"{len(hard)} Muss-Kriterien bejaht wurden: {references}."
    )


def _screening_outcome(
    profile: RuleProfile, hard: Sequence[str], score: int, unanswered: int, unknown: int
) -> tuple[str, str]:
    """Outcome and reasoning of the threshold analysis; open answers never count as no."""
    threshold = profile.points_threshold
    if hard:
        return SCREENING_REQUIRED, _hard_trigger_reasoning(profile, hard)
    if score >= threshold:
        return SCREENING_REQUIRED, (
            f"Es sind {score} der neun {profile.criteria_label} erfüllt. "
            f"Ab {threshold} Kriterien ist "
            "regelmäßig von einem voraussichtlich hohen Risiko auszugehen "
            "(WP 248 rev.01); die Folgenabschätzung ist durchzuführen."
        )
    if unanswered or unknown:
        return SCREENING_INCOMPLETE, (
            f"Die Schwellwertanalyse ist unvollständig: {unanswered} Fragen sind "
            f"unbeantwortet und {unknown} als unbekannt gekennzeichnet. Bisher sind "
            f"{score} der neun Kriterien bejaht. Ein Ergebnis wird erst nach vollständiger "
            "Erhebung vorgeschlagen; eine fehlende Angabe gilt nicht als Nein."
        )
    return SCREENING_NOT_REQUIRED, (
        f"Kein Muss-Kriterium ist erfüllt und es sind {score} der neun "
        f"{profile.criteria_label} bejaht, also "
        f"weniger als {threshold}. Eine Folgenabschätzung ist damit "
        "nicht erforderlich; das Ergebnis ist gleichwohl zu dokumentieren "
        f"({profile.norm('nachweis')})."
    )


def screen(profile: RuleProfile, answers: Mapping[str, Answer | Any]) -> ScreeningResult:
    """Evaluate hard triggers, EDSA points and the FRIA marker in profile order."""
    parsed = parse_answers(answers, profile)
    hard: list[str] = []
    points: list[str] = []
    unanswered: list[str] = []
    unknown: list[str] = []
    fria_yes = False
    fria_open = False
    trace: list[dict[str, Any]] = []
    for question in profile.questions:
        answer = parsed.get(question.key)
        if answer is None or answer.value is AnswerValue.UNKNOWN:
            (unanswered if answer is None else unknown).append(question.key)
            fria_open = fria_open or question.effect == EFFECT_FRIA
            continue
        if answer.value is not AnswerValue.YES:
            continue
        trace.append(
            {
                "step": "criterion",
                "question": question.key,
                "effect": question.effect,
                "reference": question.reference,
            }
        )
        if question.effect == EFFECT_HARD:
            hard.append(question.key)
        elif question.effect == EFFECT_POINT:
            points.append(question.key)
        elif question.effect == EFFECT_FRIA:
            fria_yes = True

    score = len(points)
    threshold = profile.points_threshold
    open_count = len(unanswered) + len(unknown)
    outcome, reasoning = _screening_outcome(profile, hard, score, len(unanswered), len(unknown))
    fria: bool | None = True if fria_yes else (None if fria_open else False)
    if fria_yes:
        reasoning += (
            " Zusätzlich handelt es sich um ein Hochrisiko-KI-System; die "
            "Grundrechte-Folgenabschätzung nach Art. 27 der Verordnung (EU) "
            "2024/1689 ist zu erstellen und darf mit dieser Abschätzung "
            "verbunden werden (Art. 27 Abs. 4)."
        )
    trace.append(
        {
            "step": "screening",
            "outcome": outcome,
            "points": score,
            "threshold": threshold,
            "open": open_count,
        }
    )
    return ScreeningResult(
        outcome=outcome,
        points=score,
        points_threshold=threshold,
        hard_triggers=tuple(hard),
        point_criteria=tuple(points),
        fria_required=fria,
        unanswered=tuple(unanswered),
        unknown=tuple(unknown),
        reasoning=reasoning,
        trace=tuple(trace),
    )


# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------


def assess_risk(profile: RuleProfile, scenarios: Iterable[Scenario | Any]) -> RiskResult:
    """Gross = severity × likelihood; net after capped measure reductions or explicit values.

    Each distinct measure reduces an axis by its catalogue value; the sum per
    axis is capped by the profile and never goes below its floor. An explicit
    residual value replaces the computed value of that axis and is flagged.
    """
    parsed = parse_scenarios(scenarios, profile)
    results: list[ScenarioResult] = []
    issues: list[Issue] = []
    levels: list[int] = []
    for index, scenario in enumerate(parsed, start=1):
        reduction_s = sum(profile.measure(m).reduces_severity for m in scenario.measures)
        reduction_l = sum(profile.measure(m).reduces_likelihood for m in scenario.measures)
        cap, floor = profile.mitigation_cap, profile.mitigation_floor
        computed_s = max(floor, scenario.severity - min(cap, reduction_s))
        computed_l = max(floor, scenario.likelihood - min(cap, reduction_l))
        explicit: list[str] = []
        net_s = computed_s
        net_l = computed_l
        if scenario.residual_severity is not None:
            net_s = scenario.residual_severity
            explicit.append("severity")
        if scenario.residual_likelihood is not None:
            net_l = scenario.residual_likelihood
            explicit.append("likelihood")
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
        gross = scenario.severity * scenario.likelihood
        net = net_s * net_l
        gross_level, gross_floor = _floored(profile, gross, scenario.severity)
        net_level, net_floor = _floored(profile, net, net_s)
        levels.append(net_level)
        edpb: dict[str, Any] = {}
        if profile.edpb:
            edpb = {
                "gross_level": gross_level,
                "net_level": net_level,
                "gross_floor": gross_floor,
                "net_floor": net_floor,
                "risk_source": scenario.risk_source,
                "modulating_factors": scenario.modulating_factors,
                "acceptance": scenario.acceptance,
                "acceptance_title": profile.acceptance_levels.get(scenario.acceptance or "", ""),
                "acceptance_note": scenario.acceptance_note,
            }
        results.append(
            ScenarioResult(
                index=index,
                dimension=scenario.dimension,
                dimension_title=profile.dimensions[scenario.dimension],
                sdm=scenario.dimension in profile.sdm_dimensions,
                description=scenario.description,
                gross_severity=scenario.severity,
                gross_likelihood=scenario.likelihood,
                gross=gross,
                gross_band=profile.band(gross_level),
                measures=scenario.measures,
                measure_titles=tuple(profile.measure(m).title for m in scenario.measures),
                reduction_severity=min(cap, reduction_s),
                reduction_likelihood=min(cap, reduction_l),
                net_severity=net_s,
                net_likelihood=net_l,
                net=net,
                net_band=profile.band(net_level),
                explicit_residual=tuple(explicit),
                residual_justification=scenario.residual_justification,
                edpb=edpb,
            )
        )
    gross_max = max((r.gross for r in results), default=0)
    net_max = max((r.net for r in results), default=0)
    level_max = max(levels, default=0)
    return RiskResult(
        scenarios=tuple(results),
        gross_maximum=gross_max,
        net_maximum=net_max,
        net_band=profile.band(level_max),
        issues=tuple(issues),
        net_level_maximum=level_max if profile.edpb else None,
    )


def _floored(profile: RuleProfile, product: int, severity: int) -> tuple[int, str | None]:
    """Level for banding: the product, raised to the floor of a severe scenario.

    A risk can be unacceptable when its impact is very severe even if it is
    unlikely (EDPB template explainer, footnote 9; DSK-Kurzpapier Nr. 18, S. 5).
    Schema 1 profiles have no floors and keep the plain product.
    """
    floor = profile.severity_floor(severity)
    if floor is None:
        return product, None
    minimum = profile.band_floor_value(floor.min_band)
    if product >= minimum:
        return product, None
    return minimum, floor.reference


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------


def _screening_issues(screening: ScreeningResult) -> list[Issue]:
    """Blocking issues for unanswered and unknown screening questions."""
    issues: list[Issue] = []
    if screening.unanswered:
        issues.append(
            Issue(
                "unanswered_questions",
                f"{len(screening.unanswered)} Fragen der Schwellwertanalyse sind unbeantwortet.",
                blocking=True,
                subject=",".join(screening.unanswered),
            )
        )
    if screening.unknown:
        issues.append(
            Issue(
                "unknown_answers",
                f"{len(screening.unknown)} Fragen sind als unbekannt gekennzeichnet.",
                blocking=True,
                subject=",".join(screening.unknown),
            )
        )
    return issues


def _risk_recommendation(profile: RuleProfile, net_maximum: int) -> str:
    """Recommendation from the highest net risk and the profile thresholds."""
    if net_maximum >= profile.consult_from:
        return RECOMMENDATION_CONSULTATION
    if net_maximum >= profile.conditions_from:
        return RECOMMENDATION_RELEASE_WITH_CONDITIONS
    return RECOMMENDATION_RELEASE


def propose(
    profile: RuleProfile,
    answers: Mapping[str, Answer | Any],
    scenarios: Iterable[Scenario | Any] = (),
) -> Proposal:
    """Combine screening and risk into a reasoned, traceable recommendation."""
    screening = screen(profile, answers)
    issues = _screening_issues(screening)
    trace = list(screening.trace)
    consultation_reference = profile.norm("konsultation")

    def result(
        recommendation: str, text: str, reasoning: str, risk: RiskResult | None, consultation: bool
    ) -> Proposal:
        """Build the proposal for one recommendation."""
        trace.append({"step": "recommendation", "value": recommendation})
        return Proposal(
            profile=profile.reference,
            regime=profile.regime,
            screening=screening,
            risk=risk,
            recommendation=recommendation,
            recommendation_text=text,
            reasoning=reasoning,
            consultation_required=consultation,
            consultation_reference=consultation_reference,
            issues=tuple(issues),
            trace=tuple(trace),
        )

    risk = assess_risk(profile, scenarios)
    issues.extend(risk.issues)
    if screening.outcome in (SCREENING_NOT_REQUIRED, SCREENING_INCOMPLETE):
        if screening.outcome == SCREENING_NOT_REQUIRED:
            recommendation = RECOMMENDATION_SCREENING_ONLY
            text = profile.recommendation_texts[RECOMMENDATION_SCREENING_ONLY]
        else:
            recommendation = RECOMMENDATION_INCOMPLETE
            text = (
                "Die Schwellwertanalyse ist nicht vollständig. Bevor ein Ergebnis "
                "vorgeschlagen werden kann, sind alle Fragen mit Ja oder Nein zu beantworten."
            )
        return result(
            recommendation, text, screening.reasoning, risk if risk.assessed else None, False
        )

    if not risk.assessed:
        issues.append(
            Issue(
                "risk_assessment_missing",
                "Die Folgenabschätzung ist durchzuführen, es ist aber noch kein "
                "Risikoszenario erfasst.",
                blocking=True,
            )
        )
        return result(
            RECOMMENDATION_INCOMPLETE,
            "Die Folgenabschätzung ist durchzuführen, es sind aber noch keine "
            "Risikoszenarien erfasst. Ohne Risikobetrachtung lässt sich das "
            f"verbleibende Risiko nicht beurteilen ({profile.norm('risiko')}).",
            screening.reasoning,
            risk,
            False,
        )
    level = risk.net_maximum if risk.net_level_maximum is None else risk.net_level_maximum
    recommendation = _risk_recommendation(profile, level)
    trace.append(
        {
            "step": "risk",
            "gross_maximum": risk.gross_maximum,
            "net_maximum": risk.net_maximum,
            "consult_from": profile.consult_from,
            "conditions_from": profile.conditions_from,
        }
    )
    reasoning = (
        f"{screening.reasoning} Das höchste Risiko vor Maßnahmen beträgt "
        f"{risk.gross_maximum} von {profile.maximum_product}, nach den vorgesehenen "
        f"Maßnahmen {risk.net_maximum} von {profile.maximum_product} und ist damit als "
        f"{risk.net_band} einzustufen."
    )
    if level != risk.net_maximum:
        reasoning += (
            f" Wegen der Schwere möglicher Schäden gilt mindestens die Stufe {risk.net_band}, "
            "auch wenn der Eintritt unwahrscheinlich ist (Mindeststufe des Regelprofils)."
        )
    return result(
        recommendation,
        profile.recommendation_texts[recommendation],
        reasoning,
        risk,
        recommendation == RECOMMENDATION_CONSULTATION,
    )


# ---------------------------------------------------------------------------
# Prefill from the register
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PrefillSuggestion:
    """A suggestion only; it never becomes an answer without confirmation."""

    question: str
    value: bool
    reason: str


def _count(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def prefill_from_activity(
    profile: RuleProfile, activity: Mapping[str, Any]
) -> dict[str, PrefillSuggestion]:
    """Suggest answers from register data (Art. 9/10 data, number of persons, transfers).

    Only explicit ``True`` flags and integer counts are used; anything else is
    ignored rather than reinterpreted.
    """
    special = activity.get("besondere_kategorien") is True
    criminal = activity.get("daten_art10") is True
    count = _count(activity.get("anzahl_betroffene"))
    large = count is not None and count >= profile.large_scale_threshold
    known = set(profile.question_keys)
    suggestions: dict[str, PrefillSuggestion] = {}

    def add(key: str, value: bool, reason: str) -> None:
        """Record a suggestion if the profile knows the question."""
        if key in known:
            suggestions[key] = PrefillSuggestion(key, value, reason)

    if special or criminal:
        source = "Artikel 9" if special else "Artikel 10"
        add(
            "edsa_04_sensible_daten",
            True,
            f"Das Verarbeitungsverzeichnis weist Daten nach {source} DSGVO aus.",
        )
        if large and count is not None:
            add(
                "art35_3_b",
                True,
                f"Das Verzeichnis weist Daten nach {source} DSGVO und {_number(count)} "
                "betroffene Personen aus; das spricht für eine umfangreiche Verarbeitung.",
            )
    if large and count is not None:
        add(
            "edsa_05_umfang",
            True,
            f"Das Verzeichnis nennt {_number(count)} betroffene Personen und erreicht damit "
            f"den Anhaltswert von {_number(profile.large_scale_threshold)} oder liegt darüber.",
        )
    if activity.get("drittlandtransfer") is True:
        add(
            "edsa_06_abgleich",
            False,
            "Das Verzeichnis weist eine Übermittlung in ein Drittland aus. Das ist für sich "
            "kein Kriterium der Liste, erhöht aber das Risiko und ist bei den Szenarien zu "
            "berücksichtigen (Kapitel V DSGVO).",
        )
    return suggestions
