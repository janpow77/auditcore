"""Ports, Antwortmodelle und Ergebnisnormalisierung der OCR-Stufe (aus ``stages/ocr.py``).

Jede Normalisierung liefert ein ``OcrOutput`` mit den Schlüsseln des Originals;
die Werte der Gateway-/Engine-Rohantworten bleiben unverändert erhalten.
"""

from __future__ import annotations

import io
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, TypedDict

from auditcore_documents.pipeline.donut import DonutResult


class OcrOutput(TypedDict, total=False):
    """Normalisiertes OCR-Ergebnis (Schlüssel wie im Original, alle optional)."""

    text: str
    raw_json: dict[str, Any] | None
    pages: list[Any]
    avg_confidence: float
    min_confidence: float
    max_confidence: float
    pages_processed: int
    pages_failed: int
    engine_version: str
    duration_ms: int
    timings_ms: Any
    retries: int
    error: str


OcrBackendName = Literal["auto", "chandra", "tesseract", "none", "donut"]
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
    fields: object = None
    duration_ms: int | None = None


class RouterOcr(Protocol):
    async def __call__(
        self, data: bytes, *, filename: str, model: str, language: str
    ) -> tuple[RouterResult | None, str | None]: ...


Rasterizer = Callable[[bytes], list[tuple[int, bytes]] | None]


class ChandraService(Protocol):
    """Chandra-Dienst des Originals: verarbeitet ein PDF zu einem Rohergebnis."""

    def process_pdf(self, path: Path) -> Mapping[str, Any]: ...


class ChandraPort(Protocol):
    def available(self) -> bool: ...

    def service(
        self, *, max_output_tokens: int, max_image_size: int
    ) -> ChandraService | None: ...


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
) -> OcrOutput:
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
) -> OcrOutput:
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
) -> OcrOutput:
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


def chandra_result(result: Mapping[str, Any], fallback_pages: int) -> OcrOutput:
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


def tesseract_result(parsed: ParsedDocument, languages: str) -> OcrOutput:
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


DONUT_LABELS = (
    ("invoice_number", "Rechnungsnummer"),
    ("invoice_date", "Rechnungsdatum"),
    ("supply_date", "Leistungsdatum"),
    ("due_date", "Fällig am"),
    ("net_amount", "Nettobetrag"),
    ("total", "Gesamtbetrag"),
    ("iban", "IBAN"),
    ("bic", "BIC"),
)
#: Pflichtfelder für die OCR-Konfidenz eines Donut-Laufs.
DONUT_REQUIRED_CONFIDENCE = ("total", "invoice_date", "invoice_number", "supplier.vat_id", "iban")


def donut_text(fields: Mapping[str, Any]) -> str:
    """Zeilenweise Darstellung der Donut-Felder mit deutschen Beschriftungen."""
    lines = []
    supplier = fields.get("supplier") if isinstance(fields.get("supplier"), dict) else {}
    if supplier and supplier.get("name"):
        lines.append(str(supplier["name"]))
    for key, label in DONUT_LABELS[:4]:
        if fields.get(key):
            lines.append(f"{label}: {fields[key]}")
    if supplier and supplier.get("vat_id"):
        lines.append(f"USt-IdNr.: {supplier['vat_id']}")
    if fields.get("net_amount"):
        lines.append(f"Nettobetrag: {fields['net_amount']}")
    for line in fields.get("vat_lines") or []:
        if isinstance(line, dict) and line.get("amount"):
            lines.append(f"USt {line.get('rate', '')}: {line['amount']}")
    for key, label in DONUT_LABELS[5:]:
        if fields.get(key):
            lines.append(f"{label}: {fields[key]}")
    return "\n".join(lines)


def donut_result(
    results: list[tuple[int, DonutResult]], tesseract: Mapping[str, object] | None
) -> OcrOutput:
    """Seitenergebnisse → OCR-Ergebnis; ``ocr_text`` ist der Tesseract-Text, sonst Donut-Text.

    Konfidenz: Minimum/Mittel der Feldkonfidenzen der Pflichtfelder; liefert der
    Motor keine Feldkonfidenzen, gilt 0,80 (Prüfbereich, nie automatisch OK).
    """
    first = results[0][1]
    pages = [
        {"page": number, **result.to_dict()} for number, result in results
    ]
    confidences = [
        value
        for _, result in results
        for key, value in result.field_confidence.items()
        if key in DONUT_REQUIRED_CONFIDENCE
    ]
    avg = sum(confidences) / len(confidences) if confidences else 0.80
    low = min(confidences) if confidences else 0.80
    high = max(confidences) if confidences else 0.80
    donut_lines = "\n\n".join(donut_text(result.fields) for _, result in results)
    text = str((tesseract or {}).get("text") or "") or donut_lines
    return {
        "text": text,
        "raw_json": {
            "engine": "donut",
            "model_id": first.model_id,
            "model_sha256": first.model_sha256,
            "device": first.device,
            "pages": pages,
            "donut_text": donut_lines,
            "tesseract": (
                {"text": tesseract.get("text", ""), "engine_version": tesseract.get(
                    "engine_version"), "error": tesseract.get("error")}
                if tesseract is not None
                else None
            ),
        },
        "pages": [{"page": number, "text": donut_text(r.fields)} for number, r in results],
        "avg_confidence": avg,
        "min_confidence": low,
        "max_confidence": high,
        "pages_processed": len(results),
        "pages_failed": 0,
        "engine_version": f"{first.model_id}@{first.model_sha256[:12]}",
    }


RouterCall = Callable[..., Awaitable[tuple[RouterResult | None, str | None]]]
