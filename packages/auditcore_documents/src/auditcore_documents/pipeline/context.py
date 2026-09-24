"""Pipeline-Kontext und Hilfsmodelle (aus flowinvoice ``app/pipeline/context.py``).

Das Original nutzt pydantic-Modelle. Hier sind es Datenklassen der
Standardbibliothek mit denselben Feldern, Vorgaben, Wertebereichen und
Zustandsübergängen; Enum-Werte werden aus Zeichenketten übernommen wie bei
pydantic. ``to_dict()`` entspricht ``model_dump()``, ``artifacts_json()``
bytegleich ``artifacts.model_dump_json()`` (Grundlage der Stufen-Hashes).
Die Uhr ist injizierbar (``clock``); sie gehört nicht zum Datenvertrag.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from auditcore_documents.pipeline.jsonfmt import dumps_compact

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid.uuid4())


class PipelineValueError(ValueError):
    """Ungültiger Wert für ein Pipeline-Modell (entspricht pydantic ``ValidationError``)."""


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


class OcrBackend(StrEnum):
    AUTO = "auto"
    CHANDRA = "chandra"
    TESSERACT = "tesseract"
    NONE = "none"
    DONUT = "donut"


class ExtractionMethod(StrEnum):
    REGEX = "regex"
    LLM = "llm"
    HYBRID = "hybrid"


def _range(owner: object, name: str, low: float | None, high: float | None) -> None:
    value = getattr(owner, name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PipelineValueError(f"{type(owner).__name__}.{name}: Zahl erwartet")
    if low is not None and value < low:
        raise PipelineValueError(f"{type(owner).__name__}.{name}: größer oder gleich {low}")
    if high is not None and value > high:
        raise PipelineValueError(f"{type(owner).__name__}.{name}: kleiner oder gleich {high}")


def _dump(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value


class _Model:
    """Gemeinsame Serialisierung in Feldreihenfolge (ohne interne Uhr)."""

    def to_dict(self) -> dict[str, Any]:
        return {f.name: _dump(getattr(self, f.name)) for f in fields(self) if f.name != "clock"}  # type: ignore[arg-type]

    def to_json(self) -> str:
        return dumps_compact(self.to_dict())


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
class OcrSettings(_Model):
    backend: OcrBackend = OcrBackend.AUTO
    chandra_image_size: int = 1200
    chandra_max_tokens: int = 4096
    chandra_detail_level: str = "high"
    tesseract_languages: str = "deu+eng"
    tesseract_psm: int = 3
    tesseract_oem: int = 3

    def __post_init__(self) -> None:
        self.backend = OcrBackend(self.backend)
        _range(self, "chandra_image_size", 400, 2400)
        _range(self, "chandra_max_tokens", 1024, 16384)
        _range(self, "tesseract_psm", 0, 13)
        _range(self, "tesseract_oem", 0, 3)


@dataclass
class ParserSettings(_Model):
    timeout_sec: int = 30
    max_pages: int = 50
    extraction_method: ExtractionMethod = ExtractionMethod.HYBRID
    pdf_dpi: int = 300
    pdf_extract_images: bool = True
    pdf_extract_tables: bool = True

    def __post_init__(self) -> None:
        self.extraction_method = ExtractionMethod(self.extraction_method)
        _range(self, "timeout_sec", 10, 300)
        _range(self, "max_pages", 1, 500)
        _range(self, "pdf_dpi", 72, 600)


@dataclass
class LlmSettings(_Model):
    provider: str = "ollama"
    model: str = "llama3.2"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_sec: int = 120
    fallback_enabled: bool = True
    fallback_provider: str | None = None
    fallback_model: str | None = None
    fallback_after_errors: int = 3

    def __post_init__(self) -> None:
        _range(self, "temperature", 0.0, 2.0)
        _range(self, "max_tokens", 500, 32000)
        _range(self, "timeout_sec", 30, 600)
        _range(self, "fallback_after_errors", 1, 10)


@dataclass
class PostProcessingSettings(_Model):
    rule_engine_enabled: bool = True
    fraud_detection_enabled: bool = True
    confidence_threshold: float = 0.7
    generate_summary: bool = True
    generate_recommendations: bool = True

    def __post_init__(self) -> None:
        _range(self, "confidence_threshold", 0.0, 1.0)


@dataclass
class RagConfig(_Model):
    enabled: bool = True
    use_cache: bool = True
    use_hybrid_search: bool = True
    use_reranking: bool = True
    use_quality_scoring: bool = True
    top_k: int = 5
    similarity_threshold: float = 0.25
    rerank_top_k: int = 3
    vector_weight: float = 0.7
    bm25_weight: float = 0.3
    chunking_profile: str | None = None
    chunk_size_override: int | None = None
    chunk_overlap_override: int | None = None
    search_invoices: bool = True
    search_errors: bool = True
    search_patterns: bool = True
    search_legal: bool = False

    def __post_init__(self) -> None:
        _range(self, "top_k", 1, 20)
        _range(self, "similarity_threshold", 0.0, 1.0)
        _range(self, "rerank_top_k", 1, 10)
        _range(self, "vector_weight", 0.0, 1.0)
        _range(self, "bm25_weight", 0.0, 1.0)


@dataclass
class AnalysisModules(_Model):
    dedup: bool = True
    plausibility: bool = True
    metadata_consistency: bool = False
    fraud_detection: bool = True
    rag_enrichment: bool = True
    rag: RagConfig = field(default_factory=RagConfig)


@dataclass
class PipelineProfileSettings(_Model):
    """Vollständiges Pipeline-Profil (``context.PipelineProfile`` des Originals)."""

    id: str = field(default_factory=new_id)
    name: str = "Standard"
    description: str | None = None
    is_default: bool = False
    is_active: bool = True
    ocr: OcrSettings = field(default_factory=OcrSettings)
    parser: ParserSettings = field(default_factory=ParserSettings)
    llm: LlmSettings = field(default_factory=LlmSettings)
    rag: RagConfig = field(default_factory=RagConfig)
    post_processing: PostProcessingSettings = field(default_factory=PostProcessingSettings)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime | None = None
    created_by: str | None = None


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
