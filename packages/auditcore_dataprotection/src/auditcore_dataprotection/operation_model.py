"""Operational decision: a separate, version-bound act of the competent body.

Releasing documentation is not a decision to operate. An operational decision
names the register version and content hash, the environment, the application
version and the scope; it never carries over to another version (GATE-07).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

OUTCOME_IN_REVIEW = "in_pruefung"
OUTCOME_REJECTED = "abgelehnt"
OUTCOME_GRANTED = "fuer_definierten_umfang_erteilt"
OUTCOMES = (OUTCOME_IN_REVIEW, OUTCOME_REJECTED, OUTCOME_GRANTED)


@dataclass(frozen=True)
class UrgentStart:
    """Narrow exception of § 64 Abs. 4 HDSIG: start after the consultation was initiated."""

    justification: str
    consultation_initiated_on: str
    follow_up: str


@dataclass(frozen=True)
class OperationalDecision:
    """Decision of the competent body on one version, environment and scope."""

    tenant_id: str
    decision_id: str
    register_id: str
    activity_id: str
    register_version: int
    content_hash: str
    environment: str
    application_version: str
    scope: str
    outcome: str
    justification: str
    decided_by: str
    decided_at: datetime
    conditions: tuple[str, ...] = ()
    urgent: UrgentStart | None = None
    gates_at_decision: tuple[str, ...] = ()


@runtime_checkable
class OperationRepository(Protocol):
    """Tenant-scoped storage of operational decisions (append-only)."""

    def add(self, decision: OperationalDecision) -> None:
        """Store a decision; decisions are never changed afterwards."""
        ...

    def list_for_activity(
        self, tenant_id: str, register_id: str, activity_id: str
    ) -> Sequence[OperationalDecision]:
        """All decisions of an activity, newest first."""
        ...
