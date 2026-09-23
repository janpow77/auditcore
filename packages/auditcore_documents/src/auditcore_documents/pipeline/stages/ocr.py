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

import io
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from auditcore_documents.pipeline.context import OcrMetrics, PipelineContext, RunStatus
from auditcore_documents.pipeline.stages.base import PipelineStage, StageError

OcrBackendName = Literal["auto", "chandra", "tesseract", "none"]
MAX_OCR_PAGES = 50
OCR_RENDER_DPI = 200


@dataclass(frozen=True)
class OcrRouting:
    """Einstellungen des Originals: ``ocr_backend``, ``flow_agent_url``/``llm_router_url``."""

    mode: str = "auto"
    gateway_url: str = ""
    languages: str = "deu+eng"


@dataclass
class RouterPage:
    text: str | None = None
    confidence: float | None = None
    model: str | None = None


@dataclass
class RouterResult:
    """Antwort des Gateways (``safe_call_ocr``)."""

    text: str | None = None
    pages: list[Any] | None = None
    confidence: float | None = None
    spoke: str | None = None
    model: str | None = None
    fields: Any = None
    duration_ms: int | None = None


class RouterOcr(Protocol):
    async def __call__(
        self, data: bytes, *, filename: str, model: str, language: str
    ) -> tuple[RouterResult | None, str | None]: ...


Rasterizer = Callable[[bytes], list[tuple[int, bytes]] | None]


class ChandraPort(Protocol):
    def available(self) -> bool: ...

    def service(self, *, max_output_tokens: int, max_image_size: int) -> Any: ...


@dataclass
class ParsedPage:
    text: str
    confidence: float | None = None


@dataclass
class ParsedDocument:
    raw_text: str
    pages: list[ParsedPage]
    extracted: Any = None
    timings_ms: Any = None


class TesseractPort(Protocol):
    def parse(self, path: Path) -> ParsedDocument: ...


def should_use_router(routing: OcrRouting, chandra_available: Callable[[], bool]) -> bool:
    mode = (routing.mode or "auto").lower()
    if mode == "router":
        return True
    if mode == "local":
        return False
    if not (routing.gateway_url or "").strip():
        return False
    return not chandra_available()


def looks_like_pdf(data: bytes) -> bool:
    return data[:1024].lstrip()[:5].startswith(b"%PDF")


