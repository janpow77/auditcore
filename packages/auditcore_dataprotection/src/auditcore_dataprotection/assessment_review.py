"""Review after register changes, reassessment and the overview of a register.

Released versions are only reported, never modified (Art. 35 Abs. 11 DSGVO);
a reassessment starts a new version from a released one.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from .assessment_core import AssessmentServiceCore, refuse_second_open_version
from .assessment_input import refuse_downgrade
from .calculation import parse_answers, parse_scenarios, propose
from .edpb import parse_action_plan, parse_dossier, parse_measure_status
from .errors import ConflictError, TenantMismatchError
from .model import (
    DEFAULT_REGISTER,
    Actor,
    Assessment,
    AssessmentStatus,
    Permission,
    RegisterVersion,
    ReviewItem,
)
from .register_content import activity_changes, find_activity
from .rules import RuleProfile


class _Documentation(TypedDict):
    dossier: Mapping[str, str]
    measure_status: Mapping[str, Mapping[str, str]]
    action_plan: tuple[Mapping[str, str], ...]


def _carried_documentation(previous: Assessment, rules: RuleProfile) -> _Documentation:
    """Schema 2 documentation of the predecessor, revalidated; empty for schema 1."""
    if not rules.edpb:
        return {"dossier": {}, "measure_status": {}, "action_plan": ()}
    return {
        "dossier": parse_dossier(previous.dossier, rules),
        "measure_status": parse_measure_status(previous.measure_status, rules),
        "action_plan": parse_action_plan(previous.action_plan, rules),
    }


class AssessmentReview(AssessmentServiceCore):
    """Operations across versions: review, reassessment and overview."""

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
            item = self._review_item(assessment, register, current.get(assessment.activity_id))
            if item is not None:
                items.append(item)
        return tuple(items)

    def _review_item(
        self,
        assessment: Assessment,
        register: RegisterVersion,
        activity: Mapping[str, object] | None,
    ) -> ReviewItem | None:
        """Review need of one released assessment: activity removed or changed."""
        if activity is None:
            reason = "Die Tätigkeit ist im Verzeichnis nicht mehr enthalten."
            changes: tuple[dict[str, Any], ...] = ()
        else:
            changes = activity_changes(
                assessment.activity_snapshot, activity, self._profile(assessment)
            )
            if not changes:
                return None
            reason = (
                f"Das Verzeichnis wurde geändert (Fassung {register.version}); "
                f"{len(changes)} wesentliche Angaben weichen ab."
            )
        return ReviewItem(
            assessment.tenant_id,
            assessment.assessment_id,
            assessment.activity_id,
            assessment.activity_name,
            assessment.version,
            register.version,
            reason,
            changes,
        )

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
        refuse_second_open_version(existing)
        rules = profile or self._profile(previous)
        refuse_downgrade(self._profile(previous), rules)
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
            **_carried_documentation(previous, rules),
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
