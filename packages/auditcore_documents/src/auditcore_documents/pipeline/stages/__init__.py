"""Pipeline-Stufen.

Einlesen → Vorverarbeitung → OCR → Nachverarbeitung → Validierung → Persistenz → Export.
"""

from auditcore_documents.pipeline.stages.base import PipelineStage, StageError

__all__ = ["PipelineStage", "StageError"]
