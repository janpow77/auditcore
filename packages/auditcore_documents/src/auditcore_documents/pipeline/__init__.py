"""Frameworkunabhängige Dokumentpipeline (aus flowinvoice ``backend/app/pipeline``).

Stufenvertrag, Ablaufsteuerung, Kontext, Hashing/Provenienz, Audit-Ereignisse,
Aufbewahrungsregeln und Pipeline-Profile. OCR-Engines, Rasterung, MIME-
Erkennung per libmagic, Persistenz, Betrugsprüfung und Export sind Ports; der
Kern benötigt nur die Standardbibliothek (kein torch/transformers/GPU).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from auditcore_documents.pipeline.audit import (
    AuditEvent,
    AuditEventType,
    AuditSink,
    InMemoryAuditLog,
)
from auditcore_documents.pipeline.context import (
    AnalysisModules,
    ComputeProfile,
    ExtractionMethod,
    LlmSettings,
    OcrBackend,
    OcrMetrics,
    OcrSettings,
    ParserSettings,
    PipelineArtifacts,
    PipelineContext,
    PipelineProfileSettings,
    PipelineValueError,
    PostProcessingSettings,
    RagConfig,
    RunStatus,
    StageMetrics,
    ValidationResult,
)
from auditcore_documents.pipeline.hashing import HashingService
from auditcore_documents.pipeline.orchestrator import ComputeProfileEnforcer, PipelineOrchestrator
from auditcore_documents.pipeline.profiles import (
    CORRECTED_PIPELINE,
    LEGACY_PIPELINE,
    PIPELINE_PROFILES,
    PipelineProfile,
)
from auditcore_documents.pipeline.retention import RetentionPolicyConfig, RetentionSweeper
from auditcore_documents.pipeline.stages.base import PipelineStage, StageError
from auditcore_documents.pipeline.stages.export import ExportStage, FileExport, WebhookExport
from auditcore_documents.pipeline.stages.ingestion import (
    IngestionStage,
    libmagic_detector,
    sniff_mime,
)
from auditcore_documents.pipeline.stages.ocr import (
    OcrRouting,
    OcrStage,
    ParsedDocument,
    ParsedPage,
    RouterResult,
)
from auditcore_documents.pipeline.stages.persist import FileArtifactStore, PersistStage
from auditcore_documents.pipeline.stages.postprocess import PostprocessStage
from auditcore_documents.pipeline.stages.preprocess import PreprocessStage
from auditcore_documents.pipeline.stages.validation import FraudAssessment, ValidationStage


def build_pipeline(
    *,
    profile: PipelineProfile,
    audit: AuditSink | None = None,
    ocr: OcrStage | None = None,
    ingestion: IngestionStage | None = None,
    validation: ValidationStage | None = None,
    persist: PersistStage | None = None,
    extra_stages: list[PipelineStage] | None = None,
    compute_enforcer: ComputeProfileEnforcer | None = None,
    hashing: HashingService | None = None,
    sleep: Callable[[float], Awaitable[None]] | None = None,
) -> PipelineOrchestrator:
    """Standardablauf des flowinvoice-Workers (Einlesen … Persistenz) mit Ports."""
    hashing = hashing or HashingService()
    postprocess = PostprocessStage(audit_service=audit, hashing_service=hashing)
    postprocess.patterns = {k: list(v) for k, v in profile.field_patterns.items()}
    stages: list[PipelineStage] = [
        ingestion or IngestionStage(audit_service=audit, hashing_service=hashing),
        PreprocessStage(audit_service=audit, hashing_service=hashing),
        ocr or OcrStage(audit_service=audit, hashing_service=hashing),
        postprocess,
        validation or ValidationStage(audit_service=audit, hashing_service=hashing),
        persist or PersistStage(audit_service=audit, hashing_service=hashing),
        *(extra_stages or []),
    ]
    orchestrator = PipelineOrchestrator(
        stages,
        audit_service=audit,
        hashing_service=hashing,
        compute_enforcer=compute_enforcer,
        preserve_review=profile.preserve_review,
    )
    if sleep is not None:
        orchestrator.sleep = sleep
    return orchestrator


__all__ = [
    "CORRECTED_PIPELINE",
    "LEGACY_PIPELINE",
    "PIPELINE_PROFILES",
    "AnalysisModules",
    "AuditEvent",
    "AuditEventType",
    "AuditSink",
    "ComputeProfile",
    "ComputeProfileEnforcer",
    "ExportStage",
    "ExtractionMethod",
    "FileArtifactStore",
    "FileExport",
    "FraudAssessment",
    "HashingService",
    "InMemoryAuditLog",
    "IngestionStage",
    "LlmSettings",
    "OcrBackend",
    "OcrMetrics",
    "OcrRouting",
    "OcrSettings",
    "OcrStage",
    "ParsedDocument",
    "ParsedPage",
    "ParserSettings",
    "PersistStage",
    "PipelineArtifacts",
    "PipelineContext",
    "PipelineOrchestrator",
    "PipelineProfile",
    "PipelineProfileSettings",
    "PipelineStage",
    "PipelineValueError",
    "PostProcessingSettings",
    "PostprocessStage",
    "PreprocessStage",
    "RagConfig",
    "RetentionPolicyConfig",
    "RetentionSweeper",
    "RouterResult",
    "RunStatus",
    "StageError",
    "StageMetrics",
    "ValidationResult",
    "ValidationStage",
    "WebhookExport",
    "build_pipeline",
    "libmagic_detector",
    "sniff_mime",
]
