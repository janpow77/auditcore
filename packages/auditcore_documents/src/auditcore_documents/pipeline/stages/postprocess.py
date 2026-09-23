"""Nachverarbeitung: Bereinigung, Feldextraktion, Normalisierung (aus ``stages/postprocess.py``).

Reine Textverarbeitung ohne Abhängigkeiten; Muster und Normalisierung
unverändert. Datumswerte, die sich nicht parsen lassen, bleiben wie im
Original als Text erhalten.
"""

from __future__ import annotations

import contextlib
import re
from datetime import datetime
from typing import Any

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage

FIELD_PATTERNS: dict[str, list[str]] = {
    "invoice_number": [
        r"Rechnungsnummer\s*:?\s*([A-Z0-9\-/]+)",
        r"Rechnungs?-?Nr\.?\s*:?\s*([A-Z0-9\-/]+)",
        r"Invoice\s*(?:No\.?|Number)?\s*:?\s*([A-Z0-9\-/]+)",
        r"Re\.?-?Nr\.?\s*:?\s*([A-Z0-9\-/]+)",
    ],
    "date": [
        r"Rechnungsdatum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"Datum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"Date\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
    ],
    "total": [
        r"Gesamtbetrag\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"Bruttobetrag\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"Total\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"Summe\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
    ],
    # Netto und Steuer werden gebraucht, damit die
    # Summen-Plausibilität (VAL_TOTAL_PLAUSIBILITY) überhaupt
    # rechnen kann — ohne diese Felder überspringt sie jeden Beleg.
    "net_amount": [
        r"Nettobetrag\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"Netto(?:summe)?\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"Zwischensumme\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"(?:Net\s*(?:amount|total)|Subtotal)\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
    ],
    "vat_amount": [
        r"(?:MwSt|USt)\.?(?:\s*\d{1,2}(?:[.,]\d+)?\s*%)?\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"(?:Mehrwertsteuer|Umsatzsteuer)\s*(?:\d{1,2}(?:[.,]\d+)?\s*%)?\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
        r"VAT\s*(?:\d{1,2}(?:[.,]\d+)?\s*%)?\s*:?\s*([\d.,]+)\s*(?:EUR|€)?",
    ],
    "iban": [r"IBAN\s*:?\s*([A-Z]{2}\d{2}[A-Z0-9\s]{11,30})"],
    "vat_id": [
        r"USt\.?-?Id\.?(?:-?Nr\.?)?\s*:?\s*([A-Z]{2}\d{9,12})",
        r"VAT\s*(?:ID|Number)?\s*:?\s*([A-Z]{2}\d{9,12})",
    ],
}

DATE_FORMATS = ("%d.%m.%Y", "%d/%m/%Y", "%d.%m.%y", "%d/%m/%y", "%Y-%m-%d")


def cleanup_text(text: str) -> str:
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_fields(text: str, patterns: dict[str, list[str]] | None = None) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for field_name, candidates in (patterns or FIELD_PATTERNS).items():
        for pattern in candidates:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                fields[field_name] = match.group(1).strip()
                break
        else:
            fields[field_name] = None
    return fields


def normalize_date(date_str: str) -> str | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


def normalize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    normalized = fields.copy()
    if normalized.get("iban"):
        normalized["iban"] = re.sub(r"\s+", "", normalized["iban"]).upper()
    for amount_field in ("total", "net_amount", "vat_amount"):
        raw_amount = normalized.get(amount_field)
        if not isinstance(raw_amount, str):
            continue
        amount_str = raw_amount.replace(".", "").replace(",", ".")
        with contextlib.suppress(ValueError):
            normalized[amount_field] = float(amount_str)
    if normalized.get("date"):
        normalized["date"] = normalize_date(normalized["date"])
    if normalized.get("vat_id"):
        normalized["vat_id"] = re.sub(r"\s+", "", normalized["vat_id"]).upper()
    return normalized


class PostprocessStage(PipelineStage):
    name = "postprocess"
    description = "Post-processing and field extraction"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.patterns = {name: list(values) for name, values in FIELD_PATTERNS.items()}

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        ocr_text = context.artifacts.ocr_text
        if not ocr_text:
            return context
        cleaned = cleanup_text(ocr_text)
        extracted = extract_fields(cleaned, self.patterns)
        context.artifacts.extracted_fields = extracted
        context.artifacts.normalized_json = normalize_fields(extracted)
        return context
