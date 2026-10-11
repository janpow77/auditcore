"""Separate status axes instead of a single ``compliant`` flag (catalogue 9.2).

Documentation, DPIA necessity, DPIA work, consultation, central register
takeover and the operational decision are derived independently. None of them
can become positive through form completeness, a point total or an unclear
answer; a released DPIA version is not an operational decision.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .model import Assessment, AssessmentStatus
from .rules import (
    DECISION_REJECTED,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_SCREENING_ONLY,
    RuleProfile,
)
from .screening import SCREENING_NOT_REQUIRED, SCREENING_REQUIRED


class DocumentationStatus(StrEnum):
    DRAFT = "entwurf"
    COMPLETE = "vollstaendig"
    CONFIRMED = "bestaetigt"
    NEEDS_REVISION = "ueberarbeitungsbeduerftig"


class NecessityStatus(StrEnum):
    UNDECIDED = "ungeklaert"
    REQUIRED = "erforderlich"
    NOT_REQUIRED = "nicht_erforderlich_begruendet"


class DpiaWorkStatus(StrEnum):
    NOT_STARTED = "nicht_begonnen"
    IN_PROGRESS = "in_arbeit"
    COMPLETED = "fachlich_abgeschlossen"
    RECHECK = "erneut_zu_pruefen"


class ConsultationStatus(StrEnum):
    UNCHECKED = "ungeprueft"
    NOT_REQUIRED = "nicht_erforderlich_begruendet"
    REQUIRED = "erforderlich"
    INITIATED = "eingeleitet"
    HANDLED = "bearbeitet"


class TransferStatus(StrEnum):
    NOT_TRANSFERRED = "nicht_uebertragen"
    EXPORTED = "exportiert"
    TRANSFERRED = "uebertragen"
    TAKEN_OVER = "uebernommen"
    CONFLICT = "konflikt"


class OperationStatus(StrEnum):
    NOT_REQUESTED = "nicht_beantragt"
    IN_REVIEW = "in_pruefung"
    REJECTED = "abgelehnt"
    GRANTED = "fuer_definierten_umfang_erteilt"
    REASSESS = "neu_zu_beurteilen"


@dataclass(frozen=True)
class StatusAxes:
    """The six axes; there is deliberately no overall "compliant" value."""

    documentation: DocumentationStatus
    necessity: NecessityStatus
    dpia_work: DpiaWorkStatus
    consultation: ConsultationStatus
    transfer: TransferStatus
    operation: OperationStatus

    def to_dict(self) -> dict[str, str]:
        """JSON form for exports and the user interface."""
        return {
            "dokumentation": self.documentation.value,
            "dsfa_erforderlichkeit": self.necessity.value,
            "dsfa_bearbeitung": self.dpia_work.value,
            "konsultation": self.consultation.value,
            "zentrale_uebernahme": self.transfer.value,
            "betriebsentscheidung": self.operation.value,
        }


def documentation_status(
    *, released: bool, blocking_issues: int, open_tasks: int, changed_since_release: bool
) -> DocumentationStatus:
    """Confirmed only for a complete released version without later relevant changes.

    A released version with open mandatory items is never shown as the
    confirmed final version (GATE-02).
    """
    if released and (changed_since_release or blocking_issues or open_tasks):
        return DocumentationStatus.NEEDS_REVISION
    if released:
        return DocumentationStatus.CONFIRMED
    if blocking_issues or open_tasks:
        return DocumentationStatus.DRAFT
    return DocumentationStatus.COMPLETE


def necessity_status(assessment: Assessment | None, profile: RuleProfile) -> NecessityStatus:
    """Not required only with a complete screening, a decision and its own reasoning."""
    if assessment is None:
        return NecessityStatus.UNDECIDED
    screening = assessment.proposal.get("screening") or {}
    if screening.get("outcome") == SCREENING_REQUIRED:
        return NecessityStatus.REQUIRED
    decision = assessment.decision
    if decision is not None and decision not in (RECOMMENDATION_SCREENING_ONLY,):
        return NecessityStatus.REQUIRED
    justified = len((assessment.decision_justification or "").strip()) >= (
        profile.min_justification_length
    )
    if (
        decision == RECOMMENDATION_SCREENING_ONLY
        and screening.get("complete")
        and screening.get("outcome") == SCREENING_NOT_REQUIRED
        and justified
    ):
        return NecessityStatus.NOT_REQUIRED
    return NecessityStatus.UNDECIDED


def _substance(assessment: Assessment) -> bool:
    return bool(
        assessment.necessity.strip() and assessment.proportionality.strip() and assessment.scenarios
    )


def dpia_work_status(
    assessment: Assessment | None, necessity: NecessityStatus, *, review_required: bool
) -> DpiaWorkStatus:
    """Completed only with substance, DPO statement and a released version (T-11, T-13)."""
    if assessment is None or necessity is not NecessityStatus.REQUIRED:
        return DpiaWorkStatus.NOT_STARTED
    if review_required or assessment.status is AssessmentStatus.SUPERSEDED:
        return DpiaWorkStatus.RECHECK
    if (
        assessment.status is AssessmentStatus.RELEASED
        and _substance(assessment)
        and assessment.dpo_at is not None
    ):
        return DpiaWorkStatus.COMPLETED
    if _substance(assessment) or assessment.scenarios or assessment.necessity.strip():
        return DpiaWorkStatus.IN_PROGRESS
    return DpiaWorkStatus.NOT_STARTED


def consultation_status(
    assessment: Assessment | None,
    necessity: NecessityStatus,
    activity: Mapping[str, object],
) -> ConsultationStatus:
    """Own axis; the § 64 Abs. 1 Nr. 2 HDSIG ground counts without a high residual risk."""
    if assessment is None or necessity is NecessityStatus.UNDECIDED:
        return ConsultationStatus.UNCHECKED
    if necessity is NecessityStatus.NOT_REQUIRED:
        return ConsultationStatus.NOT_REQUIRED
    proposal = assessment.proposal
    grounds = (proposal.get("screening") or {}).get("consultation_grounds") or ()
    required = bool(proposal.get("consultation_required")) or (
        bool(grounds) and assessment.decision != DECISION_REJECTED
    )
    required = required or assessment.decision == RECOMMENDATION_CONSULTATION
    if assessment.consultation is not None:
        return ConsultationStatus.HANDLED
    if required and activity.get("konsultation_eingeleitet_am"):
        return ConsultationStatus.INITIATED
    if required:
        return ConsultationStatus.REQUIRED
    if assessment.decision is None:
        return ConsultationStatus.UNCHECKED
    return ConsultationStatus.NOT_REQUIRED


def operation_status(
    decision_outcome: str | None, *, matches_current_version: bool
) -> OperationStatus:
    """A decision binds to one version; any other version must be assessed anew."""
    if decision_outcome is None:
        return OperationStatus.NOT_REQUESTED
    if not matches_current_version:
        return OperationStatus.REASSESS
    return OperationStatus(decision_outcome)


#: Labels for exports: "submitted for review" never reads as "released" (10.3).
STATUS_LABELS = {
    DocumentationStatus.DRAFT: "Entwurf – nicht bestätigt",
    DocumentationStatus.COMPLETE: "Vollständig erfasst – zur Prüfung, nicht bestätigt",
    DocumentationStatus.CONFIRMED: "Dokumentation bestätigt (keine Betriebsentscheidung)",
    DocumentationStatus.NEEDS_REVISION: "Überarbeitungsbedürftig – bestätigte Fassung veraltet",
}
