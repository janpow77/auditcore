"""Aufbewahrung und Löschlauf (aus ``app/pipeline/retention.py``).

Übernommen sind Richtlinienwerte, Auswahlkriterien, Löschstrategien
(Anonymisieren, weich, hart), Ergebniszählung, Fehler je Eintrag und
Audit-Ereignisse. Datenbank, Richtlinienverwaltung und Jobprotokoll bleiben
in der Anwendung (Port ``RetentionStore``).

Beibehaltene Befunde des Originals (siehe ``docs/behavior-changes.md``):
nur ``processing_logs_days`` wird durchgesetzt (PL-L07), ein Probelauf
zählt Einträge als „gelöscht“ (PL-L08), weich gelöschte Läufe ohne
``deleted_at`` erhalten den Status ``marked_for_deletion`` und werden danach
nie mehr ausgewählt (PL-L09).

Entscheidung D7 (2026-09-23, „alle empfehlungen“): Mit
``categories=ALL_CATEGORIES`` setzt der Löschlauf alle fünf Fristen durch.
Für die Kategorien außer ``processing_logs`` fragt er den optionalen
Port ``find_expired_artifacts(category, cutoff, limit)`` ab. Fehlt dieser
Port, wird das als Fehler je Kategorie gemeldet statt still übergangen.
Die Voreinstellung ``LEGACY_CATEGORIES`` bleibt originalgetreu.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Protocol

from auditcore_documents.pipeline.audit import AuditSink
from auditcore_documents.pipeline.context import PipelineValueError, utc_now

FINISHED_STATUSES = ("ok", "failed", "rejected")
SWEEP_LIMIT = 1000

#: Kategorie → Feld der Richtlinie mit der Frist in Tagen.
CATEGORY_DAYS_FIELD = {
    "original_documents": "original_document_days",
    "ocr_raw_output": "ocr_raw_output_days",
    "structured_extraction": "structured_extraction_days",
    "processing_logs": "processing_logs_days",
    "audit_events": "audit_events_days",
}
ALL_CATEGORIES: tuple[str, ...] = tuple(CATEGORY_DAYS_FIELD)
LEGACY_CATEGORIES: tuple[str, ...] = ("processing_logs",)


@dataclass
class RetentionPolicyConfig:
    name: str
    description: str | None = None
    is_default: bool = False
    original_document_days: int = 2555
    ocr_raw_output_days: int = 365
    structured_extraction_days: int = 2555
    processing_logs_days: int = 90
    audit_events_days: int = 3650
    anonymize_instead_of_delete: bool = False
    deletion_strategy: Literal["hard", "soft"] = "soft"
    soft_delete_grace_days: int = 30

    def __post_init__(self) -> None:
        if self.deletion_strategy not in ("hard", "soft"):
            raise PipelineValueError(f"deletion_strategy: {self.deletion_strategy!r}")


class RetentionStore(Protocol):
    """Port der Anwendung (Abfrage wie ``select(PipelineRun)`` im Original)."""

    async def find_expired_runs(
        self, cutoff: datetime, statuses: tuple[str, ...], limit: int
    ) -> Sequence[object]: ...

    async def delete_record(self, item: Any) -> None: ...

    async def commit(self) -> None: ...


class ArtifactRetentionStore(RetentionStore, Protocol):
    """Erweiterter Port für alle fünf Fristen (Entscheidung D7)."""

    async def find_expired_artifacts(
        self, category: str, cutoff: datetime, limit: int
    ) -> Sequence[object]: ...


FileRemover = Callable[[str], int]


def remove_local_file(file_path: str) -> int:
    """Datei löschen und Größe liefern; jeder Fehler ergibt 0 (wie im Original)."""
    try:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            path.unlink()
            return size
    except Exception:  # noqa: BLE001 - Originalvertrag
        return 0
    return 0


def cutoff_for(days: int, now: datetime) -> datetime:
    return now - timedelta(days=days)


def is_expired_run(
    created_at: datetime, status: str, policy: RetentionPolicyConfig, now: datetime
) -> bool:
    """Auswahlkriterium des Originals: abgeschlossen und älter als ``processing_logs_days``."""
    return created_at < cutoff_for(policy.processing_logs_days, now) and status in FINISHED_STATUSES


def anonymize_record(item: object) -> None:
    if hasattr(item, "user_id"):
        item.user_id = None
    if hasattr(item, "error"):
        item.error = "[ANONYMIZED]" if item.error else None
    if hasattr(item, "ocr_metrics"):
        item.ocr_metrics = None
    if hasattr(item, "validation_results"):
        item.validation_results = None


def soft_delete_record(item: object, grace_days: int, now: datetime) -> None:
    if hasattr(item, "deleted_at"):
        item.deleted_at = now + timedelta(days=grace_days)
    elif hasattr(item, "status"):
        item.status = "marked_for_deletion"


@dataclass
class SweepOutcome:
    processed: int = 0
    deleted: int = 0
    anonymized: int = 0
    bytes_freed: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)


class RetentionSweeper:
    def __init__(
        self,
        store: RetentionStore,
        audit_service: AuditSink | None = None,
        *,
        remove_file: FileRemover = remove_local_file,
        clock: Callable[[], datetime] = utc_now,
        categories: tuple[str, ...] = LEGACY_CATEGORIES,
    ) -> None:
        unknown = [c for c in categories if c not in CATEGORY_DAYS_FIELD]
        if unknown:
            raise PipelineValueError(f"Unbekannte Aufbewahrungskategorie: {unknown}")
        self.store = store
        self.audit = audit_service
        self.remove_file = remove_file
        self.clock = clock
        self.categories = tuple(categories)

    async def process(self, policy: RetentionPolicyConfig, dry_run: bool = False) -> SweepOutcome:
        now = self.clock()
        outcome = SweepOutcome()
        for category in self.categories:
            days = int(getattr(policy, CATEGORY_DAYS_FIELD[category]))
            cutoff = cutoff_for(days, now)
            if category == "processing_logs":
                items = await self.store.find_expired_runs(cutoff, FINISHED_STATUSES, SWEEP_LIMIT)
            else:
                finder = getattr(self.store, "find_expired_artifacts", None)
                if finder is None:
                    outcome.errors.append(
                        {
                            "artifact_type": category,
                            "item_id": "*",
                            "error": "Store unterstützt find_expired_artifacts nicht",
                        }
                    )
                    continue
                items = await finder(category, cutoff, SWEEP_LIMIT)
            await self._sweep(category, days, items, policy, dry_run, outcome)
        await self.store.commit()
        return outcome

    async def _sweep(
        self,
        artifact_type: str,
        days: int,
        items: Sequence[object],
        policy: RetentionPolicyConfig,
        dry_run: bool,
        outcome: SweepOutcome,
    ) -> None:
        outcome.processed += len(items)
        for item in items:
            try:
                if dry_run:
                    outcome.deleted += 1
                    continue
                if policy.anonymize_instead_of_delete:
                    anonymize_record(item)
                    outcome.anonymized += 1
                    if self.audit is not None:
                        await self.audit.log_event(
                            event_type="ANONYMIZED_BY_POLICY",
                            document_id=getattr(item, "document_id", "unknown"),
                            actor_type="SCHEDULER",
                            actor_id="retention_sweeper",
                            details={
                                "artifact_type": artifact_type,
                                "policy_name": policy.name,
                                "retention_days": days,
                            },
                        )
                else:
                    if policy.deletion_strategy == "soft":
                        soft_delete_record(item, policy.soft_delete_grace_days, self.clock())
                    else:
                        outcome.bytes_freed += await self._hard_delete(item)
                    outcome.deleted += 1
                    if self.audit is not None:
                        await self.audit.log_event(
                            event_type="DELETED_BY_POLICY",
                            document_id=getattr(item, "document_id", "unknown"),
                            actor_type="SCHEDULER",
                            actor_id="retention_sweeper",
                            details={
                                "artifact_type": artifact_type,
                                "policy_name": policy.name,
                                "retention_days": days,
                                "deletion_strategy": policy.deletion_strategy,
                            },
                        )
            except Exception as exc:  # noqa: BLE001 - Originalvertrag: Fehler je Eintrag
                item_id = getattr(item, "run_id", None) or getattr(item, "id", None)
                outcome.errors.append(
                    {"artifact_type": artifact_type, "item_id": str(item_id), "error": str(exc)}
                )

    async def _hard_delete(self, item: Any) -> int:
        freed = 0
        if getattr(item, "input_uri", None):
            freed += self.remove_file(item.input_uri)
        if getattr(item, "output_uri", None):
            freed += self.remove_file(item.output_uri)
        if getattr(item, "file_path", None):
            freed += self.remove_file(item.file_path)
        await self.store.delete_record(item)
        return freed

    async def run(
        self, policy: RetentionPolicyConfig | None, dry_run: bool = False
    ) -> dict[str, Any]:
        """Jobergebnis wie ``run_sweeper`` (ohne Speicherung des Jobs)."""
        if policy is None:
            raise ValueError("No retention policy found")
        job: dict[str, Any] = {"status": "running", "started_at": self.clock()}
        try:
            outcome = await self.process(policy, dry_run=dry_run)
            job.update(
                artifacts_processed=outcome.processed,
                artifacts_deleted=outcome.deleted,
                artifacts_anonymized=outcome.anonymized,
                bytes_freed=outcome.bytes_freed,
                errors=outcome.errors or None,
                status="completed",
            )
        except Exception as exc:  # noqa: BLE001 - Originalvertrag
            job.update(status="failed", errors=[{"error": str(exc)}])
        job["completed_at"] = self.clock()
        return job
