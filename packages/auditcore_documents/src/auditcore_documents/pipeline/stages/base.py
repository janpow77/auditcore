"""Einheitlicher Stufenvertrag (aus ``app/pipeline/stages/base.py``).

Vor- und Nachlauf (Metriken, Stufen-Hash über ``artifacts_json()``,
Audit-Ereignisse ``<STUFE>_STARTED/_DONE/_FAILED``) wie im Original. Die
Bibliothek protokolliert nicht über ``logging``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from auditcore_documents.pipeline.audit import AuditSink
from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.hashing import HashingService


class StageError(Exception):
    """Stufenfehler mit Code, Wiederholbarkeit und Details."""

    def __init__(
        self,
        stage: str,
        error_code: str,
        message: str,
        recoverable: bool = False,
        retry_after_sec: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.stage = stage
        self.error_code = error_code
        self.message = message
        self.recoverable = recoverable
        self.retry_after_sec = retry_after_sec
        self.details = details or {}
        super().__init__(f"[{stage}] {error_code}: {message}")


class PipelineStage(ABC):
    name: str = "base"
    description: str = "Base pipeline stage"

    def __init__(
        self,
        audit_service: AuditSink | None = None,
        hashing_service: HashingService | None = None,
    ) -> None:
        self.audit = audit_service
        self.hashing = hashing_service

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Stufenlogik; darf ``StageError`` auslösen."""

    async def pre_execute(self, context: PipelineContext) -> None:
        context.start_stage(self.name)
        if self.audit:
            await self.audit.log_event(
                event_type=f"{self.name.upper()}_STARTED",
                document_id=context.document_id,
                run_id=context.run_id,
                hash_original=context.hash_original,
                details={"stage": self.name},
            )

    async def post_execute(
        self, context: PipelineContext, success: bool, error: BaseException | None = None
    ) -> None:
        stage_hash = None
        if success and self.hashing:
            stage_hash = self.hashing.hash_string(context.artifacts_json())
        context.complete_stage(self.name, success=success, error=error, stage_hash=stage_hash)
        duration_ms = None
        for metric in context.stage_metrics:
            if metric.stage_name == self.name:
                duration_ms = metric.duration_ms
                break
        event_type = f"{self.name.upper()}_DONE" if success else f"{self.name.upper()}_FAILED"
        if self.audit:
            await self.audit.log_event(
                event_type=event_type,
                document_id=context.document_id,
                run_id=context.run_id,
                hash_original=context.hash_original,
                details={
                    "stage": self.name,
                    "success": success,
                    "duration_ms": duration_ms,
                    "error": str(error) if error else None,
                    "stage_hash": stage_hash,
                },
            )

    async def run(self, context: PipelineContext) -> PipelineContext:
        error: BaseException | None = None
        success = False
        try:
            await self.pre_execute(context)
            context = await self.execute(context)
            success = True
        except StageError as exc:
            error = exc
            if not exc.recoverable:
                context.fail(exc, error_code=exc.error_code, retryable=exc.recoverable)
            raise
        except Exception as exc:
            error = exc
            context.fail(exc, error_code="UNEXPECTED_ERROR", retryable=False)
            raise StageError(
                stage=self.name, error_code="UNEXPECTED_ERROR", message=str(exc), recoverable=False
            ) from exc
        finally:
            await self.post_execute(context, success=success, error=error)
        return context

    def validate_context(self, context: PipelineContext) -> None:
        if not context.document_id:
            raise StageError(
                stage=self.name,
                error_code="INVALID_CONTEXT",
                message="document_id is required",
                recoverable=False,
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"
