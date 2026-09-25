"""Records of processing activities: versions, drafts and four-eyes release.

A register version is a JSON document with a cover sheet (``deckblatt``),
departments (``referate``) and activities (``taetigkeiten``), using the field
names of the source application. Drafts are replaced only with the revision
that was read; releases require a second person who did not edit the draft.
Released versions are never changed; a new draft becomes the next version.

Content checks, identifiers and change detection live in
:mod:`.register_content`; every name stays importable from here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from .errors import (
    AuthorizationError,
    ConflictError,
    FourEyesViolation,
    StaleRevisionError,
    TenantMismatchError,
)
from .model import DEFAULT_REGISTER, Actor, AuditEvent, Permission, RegisterStatus, RegisterVersion
from .ports import AuditSink, Authorizer, Clock, IdFactory, RegisterRepository
from .register_content import (
    COUNT_FIELDS,
    FLAG_FIELDS,
    MAX_ACTIVITIES,
    MAX_CONTENT_BYTES,
    REQUIRED_TEXT,
    TEXT_FIELDS,
    activity_changes,
    check_activity,
    check_register,
    content_hash,
    find_activity,
    group_by_department,
    normalize_content,
)
from .rules import RuleProfile

__all__ = [
    "COUNT_FIELDS",
    "FLAG_FIELDS",
    "MAX_ACTIVITIES",
    "MAX_CONTENT_BYTES",
    "REQUIRED_TEXT",
    "TEXT_FIELDS",
    "RegisterService",
    "activity_changes",
    "check_activity",
    "check_register",
    "content_hash",
    "find_activity",
    "group_by_department",
    "normalize_content",
]


@dataclass
class RegisterService:
    """Create, edit, version and release registers inside a tenant."""

    repository: RegisterRepository
    authorizer: Authorizer
    audit: AuditSink
    clock: Clock
    ids: IdFactory
    profile: RuleProfile
    identifier_scheme: str = "uuid"
    require_complete_release: bool = True

    def _allow(self, actor: Actor, permission: Permission, tenant_id: str) -> None:
        if not isinstance(actor, Actor) or not actor.id:
            raise AuthorizationError("Ohne zugeordnete Person ist keine Bearbeitung möglich.")
        if not self.authorizer.authorize(actor, permission, tenant_id):
            raise AuthorizationError(f"Keine Berechtigung für {permission.value}.")

    def _scoped(self, version: RegisterVersion | None, tenant_id: str) -> RegisterVersion | None:
        if version is not None and version.tenant_id != tenant_id:
            raise TenantMismatchError("Das Verzeichnis gehört zu einem anderen Mandanten.")
        return version

    def _event(
        self, actor: Actor, action: str, version: RegisterVersion, **details: object
    ) -> None:
        self.audit.record(
            AuditEvent(
                tenant_id=version.tenant_id,
                actor_id=actor.id,
                action=action,
                entity="register",
                entity_id=version.register_id,
                version=version.version,
                at=self.clock.now(),
                details={"content_hash": version.content_hash, **details},
            )
        )

    def draft(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion | None:
        """Open draft of the register, if any."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)

    def released(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion | None:
        """Currently released version, if any."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)

    def effective(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion | None:
        """Released version if any, otherwise the draft (source-application rule)."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return self._effective(tenant_id, register_id)

    def _effective(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        released = self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)
        if released is not None:
            return released
        return self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)

    def history(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> tuple[RegisterVersion, ...]:
        """All versions of the register, newest first."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        versions = self.repository.list_versions(tenant_id, register_id)
        return tuple(v for v in versions if self._scoped(v, tenant_id) is not None)

    def save_draft(
        self,
        tenant_id: str,
        actor: Actor,
        content: Mapping[str, Any],
        *,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Create the next draft or replace the open draft (revision required).

        Released versions stay untouched; editors of the draft accumulate so
        that none of them can release it.
        """
        self._allow(actor, Permission.REGISTER_EDIT, tenant_id)
        data = normalize_content(content, self.ids, scheme=self.identifier_scheme)
        digest = content_hash(data)
        now = self.clock.now()
        draft = self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)
        if draft is not None:
            if expected_revision != draft.revision:
                raise StaleRevisionError(
                    f"Der Entwurf wurde inzwischen geändert (Revision {draft.revision}). "
                    "Bitte neu laden."
                )
            editors = draft.editors if actor.id in draft.editors else (*draft.editors, actor.id)
            updated = replace(
                draft,
                content=data,
                content_hash=digest,
                editors=editors,
                created_by=actor.id,
                created_at=now,
                revision=draft.revision + 1,
            )
            self.repository.replace(updated, expected_revision)
            self._event(actor, "register.draft_saved", updated)
            return updated
        if expected_revision is not None:
            raise StaleRevisionError("Es gibt keinen offenen Entwurf mit dieser Revision.")
        versions = self.repository.list_versions(tenant_id, register_id)
        released = self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)
        number = max((v.version for v in versions), default=0) + 1
        created = RegisterVersion(
            tenant_id=tenant_id,
            register_id=register_id,
            version=number,
            status=RegisterStatus.DRAFT,
            content=data,
            content_hash=digest,
            created_by=actor.id,
            created_at=now,
            editors=(actor.id,),
            predecessor_version=released.version if released else None,
        )
        self.repository.add(created)
        self._event(actor, "register.draft_created", created)
        return created

    def release(
        self,
        tenant_id: str,
        actor: Actor,
        *,
        expected_revision: int,
        register_id: str = DEFAULT_REGISTER,
    ) -> RegisterVersion:
        """Four-eyes release of the open draft; the previous release is superseded."""
        self._allow(actor, Permission.REGISTER_RELEASE, tenant_id)
        draft = self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)
        if draft is None:
            raise ConflictError(
                f"Es liegt kein offener Entwurf für '{register_id}' zur Freigabe vor."
            )
        if draft.revision != expected_revision:
            raise StaleRevisionError("Der Entwurf wurde seit dem Laden geändert.")
        if actor.id in draft.editors:
            raise FourEyesViolation(
                "Vier-Augen-Prinzip verletzt: Die Kennung "
                f"'{actor.id}' hat diesen Entwurf bearbeitet und darf ihn nicht freigeben. "
                "Die Freigabe muss durch eine zweite fachkundige Person erfolgen."
            )
        blocking = [i for i in check_register(draft.content, self.profile) if i.blocking]
        if self.require_complete_release and blocking:
            raise ConflictError(
                f"Das Verzeichnis ist unvollständig ({len(blocking)} Pflichtangaben fehlen), "
                f"zuerst: {blocking[0].message}."
            )
        previous = self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)
        released = replace(
            draft,
            status=RegisterStatus.RELEASED,
            released_by=actor.id,
            released_at=self.clock.now(),
            predecessor_version=previous.version if previous else None,
            revision=draft.revision + 1,
        )
        self.repository.replace(released, expected_revision)
        if previous is not None:
            self.repository.mark_superseded(
                tenant_id, register_id, previous.version, previous.revision
            )
        self._event(
            actor, "register.released", released, superseded=previous.version if previous else None
        )
        return released

    def activity(
        self, tenant_id: str, actor: Actor, activity_id: str, register_id: str = DEFAULT_REGISTER
    ) -> tuple[Mapping[str, Any], RegisterVersion]:
        """Activity of the effective version together with that version."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return find_activity(self._effective(tenant_id, register_id), activity_id)
