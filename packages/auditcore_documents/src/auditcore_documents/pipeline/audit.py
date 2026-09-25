"""Revisionssichere Audit-Ereignisse als Port (aus ``app/pipeline/audit.py``).

Das Original schreibt über SQLAlchemy in eine WORM-Tabelle. Die Bibliothek
definiert Ereignistypen, das unveränderliche Ereignis und den Port
``AuditSink``; ``InMemoryAuditLog`` ist eine Referenz ohne Update/Delete.
Persistenz, DB-Trigger und Abfragen bleiben in der Anwendung.
"""

from __future__ import annotations

import copy
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Literal, Protocol

from auditcore_documents.pipeline.context import utc_now

ActorType = Literal["SYSTEM", "USER", "SCHEDULER", "API"]


class AuditEventType:
    INGESTED = "INGESTED"
    INGESTION_STARTED = "INGESTION_STARTED"
    INGESTION_DONE = "INGESTION_DONE"
    INGESTION_FAILED = "INGESTION_FAILED"
    PREPROCESS_STARTED = "PREPROCESS_STARTED"
    PREPROCESS_DONE = "PREPROCESS_DONE"
    PREPROCESS_FAILED = "PREPROCESS_FAILED"
    OCR_STARTED = "OCR_STARTED"
    OCR_DONE = "OCR_DONE"
    OCR_FAILED = "OCR_FAILED"
    OCR_CONFIDENCE_LOW = "OCR_CONFIDENCE_LOW"
    POSTPROCESS_STARTED = "POSTPROCESS_STARTED"
    POSTPROCESS_DONE = "POSTPROCESS_DONE"
    POSTPROCESS_FAILED = "POSTPROCESS_FAILED"
    VALIDATION_STARTED = "VALIDATION_STARTED"
    VALIDATION_COMPLETE = "VALIDATION_COMPLETE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PERSIST_STARTED = "PERSIST_STARTED"
    PERSISTED = "PERSISTED"
    PERSIST_FAILED = "PERSIST_FAILED"
    EXPORT_STARTED = "EXPORT_STARTED"
    EXPORTED = "EXPORTED"
    EXPORT_FAILED = "EXPORT_FAILED"
    PIPELINE_STARTED = "PIPELINE_STARTED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    PIPELINE_FAILED = "PIPELINE_FAILED"
    MOVED_TO_REVIEW = "MOVED_TO_REVIEW"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    COMPUTE_PROFILE_REQUESTED = "COMPUTE_PROFILE_REQUESTED"
    COMPUTE_PROFILE_ACCEPTED = "COMPUTE_PROFILE_ACCEPTED"
    COMPUTE_PROFILE_DOWNGRADED = "COMPUTE_PROFILE_DOWNGRADED"
    RETENTION_POLICY_APPLIED = "RETENTION_POLICY_APPLIED"
    DELETED_BY_POLICY = "DELETED_BY_POLICY"
    ANONYMIZED_BY_POLICY = "ANONYMIZED_BY_POLICY"
    PROFILE_CREATED = "PROFILE_CREATED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    PROFILE_DELETED = "PROFILE_DELETED"
    ENDPOINT_CREATED = "ENDPOINT_CREATED"
    ENDPOINT_UPDATED = "ENDPOINT_UPDATED"
    ENDPOINT_DELETED = "ENDPOINT_DELETED"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        return tuple(v for k, v in vars(cls).items() if k.isupper() and isinstance(v, str))


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class AuditEvent:
    """Unveränderliches Ereignis; ``details`` ist schreibgeschützt."""

    id: str
    timestamp: datetime
    event_type: str
    document_id: str
    run_id: str | None = None
    project_id: str | None = None
    actor_type: ActorType = "SYSTEM"
    actor_id: str = "pipeline"
    hash_original: str | None = None
    details: Any = None
    pipeline_version: str | None = None
    ocr_engine_version: str | None = None
    ruleset_version: str | None = None

    def details_dict(self) -> Any:
        """Tiefe, veränderbare Kopie der Details (für JSON/Persistenz)."""

        def thaw(value: object) -> object:
            if isinstance(value, MappingProxyType):
                return {k: thaw(v) for k, v in value.items()}
            if isinstance(value, tuple):
                return [thaw(v) for v in value]
            return value

        return thaw(self.details)


class AuditSink(Protocol):
    """Port: nimmt ein Ereignis entgegen (nur Einfügen)."""

    async def log_event(
        self,
        event_type: str,
        document_id: str,
        run_id: str | None = None,
        project_id: str | None = None,
        actor_type: ActorType = "SYSTEM",
        actor_id: str = "pipeline",
        hash_original: str | None = None,
        details: dict[str, Any] | None = None,
        pipeline_version: str | None = None,
        ocr_engine_version: str | None = None,
        ruleset_version: str | None = None,
    ) -> object: ...


@dataclass
class InMemoryAuditLog:
    """Referenz-Senke: nur Anhängen; gelesene Ereignisse sind unveränderlich."""

    clock: Callable[[], datetime] = utc_now
    id_factory: Callable[[], str] = field(default=lambda: str(uuid.uuid4()))
    _events: list[AuditEvent] = field(default_factory=list, repr=False)

    async def log_event(
        self,
        event_type: str,
        document_id: str,
        run_id: str | None = None,
        project_id: str | None = None,
        actor_type: ActorType = "SYSTEM",
        actor_id: str = "pipeline",
        hash_original: str | None = None,
        details: dict[str, Any] | None = None,
        pipeline_version: str | None = None,
        ocr_engine_version: str | None = None,
        ruleset_version: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=self.id_factory(),
            timestamp=self.clock(),
            event_type=event_type,
            document_id=document_id,
            run_id=run_id,
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            hash_original=hash_original,
            details=_freeze(copy.deepcopy(details)),
            pipeline_version=pipeline_version,
            ocr_engine_version=ocr_engine_version,
            ruleset_version=ruleset_version,
        )
        self._events.append(event)
        return event

    def __iter__(self) -> Iterator[AuditEvent]:
        return iter(tuple(self._events))

    def __len__(self) -> int:
        return len(self._events)

    def events(
        self, *, document_id: str | None = None, run_id: str | None = None
    ) -> list[AuditEvent]:
        return [
            e
            for e in self._events
            if (document_id is None or e.document_id == document_id)
            and (run_id is None or e.run_id == run_id)
        ]
