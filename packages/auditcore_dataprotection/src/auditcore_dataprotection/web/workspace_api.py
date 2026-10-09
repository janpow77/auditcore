"""REST handlers for the wizard, the checklist, the decision and the central register.

They call the same library services as every other client: a disabled button
in the user interface is never the only control (LIB-23, GATE rules). Each
change answers with the refreshed activity overview, so the client always
shows the state the backend computed.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..access import require_permission
from ..central_register import TransferRecord
from ..checklist import ItemStatus, Transition
from ..errors import ConflictError, ValidationError
from ..model import Permission
from ..operation import DecisionRequest
from ..operation_model import UrgentStart
from ..publication import public_pattern
from ..review_package import review_package
from ..workspace import ActivityWorkspace
from .backend import Backend
from .contract import JsonObject, Principal, body_object, invalid, revision, text, text_list

_ANSWER = frozenset({"question_id", "value", "justification", "origin", "expected_revision"})
_ITEM = frozenset(
    {"status", "justification", "evidence_ids", "owner", "due", "objection", "expected_revision"}
)
_DECISION = frozenset(
    {
        "outcome",
        "environment",
        "application_version",
        "scope",
        "justification",
        "conditions",
        "urgent",
    }
)


def _records(body: Mapping[str, object], key: str) -> list[Mapping[str, object]] | None:
    value = body.get(key)
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(v, Mapping) for v in value):
        raise invalid(f"'{key}' muss eine Liste von Objekten sein.")
    return list(value)


def _urgent(value: object) -> UrgentStart | None:
    if value is None:
        return None
    fields = frozenset({"justification", "consultation_initiated_on", "follow_up"})
    data = body_object(value, fields)
    return UrgentStart(
        text(data, "justification"),
        text(data, "consultation_initiated_on"),
        text(data, "follow_up"),
    )


class WorkspaceApi:
    """Handlers of ``/activities/...`` and ``/register/transfer``."""

    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    @property
    def _work(self) -> ActivityWorkspace:
        if self.backend.workspace is None:
            raise ConflictError("Der Arbeitsbereich ist nicht konfiguriert.")
        return self.backend.workspace

    def overview(self, who: Principal, activity_id: str) -> JsonObject:
        """``GET /activities/{id}/workspace``."""
        return self._work.overview(who.tenant_id, who.actor, activity_id)

    def create(self, who: Principal, body: object) -> JsonObject:
        """``POST /activities``: new activity, the wizard starts in guided mode."""
        data = body_object(body, frozenset({"name", "expected_revision"}))
        saved = self._work.create_activity(
            who.tenant_id,
            who.actor,
            text(data, "name"),
            expected_revision=revision(data, required=False),
        )
        activity_id = str(saved.activities[-1]["id"])
        return self.overview(who, activity_id)

    def answer(self, who: Principal, activity_id: str, body: object) -> JsonObject:
        """``POST /activities/{id}/answers``."""
        data = body_object(body, _ANSWER)
        self._work.answer(
            who.tenant_id,
            who.actor,
            activity_id,
            text(data, "question_id"),
            text(data, "value", required=False),
            justification=text(data, "justification", required=False),
            origin=text(data, "origin", required=False) or "bestaetigt",
            expected_revision=revision(data, required=False),
        )
        return self.overview(who, activity_id)

    def confirm(self, who: Principal, activity_id: str, body: object) -> JsonObject:
        """``POST /activities/{id}/answers/confirm``: adopt a suggestion."""
        data = body_object(body, frozenset({"question_id", "expected_revision"}))
        self._work.confirm(
            who.tenant_id,
            who.actor,
            activity_id,
            text(data, "question_id"),
            expected_revision=revision(data, required=False),
        )
        return self.overview(who, activity_id)

    def navigate(self, who: Principal, activity_id: str, body: object) -> JsonObject:
        """``POST /activities/{id}/navigate``: guided or free mode, step."""
        data = body_object(body, frozenset({"mode", "step", "expected_revision"}))
        self._work.navigate(
            who.tenant_id,
            who.actor,
            activity_id,
            mode=text(data, "mode"),
            step=text(data, "step"),
            expected_revision=revision(data, required=False),
        )
        return self.overview(who, activity_id)

    def item(self, who: Principal, activity_id: str, item_id: str, body: object) -> JsonObject:
        """``POST /activities/{id}/checklist/{item}``."""
        data = body_object(body, _ITEM)
        try:
            status = ItemStatus(text(data, "status"))
        except ValueError as exc:
            raise invalid(f"Unbekannter Status „{data.get('status')}“.") from exc
        change = Transition(
            status=status,
            actor=who.actor.id,
            at=self._work.clock.now(),
            justification=text(data, "justification", required=False),
            evidence_ids=text_list(data, "evidence_ids"),
            owner=text(data, "owner", required=False) if "owner" in data else None,
            due=text(data, "due", required=False) if "due" in data else None,
            objection=text(data, "objection", required=False) if "objection" in data else None,
        )
        self._work.update_item(
            who.tenant_id,
            who.actor,
            activity_id,
            item_id,
            change,
            expected_revision=revision(data, required=False),
        )
        return self.overview(who, activity_id)

    def confirm_item(
        self, who: Principal, activity_id: str, item_id: str, body: object
    ) -> JsonObject:
        """``POST /activities/{id}/checklist/{item}/confirm``: second person."""
        data = body_object(body, frozenset({"expected_revision"}))
        self._work.confirm_item(
            who.tenant_id,
            who.actor,
            activity_id,
            item_id,
            expected_revision=revision(data, required=False),
        )
        return self.overview(who, activity_id)

    def records(self, who: Principal, activity_id: str, body: object) -> JsonObject:
        """``POST /activities/{id}/records``: evidence catalogue and safeguards."""
        data = body_object(body, frozenset({"evidence", "safeguards", "expected_revision"}))
        self._work.set_records(
            who.tenant_id,
            who.actor,
            activity_id,
            evidence=_records(data, "evidence"),
            safeguards=_records(data, "safeguards"),
            expected_revision=revision(data, required=False),
        )
        return self.overview(who, activity_id)

    def decide(self, who: Principal, activity_id: str, body: object) -> JsonObject:
        """``POST /activities/{id}/operation``: version-bound operational decision."""
        if self.backend.operations is None:
            raise ConflictError("Betriebsentscheidungen sind nicht konfiguriert.")
        data = body_object(body, _DECISION)
        request = DecisionRequest(
            activity_id=activity_id,
            outcome=text(data, "outcome"),
            environment=text(data, "environment"),
            application_version=text(data, "application_version", required=False),
            scope=text(data, "scope"),
            justification=text(data, "justification"),
            conditions=text_list(data, "conditions"),
            urgent=_urgent(data.get("urgent")),
        )
        self.backend.operations.decide(who.tenant_id, who.actor, request)
        return self.overview(who, activity_id)

    def package(self, who: Principal, activity_id: str) -> JsonObject:
        """``GET /activities/{id}/review-package``."""
        return review_package(self._work, who.tenant_id, who.actor, activity_id)

    def transfer(self, who: Principal, body: object) -> JsonObject:
        """``POST /register/transfer``: transfer the released version (idempotent)."""
        body_object(body, frozenset())
        if self.backend.central is None:
            raise ConflictError("Die zentrale Übernahme ist nicht konfiguriert.")
        released = self.backend.registers.released(who.tenant_id, who.actor)
        if released is None:
            raise ConflictError("Es gibt keine freigegebene Fassung.")
        record = self.backend.central.transfer(who.actor, released, dict(released.content))
        return _transfer_view(record)

    def confirm_transfer(self, who: Principal, body: object) -> JsonObject:
        """``POST /register/transfer/confirm``: takeover with central id and proof."""
        if self.backend.central is None:
            raise ConflictError("Die zentrale Übernahme ist nicht konfiguriert.")
        data = body_object(body, frozenset({"key", "central_id", "proof"}))
        record = self.backend.central.confirm_takeover(
            who.actor,
            who.tenant_id,
            text(data, "key"),
            central_id=text(data, "central_id"),
            proof=text(data, "proof"),
        )
        return _transfer_view(record)

    def public_pattern(self, who: Principal) -> JsonObject:
        """``POST /register/public-pattern``: abstract structure only, never content."""
        require_permission(
            self.backend.registers.authorizer, who.actor, Permission.EXPORT_PUBLIC, who.tenant_id
        )
        released = self.backend.registers.released(who.tenant_id, who.actor)
        if released is None:
            raise ValidationError("Es gibt keine freigegebene Fassung.")
        return public_pattern(released.content)


def _transfer_view(record: TransferRecord) -> JsonObject:
    return {
        "key": record.key,
        "version": record.version,
        "status": record.status.value,
        "central_id": record.central_id,
        "message": record.message,
    }
