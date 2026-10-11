"""Service for the operational decision on one released register version.

Only actors with ``operation.decide`` may decide (T-17); administrators do
not get it implicitly. A positive decision requires that no gate applies
(GATE-01 to GATE-07). There is no general "start anyway" (T-15): the only
exception is the urgent start of § 64 Abs. 4 HDSIG after the consultation was
initiated, with justification and follow-up, and it never bypasses any other
gate.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .access import require_permission
from .errors import ConflictError, ValidationError
from .gates import ACTION_DECIDE_OPERATION, blocking_for
from .model import DEFAULT_REGISTER, Actor, AuditEvent, Permission
from .operation_model import (
    OUTCOME_GRANTED,
    OUTCOMES,
    OperationalDecision,
    OperationRepository,
    UrgentStart,
)
from .ports import AuditSink, Authorizer, Clock, IdFactory
from .status import ConsultationStatus
from .workspace import ActivityWorkspace

URGENT_REGIME = "hdsig_ji"


@dataclass(frozen=True)
class DecisionRequest:
    """What the competent body decides on."""

    activity_id: str
    outcome: str
    environment: str
    application_version: str
    scope: str
    justification: str
    conditions: tuple[str, ...] = ()
    urgent: UrgentStart | None = None


@dataclass
class OperationService:
    """Records version-bound operational decisions after the backend gates."""

    workspace: ActivityWorkspace
    repository: OperationRepository
    authorizer: Authorizer
    audit: AuditSink
    clock: Clock
    ids: IdFactory

    def history(
        self, tenant_id: str, actor: Actor, activity_id: str, register_id: str = DEFAULT_REGISTER
    ) -> Sequence[OperationalDecision]:
        """All decisions of an activity, newest first."""
        require_permission(self.authorizer, actor, Permission.ASSESSMENT_READ, tenant_id)
        return self.repository.list_for_activity(tenant_id, register_id, activity_id)

    def _check_request(self, request: DecisionRequest) -> None:
        if request.outcome not in OUTCOMES:
            raise ValidationError(f"Unbekanntes Ergebnis „{request.outcome}“.")
        minimum = self.workspace.profile.min_justification_length
        if len(request.justification.strip()) < minimum:
            raise ValidationError(
                f"Die Entscheidung braucht eine Begründung von mindestens {minimum} Zeichen."
            )
        if not request.environment.strip() or not request.scope.strip():
            raise ValidationError("Umgebung und Nutzungsumfang sind anzugeben.")

    def _check_urgent(self, urgent: UrgentStart, consultation: ConsultationStatus) -> None:
        """§ 64 Abs. 4 HDSIG only, only after initiation, with reason and follow-up."""
        if self.workspace.profile.regime != URGENT_REGIME:
            raise ConflictError("Der Dringlichkeitsfall ist nur im Dritten Teil HDSIG vorgesehen.")
        if consultation is not ConsultationStatus.INITIATED:
            raise ConflictError(
                "Der Dringlichkeitsfall setzt eine eingeleitete Konsultation voraus."
            )
        minimum = self.workspace.profile.min_justification_length
        if len(urgent.justification.strip()) < minimum or not urgent.follow_up.strip():
            raise ValidationError(
                "Der Dringlichkeitsfall braucht eine Begründung der Dringlichkeit und eine "
                "Nachverfolgung."
            )

    def _record(self, actor: Actor, decision: OperationalDecision) -> None:
        self.audit.record(
            AuditEvent(
                decision.tenant_id,
                actor.id,
                "operation.decided",
                "operation",
                decision.decision_id,
                decision.register_version,
                decision.decided_at,
                {
                    "outcome": decision.outcome,
                    "activity_id": decision.activity_id,
                    "urgent": decision.urgent is not None,
                },
            )
        )

    def decide(
        self,
        tenant_id: str,
        actor: Actor,
        request: DecisionRequest,
        *,
        register_id: str = DEFAULT_REGISTER,
    ) -> OperationalDecision:
        """Record a decision; a positive one is refused while a gate applies."""
        require_permission(self.authorizer, actor, Permission.OPERATION_DECIDE, tenant_id)
        self._check_request(request)
        released = self.workspace.registers.released(tenant_id, actor, register_id)
        if released is None:
            raise ConflictError("Entschieden wird über eine bestätigte (freigegebene) Fassung.")
        result = self.workspace.evaluate(
            tenant_id, actor, request.activity_id, register_id=register_id
        )
        blocking = blocking_for(result.gates, ACTION_DECIDE_OPERATION)
        if request.outcome == OUTCOME_GRANTED:
            if request.urgent is not None:
                self._check_urgent(request.urgent, result.axes.consultation)
                blocking = tuple(g for g in blocking if g.id != "GATE-05")
            if blocking:
                raise ConflictError(
                    "Betriebsentscheidung gesperrt: "
                    + " | ".join(f"{g.id}: {g.reason} → {g.next_step}" for g in blocking)
                )
        decision = OperationalDecision(
            tenant_id=tenant_id,
            decision_id=self.ids.new_id("operation"),
            register_id=register_id,
            activity_id=request.activity_id,
            register_version=released.version,
            content_hash=released.content_hash,
            environment=request.environment.strip(),
            application_version=request.application_version.strip(),
            scope=request.scope.strip(),
            outcome=request.outcome,
            justification=request.justification.strip(),
            decided_by=actor.id,
            decided_at=self.clock.now(),
            conditions=tuple(c.strip() for c in request.conditions if c.strip()),
            urgent=request.urgent,
            gates_at_decision=tuple(g.id for g in result.gates),
        )
        self.repository.add(decision)
        self._record(actor, decision)
        return decision
