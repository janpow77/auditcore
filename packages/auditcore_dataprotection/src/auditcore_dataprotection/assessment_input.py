"""Input handling of DPIA edits: omitted fields, change detection, review reset.

``UNSET`` marks an omitted keyword argument of
:meth:`~auditcore_dataprotection.assessment.AssessmentService.update`, so that
an explicitly given empty value still counts as a change.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from .answers import Answer, Scenario, parse_answers, parse_scenarios
from .calculation import finalize_consultation
from .edpb import parse_action_plan, parse_dossier, parse_measure_status, reject_edpb_fields
from .errors import ConflictError, ValidationError
from .model import Assessment, AssessmentStatus
from .rules import RECOMMENDATION_INCOMPLETE, RuleProfile

#: Sentinel for omitted keyword arguments. Typed ``Any`` so it can be the default
#: of parameters of any type (``answers: Mapping[str, Any] = UNSET``).
UNSET: Any = object()


def texts(current: Assessment, **values: object) -> dict[str, str]:
    """New free-text fields; omitted ones keep the stored value."""
    result = {}
    for name, value in values.items():
        if value is UNSET:
            result[name] = getattr(current, name)
        elif not isinstance(value, str):
            raise ValidationError(f"'{name}' muss Text sein.")
        else:
            result[name] = value.strip()
    return result


def documentation(assessment: Assessment) -> dict[str, Any]:
    """Schema 2 documentation in comparable form."""
    return {
        "dossier": dict(assessment.dossier),
        "measure_status": {k: dict(v) for k, v in assessment.measure_status.items()},
        "action_plan": tuple(dict(item) for item in assessment.action_plan),
    }


def updated_documentation(
    current: Assessment, rules: RuleProfile, given: Mapping[str, Any]
) -> dict[str, Any]:
    """Stored documentation with the given sections replaced (schema 2 only).

    Schema 1 profiles refuse stored and given EDPB documentation instead of
    ignoring it.
    """
    result = documentation(current)
    if not rules.edpb:
        reject_edpb_fields(
            {
                **{k: v for k, v in result.items() if v},
                **{k: v for k, v in given.items() if v is not UNSET},
            },
            rules,
        )
        return result
    if given["dossier"] is not UNSET:
        result["dossier"] = parse_dossier(given["dossier"], rules)
    if given["measure_status"] is not UNSET:
        result["measure_status"] = parse_measure_status(given["measure_status"], rules)
    if given["action_plan"] is not UNSET:
        result["action_plan"] = parse_action_plan(given["action_plan"], rules)
    return result


def changed(
    current: Assessment,
    answers: Mapping[str, Answer],
    scenarios: tuple[Scenario, ...],
    new_texts: Mapping[str, str],
    rules: RuleProfile,
    activity: Mapping[str, object],
    new_documentation: Mapping[str, object] | None = None,
) -> bool:
    """True if content, profile or the activity snapshot differ from the stored version."""
    stored_profile = {
        "id": current.profile_id,
        "version": current.profile_version,
        "fingerprint": current.profile_fingerprint,
    }
    return (
        dict(answers) != dict(current.answers)
        or scenarios != current.scenarios
        or any(new_texts[name] != getattr(current, name) for name in new_texts)
        or rules.reference != stored_profile
        or dict(activity) != dict(current.activity_snapshot)
        or any(
            value != documentation(current)[name]
            for name, value in (new_documentation or {}).items()
        )
    )


def without_review(assessment: Assessment) -> Assessment:
    """Remove decision, DPO involvement and consultation after a substantive change."""
    return replace(
        assessment,
        status=AssessmentStatus.DRAFT,
        decision=None,
        deviation=False,
        deviation_justification=None,
        decided_by=None,
        decided_at=None,
        dpo_vote=None,
        dpo_statement=None,
        dpo_by=None,
        dpo_at=None,
        dpo_conclusion=None,
        dpo_conclusion_by=None,
        leadership_presented_to=None,
        leadership_presented_at=None,
        consultation=None,
        conditions=(),
        dpo_requested_from=None,
        dpo_requested_on=None,
        dpo_requested_by=None,
        dpo_requested_at=None,
    )


def refuse_downgrade(stored: RuleProfile, target: RuleProfile) -> None:
    """A schema 2 assessment cannot continue under a schema 1 profile.

    Its master data, implementation status and scenario fields would be lost
    or could no longer be edited; switching back is refused explicitly.
    """
    if stored.edpb and not target.edpb:
        raise ValidationError(
            f"Die Folgenabschätzung wurde nach Profil {stored.id} {stored.version} "
            "(EDSA-Vorlage) erstellt. Ein Wechsel auf ein Profil nach Schema 1 "
            f"({target.id} {target.version}) ist nicht möglich, weil Angaben zur Vorlage "
            "verloren gingen."
        )


def validated_conditions(
    conditions: Sequence[str], decision: str, rules: RuleProfile
) -> tuple[str, ...]:
    """Conditions of a conditional approval; required only in blocking mode."""
    items = condition_items(conditions, decision, rules)
    if decision in rules.conditions_required_for and not items and not rules.documentation_mode:
        raise ValidationError(
            "Eine Freigabe mit Auflagen braucht mindestens eine Bedingung, die vor Beginn "
            "der Verarbeitung zu erfüllen ist (EDSA-Vorlage 2026, Abschnitt 6)."
        )
    return items


def condition_items(
    conditions: Sequence[str], decision: str, rules: RuleProfile
) -> tuple[str, ...]:
    """Conditions of a conditional approval (EDPB template, section 6)."""
    if isinstance(conditions, str) or not isinstance(conditions, Sequence):
        raise ValidationError("Bedingungen sind als Liste von Texten anzugeben.")
    items = []
    for item in conditions:
        if not isinstance(item, str):
            raise ValidationError("Jede Bedingung muss Text sein.")
        if item.strip():
            items.append(item.strip())
    if items and not rules.edpb:
        raise ValidationError("Bedingungen kennt nur ein Profil nach der EDSA-Vorlage.")
    if items and decision not in rules.conditions_required_for:
        raise ValidationError(f"Zur Entscheidung '{decision}' werden keine Bedingungen erfasst.")
    return tuple(items)


def survey(
    current: Assessment,
    rules: RuleProfile,
    answers: Mapping[str, object],
    scenarios: Sequence[object],
    profile_changed: bool,
) -> tuple[Mapping[str, Answer], tuple[Scenario, ...]]:
    """Answers and scenarios after an edit, validated against the target profile.

    Stored answers are revalidated when only the profile changes; stored
    scenarios are always revalidated.
    """
    new_answers: Mapping[str, Answer] = (
        current.answers if answers is UNSET else parse_answers(answers, rules)
    )
    if profile_changed and answers is UNSET:
        new_answers = parse_answers(dict(current.answers), rules)
    new_scenarios = (
        parse_scenarios([s.to_dict() for s in current.scenarios], rules)
        if scenarios is UNSET
        else parse_scenarios(scenarios, rules)
    )
    return new_answers, new_scenarios


def refuse_open_issues(current: Assessment, rules: RuleProfile) -> None:
    """DP-C21: the final assessment requires a survey without blocking issues."""
    if rules.consultation_notice is None or rules.documentation_mode:
        return
    open_issues = [
        str(i.get("message")) for i in current.proposal.get("issues") or () if i.get("blocking")
    ]
    if open_issues:
        # DP-C21: the final assessment, and with it the final consultation
        # notice, requires a complete survey without blocking issues.
        raise ConflictError(
            "Die Bewertung ist noch nicht abschließend; vor der Entscheidung sind "
            "die blockierenden Prüfhinweise zu erledigen: " + " ".join(open_issues)
        )


def checked_justification(justification: object, deviation: bool, rules: RuleProfile) -> str:
    """Stripped justification; a deviation needs a substantive one in blocking mode."""
    if not isinstance(justification, str):
        raise ValidationError("Die Begründung muss Text sein.")
    if (
        deviation
        and len(justification.strip()) < rules.min_justification_length
        and not rules.documentation_mode
    ):
        raise ValidationError(
            "Wer vom Vorschlag abweicht, muss das begründen. Die Begründung muss "
            f"mindestens {rules.min_justification_length} Zeichen umfassen und "
            "nachvollziehbar darlegen, warum die Einschätzung des Systems hier "
            "nicht trägt (Art. 5 Abs. 2 DSGVO)."
        )
    return justification.strip()


@dataclass(frozen=True)
class SurveyEdit:
    """New survey content of an update: answers, scenarios, texts and documentation."""

    answers: Mapping[str, Answer]
    scenarios: tuple[Scenario, ...]
    texts: Mapping[str, str]
    documentation: Mapping[str, Any]

    def substantive(
        self, current: Assessment, rules: RuleProfile, activity: Mapping[str, object]
    ) -> bool:
        """True if the edit changes the assessment itself.

        Implementation status and action plan document how the assessment is
        carried out; they do not change the assessment and keep the decision
        and the DPO statement (decision of 23.09.2026).
        """
        return changed(
            current,
            self.answers,
            self.scenarios,
            self.texts,
            rules,
            activity,
            {"dossier": self.documentation["dossier"]},
        )

    def fields(self) -> dict[str, Any]:
        """Assessment fields of the edit."""
        return {
            "answers": dict(self.answers),
            "scenarios": self.scenarios,
            "necessity": self.texts["necessity"],
            "proportionality": self.texts["proportionality"],
            "data_subject_view": self.texts["data_subject_view"],
            "dossier": self.documentation["dossier"],
            "measure_status": self.documentation["measure_status"],
            "action_plan": self.documentation["action_plan"],
        }


def keep_final_notice(
    updated: Assessment, rules: RuleProfile, proposal: Mapping[str, Any]
) -> Assessment:
    """DP-C21: unchanged content keeps the final consultation notice of the decision."""
    if (
        updated.decision is not None
        and rules.consultation_notice is not None
        and proposal.get("recommendation") != RECOMMENDATION_INCOMPLETE
    ):
        return replace(updated, proposal=finalize_consultation(rules, proposal, updated.decision))
    return updated


@dataclass(frozen=True)
class CheckedDecision:
    """Validated parts of a decision."""

    conditions: tuple[str, ...]
    deviation: bool
    justification: str
    complete: bool


def check_decision(
    current: Assessment,
    rules: RuleProfile,
    decision: str,
    conditions: Sequence[str],
    justification: object,
) -> CheckedDecision:
    """Validate a decision on the proposal in the order of the checks."""
    recommendation = current.proposal.get("recommendation")
    complete = recommendation not in (None, RECOMMENDATION_INCOMPLETE)
    if not complete and not rules.documentation_mode:
        raise ConflictError(
            "Die Erhebung ist unvollständig; über den Vorschlag kann erst nach vollständiger "
            "Schwellwertanalyse und Risikobetrachtung entschieden werden."
        )
    if decision not in rules.decisions:
        raise ValidationError(
            f"Unbekannte Entscheidung '{decision}'. Zulässig sind: {', '.join(rules.decisions)}."
        )
    condition_list = validated_conditions(conditions, decision, rules)
    refuse_open_issues(current, rules)
    deviation = decision != recommendation
    reason = checked_justification(justification, deviation, rules)
    return CheckedDecision(condition_list, deviation, reason, complete)
