"""DPIA workflow: create from an activity version, edit, decide, involve the DPO, release.

Transitions (status values shared with the source application)::

    entwurf ──DSB-Stellungnahme──▶ dsb_beteiligung ──Freigabe──▶ freigegeben ──▶ abgeloest
       ▲                                  │
       └──── inhaltliche Änderung ────────┘   (Entscheidung und Stellungnahme entfallen)

Every operation checks the authorizer port and the tenant, compares the
revision that was read, records an audit event and never changes a released
version. A release requires a person who neither edited the version nor gave
the DPO statement. Corrections compared with the source application are
listed in ``docs/behavior-changes.md``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from .assessment_checks import HIGH_RESIDUAL_RISK, check_release_actor, release_checks
from .assessment_core import ProfileResolver, refuse_second_open_version
from .assessment_input import (
    UNSET,
    changed,
    checked_justification,
    refuse_downgrade,
    refuse_open_issues,
    survey,
    texts,
    updated_documentation,
    validated_conditions,
    without_review,
)
from .assessment_involvement import AssessmentInvolvement
from .assessment_review import AssessmentReview
from .calculation import finalize_consultation, propose
from .edpb import edpb_hints
from .errors import ConflictError, ValidationError
from .model import DEFAULT_REGISTER, Actor, Assessment, AssessmentStatus, Permission
from .register_content import find_activity
from .rules import RECOMMENDATION_INCOMPLETE, RuleProfile

__all__ = ["HIGH_RESIDUAL_RISK", "UNSET", "AssessmentService", "ProfileResolver"]


@dataclass
class AssessmentService(AssessmentInvolvement, AssessmentReview):
    """Operations on DPIAs of one register; persistence and identity via ports.

    ``require_consultation_record``: when the proposal recommends consulting
    the supervisory authority, a release requires the documented consultation
    (framework requirement ``release_dsfa``). The source application released
    without it; it can be disabled explicitly by a consumer that decided
    otherwise. With profiles that define ``consultation_notice`` (2026.10.2,
    DP-C21, user decision A5 of 2026-09-23) the notice only becomes final with
    the decision on a complete assessment and only if the net risk is still
    high (Art. 36 Abs. 1 DSGVO, Erwägungsgrund 94 DSGVO).
    """

    # -------------------------------------------------------------- create

    def start(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        profile: RuleProfile,
        *,
        register_id: str = DEFAULT_REGISTER,
    ) -> Assessment:
        """Create the next version for an activity of the effective register version."""
        self._allow(actor, Permission.ASSESSMENT_EDIT, tenant_id)
        activity, register = find_activity(self._effective(tenant_id, register_id), activity_id)
        existing = self.versions(tenant_id, actor, activity_id, register_id)
        refuse_second_open_version(existing)
        now = self.clock.now()
        proposal = propose(profile, {}, ())
        created = Assessment(
            tenant_id=tenant_id,
            assessment_id=self.ids.new_id("assessment"),
            register_id=register_id,
            activity_id=activity_id,
            activity_name=str(activity.get("name") or "")[:255],
            version=(existing[0].version + 1) if existing else 1,
            status=AssessmentStatus.DRAFT,
            profile_id=profile.id,
            profile_version=profile.version,
            profile_fingerprint=profile.fingerprint,
            register_version=register.version,
            activity_snapshot=dict(activity),
            answers={},
            scenarios=(),
            proposal=proposal.to_dict(),
            created_by=actor.id,
            created_at=now,
            updated_at=now,
            editors=(actor.id,),
            predecessor_id=existing[0].assessment_id if existing else None,
        )
        self.assessments.add(created)
        self._event(actor, "assessment.created", created)
        return created

    # ---------------------------------------------------------------- edit

    def update(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        expected_revision: int,
        answers: Mapping[str, object] = UNSET,
        scenarios: Sequence[object] = UNSET,
        necessity: str = UNSET,
        proportionality: str = UNSET,
        data_subject_view: str = UNSET,
        profile: RuleProfile = UNSET,
        dossier: Mapping[str, object] = UNSET,
        measure_status: Mapping[str, object] = UNSET,
        action_plan: Sequence[object] = UNSET,
    ) -> Assessment:
        """Change the survey; the proposal is recalculated with the current register data.

        Omitted fields keep their value. A substantive change after a decision
        or DPO statement removes both, because they referred to other content.
        ``dossier``, ``measure_status`` and ``action_plan`` (EDPB template
        sections 0.5, 2.3/4.2.a and 4.2.c) require a schema 2 profile.
        """
        self._allow(actor, Permission.ASSESSMENT_EDIT, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current) if profile is UNSET else profile
        refuse_downgrade(self._profile(current), rules)
        new_answers, new_scenarios = survey(
            current, rules, answers, scenarios, profile is not UNSET
        )
        new_texts = texts(
            current,
            necessity=necessity,
            proportionality=proportionality,
            data_subject_view=data_subject_view,
        )
        documentation = updated_documentation(
            current,
            rules,
            {"dossier": dossier, "measure_status": measure_status, "action_plan": action_plan},
        )
        activity, register = find_activity(
            self._effective(tenant_id, current.register_id), current.activity_id
        )
        proposal = propose(rules, new_answers, new_scenarios).to_dict()
        # Implementation status and action plan document how the assessment is
        # carried out; they do not change the assessment itself and keep the
        # decision and the DPO statement (decision of 23.09.2026).
        substantive = changed(
            current,
            new_answers,
            new_scenarios,
            new_texts,
            rules,
            activity,
            {"dossier": documentation["dossier"]},
        )
        reset = substantive and (current.decision is not None or current.dpo_vote is not None)
        updated = replace(
            current,
            answers=dict(new_answers),
            scenarios=new_scenarios,
            proposal=proposal,
            profile_id=rules.id,
            profile_version=rules.version,
            profile_fingerprint=rules.fingerprint,
            activity_snapshot=dict(activity),
            activity_name=str(activity.get("name") or "")[:255],
            register_version=register.version,
            updated_at=self.clock.now(),
            editors=self._with_editor(current, actor),
            revision=current.revision + 1,
            necessity=new_texts["necessity"],
            proportionality=new_texts["proportionality"],
            data_subject_view=new_texts["data_subject_view"],
            dossier=documentation["dossier"],
            measure_status=documentation["measure_status"],
            action_plan=documentation["action_plan"],
        )
        if reset:
            updated = without_review(updated)
        elif (
            updated.decision is not None
            and rules.consultation_notice is not None
            and proposal.get("recommendation") != RECOMMENDATION_INCOMPLETE
        ):
            # DP-C21: unchanged content keeps the final notice of the decision.
            updated = replace(
                updated, proposal=finalize_consultation(rules, proposal, updated.decision)
            )
        self._store(current, updated)
        self._event(actor, "assessment.updated", updated, review_reset=reset)
        return updated

    def decide(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        expected_revision: int,
        decision: str,
        justification: str = "",
        conditions: Sequence[str] = (),
    ) -> Assessment:
        """Adopt the proposal or deviate with a substantive justification.

        Schema 2 profiles also accept ``verworfen`` (the processing is
        abandoned) and require the conditions of a conditional approval
        (EDPB template, section 6).
        """
        self._allow(actor, Permission.ASSESSMENT_DECIDE, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current)
        recommendation = current.proposal.get("recommendation")
        complete = recommendation not in (None, RECOMMENDATION_INCOMPLETE)
        if not complete and not rules.documentation_mode:
            raise ConflictError(
                "Die Erhebung ist unvollständig; über den Vorschlag kann erst nach vollständiger "
                "Schwellwertanalyse und Risikobetrachtung entschieden werden."
            )
        if decision not in rules.decisions:
            raise ValidationError(
                f"Unbekannte Entscheidung '{decision}'. Zulässig sind: "
                f"{', '.join(rules.decisions)}."
            )
        condition_list = validated_conditions(conditions, decision, rules)
        refuse_open_issues(current, rules)
        deviation = decision != recommendation
        reason = checked_justification(justification, deviation, rules)
        proposal = (
            current.proposal
            if rules.consultation_notice is None or not complete
            else finalize_consultation(rules, current.proposal, decision)
        )
        updated = replace(
            current,
            proposal=proposal,
            decision=decision,
            deviation=deviation,
            deviation_justification=reason if deviation else None,
            decided_by=actor.id,
            decided_at=self.clock.now(),
            conditions=condition_list,
            editors=self._with_editor(current, actor),
            updated_at=self.clock.now(),
            revision=current.revision + 1,
        )
        self._store(current, updated)
        notice = proposal.get("consultation_notice") or {}
        self._event(
            actor,
            "assessment.decided",
            updated,
            decision=decision,
            deviation=deviation,
            **({"consultation_notice": notice["status"]} if notice else {}),
            **({"conditions": list(condition_list)} if condition_list else {}),
        )
        return updated

    # ------------------------------------------------------------- release

    def release_blockers(self, assessment: Assessment) -> tuple[str, ...]:
        """All reasons that currently prevent a release, in checking order.

        Profiles in documentation mode never block: see :meth:`open_points`.
        """
        rules = self._profile(assessment)
        if rules.documentation_mode:
            return ()
        return self._checks(assessment, rules)

    def open_points(self, assessment: Assessment) -> tuple[str, ...]:
        """Everything still open: failed checks and, for schema 2, template hints.

        In documentation mode these points are recorded with the release
        instead of preventing it.
        """
        rules = self._profile(assessment)
        points = list(self._checks(assessment, rules))
        if rules.edpb:
            points.extend(edpb_hints(assessment, rules))
        return tuple(points)

    def _checks(self, assessment: Assessment, rules: RuleProfile) -> tuple[str, ...]:
        """Checks of the release in checking order (blocking or documented)."""
        return release_checks(
            assessment, rules, require_consultation_record=self.require_consultation_record
        )

    def hints(self, assessment: Assessment) -> tuple[str, ...]:
        """Non-blocking notes against the EDPB template (schema 2 profiles only)."""
        rules = self._profile(assessment)
        return edpb_hints(assessment, rules) if rules.edpb else ()

    def release(
        self, tenant_id: str, actor: Actor, assessment_id: str, *, expected_revision: int
    ) -> Assessment:
        """Four-eyes release; the version is locked and older releases are superseded."""
        self._allow(actor, Permission.ASSESSMENT_RELEASE, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current)
        blockers = self.release_blockers(current)
        if blockers:
            raise ConflictError(blockers[0])
        open_points = self.open_points(current) if rules.documentation_mode else ()
        check_release_actor(actor, current)
        superseded = [
            a
            for a in self.assessments.list_for_activity(
                tenant_id, current.register_id, current.activity_id
            )
            if a.assessment_id != current.assessment_id and a.status is AssessmentStatus.RELEASED
        ]
        now = self.clock.now()
        released = replace(
            current,
            status=AssessmentStatus.RELEASED,
            released_by=actor.id,
            released_at=now,
            updated_at=now,
            revision=current.revision + 1,
            release_open_points=open_points,
        )
        self._store(current, released)
        for older in superseded:
            self.assessments.mark_superseded(tenant_id, older.assessment_id, older.revision)
        self._event(
            actor,
            "assessment.released",
            released,
            superseded=[a.assessment_id for a in superseded],
            **({"open_points": len(open_points)} if rules.documentation_mode else {}),
        )
        return released
