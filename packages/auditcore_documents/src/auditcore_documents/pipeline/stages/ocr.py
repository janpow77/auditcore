"""Texterkennung über austauschbare OCR-Ports (aus ``stages/ocr.py``).

Die Bibliothek enthält kein OCR-Modell (kein torch/transformers/GPU). Sie
bildet die Entscheidungen und Normalisierungen des Originals ab:

* Routing ``should_use_router`` (``router``/``local``/``auto``),
* Gateway-Pfad (``RouterOcr``-Port, seitenweise Rasterung über
  ``Rasterizer``, Zusammenfassung von Text, Konfidenzen und Seitenfehlern,
  „degradiertes“ Ergebnis bei Ausfall),
* lokaler Pfad (``ChandraPort``/``TesseractPort``, Auswahl und Rückfall,
  Konfidenzheuristiken),
* Qualitätsbewertung (OK ≥ 0,85; Review ≥ 0,60; sonst REJECTED).

Zeitmessung und Rasterung sind injizierbar; ``pdfium_rasterizer`` nutzt wie
das Original pypdfium2/Pillow (Extra ``ocr-raster``).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from auditcore_documents.pipeline.context import OcrMetrics, PipelineContext, RunStatus
from auditcore_documents.pipeline.donut import DonutPort
from auditcore_documents.pipeline.stages.base import PipelineStage, StageError
from auditcore_documents.pipeline.stages.ocr_results import (
    DONUT_LABELS,
    DONUT_REQUIRED_CONFIDENCE,
    MAX_OCR_PAGES,
    OCR_RENDER_DPI,
    ChandraPort,
    OcrBackendName,
    OcrOutput,
    OcrRouting,
    ParsedDocument,
    ParsedPage,
    Rasterizer,
    RouterCall,
    RouterOcr,
    RouterPage,
    RouterResult,
    TesseractPort,
    chandra_result,
    combine_router_pages,
    degraded_result,
    donut_result,
    donut_text,
    looks_like_pdf,
    pdfium_rasterizer,
    should_use_router,
    single_router_result,
    tesseract_result,
)

__all__ = [
    "DONUT_LABELS",
    "DONUT_REQUIRED_CONFIDENCE",
    "MAX_OCR_PAGES",
    "OCR_RENDER_DPI",
    "ChandraPort",
    "OcrBackendName",
    "OcrOutput",
    "OcrRouting",
    "OcrStage",
    "ParsedDocument",
    "ParsedPage",
    "Rasterizer",
    "RouterCall",
    "RouterOcr",
    "RouterPage",
    "RouterResult",
    "TesseractPort",
    "chandra_result",
    "combine_router_pages",
    "degraded_result",
    "donut_result",
    "donut_text",
    "looks_like_pdf",
    "pdfium_rasterizer",
    "should_use_router",
    "single_router_result",
    "tesseract_result",
]


class OcrStage(PipelineStage):
    name = "ocr"
    description = "Text extraction using OCR"

    def __init__(
        self,
        *args: object,
        backend: OcrBackendName = "auto",
        chandra_image_size: int = 1200,
        chandra_max_tokens: int = 4096,
        tesseract_languages: str = "deu+eng",
        min_confidence_ok: float = 0.85,
        min_confidence_review: float = 0.60,
        max_retries: int = 2,
        routing: OcrRouting | None = None,
        router: RouterOcr | None = None,
        rasterizer: Rasterizer | None = pdfium_rasterizer,
        chandra: ChandraPort | None = None,
        tesseract: TesseractPort | None = None,
        timer: Callable[[], float] = time.time,
        gateway_outage_is_error: bool = False,
        donut: DonutPort | None = None,
        donut_cross_check: bool = True,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.backend: str = backend
        self.chandra_image_size = chandra_image_size
        self.chandra_max_tokens = chandra_max_tokens
        self.tesseract_languages = tesseract_languages
        self.min_confidence_ok = min_confidence_ok
        self.min_confidence_review = min_confidence_review
        self.max_retries = max_retries
        self.routing = routing or OcrRouting()
        self.router = router
        self.rasterizer = rasterizer
        self.chandra = chandra
        self.tesseract = tesseract
        self.timer = timer
        #: Entscheidung D6: Gateway-Ausfall ist ein wiederholbarer Fehler, keine Ablehnung.
        self.gateway_outage_is_error = gateway_outage_is_error
        #: Donut-Port (nur Backend ``donut``); Tesseract läuft zum Zwei-Motoren-Abgleich mit.
        self.donut = donut
        self.donut_cross_check = donut_cross_check

    def _chandra_available(self) -> bool:
        try:
            return bool(self.chandra and self.chandra.available())
        except Exception:  # noqa: BLE001 - Originalvertrag
            return False

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        if self.backend == "donut":
            # Ausdrücklich gewählt (Profil DONUT_PIPELINE); kein Gateway-/Chandra-Routing.
            result = await self._run_local(context, "donut")
            engine = "donut"
        elif should_use_router(self.routing, self._chandra_available):
            result = await self._run_router_ocr(context)
            engine = "router"
        else:
            selected = self.select_backend()
            if selected == "none":
                return context
            result = await self._run_local(context, selected)
            engine = selected
        context.ocr_metrics = OcrMetrics(
            engine=engine,
            avg_confidence=result["avg_confidence"],
            min_confidence=result["min_confidence"],
            max_confidence=result.get("max_confidence", 1.0),
            pages_processed=result["pages_processed"],
            pages_failed=result.get("pages_failed", 0),
            duration_ms=result["duration_ms"],
            retries=result.get("retries", 0),
        )
        context.ocr_engine_version = result.get("engine_version")
        context.artifacts.ocr_text = result["text"]
        context.artifacts.ocr_raw_json = result.get("raw_json")
        context.artifacts.ocr_pages = result.get("pages")
        await self.evaluate_quality(context)
        return context

    def _elapsed_ms(self, start: float) -> int:
        return int((self.timer() - start) * 1000)

    async def _run_router_ocr(self, context: PipelineContext) -> OcrOutput:
        start = self.timer()
        path = self._input(context)
        try:
            file_bytes = path.read_bytes()
        except FileNotFoundError as exc:
            raise StageError(
                stage=self.name,
                error_code="INPUT_NOT_FOUND",
                message=f"OCR-Input nicht lesbar: {context.input_uri}",
                recoverable=False,
            ) from exc
        if self.router is None:
            raise StageError(
                stage=self.name,
                error_code="ROUTER_NOT_CONFIGURED",
                message="No OCR router configured",
                recoverable=False,
            )
        page_images = (
            self.rasterizer(file_bytes)
            if self.rasterizer is not None and looks_like_pdf(file_bytes)
            else None
        )
        if page_images:
            return await self._router_pages(self.router, path, page_images, start)
        result, error = await self.router(
            file_bytes, filename=path.name or "upload.pdf", model="auto", language="auto"
        )
        if error or result is None:
            self._raise_outage(str(error) if error else "no_result")
        return single_router_result(result, error, self._elapsed_ms(start))

    async def _router_pages(
        self, router: RouterOcr, path: Path, page_images: list[tuple[int, bytes]], start: float
    ) -> OcrOutput:
        """Seitenweise Gateway-Erkennung; Seitenfehler werden gesammelt, nicht abgebrochen."""
        page_texts: list[dict[str, object]] = []
        page_errors: list[str] = []
        for page_no, png in page_images:
            page_result, page_error = await router(
                png,
                filename=f"{path.stem or 'seite'}-{page_no}.png",
                model="auto",
                language=self.routing.languages,
            )
            if page_error or page_result is None:
                page_errors.append(f"S.{page_no}: {page_error}")
                continue
            page_texts.append(
                {
                    "page": page_no,
                    "text": page_result.text or "",
                    "confidence": page_result.confidence,
                    "model": page_result.model,
                }
            )
        if not page_texts:
            self._raise_outage("; ".join(page_errors) or "no_result")
        return combine_router_pages(
            page_texts, page_errors, len(page_images), self._elapsed_ms(start)
        )

    def _raise_outage(self, reason: str) -> None:
        """Entscheidung D6: Gateway-Ausfall als wiederholbarer Fehler statt Ablehnung."""
        if self.gateway_outage_is_error:
            raise StageError(
                stage=self.name,
                error_code="OCR_GATEWAY_UNAVAILABLE",
                message=f"OCR-Gateway nicht verfügbar: {reason}",
                recoverable=True,
                retry_after_sec=5,
            )

    def select_backend(self) -> str:
        if self.backend != "auto":
            return self.backend
        return "chandra" if self._chandra_available() else "tesseract"

    async def _run_local(self, context: PipelineContext, backend: str) -> OcrOutput:
        start = self.timer()
        try:
            if backend == "chandra":
                result = self._run_chandra(context)
            elif backend == "tesseract":
                result = self._run_tesseract(context)
            elif backend == "donut":
                result = self._run_donut(context)
            else:
                raise StageError(
                    stage=self.name,
                    error_code="UNKNOWN_BACKEND",
                    message=f"Unknown OCR backend: {backend}",
                    recoverable=False,
                )
            result["duration_ms"] = self._elapsed_ms(start)
            return result
        except StageError:
            raise
        except Exception as exc:  # noqa: BLE001 - Originalvertrag
            raise StageError(
                stage=self.name,
                error_code="OCR_FAILED",
                message=f"OCR failed: {exc}",
                recoverable=True,
                retry_after_sec=5,
            ) from exc

    def _input(self, context: PipelineContext) -> Path:
        if not context.input_uri:
            raise StageError(
                stage=self.name,
                error_code="NO_INPUT_URI",
                message="No input URI provided for OCR",
                recoverable=False,
            )
        return Path(context.input_uri)

    def _run_chandra(self, context: PipelineContext) -> OcrOutput:
        path = self._input(context)
        if self.chandra is None:
            # Original: ImportError des Chandra-Moduls → Tesseract (ohne Umhüllung).
            return self._run_tesseract(context)
        try:
            if not self.chandra.available():
                return self._run_tesseract(context)
            service = self.chandra.service(
                max_output_tokens=self.chandra_max_tokens, max_image_size=self.chandra_image_size
            )
            if not service:
                return self._run_tesseract(context)
            return chandra_result(service.process_pdf(path), context.artifacts.page_count or 1)
        except Exception as exc:  # noqa: BLE001 - Originalvertrag (auch Tesseract-Rückfall)
            raise StageError(
                stage=self.name,
                error_code="CHANDRA_OCR_FAILED",
                message=f"Chandra OCR failed: {exc}",
                recoverable=True,
                retry_after_sec=5,
            ) from exc

    def _run_tesseract(self, context: PipelineContext) -> OcrOutput:
        path = self._input(context)
        try:
            if self.tesseract is None:
                raise RuntimeError("No Tesseract engine configured")
            return tesseract_result(self.tesseract.parse(path), self.tesseract_languages)
        except Exception as exc:  # noqa: BLE001 - Originalvertrag
            raise StageError(
                stage=self.name,
                error_code="TESSERACT_OCR_FAILED",
                message=f"Tesseract OCR failed: {exc}",
                recoverable=True,
                retry_after_sec=5,
            ) from exc

    def _run_donut(self, context: PipelineContext) -> OcrOutput:
        """Seitenweise Donut-Inferenz; Tesseract-Text für Abgleich und Regex-Rückfall."""
        path = self._input(context)
        if self.donut is None:
            raise StageError(
                stage=self.name,
                error_code="DONUT_NOT_CONFIGURED",
                message="No Donut port configured",
                recoverable=False,
            )
        data = path.read_bytes()
        if looks_like_pdf(data):
            pages = self.rasterizer(data) if self.rasterizer is not None else None
            if not pages:
                raise StageError(
                    stage=self.name,
                    error_code="DONUT_RASTER_FAILED",
                    message="PDF could not be rasterized for Donut",
                    recoverable=False,
                )
        else:
            pages = [(1, data)]
        results = [(number, self.donut.parse(png)) for number, png in pages]
        tesseract: OcrOutput | None = None
        if self.donut_cross_check and self.tesseract is not None:
            try:
                tesseract = tesseract_result(self.tesseract.parse(path), self.tesseract_languages)
            except Exception as exc:  # noqa: BLE001 - Abgleich fehlt → Prüfung statt Abbruch
                tesseract = {"text": "", "error": str(exc)}
        return donut_result(results, tesseract)

    async def evaluate_quality(self, context: PipelineContext) -> None:
        if not context.ocr_metrics:
            return
        avg = context.ocr_metrics.avg_confidence
        if avg >= self.min_confidence_ok:
            return
        if avg >= self.min_confidence_review:
            context.add_validation_flag("LOW_OCR_CONFIDENCE")
            context.status = RunStatus.REVIEW_NEEDED
            if self.audit is not None:
                await self.audit.log_event(
                    event_type="OCR_CONFIDENCE_LOW",
                    document_id=context.document_id,
                    run_id=context.run_id,
                    hash_original=context.hash_original,
                    details={
                        "avg_confidence": avg,
                        "threshold_ok": self.min_confidence_ok,
                        "threshold_review": self.min_confidence_review,
                    },
                )
        else:
            context.add_validation_flag("VERY_LOW_OCR_CONFIDENCE")
            context.status = RunStatus.REJECTED
