"""Abbildung eines Pipeline-Laufs auf die Antwort des Vertrags ``documents_extraction/1``."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from auditcore_documents.pipeline import PipelineContext

#: Anzeige-Reihenfolge der bekannten Felder; weitere folgen alphabetisch.
FIELD_ORDER = (
    "invoice_number",
    "date",
    "supply_date",
    "due_date",
    "supplier_name",
    "net_amount",
    "vat_amount",
    "total",
    "iban",
    "bic",
    "vat_id",
)
_MERGE = "donut_merge"


@dataclass(frozen=True)
class Thresholds:
    """Konfidenzschwellen der OCR-Qualität (Original: OK ≥ 0,85, Prüfung ≥ 0,60)."""

    ok: float = 0.85
    review: float = 0.60

    def to_dict(self) -> dict[str, float]:
        return {"ok": self.ok, "review": self.review}

    def quality(self, confidence: float) -> str:
        """``ok``, ``review`` oder ``rejected`` wie ``OcrStage.evaluate_quality``."""
        if confidence >= self.ok:
            return "ok"
        return "review" if confidence >= self.review else "rejected"


def _plain(value: object) -> object:
    """JSON-taugliche Kopie (Decimal, Datum und Aufzählungen als Text)."""
    loaded: object = json.loads(json.dumps(value, default=str, ensure_ascii=False))
    return loaded


def _field_names(normalized: Mapping[str, object], merged: Mapping[str, object]) -> list[str]:
    names = {k for k in normalized if k != _MERGE} | set(merged)
    known = [n for n in FIELD_ORDER if n in names]
    return known + sorted(names - set(known))


Fields = Mapping[str, object]


def _field(name: str, normalized: Fields, raw: Fields, merged: Fields) -> dict[str, object]:
    donut = merged.get(name)
    entry: dict[str, object] = {
        "name": name,
        "value": _plain(normalized.get(name)),
        "raw": _plain(raw.get(name)),
        "confidence": None,
        "decision": None,
        "proposal": None,
        "text_match": None,
        "checks": [],
    }
    if isinstance(donut, Mapping):
        entry.update(
            confidence=donut.get("confidence"),
            decision=donut.get("decision"),
            proposal=_plain(donut.get("donut")),
            text_match=donut.get("text_match"),
            checks=_plain(donut.get("checks") or []),
        )
    return entry


def fields_of(context: PipelineContext) -> list[dict[str, object]]:
    """Felder mit Normalwert, Rohwert und – bei Donut – Feldkonfidenz und Entscheidung."""
    artifacts = context.artifacts
    normalized = artifacts.normalized_json or {}
    raw = artifacts.extracted_fields or {}
    merge = normalized.get(_MERGE)
    fields = merge.get("fields") if isinstance(merge, Mapping) else None
    merged: Mapping[str, object] = fields if isinstance(fields, Mapping) else {}
    return [_field(n, normalized, raw, merged) for n in _field_names(normalized, merged)]


def _ocr(context: PipelineContext, thresholds: Thresholds) -> dict[str, object] | None:
    metrics = context.ocr_metrics
    if metrics is None:
        return None
    return {**metrics.to_dict(), "quality": thresholds.quality(metrics.avg_confidence)}


def _pages(context: PipelineContext) -> list[dict[str, object]]:
    pages = context.artifacts.ocr_pages or []
    return [
        {
            "page": page.get("page", index + 1),
            "confidence": page.get("confidence"),
            "text": str(page.get("text") or ""),
        }
        for index, page in enumerate(pages)
        if isinstance(page, Mapping)
    ]


def _findings(context: PipelineContext) -> list[dict[str, object]]:
    return [
        {
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "severity": r.severity,
            "outcome": r.outcome,
            "message": r.message,
            "evidence": _plain(r.evidence),
        }
        for r in context.validation_results
    ]


def run_result(
    context: PipelineContext, document: Mapping[str, object], thresholds: Thresholds
) -> dict[str, object]:
    """Lauf, Dokument, OCR, Seiten, Felder und Befunde eines abgeschlossenen Kontexts."""
    artifacts = context.artifacts
    return {
        "run": {
            "run_id": context.run_id,
            "status": context.status.value,
            "needs_review": context.needs_review(),
            "error_code": context.error_code,
            "error": context.error,
            "retryable": context.retryable,
            "completed_stages": list(context.completed_stages),
            "hash_chain": list(context.hash_chain),
            "duration_ms": context.total_duration_ms,
        },
        "document": {
            **document,
            "size_bytes": artifacts.file_size_bytes,
            "mime_type": artifacts.mime_type,
            "page_count": artifacts.page_count,
        },
        "ocr": _ocr(context, thresholds),
        "pages": _pages(context),
        "fields": fields_of(context),
        "findings": _findings(context),
        "flags": list(context.validation_flags),
        "stored": False,
    }
