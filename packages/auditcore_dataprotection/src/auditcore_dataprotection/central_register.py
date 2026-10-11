"""Transfer of a released register version to the central register (Hausverzeichnis).

"Exportiert", "übertragen" and "übernommen" are different states (LIB-19);
"übernommen" needs a receipt with the central identifier. A transfer is keyed
by register, version and content hash, so sending the same version again is
idempotent and never creates a duplicate (LIB-18, T-25). A missing or
conflicting receipt never reads as taken over (T-26). The central register is
reached only through an explicitly configured port; the library itself makes
no network calls.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol, runtime_checkable

from .access import require_permission
from .errors import ConflictError, NotFoundError, ValidationError
from .model import Actor, AuditEvent, Permission, RegisterStatus, RegisterVersion
from .ports import AuditSink, Authorizer, Clock
from .status import TransferStatus

RECEIPT_RECEIVED = "empfangen"
RECEIPT_TAKEN_OVER = "uebernommen"
RECEIPT_CONFLICT = "konflikt"
RECEIPT_STATUSES = (RECEIPT_RECEIVED, RECEIPT_TAKEN_OVER, RECEIPT_CONFLICT)


class CentralRegisterUnavailable(ConflictError):
    """The central register cannot be reached; nothing in operation is switched off."""

    code = "central_register_unavailable"


@dataclass(frozen=True)
class Receipt:
    """Answer of the central register."""

    status: str
    central_id: str = ""
    message: str = ""


@runtime_checkable
class CentralRegisterPort(Protocol):
    """Explicitly configured connection to the central register."""

    def submit(self, key: str, payload: Mapping[str, object]) -> Receipt:
        """Submit one version; the same key must not create a second entry."""
        ...


@dataclass(frozen=True)
class TransferRecord:
    """State of one register version towards the central register."""

    tenant_id: str
    key: str
    register_id: str
    version: int
    content_hash: str
    status: TransferStatus
    central_id: str = ""
    message: str = ""
    updated_by: str = ""
    updated_at: datetime | None = None
    proof: str = ""


@runtime_checkable
class TransferRepository(Protocol):
    """Tenant-scoped storage of transfer records."""

    def get(self, tenant_id: str, key: str) -> TransferRecord | None:
        """Record of one version key or None."""
        ...

    def put(self, record: TransferRecord) -> None:
        """Insert or replace the record of its key."""
        ...

    def latest(self, tenant_id: str, register_id: str) -> TransferRecord | None:
        """Record of the highest transferred version of a register, if any."""
        ...


def transfer_key(version: RegisterVersion) -> str:
    """Idempotency key: register, version and content hash."""
    return f"{version.register_id}:{version.version}:{version.content_hash}"


@dataclass
class CentralRegisterService:
    """Exports, transfers and confirmations of released register versions."""

    repository: TransferRepository
    authorizer: Authorizer
    audit: AuditSink
    clock: Clock
    port: CentralRegisterPort | None = None

    def _allow(self, actor: Actor, permission: Permission, tenant_id: str) -> None:
        require_permission(self.authorizer, actor, permission, tenant_id)

    def _store(self, actor: Actor, record: TransferRecord, action: str) -> TransferRecord:
        self.repository.put(record)
        self.audit.record(
            AuditEvent(
                record.tenant_id,
                actor.id,
                action,
                "central_register",
                record.key,
                record.version,
                self.clock.now(),
                {"status": record.status.value, "central_id": record.central_id},
            )
        )
        return record

    def _base(self, version: RegisterVersion) -> TransferRecord:
        if version.status is not RegisterStatus.RELEASED:
            raise ConflictError("Nur eine freigegebene Fassung kann übertragen werden.")
        return TransferRecord(
            version.tenant_id,
            transfer_key(version),
            version.register_id,
            version.version,
            version.content_hash,
            TransferStatus.NOT_TRANSFERRED,
        )

    def mark_exported(self, actor: Actor, version: RegisterVersion) -> TransferRecord:
        """A file was produced; that is neither a transfer nor a takeover."""
        self._allow(actor, Permission.CENTRAL_REGISTER_TRANSFER, version.tenant_id)
        existing = self.repository.get(version.tenant_id, transfer_key(version))
        if existing is not None and existing.status is not TransferStatus.NOT_TRANSFERRED:
            return existing
        record = replace(
            self._base(version),
            status=TransferStatus.EXPORTED,
            updated_by=actor.id,
            updated_at=self.clock.now(),
        )
        return self._store(actor, record, "central_register.exported")

    def transfer(
        self, actor: Actor, version: RegisterVersion, payload: Mapping[str, object]
    ) -> TransferRecord:
        """Submit once; a repeated call for the same version returns the stored state."""
        self._allow(actor, Permission.CENTRAL_REGISTER_TRANSFER, version.tenant_id)
        base = self._base(version)
        existing = self.repository.get(version.tenant_id, base.key)
        if existing is not None and existing.status in (
            TransferStatus.TRANSFERRED,
            TransferStatus.TAKEN_OVER,
        ):
            return existing
        if self.port is None:
            raise ConflictError("Es ist keine Verbindung zum zentralen Verzeichnis konfiguriert.")
        try:
            receipt = self.port.submit(base.key, payload)
        except (OSError, TimeoutError, CentralRegisterUnavailable) as exc:
            raise CentralRegisterUnavailable(
                "Das zentrale Verzeichnis ist nicht erreichbar. Der Stand bleibt unverändert; "
                "die Übertragung ist später nachzuführen. Der laufende Betrieb ist davon "
                "nicht berührt."
            ) from exc
        record = replace(
            base,
            status=_status_of(receipt),
            central_id=receipt.central_id,
            message=receipt.message,
            updated_by=actor.id,
            updated_at=self.clock.now(),
        )
        return self._store(actor, record, "central_register.transferred")

    def confirm_takeover(
        self, actor: Actor, tenant_id: str, key: str, *, central_id: str, proof: str
    ) -> TransferRecord:
        """The central register body confirms the takeover with identifier and proof."""
        self._allow(actor, Permission.CENTRAL_REGISTER_CONFIRM, tenant_id)
        record = self.repository.get(tenant_id, key)
        if record is None:
            raise NotFoundError("Zu dieser Fassung gibt es keine Übertragung.")
        if not central_id.strip() or not proof.strip():
            raise ValidationError("Die Übernahme braucht zentrale Kennung und Nachweis.")
        if record.status not in (TransferStatus.TRANSFERRED, TransferStatus.TAKEN_OVER):
            raise ConflictError(
                f"Übernahme kann im Stand „{record.status.value}“ nicht bestätigt werden."
            )
        confirmed = replace(
            record,
            status=TransferStatus.TAKEN_OVER,
            central_id=central_id.strip(),
            proof=proof.strip(),
            updated_by=actor.id,
            updated_at=self.clock.now(),
        )
        return self._store(actor, confirmed, "central_register.confirmed")


def _status_of(receipt: Receipt) -> TransferStatus:
    """Only a takeover receipt with a central id counts as taken over."""
    if receipt.status not in RECEIPT_STATUSES:
        raise ValidationError(f"Unbekannte Rückmeldung des Verzeichnisses „{receipt.status}“.")
    if receipt.status == RECEIPT_CONFLICT:
        return TransferStatus.CONFLICT
    if receipt.status == RECEIPT_TAKEN_OVER and receipt.central_id.strip():
        return TransferStatus.TAKEN_OVER
    return TransferStatus.TRANSFERRED


def transfer_status(
    record: TransferRecord | None, version: RegisterVersion | None
) -> TransferStatus:
    """Axis value for the current released version (an older takeover does not count)."""
    if record is None or version is None or record.key != transfer_key(version):
        return TransferStatus.NOT_TRANSFERRED
    return record.status
