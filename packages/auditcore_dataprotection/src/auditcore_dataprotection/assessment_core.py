"""Ports, guards and read access shared by all DPIA operations.

Every operation checks the authorizer port and the tenant, compares the
revision that was read and records an audit event; this module holds those
building blocks and the read-only operations of
:class:`~auditcore_dataprotection.assessment.AssessmentService`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from .errors import (
    AuthorizationError,
    ConflictError,
    LockedVersionError,
    NotFoundError,
    ProfileError,
    StaleRevisionError,
    TenantMismatchError,
)
from .model import DEFAULT_REGISTER, Actor, Assessment, AuditEvent, Permission, RegisterVersion
from .ports import AssessmentRepository, AuditSink, Authorizer, Clock, IdFactory, RegisterRepository
from .prefill import prefill_from_activity
from .register_content import find_activity
from .rules import RuleProfile, load_profile

ProfileResolver = Callable[[str, str], RuleProfile]


def refuse_second_open_version(existing: Sequence[Assessment]) -> None:
    """Only one version of an activity's assessment may be open at a time."""
    open_ = [a for a in existing if not a.locked]
    if open_:
        raise ConflictError(
            f"Zu dieser Tätigkeit ist bereits Fassung {open_[0].version} in Bearbeitung."
        )


@dataclass
class AssessmentServiceCore:
    """Ports of the DPIA service and the guards every operation uses."""

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

    def _event(self, actor: Actor, action: str, assessment: Assessment, **details: object) -> None:
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
