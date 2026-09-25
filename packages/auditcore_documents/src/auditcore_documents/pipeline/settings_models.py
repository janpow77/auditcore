"""Einstellungsmodelle eines Pipeline-Profils (OCR, Parser, LLM, Nachbearbeitung, RAG)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from auditcore_documents.pipeline.model_base import _Model, _range, new_id, utc_now


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
