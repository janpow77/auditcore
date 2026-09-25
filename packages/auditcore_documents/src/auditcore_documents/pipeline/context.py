"""Pipeline-Kontext und Hilfsmodelle (aus flowinvoice ``app/pipeline/context.py``).

Das Original nutzt pydantic-Modelle. Hier sind es Datenklassen der
Standardbibliothek mit denselben Feldern, Vorgaben, Wertebereichen und
Zustandsübergängen; Enum-Werte werden aus Zeichenketten übernommen wie bei
pydantic. ``to_dict()`` entspricht ``model_dump()``, ``artifacts_json()``
bytegleich ``artifacts.model_dump_json()`` (Grundlage der Stufen-Hashes).
Die Uhr ist injizierbar (``clock``); sie gehört nicht zum Datenvertrag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from auditcore_documents.pipeline.model_base import (
    Clock,
    PipelineValueError,
    _Model,
    _range,
    new_id,
    utc_now,
)
from auditcore_documents.pipeline.settings_models import (
    AnalysisModules,
    ExtractionMethod,
    LlmSettings,
    OcrBackend,
    OcrSettings,
    ParserSettings,
    PipelineProfileSettings,
    PostProcessingSettings,
    RagConfig,
)

__all__ = [
    "AnalysisModules",
    "Clock",
    "ComputeProfile",
    "ExtractionMethod",
    "LlmSettings",
    "OcrBackend",
    "OcrMetrics",
    "OcrSettings",
    "ParserSettings",
    "PipelineArtifacts",
    "PipelineContext",
    "PipelineProfileSettings",
    "PipelineValueError",
    "PostProcessingSettings",
    "RagConfig",
    "RunStatus",
    "StageMetrics",
    "ValidationResult",
    "new_id",
    "utc_now",
]


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    OK = "ok"
    REVIEW_NEEDED = "review_needed"
    REJECTED = "rejected"
    FAILED = "failed"


class ComputeProfile(StrEnum):
    CPU = "cpu"
    GPU_1 = "gpu_1"
    GPU_2 = "gpu_2"
    AUTO = "auto"


@dataclass
class StageMetrics(_Model):
    stage_name: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    success: bool = False
    error_message: str | None = None
    error_code: str | None = None

    def complete(
        self, success: bool = True, error: BaseException | None = None, *, now: datetime
    ) -> None:
        self.completed_at = now
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        self.success = success
        if error:
            self.error_message = str(error)
            self.error_code = type(error).__name__


@dataclass
class OcrMetrics(_Model):
    engine: str
    avg_confidence: float
    min_confidence: float
    max_confidence: float = 1.0
    pages_processed: int = 0
    pages_failed: int = 0
    duration_ms: int = 0
    retries: int = 0

    def __post_init__(self) -> None:
        for name in ("avg_confidence", "min_confidence", "max_confidence"):
            _range(self, name, 0.0, 1.0)
        for name in ("pages_processed", "pages_failed", "duration_ms", "retries"):
            _range(self, name, 0, None)


@dataclass
class ValidationResult(_Model):
    rule_id: str
    rule_name: str
    severity: Literal["INFO", "WARN", "CRITICAL"]
    outcome: Literal["PASS", "FAIL", "REVIEW"]
    message: str
    evidence: dict[str, Any] | None = None
    source_location: str | None = None
    evaluated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.severity not in ("INFO", "WARN", "CRITICAL"):
            raise PipelineValueError(f"ValidationResult.severity: {self.severity!r}")
        if self.outcome not in ("PASS", "FAIL", "REVIEW"):
            raise PipelineValueError(f"ValidationResult.outcome: {self.outcome!r}")


@dataclass
class PipelineArtifacts(_Model):
    ocr_text: str | None = None
    ocr_raw_json: dict[str, Any] | None = None
    ocr_pages: list[dict[str, Any]] | None = None
    layout_json: dict[str, Any] | None = None
    normalized_json: dict[str, Any] | None = None
    extracted_fields: dict[str, Any] | None = None
    preprocessed_images: list[str] | None = None
    deskew_angles: list[float] | None = None
    page_count: int | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None


@dataclass
class PipelineContext(_Model):
    """Zentrales Objekt, das durch alle Stufen fließt."""

    document_id: str
    run_id: str = field(default_factory=new_id)
    project_id: str | None = None
    user_id: str | None = None
    hash_original: str | None = None
    hash_chain: list[str] = field(default_factory=list)
    input_uri: str = ""
    storage_key: str = ""
    compute_profile_requested: ComputeProfile = ComputeProfile.AUTO
    compute_profile_accepted: ComputeProfile | None = None
    compute_downgrade_reason: str | None = None
    gpu_minutes_used: float = 0.0
    status: RunStatus = RunStatus.QUEUED
    current_stage: str | None = None
    completed_stages: list[str] = field(default_factory=list)
    stage_metrics: list[StageMetrics] = field(default_factory=list)
    ocr_metrics: OcrMetrics | None = None
    total_duration_ms: int | None = None
    artifacts: PipelineArtifacts = field(default_factory=PipelineArtifacts)
    validation_results: list[ValidationResult] = field(default_factory=list)
    validation_flags: list[str] = field(default_factory=list)
    analysis_modules: AnalysisModules = field(default_factory=AnalysisModules)
    ocr_settings: OcrSettings = field(default_factory=OcrSettings)
    parser_settings: ParserSettings = field(default_factory=ParserSettings)
    llm_settings: LlmSettings = field(default_factory=LlmSettings)
    post_processing_settings: PostProcessingSettings = field(default_factory=PostProcessingSettings)
    pipeline_version: str = "1.0.0"
    ocr_engine_version: str | None = None
    ruleset_id: str | None = None
    ruleset_version: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    error_code: str | None = None
    retryable: bool = False
    clock: Clock = field(default=utc_now, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.status = RunStatus(self.status)
        self.compute_profile_requested = ComputeProfile(self.compute_profile_requested)
        if self.compute_profile_accepted is not None:
            self.compute_profile_accepted = ComputeProfile(self.compute_profile_accepted)
        if self.created_at is None:
            self.created_at = self.clock()

    # ------------------------------------------------------------------ Zustand

    def start_stage(self, stage_name: str) -> StageMetrics:
        self.current_stage = stage_name
        self.status = RunStatus.RUNNING
        self.updated_at = self.clock()
        metrics = StageMetrics(stage_name=stage_name, started_at=self.clock())
        self.stage_metrics.append(metrics)
        return metrics

    def complete_stage(
        self,
        stage_name: str,
        success: bool = True,
        error: BaseException | None = None,
        stage_hash: str | None = None,
    ) -> None:
        for metric in self.stage_metrics:
            if metric.stage_name == stage_name and metric.completed_at is None:
                metric.complete(success=success, error=error, now=self.clock())
                break
        if success:
            self.completed_stages.append(stage_name)
        if stage_hash:
            self.hash_chain.append(stage_hash)
        self.updated_at = self.clock()

    def fail(
        self, error: BaseException, error_code: str | None = None, retryable: bool = False
    ) -> None:
        self.status = RunStatus.FAILED
        self.error = str(error)
        self.error_code = error_code or type(error).__name__
        self.retryable = retryable
        self.completed_at = self.clock()
        self.updated_at = self.clock()
        if self.stage_metrics:
            self._calculate_total_duration()

    def complete(self, status: RunStatus = RunStatus.OK) -> None:
        self.status = status
        self.completed_at = self.clock()
        self.updated_at = self.clock()
        self._calculate_total_duration()

    def add_validation_flag(self, flag: str) -> None:
        if flag not in self.validation_flags:
            self.validation_flags.append(flag)

    def needs_review(self) -> bool:
        return self.status == RunStatus.REVIEW_NEEDED or any(
            r.outcome == "REVIEW" for r in self.validation_results
        )

    def _calculate_total_duration(self) -> None:
        if self.stage_metrics:
            self.total_duration_ms = sum(
                m.duration_ms or 0 for m in self.stage_metrics if m.completed_at is not None
            )

    def to_audit_details(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "document_id": self.document_id,
            "status": self.status.value,
            "hash_original": self.hash_original,
            "compute_profile": (
                self.compute_profile_accepted.value if self.compute_profile_accepted else None
            ),
            "completed_stages": self.completed_stages,
            "validation_flags": self.validation_flags,
            "total_duration_ms": self.total_duration_ms,
            "pipeline_version": self.pipeline_version,
        }

    def artifacts_json(self) -> str:
        """Bytegleich zu ``artifacts.model_dump_json()`` des Originals."""
        return self.artifacts.to_json()
