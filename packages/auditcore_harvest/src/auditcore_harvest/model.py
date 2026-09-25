"""Versioned data contracts of the harvest core (``auditcore_harvest.contract/1``).

All records are frozen dataclasses with JSON-compatible payloads. Values a
source does not state stay ``None``/``UNKNOWN``; the core never guesses them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

CONTRACT_VERSION = "auditcore_harvest.contract/1"

#: JSON payload at the source boundary. This is the one deliberate ``Any`` of the
#: contract: raw source documents are only known to be JSON-compatible, and
#: adapters narrow them with ``isinstance`` before use.
JSON = Any
Cursor = Mapping[str, JSON]


class SnapshotSemantics(StrEnum):
    """What a complete run means for the consumer's stored inventory.

    The core never deletes; it only reports whether a run was complete enough
    for the consumer to apply the profile's own replace/deletion rule.
    """

    INCREMENTAL_UPSERT = "incremental_upsert"
    FULL_SNAPSHOT_REPLACE = "full_snapshot_replace"
    APPEND_ONLY = "append_only"
    UNKNOWN = "unknown"


class AuthKind(StrEnum):
    """Credential need of a source; secrets come from the credential provider."""

    NONE = "none"
    API_KEY = "api_key"
    BASIC = "basic"
    TOKEN = "token"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Capabilities:
    """Declared adapter capabilities; ``None`` means explicitly unknown."""

    pagination: bool | None = None
    incremental: bool | None = None
    full_snapshot: bool | None = None
    deletions: bool | None = None

    def to_dict(self) -> dict[str, bool | None]:
        """JSON view."""
        return {
            "pagination": self.pagination,
            "incremental": self.incremental,
            "full_snapshot": self.full_snapshot,
            "deletions": self.deletions,
        }


@dataclass(frozen=True)
class Source:
    """Identity and declared behavior of one source profile."""

    source_id: str
    title: str
    family: str
    adapter_version: str
    profile_version: str
    data_format: str
    auth: AuthKind = AuthKind.UNKNOWN
    capabilities: Capabilities = field(default_factory=Capabilities)
    snapshot_semantics: SnapshotSemantics = SnapshotSemantics.UNKNOWN
    filters: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, JSON]:
        """JSON view."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "family": self.family,
            "adapter_version": self.adapter_version,
            "profile_version": self.profile_version,
            "data_format": self.data_format,
            "auth": self.auth.value,
            "capabilities": self.capabilities.to_dict(),
            "snapshot_semantics": self.snapshot_semantics.value,
            "filters": list(self.filters),
        }


@dataclass(frozen=True)
class HarvestRequest:
    """What the consumer asks for; limits bound every run."""

    source_id: str
    run_id: str
    filters: Mapping[str, JSON] = field(default_factory=dict)
    since: str | None = None
    page_size: int | None = None
    max_pages: int = 100
    max_records: int = 100_000
    max_duration_seconds: float = 3600.0
    resume: bool = True


@dataclass(frozen=True)
class Provenance:
    """Origin of one record."""

    source_id: str
    adapter_version: str
    profile_version: str
    retrieved_at: str
    locator: str
    raw_sha256: str

    def to_dict(self) -> dict[str, str]:
        """JSON view."""
        return {
            "source_id": self.source_id,
            "adapter_version": self.adapter_version,
            "profile_version": self.profile_version,
            "retrieved_at": self.retrieved_at,
            "locator": self.locator,
            "raw_sha256": self.raw_sha256,
        }


def canonical_hash(value: JSON) -> str:
    """SHA-256 over canonical JSON; the stable content hash of a record."""
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class HarvestRecord:
    """One source record: stable id, raw and normalized payload, provenance.

    ``content_hash`` covers the normalized payload and the deletion flag, so a
    re-delivery of unchanged content is recognisable as a duplicate.
    """

    source_id: str
    record_id: str
    raw: JSON
    normalized: Mapping[str, JSON]
    provenance: Provenance
    deleted: bool = False
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("HarvestRecord braucht eine stabile Quellen-ID.")
        if not self.content_hash:
            digest = canonical_hash({"normalized": self.normalized, "deleted": self.deleted})
            object.__setattr__(self, "content_hash", digest)

    @property
    def key(self) -> tuple[str, str]:
        """Identity used for deduplication and idempotent delivery."""
        return (self.source_id, self.record_id)

    def to_dict(self) -> dict[str, JSON]:
        """JSON view (for sinks, fixtures and replay output)."""
        return {
            "source_id": self.source_id,
            "record_id": self.record_id,
            "content_hash": self.content_hash,
            "deleted": self.deleted,
            "normalized": dict(self.normalized),
            "raw": self.raw,
            "provenance": self.provenance.to_dict(),
        }


