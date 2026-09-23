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

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from .calculation import (
    Answer,
    Scenario,
    parse_answers,
    parse_scenarios,
    prefill_from_activity,
    propose,
)
from .edpb import (
    edpb_hints,
    parse_action_plan,
    parse_dossier,
    parse_measure_status,
    reject_edpb_fields,
)
from .errors import (
    AuthorizationError,
    ConflictError,
    FourEyesViolation,
    LockedVersionError,
    NotFoundError,
    ProfileError,
    StaleRevisionError,
    TenantMismatchError,
    ValidationError,
)
from .model import (
    DEFAULT_REGISTER,
    Actor,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    Consultation,
    Permission,
    RegisterVersion,
    ReviewItem,
)
from .ports import AssessmentRepository, AuditSink, Authorizer, Clock, IdFactory, RegisterRepository
from .register import activity_changes, find_activity
from .rules import (
    DECISION_REJECTED,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_INCOMPLETE,
    RECOMMENDATION_SCREENING_ONLY,
    RuleProfile,
    load_profile,
)

UNSET: Any = object()
ProfileResolver = Callable[[str, str], RuleProfile]


def _texts(current: Assessment, **values: Any) -> dict[str, str]:
    """New free-text fields; omitted ones keep the stored value."""
    texts = {}
    for name, value in values.items():
        if value is UNSET:
            texts[name] = getattr(current, name)
        elif not isinstance(value, str):
            raise ValidationError(f"'{name}' muss Text sein.")
        else:
            texts[name] = value.strip()
    return texts


def _changed(
    current: Assessment,
    answers: Mapping[str, Answer],
    scenarios: tuple[Scenario, ...],
    texts: Mapping[str, str],
    rules: RuleProfile,
    activity: Mapping[str, Any],
    documentation: Mapping[str, Any] | None = None,
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
        or any(texts[name] != getattr(current, name) for name in texts)
        or rules.reference != stored_profile
        or dict(activity) != dict(current.activity_snapshot)
        or any(
            value != _documentation(current)[name] for name, value in (documentation or {}).items()
        )
    )


def _documentation(assessment: Assessment) -> dict[str, Any]:
    """Schema 2 documentation in comparable form."""
    return {
        "dossier": dict(assessment.dossier),
        "measure_status": {k: dict(v) for k, v in assessment.measure_status.items()},
        "action_plan": tuple(dict(item) for item in assessment.action_plan),
    }


def _without_review(assessment: Assessment) -> Assessment:
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
    )


HIGH_RESIDUAL_RISK = "hohes_restrisiko"


def _refuse_downgrade(stored: RuleProfile, target: RuleProfile) -> None:
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


def _conditions(conditions: Sequence[str], decision: str, rules: RuleProfile) -> tuple[str, ...]:
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
    if decision in rules.conditions_required_for and not items:
        raise ValidationError(
            "Eine Freigabe mit Auflagen braucht mindestens eine Bedingung, die vor Beginn "
            "der Verarbeitung zu erfüllen ist (EDSA-Vorlage 2026, Abschnitt 6)."
        )
    if items and decision not in rules.conditions_required_for:
        raise ValidationError(f"Zur Entscheidung '{decision}' werden keine Bedingungen erfasst.")
    return tuple(items)


