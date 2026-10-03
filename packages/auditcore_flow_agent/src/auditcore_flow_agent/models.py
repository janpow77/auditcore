"""Unveränderliche Aufträge; technische Standardwerte sind pro Auftrag überschreibbar."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast

from auditcore_common.frozen import freeze
from auditcore_common.json_values import JsonValue, jsonable

from .validation import identifier, integer, names, number, positive


class State(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    RETRY = "retry"
    RECOVERING = "recovering"
    CANCELLING = "cancelling"
    PAUSING = "pausing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


TERMINAL = frozenset({State.SUCCEEDED, State.FAILED, State.BLOCKED, State.CANCELLED})


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_s: float = 5
    max_delay_s: float = 300

    def __post_init__(self) -> None:
        integer(self.max_attempts, "max_attempts", minimum=1)
        positive(self.initial_delay_s, "initial_delay_s")
        number(self.max_delay_s, "max_delay_s", minimum=self.initial_delay_s)

    def delay(self, attempts: int) -> float:
        """Gedeckelte Wartezeit; auch sehr große Versuchszahlen bleiben beschränkt."""
        integer(attempts, "attempts", minimum=1)
        return min(self.max_delay_s, self.initial_delay_s * 2.0 ** min(attempts - 1, 60))


@dataclass(frozen=True)
class ResourceRequest:
    cpus: int = 1
    memory_mb: int = 0
    gpu_count: int = 0
    min_vram_mb: int = 0

    def __post_init__(self) -> None:
        integer(self.cpus, "cpus", minimum=1)
        integer(self.memory_mb, "memory_mb")
        integer(self.gpu_count, "gpu_count")
        integer(self.min_vram_mb, "min_vram_mb")
        if self.gpu_count == 0 and self.min_vram_mb:
            raise ValueError("VRAM-Anforderung benötigt mindestens eine GPU.")


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    scope: str
    capability: str
    resources: ResourceRequest = field(default_factory=ResourceRequest)
    payload: Mapping[str, JsonValue] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    priority: int = 0
    not_before: float = 0
    timeout_s: float = 3600
    lease_s: float = 30
    stall_timeout_s: float | None = None
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    model: str | None = None
    allowed_nodes: tuple[str, ...] = ()
    preferred_nodes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.job_id, self.scope, self.capability):
            identifier(value)
        for values in (self.dependencies, self.allowed_nodes, self.preferred_nodes):
            names(values)
        if self.job_id in self.dependencies:
            raise ValueError("Ein Auftrag darf nicht von sich selbst abhängen.")
        integer(self.priority, "priority")
        number(self.not_before, "not_before")
        for key in ("timeout_s", "lease_s"):
            positive(getattr(self, key), key)
        if self.stall_timeout_s is not None:
            positive(self.stall_timeout_s, "stall_timeout_s")
        if self.model is not None:
            identifier(self.model)
        if not isinstance(self.resources, ResourceRequest) or not isinstance(
            self.retry, RetryPolicy
        ):
            raise ValueError("Ressourcen- und Wiederholungsregeln fehlen.")
        self._freeze_payload()

    def _freeze_payload(self) -> None:
        if not isinstance(self.payload, Mapping) or not all(
            isinstance(k, str) for k in self.payload
        ):
            raise ValueError("payload muss ein JSON-Objekt mit Textschlüsseln sein.")
        encoded = json.dumps(jsonable(self.payload), allow_nan=False)
        object.__setattr__(self, "payload", freeze(json.loads(encoded)))


@dataclass(frozen=True)
class Job:
    spec: JobSpec
    state: State
    attempts: int
    available_at: float
    created_at: float
    error: str = ""


@dataclass(frozen=True)
class Lease:
    token: str
    job: JobSpec
    node_id: str
    gpu_ids: tuple[str, ...]
    attempt: int
    started_at: float
    expires_at: float
    deadline: float


@dataclass(frozen=True)
class StopRequest:
    token: str
    node_id: str
    scope: str
    job_id: str
    reason: str


@dataclass(frozen=True)
class Outcome:
    kind: str
    message: str = ""
    retry_at: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"succeeded", "retryable", "permanent", "deferred"}:
            raise ValueError("Unbekanntes Auftragsergebnis.")
        if self.kind == "deferred":
            if self.retry_at is None:
                raise ValueError("Zurückstellen benötigt retry_at.")
            number(self.retry_at, "retry_at")
        elif self.retry_at is not None:
            raise ValueError("retry_at ist nur beim Zurückstellen zulässig.")


def payload_dict(spec: JobSpec) -> dict[str, JsonValue]:
    """Veränderbare JSON-Kopie für einen Consumer; der Auftrag bleibt unverändert."""
    return cast(dict[str, JsonValue], jsonable(spec.payload))
