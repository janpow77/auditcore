"""Persistenz der Laufdaten und Artefakte über Ports (aus ``stages/persist.py``).

``run_create_fields``/``run_update_fields`` liefern exakt die Felder, die das
Original in ``PipelineRun`` schreibt; ``artifact_files`` die Dateien samt
JSON-Format. ``RunRepository`` und ``ArtifactStore`` sind Ports; Fehler
beenden die Stufe wie im Original nicht, sondern gehen an ``on_error``.
``FileArtifactStore`` weist Schlüssel außerhalb des Basisverzeichnisses ab.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage


class RunRepository(Protocol):
    async def upsert(self, run_id: str, create: dict[str, Any], update: dict[str, Any]) -> None: ...


class ArtifactStore(Protocol):
    async def store(self, key: str, data: bytes) -> None: ...


def run_update_fields(context: PipelineContext, now: Any) -> dict[str, Any]:
    return {
        "status": context.status.value,
        "current_stage": context.current_stage,
        "completed_stages": context.completed_stages,
        "hash_original": context.hash_original,
        "hash_chain": context.hash_chain,
        "compute_profile_accepted": (
            context.compute_profile_accepted.value if context.compute_profile_accepted else None
        ),
        "total_duration_ms": context.total_duration_ms,
        "stage_metrics": (
            [m.to_dict() for m in context.stage_metrics] if context.stage_metrics else None
        ),
        "ocr_metrics": context.ocr_metrics.to_dict() if context.ocr_metrics else None,
        "validation_flags": context.validation_flags,
        "validation_results": (
            [r.to_dict() for r in context.validation_results]
            if context.validation_results
            else None
        ),
        "pipeline_version": context.pipeline_version,
        "ocr_engine_version": context.ocr_engine_version,
        "ruleset_id": context.ruleset_id,
        "ruleset_version": context.ruleset_version,
        "error": context.error,
        "error_code": context.error_code,
        "retryable": context.retryable,
        "completed_at": context.completed_at,
        "updated_at": now,
    }


def run_create_fields(context: PipelineContext) -> dict[str, Any]:
    return {
        "run_id": context.run_id,
        "document_id": context.document_id,
        "project_id": context.project_id,
        "user_id": context.user_id,
        "status": context.status.value,
        "current_stage": context.current_stage,
        "completed_stages": context.completed_stages,
        "hash_original": context.hash_original,
        "hash_chain": context.hash_chain,
        "compute_profile_requested": (
            context.compute_profile_requested.value if context.compute_profile_requested else None
        ),
        "compute_profile_accepted": (
            context.compute_profile_accepted.value if context.compute_profile_accepted else None
        ),
        "total_duration_ms": context.total_duration_ms,
        "stage_metrics": (
            [m.to_dict() for m in context.stage_metrics] if context.stage_metrics else None
        ),
        "ocr_metrics": context.ocr_metrics.to_dict() if context.ocr_metrics else None,
        "validation_flags": context.validation_flags,
        "validation_results": (
            [r.to_dict() for r in context.validation_results]
            if context.validation_results
            else None
        ),
        "pipeline_version": context.pipeline_version,
        "ocr_engine_version": context.ocr_engine_version,
        "ruleset_id": context.ruleset_id,
        "ruleset_version": context.ruleset_version,
        "input_uri": context.input_uri,
        "created_at": context.created_at,
        "completed_at": context.completed_at,
    }


def artifact_files(context: PipelineContext) -> dict[str, bytes]:
    """Relative Dateinamen → Inhalt; Formate wie im Original (``indent=2``)."""
    files: dict[str, bytes] = {}
    artifacts = context.artifacts
    if artifacts.ocr_text:
        files["ocr_text.txt"] = artifacts.ocr_text.encode("utf-8")
    if artifacts.ocr_raw_json:
        files["ocr_raw.json"] = json.dumps(artifacts.ocr_raw_json, indent=2).encode("utf-8")
    if artifacts.normalized_json:
        files["normalized.json"] = json.dumps(artifacts.normalized_json, indent=2).encode("utf-8")
    if artifacts.extracted_fields:
        files["extracted_fields.json"] = json.dumps(artifacts.extracted_fields, indent=2).encode(
            "utf-8"
        )
    if context.validation_results:
        files["validation_results.json"] = json.dumps(
            [r.to_dict() for r in context.validation_results], indent=2, default=str
        ).encode("utf-8")
    if context.stage_metrics:
        files["stage_metrics.json"] = json.dumps(
            [m.to_dict() for m in context.stage_metrics], indent=2, default=str
        ).encode("utf-8")
    return files


def stored_artifact_names(context: PipelineContext) -> list[str]:
    names = []
    artifacts = context.artifacts
    if artifacts.ocr_text:
        names.append("ocr_text")
    if artifacts.ocr_raw_json:
        names.append("ocr_raw_json")
    if artifacts.normalized_json:
        names.append("normalized_json")
    if artifacts.extracted_fields:
        names.append("extracted_fields")
    if context.validation_results:
        names.append("validation_results")
    if context.stage_metrics:
        names.append("stage_metrics")
    return names


class FileArtifactStore:
    """Ablage unter ``<base>/pipeline_artifacts/<key>`` wie im Original, ohne Ausbruch."""

    def __init__(self, base: Path) -> None:
        self.root = (base / "pipeline_artifacts").resolve()

    async def store(self, key: str, data: bytes) -> None:
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError(f"Artefaktschlüssel verlässt das Ablageverzeichnis: {key}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


class PersistStage(PipelineStage):
    name = "persist"
    description = "Persist all artifacts and run data"

    def __init__(
        self,
        *args: object,
        repository: RunRepository | None = None,
        store: ArtifactStore | None = None,
        on_error: Callable[[str, BaseException], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.repository = repository
        self.store = store
        self.on_error = on_error

    def _report(self, where: str, exc: BaseException) -> None:
        if self.on_error is not None:
            self.on_error(where, exc)

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        if self.repository is not None:
            try:
                await self.repository.upsert(
                    context.run_id,
                    run_create_fields(context),
                    run_update_fields(context, context.clock()),
                )
            except Exception as exc:  # noqa: BLE001 - Original: Rollback, Pipeline läuft weiter
                self._report("run", exc)
        if context.storage_key and self.store is not None:
            for name, data in artifact_files(context).items():
                try:
                    await self.store.store(f"{context.storage_key}/{name}", data)
                except Exception as exc:  # noqa: BLE001 - Original: Warnung, weiter
                    self._report(name, exc)
        if self.audit:
            await self.audit.log_event(
                event_type="PERSISTED",
                document_id=context.document_id,
                run_id=context.run_id,
                hash_original=context.hash_original,
                details={
                    "storage_key": context.storage_key,
                    "artifacts_stored": stored_artifact_names(context),
                    "total_duration_ms": context.total_duration_ms,
                },
            )
        return context
