"""DSFA calculation: threshold analysis, gross/net risk and a reasoned proposal.

Pure functions over an explicitly selected :class:`~auditcore_dataprotection.rules.RuleProfile`.
Unlike the source application, missing or unknown answers never count as
"no": they keep the result visibly ``unvollstaendig``. Input is validated at
the boundary; unknown keys, non-boolean answers, values outside the scale and
duplicate criteria or measures are rejected instead of being skipped.

The proposal is a recommendation for a human decision. It never releases
anything and always names the profile id, version and fingerprint it used.

The parts live in :mod:`.answers` (input), :mod:`.screening`, :mod:`.risk`,
:mod:`.results` and :mod:`.prefill`; this module combines them and keeps
every name importable from its original place.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .answers import (
    EDPB_SCENARIO_FIELDS,
    Answer,
    AnswerValue,
    Scenario,
    parse_answer_list,
    parse_answers,
    parse_scenarios,
)
from .errors import ValidationError
from .prefill import PrefillSuggestion, prefill_from_activity
from .results import (
    CALCULATION_VERSION,
    Issue,
    Proposal,
    RiskResult,
    ScenarioResult,
    ScreeningResult,
)
from .risk import assess_risk
from .rules import (
    DECISION_REJECTED,
    NOTICE_NONE,
    NOTICE_NOT_REQUIRED,
    NOTICE_PRELIMINARY,
    NOTICE_REQUIRED,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_INCOMPLETE,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_SCREENING_ONLY,
    RuleProfile,
)
from .screening import (
    SCREENING_INCOMPLETE,
    SCREENING_NOT_REQUIRED,
    SCREENING_REQUIRED,
    screen,
)

__all__ = [
    "CALCULATION_VERSION",
    "EDPB_SCENARIO_FIELDS",
    "SCREENING_INCOMPLETE",
    "SCREENING_NOT_REQUIRED",
    "SCREENING_REQUIRED",
    "Answer",
    "AnswerValue",
    "Issue",
    "PrefillSuggestion",
    "Proposal",
    "RiskResult",
    "Scenario",
    "ScenarioResult",
    "ScreeningResult",
    "assess_risk",
    "finalize_consultation",
    "parse_answer_list",
    "parse_answers",
    "parse_scenarios",
    "prefill_from_activity",
    "propose",
    "screen",
]

_INCOMPLETE_SCREENING_TEXT = (
    "Die Schwellwertanalyse ist nicht vollständig. Bevor ein Ergebnis "
    "vorgeschlagen werden kann, sind alle Fragen mit Ja oder Nein zu beantworten."
)


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


def _matrix_assessment(
    profile: RuleProfile, screening: ScreeningResult, risk: RiskResult
) -> tuple[str, dict[str, object], str]:
    """Recommendation, trace step and reasoning from the risk matrix (schema 2)."""
    step: dict[str, object] = {
        "step": "risk",
        "method": risk.method,
        "gross_band": risk.gross_band,
        "net_band": risk.net_band,
        "gross_maximum": risk.gross_maximum,
        "net_maximum": risk.net_maximum,
        "floored": list(risk.floored),
    }
    reasoning = (
        f"{screening.reasoning} Nach der Risikomatrix des Regelprofils liegt das höchste "
        f"Risiko vor Maßnahmen in der Stufe {risk.gross_band}, nach den vorgesehenen "
        f"Maßnahmen in der Stufe {risk.net_band}."
    )
    if risk.floored:
        numbers = ", ".join(str(i) for i in risk.floored)
        reasoning += (
            f" Für Szenario {numbers} gilt wegen der Schwere vor Maßnahmen mindestens "
            "diese Stufe, auch wenn der Eintritt unwahrscheinlich ist oder Maßnahmen die "
            "Schwere mindern (Mindeststufe des Regelprofils)."
        )
    return profile.band_recommendations[risk.net_band], step, reasoning


def _product_assessment(
    profile: RuleProfile, screening: ScreeningResult, risk: RiskResult
) -> tuple[str, dict[str, object], str]:
    """Recommendation, trace step and reasoning from the risk product (schema 1)."""
    step: dict[str, object] = {
        "step": "risk",
        "gross_maximum": risk.gross_maximum,
        "net_maximum": risk.net_maximum,
        "consult_from": profile.consult_from,
        "conditions_from": profile.conditions_from,
    }
    reasoning = (
        f"{screening.reasoning} Das höchste Risiko vor Maßnahmen beträgt "
        f"{risk.gross_maximum} von {profile.maximum_product}, nach den vorgesehenen "
        f"Maßnahmen {risk.net_maximum} von {profile.maximum_product} und ist damit als "
        f"{risk.net_band} einzustufen."
    )
    return _risk_recommendation(profile, risk.net_maximum), step, reasoning


@dataclass
class _ProposalBuilder:
    """Collects issues and trace steps and builds the proposal for one recommendation."""

    profile: RuleProfile
    screening: ScreeningResult
    issues: list[Issue]
    trace: list[Mapping[str, object]]
    consultation_reference: str

    def build(
        self,
        recommendation: str,
        text: str,
        reasoning: str,
        risk: RiskResult | None,
        consultation: bool,
    ) -> Proposal:
        """Build the proposal for one recommendation."""
        self.trace.append({"step": "recommendation", "value": recommendation})
        notice: dict[str, object] | None = None
        rule = self.profile.consultation_notice
        if rule is not None:
            # DP-C21: before the final assessment at most a preliminary notice.
            preliminary = recommendation == RECOMMENDATION_CONSULTATION
            notice = {
                "timing": rule.timing,
                "final": False,
                "status": NOTICE_PRELIMINARY if preliminary else NOTICE_NONE,
                "text": rule.preliminary_text if preliminary else "",
                "legal_basis": rule.legal_basis,
            }
            if preliminary:
                text = rule.preliminary_text
            consultation = False
            self.trace.append({"step": "consultation_notice", "status": notice["status"]})
        return Proposal(
            profile=self.profile.reference,
            regime=self.profile.regime,
            screening=self.screening,
            risk=risk,
            recommendation=recommendation,
            recommendation_text=text,
            reasoning=reasoning,
            consultation_required=consultation,
            consultation_reference=self.consultation_reference,
            issues=tuple(self.issues),
            trace=tuple(self.trace),
            consultation_notice=notice,
        )


def _without_risk_assessment(builder: _ProposalBuilder, risk: RiskResult) -> Proposal:
    """A DPIA is required but no risk scenario has been recorded yet."""
    builder.issues.append(
        Issue(
            "risk_assessment_missing",
            "Die Folgenabschätzung ist durchzuführen, es ist aber noch kein "
            "Risikoszenario erfasst.",
            blocking=True,
        )
    )
    return builder.build(
        RECOMMENDATION_INCOMPLETE,
        "Die Folgenabschätzung ist durchzuführen, es sind aber noch keine "
        "Risikoszenarien erfasst. Ohne Risikobetrachtung lässt sich das "
        f"verbleibende Risiko nicht beurteilen ({builder.profile.norm('risiko')}).",
        builder.screening.reasoning,
        risk,
        False,
    )


def propose(
    profile: RuleProfile,
    answers: Mapping[str, object],
    scenarios: Iterable[object] = (),
) -> Proposal:
    """Combine screening and risk into a reasoned, traceable recommendation."""
    screening = screen(profile, answers)
    builder = _ProposalBuilder(
        profile,
        screening,
        _screening_issues(screening),
        list(screening.trace),
        profile.norm("konsultation"),
    )
    risk = assess_risk(profile, scenarios)
    builder.issues.extend(risk.issues)
    if screening.outcome == SCREENING_NOT_REQUIRED:
        return builder.build(
            RECOMMENDATION_SCREENING_ONLY,
            profile.recommendation_texts[RECOMMENDATION_SCREENING_ONLY],
            screening.reasoning,
            risk if risk.assessed else None,
            False,
        )
    if screening.outcome == SCREENING_INCOMPLETE:
        return builder.build(
            RECOMMENDATION_INCOMPLETE,
            _INCOMPLETE_SCREENING_TEXT,
            screening.reasoning,
            risk if risk.assessed else None,
            False,
        )
    if not risk.assessed:
        return _without_risk_assessment(builder, risk)
    assessment = _matrix_assessment if profile.edpb else _product_assessment
    recommendation, step, reasoning = assessment(profile, screening, risk)
    builder.trace.append(step)
    return builder.build(
        recommendation,
        profile.recommendation_texts[recommendation],
        reasoning,
        risk,
        recommendation == RECOMMENDATION_CONSULTATION,
    )


def finalize_consultation(
    profile: RuleProfile, proposal: Mapping[str, Any], decision: str
) -> dict[str, Any]:
    """Final consultation notice after the final assessment (DP-C21).

    Called with the decision of the controller on a complete proposal. The
    notice is final and says "erforderlich" only if the net risk after
    measures is still high (the proposal recommends the consultation) and the
    processing is not abandoned. Profiles without a ``consultation_notice``
    section return the proposal unchanged.
    """
    rule = profile.consultation_notice
    result = dict(proposal)
    if rule is None:
        return result
    if proposal.get("recommendation") in (None, RECOMMENDATION_INCOMPLETE):
        raise ValidationError(
            "Ein endgültiger Konsultationshinweis setzt eine vollständige Bewertung voraus."
        )
    high = proposal.get("recommendation") == RECOMMENDATION_CONSULTATION
    required = high and decision != DECISION_REJECTED
    if required:
        status, text = NOTICE_REQUIRED, rule.final_text
        result["recommendation_text"] = rule.final_text
    elif high:
        status, text = NOTICE_NOT_REQUIRED, rule.rejected_text
    else:
        status, text = NOTICE_NOT_REQUIRED, rule.not_required_text
    result["consultation_required"] = required
    result["consultation_notice"] = {
        "timing": rule.timing,
        "final": True,
        "status": status,
        "text": text,
        "legal_basis": rule.legal_basis,
        "net_risk_high": high,
        "decision": decision,
    }
    result["trace"] = [
        *(proposal.get("trace") or ()),
        {"step": "consultation_notice", "status": status, "final": True},
    ]
    return result
