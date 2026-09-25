"""Release checks of a DPIA version, in checking order.

Every check returns the reasons it finds; :func:`release_checks` concatenates
them in a fixed order. In blocking mode they prevent the release, in
documentation mode they are recorded with it.
"""

from __future__ import annotations

from collections.abc import Callable

from .errors import FourEyesViolation
from .model import Actor, Assessment
from .rules import (
    DECISION_REJECTED,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_SCREENING_ONLY,
    RuleProfile,
)

HIGH_RESIDUAL_RISK = "hohes_restrisiko"
#: Issue codes already covered by the screening and scenario checks.
_COVERED_ISSUES = ("unanswered_questions", "unknown_answers", "risk_assessment_missing")

_Check = Callable[[Assessment, RuleProfile], list[str]]


def _decision(assessment: Assessment, rules: RuleProfile) -> list[str]:
    if assessment.decision:
        return []
    return ["Vor der Freigabe ist über den Vorschlag zu entscheiden."]


def _dpo_involvement(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Blocking mode needs the statement; documentation mode at least the request."""
    if assessment.dpo_at is not None:
        return []
    if not rules.documentation_mode:
        return [
            "Vor der Freigabe ist die oder der Datenschutzbeauftragte zu "
            f"beteiligen ({rules.norm('dsb')})."
        ]
    if assessment.dpo_requested_on is None:
        return [
            "Es ist nicht dokumentiert, dass der Rat der oder des "
            f"Datenschutzbeauftragten eingeholt wurde ({rules.norm('dsb')})."
        ]
    return [
        "Die Stellungnahme der oder des Datenschutzbeauftragten liegt noch nicht "
        f"vor; eingeholt am {assessment.dpo_requested_on} bei "
        f"{assessment.dpo_requested_from}."
    ]


def _documented_deviation(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Documentation mode: a deviation still needs its justification."""
    justification = (assessment.deviation_justification or "").strip()
    if (
        rules.documentation_mode
        and assessment.deviation
        and len(justification) < rules.min_justification_length
    ):
        return [
            "Die Entscheidung weicht vom Vorschlag ab; eine Begründung von mindestens "
            f"{rules.min_justification_length} Zeichen fehlt (Art. 5 Abs. 2 DSGVO)."
        ]
    return []


def _documented_consultation_ground(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Documentation mode: the ground "high residual risk" must match the assessment."""
    consultation = assessment.consultation
    if (
        rules.documentation_mode
        and consultation is not None
        and consultation.ground == HIGH_RESIDUAL_RISK
        and not assessment.proposal.get("consultation_required")
    ):
        return [
            "Als Grund der Konsultation ist ein hohes Restrisiko angegeben, die Bewertung "
            "ergibt aber kein hohes Restrisiko."
        ]
    return []


def _screening_complete(assessment: Assessment, rules: RuleProfile) -> list[str]:
    screening = assessment.proposal.get("screening") or {}
    if screening.get("complete"):
        return []
    return [
        "Die Schwellwertanalyse ist unvollständig; alle Fragen sind mit Ja oder Nein "
        "zu beantworten."
    ]


def _substance(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """After a screening that requires a DPIA: necessity and at least one scenario."""
    if not assessment.decision or assessment.decision == RECOMMENDATION_SCREENING_ONLY:
        return []
    reasons: list[str] = []
    if not assessment.necessity or not assessment.proportionality:
        reasons.append(
            "Vor der Freigabe sind die Notwendigkeit und die Verhältnismäßigkeit der "
            "Verarbeitung in Bezug auf den Zweck zu bewerten "
            f"({rules.norm('notwendigkeit')})."
        )
    if not assessment.scenarios:
        reasons.append(
            "Vor der Freigabe ist mindestens ein Risikoszenario mit den vorgesehenen "
            f"Maßnahmen zu erfassen ({rules.norm('risiko')}, {rules.norm('massnahmen')})."
        )
    return reasons


def _blocking_issues(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Blocking calculation issues not already covered by another check."""
    return [
        str(issue.get("message"))
        for issue in assessment.proposal.get("issues") or ()
        if issue.get("blocking") and issue.get("code") not in _COVERED_ISSUES
    ]


def _consultation_record(assessment: Assessment, rules: RuleProfile) -> list[str]:
    proposal = assessment.proposal
    consult = assessment.decision == RECOMMENDATION_CONSULTATION or (
        bool(proposal.get("consultation_required")) and assessment.decision != DECISION_REJECTED
    )
    if not consult or assessment.consultation is not None:
        return []
    return [
        "Bei verbleibendem hohem Risiko ist vor der Verarbeitung die Aufsichtsbehörde "
        f"zu konsultieren ({rules.norm('konsultation')}); das Ergebnis ist zu "
        "dokumentieren."
    ]


def _dpo_conditions(assessment: Assessment, rules: RuleProfile) -> list[str]:
    if assessment.dpo_vote == "zugestimmt_mit_auflagen" and not assessment.dpo_conclusion:
        return [
            "Die oder der Datenschutzbeauftragte hat mit Auflagen zugestimmt. Vor der "
            "Freigabe ist zu dokumentieren, wie die Auflagen umgesetzt werden."
        ]
    return []


def _dpo_rejection(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Releasing against a rejecting statement needs a reason and the leadership."""
    if assessment.dpo_vote != "abgelehnt" or assessment.decision == DECISION_REJECTED:
        return []
    reasons: list[str] = []
    if len(assessment.dpo_conclusion or "") < rules.min_justification_length:
        reasons.append(
            "Die oder der Datenschutzbeauftragte hat die Abschätzung abgelehnt. Eine "
            "Freigabe ist möglich, aber nur mit einer aktenfesten Begründung von "
            f"mindestens {rules.min_justification_length} Zeichen, warum von der "
            "Stellungnahme abgewichen wird (Art. 5 Abs. 2 DSGVO)."
        )
    if assessment.leadership_presented_at is None:
        reasons.append(
            "Wird von einer ablehnenden Stellungnahme abgewichen, ist die Abschätzung "
            "vor der Freigabe der Behördenleitung vorzulegen; die Verantwortung für die "
            "Verarbeitung liegt bei ihr (Art. 24 DSGVO). Die Vorlage ist zu dokumentieren."
        )
    return reasons


def edpb_blockers(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Release blockers of schema 2 profiles: required master data and conditions."""
    if not rules.edpb:
        return []
    reasons: list[str] = []
    screening_only = assessment.decision == RECOMMENDATION_SCREENING_ONLY
    missing = [
        f.title
        for f in rules.dossier_fields
        if f.required and not screening_only and not assessment.dossier.get(f.key)
    ]
    if missing:
        reasons.append(
            "Vor der Freigabe fehlen Angaben zur Folgenabschätzung: " + "; ".join(missing) + "."
        )
    if assessment.decision in rules.conditions_required_for and not assessment.conditions:
        reasons.append(
            "Die Freigabe mit Auflagen braucht die Bedingungen, die vor Beginn der "
            "Verarbeitung zu erfüllen sind."
        )
    return reasons


def check_release_actor(actor: Actor, current: Assessment) -> None:
    """Four eyes: neither an editor, the decider nor the DPO may release."""
    if actor.id in current.editors or actor.id == current.decided_by:
        raise FourEyesViolation(
            "Vier-Augen-Prinzip verletzt: Die Kennung "
            f"'{actor.id}' hat diese Fassung bearbeitet und darf sie nicht freigeben. "
            "Die Freigabe muss durch eine zweite fachkundige Person erfolgen."
        )
    if actor.id == current.dpo_by:
        raise FourEyesViolation(
            "Die oder der Datenschutzbeauftragte berät und gibt nicht selbst frei "
            "(Art. 38 Abs. 3 und 6 DSGVO)."
        )


_BEFORE_CONSULTATION: tuple[_Check, ...] = (
    _decision,
    _dpo_involvement,
    _documented_deviation,
    _documented_consultation_ground,
    _screening_complete,
    _substance,
    _blocking_issues,
)
_AFTER_CONSULTATION: tuple[_Check, ...] = (_dpo_conditions, _dpo_rejection, edpb_blockers)


def release_checks(
    assessment: Assessment, rules: RuleProfile, *, require_consultation_record: bool
) -> tuple[str, ...]:
    """All failed checks of a release in checking order (blocking or documented)."""
    reasons = [r for check in _BEFORE_CONSULTATION for r in check(assessment, rules)]
    if require_consultation_record:
        reasons.extend(_consultation_record(assessment, rules))
    reasons.extend(r for check in _AFTER_CONSULTATION for r in check(assessment, rules))
    return tuple(reasons)
