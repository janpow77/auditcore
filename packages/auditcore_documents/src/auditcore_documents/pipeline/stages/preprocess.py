"""Bildvorverarbeitung (aus ``stages/preprocess.py``).

Das Original ist ein Platzhalter: Für PDF entsteht je Seite der Winkel 0.0,
für Bilder ``[0.0]``; die PIL-Hilfen (Deskew, Kontrast, Entrauschen,
Binarisierung) werden in der Pipeline nicht aufgerufen (PL-L04). Die
Bibliothek bildet das ab und bietet einen Port ``angle_detector`` für eine
tatsächliche Winkelerkennung; schwere Bildverarbeitung bleibt außerhalb.
"""

from __future__ import annotations

from collections.abc import Callable

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage

AngleDetector = Callable[[PipelineContext, int], float]


class PreprocessStage(PipelineStage):
    name = "preprocess"
    description = "Image preprocessing for OCR optimization"

    def __init__(
        self, *args: object, angle_detector: AngleDetector | None = None, **kwargs: object
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.angle_detector = angle_detector
        self.deskew_enabled = True
        self.enhance_enabled = True
        self.binarize_enabled = False
        self.denoise_enabled = True

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        mime_type = context.artifacts.mime_type
        if not mime_type:
            return context
        if mime_type == "application/pdf":
            page_count = context.artifacts.page_count or 1
            context.artifacts.deskew_angles = [self._angle(context, i) for i in range(page_count)]
        elif mime_type.startswith("image/"):
            context.artifacts.deskew_angles = [self._angle(context, 0)]
        return context

    def _angle(self, context: PipelineContext, page_index: int) -> float:
        return (
            0.0 if self.angle_detector is None else float(self.angle_detector(context, page_index))
        )