def _edpb_blockers(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Release blockers of schema 2 profiles: required master data and conditions."""
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


@dataclass
class AssessmentService:
    """Operations on DPIAs of one register; persistence and identity via ports.

    ``require_consultation_record``: when the proposal recommends consulting
    the supervisory authority, a release requires the documented consultation
    (framework requirement ``release_dsfa``). The source application released
    without it; this is marked ``HUMAN_DECISION_REQUIRED`` in the docs and can
    be disabled explicitly by a consumer that decided otherwise.
    """

    assessments: AssessmentRepository
    registers: RegisterRepository
    authorizer: Authorizer
    audit: AuditSink
    clock: Clock
    ids: IdFactory
    resolve_profile: ProfileResolver = load_profile
    require_consultation_record: bool = True

    # ------------------------------------------------------------ helpers

    def _allow(self, actor: Actor, permission: Permission, tenant_id: str) -> None:
        if not isinstance(actor, Actor) or not actor.id:
            raise AuthorizationError("Ohne zugeordnete Person ist keine Bearbeitung möglich.")
        if not self.authorizer.authorize(actor, permission, tenant_id):
            raise AuthorizationError(f"Keine Berechtigung für {permission.value}.")

    def _profile(self, assessment: Assessment) -> RuleProfile:
        profile = self.resolve_profile(assessment.profile_id, assessment.profile_version)
        if profile.fingerprint != assessment.profile_fingerprint:
            raise ProfileError(
                f"Profil {assessment.profile_id} {assessment.profile_version} weicht vom bei der "
                "Bewertung verwendeten Stand ab (Fingerprint). Die Berechnung wird nicht "
                "mit geänderten Regeln fortgeführt."
            )
        return profile

    def _load(self, tenant_id: str, assessment_id: str) -> Assessment:
        found = self.assessments.get(tenant_id, assessment_id)
        if found is None:
            raise NotFoundError(f"Datenschutz-Folgenabschätzung {assessment_id} nicht gefunden")
        if found.tenant_id != tenant_id:
            raise TenantMismatchError("Die Folgenabschätzung gehört zu einem anderen Mandanten.")
        return found

    def _open(self, tenant_id: str, assessment_id: str, expected_revision: int) -> Assessment:
        assessment = self._load(tenant_id, assessment_id)
        if assessment.locked:
            raise LockedVersionError(
                f"Fassung {assessment.version} ist freigegeben und gesperrt. Für eine "
                "Änderung ist eine neue Fassung anzulegen; die freigegebene Fassung "
                "bleibt als Nachweis erhalten."
            )
        if assessment.revision != expected_revision:
            raise StaleRevisionError(
                f"Die Fassung wurde inzwischen geändert (Revision {assessment.revision}). "
                "Bitte neu laden."
            )
        return assessment

    def _effective(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        for version in (
            self.registers.get_released(tenant_id, register_id),
            self.registers.get_draft(tenant_id, register_id),
        ):
            if version is not None:
                if version.tenant_id != tenant_id:
                    raise TenantMismatchError("Das Verzeichnis gehört zu einem anderen Mandanten.")
                return version
        return None

    def _event(self, actor: Actor, action: str, assessment: Assessment, **details: Any) -> None:
        self.audit.record(
            AuditEvent(
                tenant_id=assessment.tenant_id,
                actor_id=actor.id,
                action=action,
                entity="assessment",
                entity_id=assessment.assessment_id,
                version=assessment.version,
                at=self.clock.now(),
                details={
                    "activity_id": assessment.activity_id,
                    "status": assessment.status.value,
                    "recommendation": assessment.proposal.get("recommendation"),
                    **details,
                },
            )
        )

    def _store(self, before: Assessment, after: Assessment) -> Assessment:
        self.assessments.replace(after, before.revision)
        return after

    @staticmethod
    def _with_editor(assessment: Assessment, actor: Actor) -> tuple[str, ...]:
        if actor.id in assessment.editors:
            return assessment.editors
        return (*assessment.editors, actor.id)

    # ------------------------------------------------------------- reading

    def get(self, tenant_id: str, actor: Actor, assessment_id: str) -> Assessment:
        """Return one assessment of the tenant or raise NotFoundError."""
        self._allow(actor, Permission.ASSESSMENT_READ, tenant_id)
        return self._load(tenant_id, assessment_id)

    def versions(
        self, tenant_id: str, actor: Actor, activity_id: str, register_id: str = DEFAULT_REGISTER
    ) -> tuple[Assessment, ...]:
        """All versions of an activity's assessments, newest first."""
        self._allow(actor, Permission.ASSESSMENT_READ, tenant_id)
        found = self.assessments.list_for_activity(tenant_id, register_id, activity_id)
        if any(a.tenant_id != tenant_id for a in found):
            raise TenantMismatchError("Repository lieferte Fassungen eines anderen Mandanten.")
        return tuple(sorted(found, key=lambda a: a.version, reverse=True))

    def open_version(
        self, tenant_id: str, actor: Actor, activity_id: str, register_id: str = DEFAULT_REGISTER
    ) -> Assessment | None:
        """The not yet released version of an activity, if any."""
        for assessment in self.versions(tenant_id, actor, activity_id, register_id):
            if not assessment.locked:
                return assessment
        return None

    def prefill(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        profile: RuleProfile,
        register_id: str = DEFAULT_REGISTER,
    ) -> dict[str, Any]:
        """Suggestions from the register; never stored as answers automatically."""
        self._allow(actor, Permission.ASSESSMENT_READ, tenant_id)
        activity, _ = find_activity(self._effective(tenant_id, register_id), activity_id)
        return {
            key: {"ja": s.value, "grund": s.reason}
            for key, s in prefill_from_activity(profile, activity).items()
        }

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
        open_ = [a for a in existing if not a.locked]
        if open_:
            raise ConflictError(
                f"Zu dieser Tätigkeit ist bereits Fassung {open_[0].version} in Bearbeitung."
            )
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
        answers: Mapping[str, Any] = UNSET,
        scenarios: Sequence[Any] = UNSET,
        necessity: str = UNSET,
        proportionality: str = UNSET,
        data_subject_view: str = UNSET,
        profile: RuleProfile = UNSET,
        dossier: Mapping[str, Any] = UNSET,
        measure_status: Mapping[str, Any] = UNSET,
        action_plan: Sequence[Any] = UNSET,
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
        _refuse_downgrade(self._profile(current), rules)
        new_answers: Mapping[str, Answer] = (
            current.answers if answers is UNSET else parse_answers(answers, rules)
        )
        if profile is not UNSET and answers is UNSET:
            new_answers = parse_answers(dict(current.answers), rules)
        new_scenarios: tuple[Scenario, ...] = (
            parse_scenarios([s.to_dict() for s in current.scenarios], rules)
            if scenarios is UNSET
            else parse_scenarios(scenarios, rules)
        )
        texts = _texts(
            current,
            necessity=necessity,
            proportionality=proportionality,
            data_subject_view=data_subject_view,
        )
        documentation = _documentation(current)
        given = {"dossier": dossier, "measure_status": measure_status, "action_plan": action_plan}
        if not rules.edpb:
            reject_edpb_fields(
                {
                    **{k: v for k, v in documentation.items() if v},
                    **{k: v for k, v in given.items() if v is not UNSET},
                },
                rules,
            )
        else:
            if dossier is not UNSET:
                documentation["dossier"] = parse_dossier(dossier, rules)
            if measure_status is not UNSET:
                documentation["measure_status"] = parse_measure_status(measure_status, rules)
            if action_plan is not UNSET:
                documentation["action_plan"] = parse_action_plan(action_plan, rules)
        activity, register = find_activity(
            self._effective(tenant_id, current.register_id), current.activity_id
        )
        proposal = propose(rules, new_answers, new_scenarios).to_dict()
        # Implementation status and action plan document how the assessment is
        # carried out; they do not change the assessment itself and keep the
        # decision and the DPO statement (decision of 23.09.2026).
        substantive = _changed(
            current,
            new_answers,
            new_scenarios,
            texts,
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
            necessity=texts["necessity"],
            proportionality=texts["proportionality"],
            data_subject_view=texts["data_subject_view"],
            dossier=documentation["dossier"],
            measure_status=documentation["measure_status"],
            action_plan=documentation["action_plan"],
        )
        if reset:
            updated = _without_review(updated)
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
        if recommendation in (None, RECOMMENDATION_INCOMPLETE):
            raise ConflictError(
                "Die Erhebung ist unvollständig; über den Vorschlag kann erst nach vollständiger "
                "Schwellwertanalyse und Risikobetrachtung entschieden werden."
            )
        if decision not in rules.decisions:
            raise ValidationError(
                f"Unbekannte Entscheidung '{decision}'. Zulässig sind: "
                f"{', '.join(rules.decisions)}."
            )
        condition_list = _conditions(conditions, decision, rules)
        if not isinstance(justification, str):
            raise ValidationError("Die Begründung muss Text sein.")
        deviation = decision != recommendation
        if deviation and len(justification.strip()) < rules.min_justification_length:
            raise ValidationError(
                "Wer vom Vorschlag abweicht, muss das begründen. Die Begründung muss "
                f"mindestens {rules.min_justification_length} Zeichen umfassen und "
                "nachvollziehbar darlegen, warum die Einschätzung des Systems hier "
                "nicht trägt (Art. 5 Abs. 2 DSGVO)."
            )
        updated = replace(
            current,
            decision=decision,
            deviation=deviation,
            deviation_justification=justification.strip() if deviation else None,
            decided_by=actor.id,
            decided_at=self.clock.now(),
            conditions=condition_list,
            editors=self._with_editor(current, actor),
            updated_at=self.clock.now(),
            revision=current.revision + 1,
        )
        self._store(current, updated)
        self._event(
            actor,
            "assessment.decided",
            updated,
            decision=decision,
            deviation=deviation,
            **({"conditions": list(condition_list)} if condition_list else {}),
        )
        return updated

    def record_dpo_statement(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        expected_revision: int,
        vote: str,
        statement: str,
    ) -> Assessment:
        """Statement of the data protection officer (Art. 35 Abs. 2 DSGVO), attributed."""
        self._allow(actor, Permission.ASSESSMENT_DPO_STATEMENT, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current)
        if vote not in rules.dpo_votes:
            raise ValidationError(
                f"Unbekanntes Votum '{vote}'. Zulässig sind: {', '.join(rules.dpo_votes)}."
            )
        if not isinstance(statement, str) or not statement.strip():
            raise ValidationError(
                "Die Stellungnahme der oder des Datenschutzbeauftragten ist zu "
                f"dokumentieren ({rules.norm('dsb')})."
            )
        now = self.clock.now()
        updated = replace(
            current,
            dpo_vote=vote,
            dpo_statement=statement.strip(),
            dpo_by=actor.id,
            dpo_at=now,
            dpo_conclusion=None,
            dpo_conclusion_by=None,
            leadership_presented_to=None,
            leadership_presented_at=None,
            status=AssessmentStatus.DPO_INVOLVED,
            updated_at=now,
            revision=current.revision + 1,
        )
        self._store(current, updated)
        self._event(actor, "assessment.dpo_statement", updated, vote=vote)
        return updated

    def record_dpo_conclusion(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        expected_revision: int,
        conclusion: str,
        presented_to_leadership: str | None = None,
    ) -> Assessment:
        """What follows from the statement; after a rejection with leadership submission."""
        self._allow(actor, Permission.ASSESSMENT_EDIT, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current)
        if current.dpo_at is None:
            raise ConflictError(
                "Es liegt noch keine Stellungnahme vor, auf die sich eine Folgerung "
                f"beziehen könnte ({rules.norm('dsb')})."
            )
        text = (conclusion or "").strip() if isinstance(conclusion, str) else ""
        if not text:
            raise ValidationError("Die Folgerung aus der Stellungnahme ist anzugeben.")
        if current.dpo_vote == "abgelehnt" and len(text) < rules.min_justification_length:
            raise ValidationError(
                "Wird von einer ablehnenden Stellungnahme abgewichen, ist das mit "
                f"mindestens {rules.min_justification_length} Zeichen zu begründen."
            )
        presented_to = current.leadership_presented_to
        presented_at = current.leadership_presented_at
        if presented_to_leadership is not None:
            if not isinstance(presented_to_leadership, str):
                raise ValidationError("Die Vorlage bei der Leitung ist als Text anzugeben.")
            if presented_to_leadership.strip():
                presented_to = presented_to_leadership.strip()
                presented_at = self.clock.now()
        updated = replace(
            current,
            dpo_conclusion=text,
            dpo_conclusion_by=actor.id,
            leadership_presented_to=presented_to,
            leadership_presented_at=presented_at,
            editors=self._with_editor(current, actor),
            updated_at=self.clock.now(),
            revision=current.revision + 1,
        )
        self._store(current, updated)
        self._event(
            actor, "assessment.dpo_conclusion", updated, leadership=presented_to is not None
        )
        return updated

    def record_consultation(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        expected_revision: int,
        authority: str,
        result: str,
        consulted_on: date,
        ground: str | None = None,
    ) -> Assessment:
        """Result of the prior consultation of the supervisory authority.

        Schema 2 profiles require the ground, for example high residual risk
        (Art. 36 Abs. 1) or a national law (Art. 36 Abs. 5 DSGVO).
        """
        self._allow(actor, Permission.ASSESSMENT_EDIT, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current)
        if rules.edpb and (not isinstance(ground, str) or ground not in rules.consultation_grounds):
            raise ValidationError(
                "Der Grund der Konsultation ist anzugeben. Zulässig sind: "
                f"{', '.join(rules.consultation_grounds)}."
            )
        if (
            rules.edpb
            and ground == HIGH_RESIDUAL_RISK
            and not current.proposal.get("consultation_required")
        ):
            raise ValidationError(
                "Nach der Bewertung verbleibt kein hohes Restrisiko. Eine Konsultation aus "
                "diesem Grund passt nicht zum Stand der Abschätzung; in Betracht kommt eine "
                "Konsultation aufgrund nationalen Rechts."
            )
        if not rules.edpb and ground is not None:
            raise ValidationError(
                "Einen Grund der Konsultation kennt nur ein Profil nach der EDSA-Vorlage."
            )
        if not isinstance(authority, str) or not authority.strip():
            raise ValidationError("Die konsultierte Aufsichtsbehörde ist anzugeben.")
        if not isinstance(result, str) or not result.strip():
            raise ValidationError("Das Ergebnis der Konsultation ist anzugeben.")
        if not isinstance(consulted_on, date):
            raise ValidationError("Das Datum der Konsultation ist als Datum anzugeben.")
        updated = replace(
            current,
            consultation=Consultation(
                authority=authority.strip(),
                result=result.strip(),
                consulted_on=consulted_on.isoformat(),
                recorded_by=actor.id,
                recorded_at=self.clock.now(),
                ground=ground,
            ),
            editors=self._with_editor(current, actor),
            updated_at=self.clock.now(),
            revision=current.revision + 1,
        )
        self._store(current, updated)
        self._event(
            actor, "assessment.consultation", updated, **({"ground": ground} if ground else {})
        )
        return updated

    # ------------------------------------------------------------- release

    def release_blockers(self, assessment: Assessment) -> tuple[str, ...]:
        """All reasons that currently prevent a release, in checking order."""
        rules = self._profile(assessment)
        reasons: list[str] = []
        proposal = assessment.proposal
        screening = proposal.get("screening") or {}
        if not assessment.decision:
            reasons.append("Vor der Freigabe ist über den Vorschlag zu entscheiden.")
        if assessment.dpo_at is None:
            reasons.append(
                "Vor der Freigabe ist die oder der Datenschutzbeauftragte zu "
                f"beteiligen ({rules.norm('dsb')})."
            )
        if not screening.get("complete"):
            reasons.append(
                "Die Schwellwertanalyse ist unvollständig; alle Fragen sind mit Ja oder Nein "
                "zu beantworten."
            )
        if assessment.decision and assessment.decision != RECOMMENDATION_SCREENING_ONLY:
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
        for issue in proposal.get("issues") or ():
            if issue.get("blocking") and issue.get("code") not in (
                "unanswered_questions",
                "unknown_answers",
                "risk_assessment_missing",
            ):
                reasons.append(str(issue.get("message")))
        consult = assessment.decision == RECOMMENDATION_CONSULTATION or (
            bool(proposal.get("consultation_required")) and assessment.decision != DECISION_REJECTED
        )
        if self.require_consultation_record and consult and assessment.consultation is None:
            reasons.append(
                "Bei verbleibendem hohem Risiko ist vor der Verarbeitung die Aufsichtsbehörde "
                f"zu konsultieren ({rules.norm('konsultation')}); das Ergebnis ist zu "
                "dokumentieren."
            )
        if assessment.dpo_vote == "zugestimmt_mit_auflagen" and not assessment.dpo_conclusion:
            reasons.append(
                "Die oder der Datenschutzbeauftragte hat mit Auflagen zugestimmt. Vor der "
                "Freigabe ist zu dokumentieren, wie die Auflagen umgesetzt werden."
            )
        if assessment.dpo_vote == "abgelehnt" and assessment.decision != DECISION_REJECTED:
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
        if rules.edpb:
            reasons.extend(_edpb_blockers(assessment, rules))
        return tuple(reasons)

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
        blockers = self.release_blockers(current)
        if blockers:
            raise ConflictError(blockers[0])
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
        )
        self._store(current, released)
        for older in superseded:
            self.assessments.mark_superseded(tenant_id, older.assessment_id, older.revision)
        self._event(
            actor, "assessment.released", released, superseded=[a.assessment_id for a in superseded]
        )
        return released

    # --------------------------------------------------------------- review

    def review_required(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> tuple[ReviewItem, ...]:
        """Released assessments whose activity changed in the effective register version.

        Released versions are only reported, never modified (Art. 35 Abs. 11 DSGVO).
        """
        self._allow(actor, Permission.ASSESSMENT_READ, tenant_id)
        register = self._effective(tenant_id, register_id)
        if register is None:
            return ()
        current = {str(a.get("id")): a for a in register.activities}
        items: list[ReviewItem] = []
        for assessment in self.assessments.list_for_register(tenant_id, register_id):
            if assessment.tenant_id != tenant_id:
                raise TenantMismatchError("Repository lieferte Fassungen eines anderen Mandanten.")
            if assessment.status is not AssessmentStatus.RELEASED:
                continue
            activity = current.get(assessment.activity_id)
            if activity is None:
                items.append(
                    ReviewItem(
                        tenant_id,
                        assessment.assessment_id,
                        assessment.activity_id,
                        assessment.activity_name,
                        assessment.version,
                        register.version,
                        "Die Tätigkeit ist im Verzeichnis nicht mehr enthalten.",
                        (),
                    )
                )
                continue
            changes = activity_changes(
                assessment.activity_snapshot, activity, self._profile(assessment)
            )
            if changes:
                items.append(
                    ReviewItem(
                        tenant_id,
                        assessment.assessment_id,
                        assessment.activity_id,
                        assessment.activity_name,
                        assessment.version,
                        register.version,
                        f"Das Verzeichnis wurde geändert (Fassung {register.version}); "
                        f"{len(changes)} wesentliche Angaben weichen ab.",
                        changes,
                    )
                )
        return tuple(items)

    def reassess(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        profile: RuleProfile | None = None,
    ) -> Assessment:
        """New version from a released one; answers and texts are carried over,
        decision and DPO involvement are not."""
        self._allow(actor, Permission.ASSESSMENT_EDIT, tenant_id)
        previous = self._load(tenant_id, assessment_id)
        if not previous.locked:
            raise ConflictError(
                "Nur eine freigegebene Fassung wird neu bewertet. Eine offene Fassung ist zu "
                "bearbeiten, nicht durch eine Folgefassung zu ersetzen."
            )
        existing = self.versions(tenant_id, actor, previous.activity_id, previous.register_id)
        open_ = [a for a in existing if not a.locked]
        if open_:
            raise ConflictError(
                f"Zu dieser Tätigkeit ist bereits Fassung {open_[0].version} in Bearbeitung."
            )
        rules = profile or self._profile(previous)
        _refuse_downgrade(self._profile(previous), rules)
        activity, register = find_activity(
            self._effective(tenant_id, previous.register_id), previous.activity_id
        )
        answers = parse_answers(dict(previous.answers), rules)
        scenarios = parse_scenarios([s.to_dict() for s in previous.scenarios], rules)
        changes = activity_changes(previous.activity_snapshot, activity, rules)
        now = self.clock.now()
        created = Assessment(
            tenant_id=tenant_id,
            assessment_id=self.ids.new_id("assessment"),
            register_id=previous.register_id,
            activity_id=previous.activity_id,
            activity_name=str(activity.get("name") or "")[:255],
            version=existing[0].version + 1,
            status=AssessmentStatus.DRAFT,
            profile_id=rules.id,
            profile_version=rules.version,
            profile_fingerprint=rules.fingerprint,
            register_version=register.version,
            activity_snapshot=dict(activity),
            answers=answers,
            scenarios=scenarios,
            proposal=propose(rules, answers, scenarios).to_dict(),
            created_by=actor.id,
            created_at=now,
            updated_at=now,
            editors=(actor.id,),
            necessity=previous.necessity,
            proportionality=previous.proportionality,
            data_subject_view=previous.data_subject_view,
            predecessor_id=previous.assessment_id,
            changes_to_predecessor=changes,
            dossier=parse_dossier(previous.dossier, rules) if rules.edpb else {},
            measure_status=parse_measure_status(previous.measure_status, rules)
            if rules.edpb
            else {},
            action_plan=parse_action_plan(previous.action_plan, rules) if rules.edpb else (),
        )
        self.assessments.add(created)
        self._event(
            actor,
            "assessment.reassessment_started",
            created,
            predecessor=previous.assessment_id,
            changes=len(changes),
        )
        return created

    def overview(
        self,
        tenant_id: str,
        actor: Actor,
        *,
        register_id: str = DEFAULT_REGISTER,
        department: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Activities of the effective register with the state of their newest assessment.

        ``department`` filters by case-insensitive substring; activities without
        a department stay visible in every filter so none silently disappears.
        """
        self._allow(actor, Permission.ASSESSMENT_READ, tenant_id)
        register = self._effective(tenant_id, register_id)
        if register is None:
            return ()
        review = {i.assessment_id: i for i in self.review_required(tenant_id, actor, register_id)}
        rows = []
        for position, activity in enumerate(register.activities, start=1):
            name = str(activity.get("referat") or "").strip()
            if department and name and department.casefold() not in name.casefold():
                continue
            versions = self.versions(tenant_id, actor, str(activity.get("id")), register_id)
            newest = versions[0] if versions else None
            rows.append(
                {
                    "id": activity.get("id"),
                    "position": position,
                    "name": activity.get("name") or f"Tätigkeit {position}",
                    "referat": activity.get("referat") or "",
                    "zweck": activity.get("zweck") or "",
                    "vvt_version": register.version,
                    "vvt_status": register.status.value,
                    "dsfa": None
                    if newest is None
                    else {
                        "id": newest.assessment_id,
                        "version": newest.version,
                        "status": newest.status.value,
                        "entscheidung": newest.decision,
                        "freigegeben_am": newest.released_at,
                        "pruefung_erforderlich": any(v.assessment_id in review for v in versions),
                    },
                }
            )
        return tuple(rows)
