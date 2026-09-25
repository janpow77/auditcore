"""Ablaufsteuerung der Stufen und Compute-Profil (aus ``app/pipeline/orchestrator.py``).

Ablauf, Abbruch bei REJECTED/FAILED, Wiederherstellungsstrategien und
Audit-Ereignisse wie im Original. Ports: ``sleep`` (Wartezeit bei
Wiederholungen) und ``GpuQuota`` (Kontingent). Die Datenbankabfragen des
``QuotaService`` bleiben in der Anwendung.

``preserve_review=True`` (Profil ``auditcore.pipeline`` 2026.09.1) behebt
PL-C01: Im Original setzt jede folgende Stufe den Status wieder auf RUNNING,
sodass ein zuvor gesetztes REVIEW_NEEDED am Ende als OK gemeldet wird.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from auditcore_documents.pipeline.audit import AuditSink
from auditcore_documents.pipeline.context import ComputeProfile, PipelineContext, RunStatus
from auditcore_documents.pipeline.hashing import HashingService
from auditcore_documents.pipeline.stages.base import PipelineStage, StageError

Sleep = Callable[[float], Awaitable[None]]


class GpuQuota(Protocol):
    async def check_gpu_quota(self, user_id: str) -> bool: ...


class ComputeProfileEnforcer:
    """Frontend-Wünsche werden nie ungeprüft übernommen."""

    def __init__(
        self,
        gpu_available: bool = False,
        gpu_count: int = 0,
        quota_service: GpuQuota | None = None,
    ) -> None:
        self.gpu_available = gpu_available
        self.gpu_count = gpu_count
        self.quota_service = quota_service

    async def enforce(
        self,
        user_id: str | None,
        requested_profile: ComputeProfile,
        gpu_count_requested: int = 1,
    ) -> tuple[ComputeProfile, str | None]:
        del gpu_count_requested  # im Original ungenutzt
        if requested_profile == ComputeProfile.CPU:
            return ComputeProfile.CPU, None
        if requested_profile == ComputeProfile.AUTO:
            if self.gpu_available and self.gpu_count > 0:
                return ComputeProfile.GPU_1, None
            return ComputeProfile.CPU, None
        if requested_profile in (ComputeProfile.GPU_1, ComputeProfile.GPU_2):
            if not self.gpu_available:
                return ComputeProfile.CPU, "GPU not available on this system"
            if requested_profile == ComputeProfile.GPU_2 and self.gpu_count < 2:
                return ComputeProfile.GPU_1, f"Only {self.gpu_count} GPU(s) available"
            if (
                self.quota_service
                and user_id
                and not await self.quota_service.check_gpu_quota(user_id)
            ):
                return ComputeProfile.CPU, "GPU quota exceeded"
            return requested_profile, None
        return ComputeProfile.CPU, f"Unknown profile: {requested_profile}"


class PipelineOrchestrator:
    """Führt die Stufen der Reihe nach aus."""

    def __init__(
        self,
        stages: list[PipelineStage],
        audit_service: AuditSink | None = None,
        hashing_service: HashingService | None = None,
        compute_enforcer: ComputeProfileEnforcer | None = None,
        *,
        sleep: Sleep = asyncio.sleep,
        preserve_review: bool = False,
        retry_gateway: bool = False,
    ) -> None:
        self.stages = stages
        self.audit = audit_service
        self.hashing = hashing_service or HashingService()
        self.compute_enforcer = compute_enforcer
        self.sleep = sleep
        self.preserve_review = preserve_review
        #: Entscheidung D6: Gateway-Ausfall bis zu dreimal mit Wartezeit wiederholen.
        self.retry_gateway = retry_gateway
        for stage in self.stages:
            if stage.audit is None:
                stage.audit = audit_service
            if stage.hashing is None:
                stage.hashing = self.hashing

    async def run(
        self,
        context: PipelineContext,
        start_from_stage: str | None = None,
        stop_after_stage: str | None = None,
    ) -> PipelineContext:
        await self._log_started(context, start_from_stage, stop_after_stage)
        await self._apply_compute_profile(context)
        stages_to_run = self.filter_stages(start_from_stage, stop_after_stage)
        if not stages_to_run:
            return context
        context.status = RunStatus.RUNNING
        context.updated_at = context.clock()
        review_seen = False
        for stage in stages_to_run:
            context, stop, review = await self._run_stage(context, stage)
            review_seen = review_seen or review
            if stop:
                break
        self._settle_status(context, review_seen)
        await self._log_finished(context)
        return context

    async def _log_started(
        self, context: PipelineContext, start_from: str | None, stop_after: str | None
    ) -> None:
        if self.audit is None:
            return
        await self.audit.log_event(
            event_type="PIPELINE_STARTED",
            document_id=context.document_id,
            run_id=context.run_id,
            project_id=context.project_id,
            details={
                "stages": [s.name for s in self.stages],
                "start_from": start_from,
                "stop_after": stop_after,
                "compute_profile_requested": context.compute_profile_requested.value,
                "analysis_modules": context.analysis_modules.to_dict(),
            },
            pipeline_version=context.pipeline_version,
        )

    async def _apply_compute_profile(self, context: PipelineContext) -> None:
        if not self.compute_enforcer:
            context.compute_profile_accepted = context.compute_profile_requested
            return
        accepted, reason = await self.compute_enforcer.enforce(
            user_id=context.user_id, requested_profile=context.compute_profile_requested
        )
        context.compute_profile_accepted = accepted
        context.compute_downgrade_reason = reason
        if reason and self.audit:
            await self.audit.log_event(
                event_type="COMPUTE_PROFILE_DOWNGRADED",
                document_id=context.document_id,
                run_id=context.run_id,
                details={
                    "requested": context.compute_profile_requested.value,
                    "accepted": accepted.value,
                    "reason": reason,
                },
            )

    async def _run_stage(
        self, context: PipelineContext, stage: PipelineStage
    ) -> tuple[PipelineContext, bool, bool]:
        """Eine Stufe mit Wiederherstellung: (Kontext, abbrechen, REVIEW_NEEDED gesehen)."""
        try:
            context = await stage.run(context)
        except StageError as exc:
            if not exc.recoverable:
                context.fail(exc, error_code=exc.error_code, retryable=False)
                return context, True, False
            recovered = await self._try_recovery(context, stage, exc)
            review = context.status == RunStatus.REVIEW_NEEDED
            if not recovered:
                context.fail(exc, error_code=exc.error_code, retryable=True)
            return context, not recovered, review
        except Exception as exc:  # noqa: BLE001 - Originalvertrag
            context.fail(exc, error_code="UNEXPECTED_ERROR", retryable=False)
            return context, True, False
        review = context.status == RunStatus.REVIEW_NEEDED
        return context, context.status in (RunStatus.REJECTED, RunStatus.FAILED), review

    def _settle_status(self, context: PipelineContext, review_seen: bool) -> None:
        keep_review = self.preserve_review and review_seen
        if context.status == RunStatus.RUNNING:
            context.complete(RunStatus.REVIEW_NEEDED if keep_review else RunStatus.OK)
        elif keep_review and context.status == RunStatus.OK:
            context.status = RunStatus.REVIEW_NEEDED

    async def _log_finished(self, context: PipelineContext) -> None:
        if self.audit is None:
            return
        await self.audit.log_event(
            event_type=(
                "PIPELINE_COMPLETED" if context.status != RunStatus.FAILED else "PIPELINE_FAILED"
            ),
            document_id=context.document_id,
            run_id=context.run_id,
            project_id=context.project_id,
            hash_original=context.hash_original,
            details=context.to_audit_details(),
            pipeline_version=context.pipeline_version,
            ocr_engine_version=context.ocr_engine_version,
            ruleset_version=context.ruleset_version,
        )

    def filter_stages(self, start_from: str | None, stop_after: str | None) -> list[PipelineStage]:
        """Unbekannte Start-/Stoppnamen werden (wie im Original) ignoriert."""
        stages = self.stages
        if start_from:
            index = next((i for i, s in enumerate(stages) if s.name == start_from), None)
            if index is not None:
                stages = stages[index:]
        if stop_after:
            index = next((i for i, s in enumerate(stages) if s.name == stop_after), None)
            if index is not None:
                stages = stages[: index + 1]
        return stages

    async def _try_recovery(
        self, context: PipelineContext, stage: PipelineStage, error: StageError
    ) -> bool:
        strategies = {
            "OCR_TIMEOUT": self._recover_ocr_timeout,
            "LLM_UNAVAILABLE": self._recover_llm_unavailable,
            "HTTP_DOWNLOAD_FAILED": self._recover_http_download,
        }
        if self.retry_gateway:
            strategies["OCR_GATEWAY_UNAVAILABLE"] = self._recover_http_download
        strategy = strategies.get(error.error_code)
        if strategy:
            try:
                return await strategy(context, stage, error)
            except Exception:  # noqa: BLE001 - Originalvertrag: Wiederherstellung gescheitert
                return False
        return False

    async def _recover_ocr_timeout(
        self, context: PipelineContext, stage: PipelineStage, error: StageError
    ) -> bool:
        await self.sleep(2)
        if hasattr(stage, "backend"):
            original_backend = stage.backend
            stage.backend = "tesseract"
            try:
                await stage.run(context)
                return True
            except Exception:  # noqa: BLE001
                stage.backend = original_backend
        return False

    async def _recover_llm_unavailable(
        self, context: PipelineContext, stage: PipelineStage, error: StageError
    ) -> bool:
        if context.analysis_modules:
            context.analysis_modules.rag_enrichment = False
            context.analysis_modules.fraud_detection = False
        context.add_validation_flag("LLM_UNAVAILABLE")
        context.status = RunStatus.REVIEW_NEEDED
        return True

    async def _recover_http_download(
        self, context: PipelineContext, stage: PipelineStage, error: StageError
    ) -> bool:
        for attempt in range(3):
            await self.sleep((error.retry_after_sec or 5) * (attempt + 1))
            try:
                await stage.run(context)
                return True
            except StageError:
                continue
            except Exception:  # noqa: BLE001, S112 - Originalvertrag: weiterer Versuch
                continue
        return False
