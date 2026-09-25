"""DPO involvement and prior consultation of a DPIA version.

Statement, conclusion and request of the data protection officer
(Art. 35 Abs. 2, Art. 38 DSGVO) and the prior consultation of the
supervisory authority (Art. 36 DSGVO / § 64 HDSIG).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from .assessment_checks import HIGH_RESIDUAL_RISK
from .assessment_core import AssessmentServiceCore
from .errors import ConflictError, ValidationError
from .model import Actor, Assessment, AssessmentStatus, Consultation, Permission
from .rules import RuleProfile


def _check_consultation_ground(current: Assessment, rules: RuleProfile, ground: str | None) -> None:
    """Schema 2 requires a known ground that fits the assessment; schema 1 knows none."""
    if rules.edpb and (not isinstance(ground, str) or ground not in rules.consultation_grounds):
        raise ValidationError(
            "Der Grund der Konsultation ist anzugeben. Zulässig sind: "
            f"{', '.join(rules.consultation_grounds)}."
        )
    if (
        rules.edpb
        and ground == HIGH_RESIDUAL_RISK
        and not current.proposal.get("consultation_required")
        and not rules.documentation_mode
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


def _check_consultation_record(authority: object, result: object, consulted_on: object) -> None:
    if not isinstance(authority, str) or not authority.strip():
        raise ValidationError("Die konsultierte Aufsichtsbehörde ist anzugeben.")
    if not isinstance(result, str) or not result.strip():
        raise ValidationError("Das Ergebnis der Konsultation ist anzugeben.")
    if not isinstance(consulted_on, date):
        raise ValidationError("Das Datum der Konsultation ist als Datum anzugeben.")


class AssessmentInvolvement(AssessmentServiceCore):
    """Operations that involve the DPO and the supervisory authority."""

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
        if (
            current.dpo_vote == "abgelehnt"
            and len(text) < rules.min_justification_length
            and not rules.documentation_mode
        ):
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

    def record_dpo_request(
        self,
        tenant_id: str,
        actor: Actor,
        assessment_id: str,
        *,
        expected_revision: int,
        requested_from: str,
        requested_on: date,
    ) -> Assessment:
        """Document that the advice of the DPO was sought (Art. 35 Abs. 2 DSGVO).

        Only for profiles in documentation mode. The statement itself can
        follow later with :meth:`record_dpo_statement`; the release does not
        wait for it.
        """
        self._allow(actor, Permission.ASSESSMENT_EDIT, tenant_id)
        current = self._open(tenant_id, assessment_id, expected_revision)
        rules = self._profile(current)
        if not rules.documentation_mode:
            raise ValidationError(
                "Die Einholung der Stellungnahme wird nur im Dokumentationsmodus gesondert "
                "erfasst; hier ist die Stellungnahme selbst zu dokumentieren."
            )
        if not isinstance(requested_from, str) or not requested_from.strip():
            raise ValidationError("Anzugeben ist, bei wem die Stellungnahme eingeholt wurde.")
        if not isinstance(requested_on, date):
            raise ValidationError("Das Datum der Anfrage ist als Datum anzugeben.")
        now = self.clock.now()
        updated = replace(
            current,
            dpo_requested_from=requested_from.strip(),
            dpo_requested_on=requested_on.isoformat(),
            dpo_requested_by=actor.id,
            dpo_requested_at=now,
            editors=self._with_editor(current, actor),
            updated_at=now,
            revision=current.revision + 1,
        )
        self._store(current, updated)
        self._event(
            actor, "assessment.dpo_requested", updated, requested_on=updated.dpo_requested_on
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
        _check_consultation_ground(current, rules, ground)
        _check_consultation_record(authority, result, consulted_on)
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
