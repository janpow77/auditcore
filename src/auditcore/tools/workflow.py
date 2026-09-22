"""Explicit state machines; transitions require nonempty execution evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from auditcore.exceptions import InvalidTransition
from auditcore.tools.common import now

CONSOLIDATION_STATES = (
    "CREATED",
    "INVENTORY_REQUIRED",
    "INVENTORY_RUNNING",
    "INVENTORY_COMPLETE",
    "KIRA_SYNCHRONIZED",
    "CANDIDATES_DETECTED",
    "DEPENDENCIES_ANALYZED",
    "CONFLICTS_ANALYZED",
    "READY_FOR_CONSOLIDATION",
    "CHARACTERIZED",
    "LIBRARY_CREATED",
    "LIBRARY_TESTED",
    "APPLICATIONS_MIGRATED",
    "APPLICATIONS_TESTED",
    "QUALITY_CHECKED",
    "OPTIMIZED",
    "KIRA_UPDATED",
    "COMPLETE",
)
REFACTOR_STATES = (
    "CREATED",
    "APPLICATION_ANALYZED",
    "REFACTOR_PLAN_CREATED",
    "DRY_RUN_COMPLETE",
    "LEGACY_CHARACTERIZED",
    "MIGRATION_APPLIED",
    "APPLICATION_TESTED",
    "OPTIMIZATION_APPLIED",
    "REGRESSION_VERIFIED",
    "INTEGRATION_VERIFIED",
    "QUALITY_VERIFIED",
    "READY_FOR_DEPLOYMENT",
)
DEPLOY_STATES = (
    "CREATED",
    "APPLICATION_INSPECTED",
    "DEPLOYMENT_PLAN_CREATED",
    "QUALITY_VERIFIED",
    "BACKEND_BUILT",
    "FRONTEND_BUILT",
    "PACKAGE_STAGED",
    "DEB_BUILT",
    "PACKAGE_VALIDATED",
    "INSTALL_TESTED",
    "UPGRADE_TESTED",
    "HEALTH_CHECKED",
    "APT_READY",
    "PUBLISHED",
    "COMPLETE",
)


@dataclass
class StateMachine:
    """Sequential guarded states with an explicit human-decision pause."""

    states: tuple[str, ...]
    state: str = "CREATED"
    history: list[dict[str, Any]] = field(default_factory=list)
    resume_state: str | None = None

    def transition(self, target: str, evidence: dict[str, Any]) -> None:
        """Reject skipped stages, failed evidence and fabricated completion."""
        if self.state in {"FAILED", self.states[-1]}:
            raise InvalidTransition("Terminal state")
        if target == "FAILED":
            self.state = target
        elif target == "WAITING_FOR_HUMAN_DECISION":
            if self.resume_state:
                raise InvalidTransition("Already waiting")
            self.resume_state = self.state
            self.state = target
        elif self.state == "WAITING_FOR_HUMAN_DECISION":
            if target != self.resume_state or evidence.get("classification") != "HUMAN_CONFIRMED":
                raise InvalidTransition("Human decision required")
            self.state = target
            self.resume_state = None
        else:
            next_state = self.states[self.states.index(self.state) + 1]
            if (
                target != next_state
                or evidence.get("status") not in {"PASS", "NOT_APPLICABLE_WITH_REASON"}
                or not evidence.get("reference")
            ):
                raise InvalidTransition(f"Transition {self.state} -> {target} lacks evidence")
            if evidence["status"] == "NOT_APPLICABLE_WITH_REASON" and not evidence.get("reason"):
                raise InvalidTransition("Nonapplicability requires reason")
            self.state = target
        self.history.append({"state": self.state, "at": now(), "evidence": evidence})
