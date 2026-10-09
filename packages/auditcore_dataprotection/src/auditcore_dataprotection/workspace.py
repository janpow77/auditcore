"""Work on one activity: wizard, checklist, evidence and safeguards on one record.

Every change goes through :meth:`RegisterService.save_draft`, so permissions,
optimistic locking (expected revision), audit events and validation are the
same for the user interface, the REST interface and direct calls (LIB-23,
LIB-27). Changes to relevant fields reopen dependent checklist items.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import cast

from .access import require_permission
from .assessment import AssessmentService
from .central_register import TransferRepository
from .change_impact import apply_change_impact
from .checklist import (
    ChecklistItem,
    Transition,
    apply_transition,
    confirm_not_applicable,
    items_from_data,
)
from .errors import ConflictError, NotFoundError
from .evaluation import Evaluation, EvaluationInput, evaluate, wizard_context
from .evidence import evidence_from_data, safeguards_from_data
from .model import DEFAULT_REGISTER, Actor, Permission, RegisterVersion
from .operation_model import OperationRepository
from .ports import AssessmentRepository, Authorizer, Clock
from .register import RegisterService
from .rules import RuleProfile
from .scope import duplicate_hints
from .wizard import WizardAnswer, confirm_answer, navigate, record_answer, view
from .wizard_catalog import WizardCatalog, catalog_for
from .workspace_assessment import AssessmentAnswer, answer_in_assessment

_Data = dict[str, object]


@dataclass
class ActivityWorkspace:
    """Service for the wizard and the persistent checklist of activities."""

    registers: RegisterService
    assessments: AssessmentRepository
    authorizer: Authorizer
    clock: Clock
    profile: RuleProfile
    transfers: TransferRepository | None = None
    decisions: OperationRepository | None = None
    assessment_service: AssessmentService | None = None
    catalog: WizardCatalog = field(init=False)

    def __post_init__(self) -> None:
        self.catalog = catalog_for(self.profile)

    # ---------------------------------------------------------------- reading

    def _versions(
        self, tenant_id: str, actor: Actor, register_id: str
    ) -> tuple[RegisterVersion, RegisterVersion | None]:
        draft = self.registers.draft(tenant_id, actor, register_id)
        released = self.registers.released(tenant_id, actor, register_id)
        working = draft or released
        if working is None:
            raise NotFoundError("Es gibt noch kein Verzeichnis; zuerst eine Tätigkeit anlegen.")
        return working, released

    def working(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion:
        """Open draft, otherwise the released version (the record being worked on)."""
        return self._versions(tenant_id, actor, register_id)[0]

    @staticmethod
    def _activity(version: RegisterVersion | None, activity_id: str) -> Mapping[str, object] | None:
        if version is None:
            return None
        return next((a for a in version.activities if a.get("id") == activity_id), None)

    def evaluate(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        *,
        register_id: str = DEFAULT_REGISTER,
        today: date | None = None,
    ) -> Evaluation:
        """Status axes, gates, checklist and open work of the working version."""
        working, released = self._versions(tenant_id, actor, register_id)
        activity = self._activity(working, activity_id)
        if activity is None:
            raise NotFoundError(f"Verarbeitungstätigkeit mit ID {activity_id} nicht gefunden")
        require_permission(self.authorizer, actor, Permission.ASSESSMENT_READ, tenant_id)
        assessments = self.assessments.list_for_activity(tenant_id, register_id, activity_id)
        decisions = (
            ()
            if self.decisions is None
            else self.decisions.list_for_activity(tenant_id, register_id, activity_id)
        )
        return evaluate(
            EvaluationInput(
                profile=self.profile,
                catalog=self.catalog,
                working=working,
                activity=activity,
                released=released,
                released_activity=self._activity(released, activity_id),
                assessments=assessments,
                transfer=None
                if self.transfers is None
                else self.transfers.latest(tenant_id, register_id),
                decision=decisions[0] if decisions else None,
                today=today or self.clock.now().date(),
            )
        )

    def overview(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        *,
        register_id: str = DEFAULT_REGISTER,
    ) -> dict[str, object]:
        """Everything for the wizard, the work list and the review view."""
        working, _ = self._versions(tenant_id, actor, register_id)
        result = self.evaluate(tenant_id, actor, activity_id, register_id=register_id)
        activity = self._activity(working, activity_id) or {}
        context = wizard_context(activity, result.assessment)
        return {
            "register": {
                "register_id": working.register_id,
                "version": working.version,
                "status": working.status.value,
                "revision": working.revision,
            },
            "profil": dict(self.profile.reference),
            "assistent": view(self.catalog, activity, context),
            "dubletten": list(duplicate_hints(working.activities)),
            **result.to_dict(),
        }

    # ---------------------------------------------------------------- writing

    def _change(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        change: Callable[[Mapping[str, object]], _Data],
        register_id: str,
        expected_revision: int | None,
    ) -> RegisterVersion:
        working, released = self._versions(tenant_id, actor, register_id)
        content = cast(_Data, copy.deepcopy(dict(working.content)))
        activities = cast(list[_Data], content.get("taetigkeiten") or [])
        for index, activity in enumerate(activities):
            if activity.get("id") == activity_id:
                updated = change(activity)
                baseline = self._activity(released, activity_id) or activity
                activities[index] = apply_change_impact(baseline, updated, self.clock.now())
                break
        else:
            raise NotFoundError(f"Verarbeitungstätigkeit mit ID {activity_id} nicht gefunden")
        content["taetigkeiten"] = activities
        revision = expected_revision if working is not released else None
        return self.registers.save_draft(
            tenant_id, actor, content, register_id=register_id, expected_revision=revision
        )

    def create_activity(
        self,
        tenant_id: str,
        actor: Actor,
        name: str,
        *,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
        content_if_new: Mapping[str, object] | None = None,
    ) -> RegisterVersion:
        """New activity started from the wizard (guided mode by default)."""
        draft = self.registers.draft(tenant_id, actor, register_id)
        base = draft or self.registers.released(tenant_id, actor, register_id)
        content = cast(_Data, copy.deepcopy(dict(base.content if base else (content_if_new or {}))))
        activities = list(cast(Sequence[_Data], content.get("taetigkeiten") or []))
        activities.append({"name": name, "assistent": {"modus": "gefuehrt", "schritt": "W01"}})
        content["taetigkeiten"] = activities
        return self.registers.save_draft(
            tenant_id,
            actor,
            content,
            register_id=register_id,
            expected_revision=expected_revision if draft is not None else None,
        )

    def _context(
        self, tenant_id: str, register_id: str, activity: Mapping[str, object]
    ) -> dict[str, str]:
        found = self.assessments.list_for_activity(tenant_id, register_id, str(activity.get("id")))
        return wizard_context(activity, found[0] if found else None)

    def answer(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        question_id: str,
        value: str,
        *,
        justification: str = "",
        origin: str = "bestaetigt",
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Store one wizard answer; the same validation applies to every client.

        Screening questions (W09) and DPIA texts (W10) are written to the open
        DPIA version of the activity, so they are never recorded twice.
        """
        target = self.catalog.question(question_id).target
        if target.startswith(("screening:", "assessment:")):
            if self.assessment_service is None:
                raise ConflictError(
                    "Für Fragen der Folgenabschätzung ist kein Dienst konfiguriert."
                )
            found = self.assessments.list_for_activity(tenant_id, register_id, activity_id)
            answer_in_assessment(
                self.assessment_service,
                AssessmentAnswer(tenant_id, actor, target, value, justification, origin),
                found[0] if found else None,
                expected_revision,
            )
            return self._versions(tenant_id, actor, register_id)[0]
        answer = WizardAnswer(value, justification, actor.id, self.clock.now().isoformat(), origin)

        def change(activity: Mapping[str, object]) -> _Data:
            context = self._context(tenant_id, register_id, activity)
            return record_answer(self.catalog, activity, context, question_id, answer)

        return self._change(tenant_id, actor, activity_id, change, register_id, expected_revision)

    def confirm(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        question_id: str,
        *,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """A person adopts an imported, template or AI suggestion."""

        def change(activity: Mapping[str, object]) -> _Data:
            context = self._context(tenant_id, register_id, activity)
            return confirm_answer(
                self.catalog, activity, context, question_id, actor.id, self.clock.now()
            )

        return self._change(tenant_id, actor, activity_id, change, register_id, expected_revision)

    def navigate(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        *,
        mode: str,
        step: str,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Switch between guided and free mode or move to another step."""

        def change(activity: Mapping[str, object]) -> _Data:
            context = self._context(tenant_id, register_id, activity)
            return navigate(self.catalog, activity, context, mode=mode, step=step)

        return self._change(tenant_id, actor, activity_id, change, register_id, expected_revision)

    def update_item(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        item_id: str,
        transition: Transition,
        *,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Change one checklist item; "nachgewiesen" needs usable evidence."""
        require_permission(self.authorizer, actor, Permission.CHECKLIST_EDIT, tenant_id)

        def change(activity: Mapping[str, object]) -> _Data:
            items = items_from_data(activity.get("pruefpunkte"))
            catalog = evidence_from_data(activity.get("nachweise"))
            items[item_id] = apply_transition(
                _item(items, item_id), transition, catalog, self.profile.min_justification_length
            )
            return {**activity, "pruefpunkte": {k: v.to_dict() for k, v in items.items()}}

        return self._change(tenant_id, actor, activity_id, change, register_id, expected_revision)

    def confirm_item(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        item_id: str,
        *,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Second person confirms "nicht anwendbar" of an essential item."""
        require_permission(self.authorizer, actor, Permission.CHECKLIST_EDIT, tenant_id)

        def change(activity: Mapping[str, object]) -> _Data:
            items = items_from_data(activity.get("pruefpunkte"))
            items[item_id] = confirm_not_applicable(_item(items, item_id), actor.id)
            return {**activity, "pruefpunkte": {k: v.to_dict() for k, v in items.items()}}

        return self._change(tenant_id, actor, activity_id, change, register_id, expected_revision)

    def set_records(
        self,
        tenant_id: str,
        actor: Actor,
        activity_id: str,
        *,
        evidence: Sequence[Mapping[str, object]] | None = None,
        safeguards: Sequence[Mapping[str, object]] | None = None,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Replace the evidence catalogue and/or safeguards (validated)."""
        require_permission(self.authorizer, actor, Permission.CHECKLIST_EDIT, tenant_id)
        new: _Data = {}
        if evidence is not None:
            evidence_from_data(list(evidence))
            new["nachweise"] = [dict(e) for e in evidence]
        if safeguards is not None:
            safeguards_from_data(list(safeguards))
            new["schutzmassnahmen"] = [dict(s) for s in safeguards]

        def change(activity: Mapping[str, object]) -> _Data:
            return {**activity, **new}

        return self._change(tenant_id, actor, activity_id, change, register_id, expected_revision)


def _item(items: Mapping[str, ChecklistItem], item_id: str) -> ChecklistItem:
    if item_id not in items:
        raise NotFoundError(f"Prüfpunkt {item_id} nicht gefunden.")
    return items[item_id]