class PageStatus(StrEnum):
    """Result of one page fetch as seen by the adapter."""

    OK = "ok"
    PARTIAL = "partial"


@dataclass(frozen=True)
class RecordIssue:
    """A single source item that could not be parsed; never dropped silently."""

    locator: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """JSON view."""
        return {"locator": self.locator, "message": self.message}


@dataclass(frozen=True)
class PageResult:
    """One bounded page: records, next cursor and an explicit completion flag.

    ``complete=True`` means the source reported no further page. A page that
    is not complete must carry ``next_cursor``; otherwise the core raises a
    parser error instead of stopping as if everything had been read.
    """

    records: tuple[HarvestRecord, ...]
    next_cursor: Cursor | None
    complete: bool
    status: PageStatus = PageStatus.OK
    issues: tuple[RecordIssue, ...] = ()
    total_hint: int | None = None


def page_result(
    records: Sequence[HarvestRecord],
    issues: Sequence[RecordIssue] = (),
    next_cursor: Cursor | None = None,
    *,
    total_hint: int | None = None,
) -> PageResult:
    """The usual page of an adapter: complete exactly when there is no next cursor.

    The status is ``PARTIAL`` as soon as one item was reported as an issue.
    """
    return PageResult(
        records=tuple(records),
        next_cursor=None if next_cursor is None else dict(next_cursor),
        complete=next_cursor is None,
        status=PageStatus.PARTIAL if issues else PageStatus.OK,
        issues=tuple(issues),
        total_hint=total_hint,
    )


@dataclass(frozen=True)
class Checkpoint:
    """Confirmed progress of a source; advanced only after the sink confirmed."""

    source_id: str
    profile_version: str
    cursor: Cursor | None
    run_id: str
    updated_at: str
    pages_confirmed: int
    records_confirmed: int
    finished: bool

    def to_dict(self) -> dict[str, JSON]:
        """JSON view."""
        return {
            "source_id": self.source_id,
            "profile_version": self.profile_version,
            "cursor": None if self.cursor is None else dict(self.cursor),
            "run_id": self.run_id,
            "updated_at": self.updated_at,
            "pages_confirmed": self.pages_confirmed,
            "records_confirmed": self.records_confirmed,
            "finished": self.finished,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, JSON]) -> Checkpoint:
        """Inverse of :meth:`to_dict`."""
        return cls(
            source_id=str(data["source_id"]),
            profile_version=str(data["profile_version"]),
            cursor=data.get("cursor"),
            run_id=str(data["run_id"]),
            updated_at=str(data["updated_at"]),
            pages_confirmed=int(data["pages_confirmed"]),
            records_confirmed=int(data["records_confirmed"]),
            finished=bool(data["finished"]),
        )


@dataclass(frozen=True)
class SinkReceipt:
    """What the sink confirmed; unknown keys in the receipt are a sink error."""

    accepted: tuple[tuple[str, str], ...]
    duplicates: tuple[tuple[str, str], ...] = ()


class RunStatus(StrEnum):
    """Overall outcome of a run."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class HarvestResult:
    """Structured run result; counts are never inferred from an empty list."""

    source_id: str
    run_id: str
    contract: str
    status: RunStatus
    started_at: str
    finished_at: str
    pages: int
    records_received: int
    records_delivered: int
    duplicates_in_run: int
    duplicates_at_sink: int
    issues: tuple[RecordIssue, ...]
    errors: tuple[Mapping[str, JSON], ...]
    checkpoint_before: Checkpoint | None
    checkpoint_after: Checkpoint | None
    source_exhausted: bool
    snapshot_complete: bool
    attempts: int

    def to_dict(self) -> dict[str, JSON]:
        """JSON view."""
        return {
            "source_id": self.source_id,
            "run_id": self.run_id,
            "contract": self.contract,
            "status": self.status.value,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "pages": self.pages,
            "records_received": self.records_received,
            "records_delivered": self.records_delivered,
            "duplicates_in_run": self.duplicates_in_run,
            "duplicates_at_sink": self.duplicates_at_sink,
            "issues": [i.to_dict() for i in self.issues],
            "errors": [dict(e) for e in self.errors],
            "checkpoint_before": None
            if self.checkpoint_before is None
            else self.checkpoint_before.to_dict(),
            "checkpoint_after": None
            if self.checkpoint_after is None
            else self.checkpoint_after.to_dict(),
            "source_exhausted": self.source_exhausted,
            "snapshot_complete": self.snapshot_complete,
            "attempts": self.attempts,
        }


def iso(moment: datetime) -> str:
    """Timezone-aware ISO timestamp; naive datetimes are rejected."""
    if moment.tzinfo is None:
        raise ValueError("Zeitangaben müssen eine Zeitzone tragen.")
    return moment.isoformat()