def pdfium_rasterizer(data: bytes) -> list[tuple[int, bytes]] | None:
    """Seiten als PNG (höchstens 50, 200 dpi); ``None`` ohne pypdfium2 oder bei Fehlern."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return None
    try:
        document = pdfium.PdfDocument(data)
    except Exception:  # noqa: BLE001 - Originalvertrag
        return None
    pages: list[tuple[int, bytes]] = []
    try:
        for index in range(min(len(document), MAX_OCR_PAGES)):
            page = document[index]
            try:
                bitmap = page.render(scale=OCR_RENDER_DPI / 72.0)
                buffer = io.BytesIO()
                bitmap.to_pil().save(buffer, format="PNG")
                pages.append((index + 1, buffer.getvalue()))
            finally:
                page.close()
    except Exception:  # noqa: BLE001 - Originalvertrag: Teilergebnis
        return pages or None
    finally:
        document.close()
    return pages or None


def degraded_result(
    raw_json: dict[str, Any], pages_failed: int, duration_ms: int
) -> dict[str, Any]:
    return {
        "text": "",
        "raw_json": raw_json,
        "pages": [],
        "avg_confidence": 0.0,
        "min_confidence": 0.0,
        "max_confidence": 0.0,
        "pages_processed": 0,
        "pages_failed": pages_failed,
        "engine_version": "router-degraded",
        "duration_ms": duration_ms,
    }


def combine_router_pages(
    page_texts: list[dict[str, Any]], page_errors: list[str], page_count: int, duration_ms: int
) -> dict[str, Any]:
    """Zusammenfassung der seitenweisen Gateway-Ergebnisse."""
    if not page_texts:
        return degraded_result(
            {"router_error": "; ".join(page_errors) or "no_result"}, page_count, duration_ms
        )
    confs = [
        float(p["confidence"]) for p in page_texts if isinstance(p.get("confidence"), (int, float))
    ]
    avg_conf = sum(confs) / len(confs) if confs else 0.85
    model_used = next((str(p.get("model")) for p in page_texts if p.get("model")), "auto")
    return {
        "text": "\n\n".join(p["text"] for p in page_texts),
        "raw_json": {
            "spoke": "",
            "model": model_used,
            "fields": None,
            "page_errors": page_errors or None,
        },
        "pages": page_texts,
        "avg_confidence": avg_conf,
        "min_confidence": min(confs) if confs else avg_conf,
        "max_confidence": max(confs) if confs else avg_conf,
        "pages_processed": len(page_texts),
        "pages_failed": len(page_errors),
        "engine_version": f"router-{model_used}",
        "duration_ms": duration_ms,
    }


def single_router_result(
    result: RouterResult | None, error: str | None, duration_ms: int
) -> dict[str, Any]:
    """Normalisierung einer Gateway-Antwort für das ganze Dokument."""
    if error or result is None:
        return degraded_result(
            {"router_error": str(error) if error else "no_result"}, 0, duration_ms
        )
    pages_raw = list(result.pages or [])
    confidence = result.confidence
    page_confidences: list[float] = []
    for page in pages_raw:
        if isinstance(page, dict):
            value = page.get("confidence")
            if isinstance(value, (int, float)):
                page_confidences.append(float(value))
    if confidence is None and page_confidences:
        confidence = sum(page_confidences) / len(page_confidences)
    avg_conf = float(confidence) if confidence is not None else 0.85
    return {
        "text": result.text or "",
        "raw_json": {"spoke": result.spoke, "model": result.model, "fields": result.fields},
        "pages": pages_raw,
        "avg_confidence": avg_conf,
        "min_confidence": min(page_confidences) if page_confidences else avg_conf,
        "max_confidence": max(page_confidences) if page_confidences else avg_conf,
        "pages_processed": len(pages_raw) if pages_raw else 1,
        "pages_failed": 0,
        "engine_version": f"router-{result.model or 'auto'}",
        "duration_ms": result.duration_ms or duration_ms,
    }


def chandra_result(result: dict[str, Any], fallback_pages: int) -> dict[str, Any]:
    """Konfidenzheuristik des Originals: 0,92 bei Erfolg ohne Fehler, sonst 0,75."""
    page_count = result.get("pages", fallback_pages)
    success = result.get("success", False)
    error_count = result.get("error_count", 0)
    avg_conf = 0.92 if success and error_count == 0 else 0.75
    return {
        "text": result.get("text", ""),
        "raw_json": {"token_count": result.get("token_count", 0)},
        "pages": [{"page": i + 1, "text": ""} for i in range(page_count)],
        "avg_confidence": avg_conf,
        "min_confidence": avg_conf - 0.05,
        "max_confidence": avg_conf + 0.05,
        "pages_processed": page_count,
        "pages_failed": error_count or 0,
        "engine_version": "chandra-1.0",
    }


def tesseract_result(parsed: ParsedDocument, languages: str) -> dict[str, Any]:
    confidences = [p.confidence for p in parsed.pages if p.confidence]
    return {
        "text": parsed.raw_text,
        "raw_json": parsed.extracted,
        "pages": [{"page": i + 1, "text": p.text} for i, p in enumerate(parsed.pages)],
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.80,
        "min_confidence": min(confidences) if confidences else 0.70,
        "max_confidence": max(confidences) if confidences else 0.90,
        "pages_processed": len(parsed.pages) if parsed.pages else 1,
        "pages_failed": 0,
        "engine_version": f"tesseract-{languages}",
        "timings_ms": parsed.timings_ms,
    }


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

    def _chandra_available(self) -> bool:
        try:
            return bool(self.chandra and self.chandra.available())
        except Exception:  # noqa: BLE001 - Originalvertrag
            return False

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        if should_use_router(self.routing, self._chandra_available):
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

    async def _run_router_ocr(self, context: PipelineContext) -> dict[str, Any]:
        start = self.timer()
        input_path = context.input_uri
        if not input_path:
            raise StageError(
                stage=self.name,
                error_code="NO_INPUT_URI",
                message="No input URI provided for OCR",
                recoverable=False,
            )
        path = Path(input_path)
        try:
            file_bytes = path.read_bytes()
        except FileNotFoundError as exc:
            raise StageError(
                stage=self.name,
                error_code="INPUT_NOT_FOUND",
                message=f"OCR-Input nicht lesbar: {input_path}",
                recoverable=False,
            ) from exc
        if self.router is None:
            raise StageError(
                stage=self.name,
                error_code="ROUTER_NOT_CONFIGURED",
                message="No OCR router configured",
                recoverable=False,
            )
        filename = path.name or "upload.pdf"
        page_images = (
            self.rasterizer(file_bytes)
            if self.rasterizer is not None and looks_like_pdf(file_bytes)
            else None
        )
        if page_images:
            page_texts: list[dict[str, Any]] = []
            page_errors: list[str] = []
            for page_no, png in page_images:
                page_result, page_error = await self.router(
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
            return combine_router_pages(
                page_texts, page_errors, len(page_images), self._elapsed_ms(start)
            )
        result, error = await self.router(
            file_bytes, filename=filename, model="auto", language="auto"
        )
        return single_router_result(result, error, self._elapsed_ms(start))

    def select_backend(self) -> str:
        if self.backend != "auto":
            return self.backend
        return "chandra" if self._chandra_available() else "tesseract"

    async def _run_local(self, context: PipelineContext, backend: str) -> dict[str, Any]:
        start = self.timer()
        try:
            if backend == "chandra":
                result = self._run_chandra(context)
            elif backend == "tesseract":
                result = self._run_tesseract(context)
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

    def _run_chandra(self, context: PipelineContext) -> dict[str, Any]:
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

    def _run_tesseract(self, context: PipelineContext) -> dict[str, Any]:
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

    async def evaluate_quality(self, context: PipelineContext) -> None:
        if not context.ocr_metrics:
            return
        avg = context.ocr_metrics.avg_confidence
        if avg >= self.min_confidence_ok:
            return
        if avg >= self.min_confidence_review:
            context.add_validation_flag("LOW_OCR_CONFIDENCE")
            context.status = RunStatus.REVIEW_NEEDED
            if self.audit:
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


RouterCall = Callable[..., Awaitable[tuple[RouterResult | None, str | None]]]
