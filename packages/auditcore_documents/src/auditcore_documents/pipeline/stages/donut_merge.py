"""Zusammenführung der Donut-Felder mit Pflicht-Plausibilitätsprüfung (Plan 2a).

Ein Donut-Wert wird nur übernommen, wenn er die Plausibilitätsprüfung besteht
**und** entweder seine Feldkonfidenz den Profilschwellwert erreicht oder der
gleiche Wert im Tesseract-Text vorkommt (Zwei-Motoren-Abgleich). Beträge
brauchen zusätzlich die Summenprüfung ``netto + USt = brutto``; ist sie mangels
Angaben nicht rechenbar, muss der Betrag im Tesseract-Text bestätigt sein. Ein
Betrag aus Donut führt damit nie ungeprüft zu ``OK``.

Sonst bleibt der Regex-Wert aus ``PostprocessStage`` (bzw. das Feld leer) und
die Regeln ``VAL_DONUT_PLAUSIBILITY``/``VAL_DONUT_DISAGREEMENT`` setzen
``REVIEW_NEEDED``. Der Entscheidungsbericht steht in
``normalized_json["donut_merge"]``.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage
from auditcore_documents.pipeline.stages.donut_checks import plausibility_failures
from auditcore_documents.pipeline.stages.donut_values import (
    ALLOWED_VAT_RATES,
    AMOUNTS,
    CENT,
    CORE_FIELDS,
    MONTHS,
    TEXT_CONFIRMED_FIELDS,
    amount,
    at_uid_check_digit,
    clean_amount,
    combine_confidence,
    combine_pages,
    compact,
    confirmed_in_text,
    de_vat_check_digit,
    iso_date,
    rate,
    text_amounts,
    text_dates,
    vat_id_check,
)
from auditcore_documents.pipeline.stages.validation import ValidationRule

__all__ = [
    "ALLOWED_VAT_RATES",
    "AMOUNTS",
    "CENT",
    "CORE_FIELDS",
    "MONTHS",
    "TEXT_CONFIRMED_FIELDS",
    "DonutDisagreementRule",
    "DonutFieldMergeStage",
    "DonutPlausibilityRule",
    "amount",
    "at_uid_check_digit",
    "clean_amount",
    "combine_confidence",
    "combine_pages",
    "compact",
    "confirmed_in_text",
    "de_vat_check_digit",
    "donut_rules",
    "iso_date",
    "rate",
    "text_amounts",
    "text_dates",
    "vat_id_check",
]


# --------------------------------------------------------------------------- Stufe
class DonutFieldMergeStage(PipelineStage):
    """Nach ``PostprocessStage``: Donut-Werte prüfen, abgleichen und übernehmen."""

    name = "donut_merge"
    description = "Merge Donut fields after mandatory plausibility checks"

    def __init__(
        self,
        *args: object,
        min_field_confidence: float = 0.90,
        today: Callable[[], date] = date.today,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.min_field_confidence = min_field_confidence
        self.today = today

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        raw = context.artifacts.ocr_raw_json or {}
        if raw.get("engine") != "donut":
            return context
        pages = list(raw.get("pages") or [])
        donut = combine_pages(pages)
        confidence = combine_confidence(pages)
        text = str((raw.get("tesseract") or {}).get("text") or "")
        normalized = dict(context.artifacts.normalized_json or {})
        extracted = dict(context.artifacts.extracted_fields or {})
        report = self.merge(donut, confidence, text, normalized, extracted)
        report.update(
            {
                "model_id": raw.get("model_id"),
                "model_sha256": raw.get("model_sha256"),
                "threshold": self.min_field_confidence,
                "tesseract_text": bool(text),
            }
        )
        normalized["donut_merge"] = report
        context.artifacts.normalized_json = normalized
        context.artifacts.extracted_fields = extracted
        return context

    # -- Kandidaten ----------------------------------------------------------
    @staticmethod
    def candidates(donut: dict[str, Any]) -> dict[str, tuple[str, Any]]:
        """Pipeline-Feld → (gedruckter Rohwert, normalisierter Wert oder ``None``)."""
        result: dict[str, tuple[str, Any]] = {}
        supplier = donut.get("supplier") if isinstance(donut.get("supplier"), dict) else {}
        simple = {
            "invoice_number": donut.get("invoice_number"),
            "date": donut.get("invoice_date"),
            "net_amount": donut.get("net_amount"),
            "total": donut.get("total"),
            "iban": donut.get("iban"),
            "vat_id": supplier.get("vat_id") if supplier else None,
            "supplier_name": supplier.get("name") if supplier else None,
            "supply_date": donut.get("supply_date"),
            "due_date": donut.get("due_date"),
            "bic": donut.get("bic"),
        }
        for name, value in simple.items():
            if not isinstance(value, str) or not value.strip():
                continue
            if name in AMOUNTS:
                parsed: Any = amount(value)
            elif name in {"date", "supply_date", "due_date"}:
                parsed = iso_date(value)
            elif name in {"iban", "vat_id", "bic"}:
                parsed = compact(value)
            else:
                parsed = " ".join(value.split())
            result[name] = (value, parsed)
        lines = donut.get("vat_lines")
        if isinstance(lines, list) and lines:
            amounts = [amount(str(line.get("amount", ""))) for line in lines]
            raw_text = " + ".join(str(line.get("amount", "")) for line in lines)
            total = (
                sum((a for a in amounts if a is not None), Decimal(0))
                if all(a is not None for a in amounts)
                else None
            )
            result["vat_amount"] = (raw_text, total)
            result["vat_rates"] = (
                " + ".join(str(line.get("rate", "")) for line in lines),
                [rate(str(line.get("rate", ""))) for line in lines],
            )
            result["_vat_lines"] = (
                "",
                [
                    (
                        rate(str(line.get("rate", ""))),
                        amount(str(line.get("base", ""))) if line.get("base") else None,
                        amount(str(line.get("amount", ""))),
                    )
                    for line in lines
                ],
            )
        return result

    # -- Plausibilität -------------------------------------------------------
    def plausibility(self, values: dict[str, tuple[str, Any]]) -> dict[str, list[str]]:
        """Fehlgeschlagene Pflichtprüfungen je Feld (leere Liste = plausibel)."""
        return plausibility_failures(values, self.today())

    # -- Zusammenführung -----------------------------------------------------
    def merge(
        self,
        donut: dict[str, Any],
        confidence: dict[str, float],
        text: str,
        normalized: dict[str, Any],
        extracted: dict[str, Any],
    ) -> dict[str, Any]:
        values = self.candidates(donut)
        failed = self.plausibility(values)
        sum_checked = all(values.get(n, ("", None))[1] is not None for n in AMOUNTS)
        line_amounts = [a for _, _, a in values.get("_vat_lines", ("", []))[1]]
        fields: dict[str, Any] = {}
        for name, (raw, parsed) in values.items():
            if name.startswith("_"):
                continue
            conf = _field_confidence(name, confidence)
            match = parsed is not None and confirmed_in_text(name, parsed, text, line_amounts)
            # Ohne Tesseract-Text stammen Regex-Werte aus der Donut-Darstellung selbst.
            regex_value = normalized.get(name) if text else None
            entry: dict[str, Any] = {
                "donut": raw,
                "confidence": conf,
                "text_match": match,
                "checks": failed.get(name, []),
                "regex": regex_value,
            }
            final = self._value(name, parsed)
            entry["decision"] = self._decision(
                name, bool(failed.get(name)), regex_value, final, match, sum_checked, conf
            )
            if entry["decision"] == "accepted":
                _take(name, raw, parsed, final, normalized, extracted)
            entry["value"] = normalized.get(name)
            fields[name] = entry
        return {"fields": fields, "sum_checked": sum_checked}

    def _decision(
        self,
        name: str,
        rejected: bool,
        regex_value: object,
        final: object,
        match: bool,
        sum_checked: bool,
        conf: float | None,
    ) -> str:
        """Entscheidung je Feld in der Vorrangfolge des Plans 2a."""
        if rejected:
            return "rejected"
        if (
            regex_value is not None
            and name in TEXT_CONFIRMED_FIELDS
            and not match
            and not _same(name, regex_value, final)
        ):
            return "disagreement"
        if name in AMOUNTS and not sum_checked and not match:
            return "unconfirmed"
        if (conf is not None and conf >= self.min_field_confidence) or match:
            return "accepted"
        return "unconfirmed" if name in CORE_FIELDS else "not_taken"

    @staticmethod
    def _value(name: str, parsed: Any) -> Any:
        if name in AMOUNTS and parsed is not None:
            return float(parsed)
        if name == "vat_rates" and parsed is not None:
            return [float(r) for r in parsed if r is not None]
        return parsed


#: Pipeline-Feld → Schlüssel der Donut-Feldkonfidenz (sonst gleichnamig).
CONFIDENCE_KEYS = {
    "date": "invoice_date",
    "vat_id": "supplier.vat_id",
    "supplier_name": "supplier.name",
}


def _field_confidence(name: str, confidence: dict[str, float]) -> float | None:
    """Feldkonfidenz; Steuerbetrag/-sätze: Minimum über alle Steuerzeilen."""
    if name in {"vat_amount", "vat_rates"}:
        suffix = "amount" if name == "vat_amount" else "rate"
        keys = [k for k in confidence if k.startswith("vat_lines.") and k.endswith(suffix)]
        return min((confidence[k] for k in keys), default=None)
    return confidence.get(CONFIDENCE_KEYS.get(name, name))


def _take(
    name: str,
    raw: str,
    parsed: Any,
    final: object,
    normalized: dict[str, Any],
    extracted: dict[str, Any],
) -> None:
    """Übernimmt einen akzeptierten Donut-Wert in normalisierte und extrahierte Felder."""
    normalized[name] = final
    if name in AMOUNTS:
        extracted[name] = clean_amount(raw) if name != "vat_amount" else f"{parsed}"
    elif name in extracted or name in TEXT_CONFIRMED_FIELDS:
        extracted[name] = raw.strip()


def _same(name: str, left: Any, right: Any) -> bool:
    if name in AMOUNTS:
        try:
            return Decimal(str(left)).quantize(CENT) == Decimal(str(right)).quantize(CENT)
        except (InvalidOperation, ValueError):
            return False
    if name in {"iban", "vat_id"}:
        return compact(str(left)) == compact(str(right))
    return str(left).strip() == str(right).strip()


# --------------------------------------------------------------------------- Regeln
def _report(context: PipelineContext) -> dict[str, Any] | None:
    report = (context.artifacts.normalized_json or {}).get("donut_merge")
    return report if isinstance(report, dict) else None


class DonutPlausibilityRule(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_DONUT_PLAUSIBILITY",
            name="donut_plausibility",
            description="Donut-Werte bestehen die Pflicht-Plausibilitätsprüfung",
        )

    async def evaluate(self, context: PipelineContext) -> Any:
        report = _report(context)
        if report is None:
            if (context.artifacts.ocr_raw_json or {}).get("engine") == "donut":
                return self.result(self.severity, "REVIEW", "Donut ohne Zusammenführungsbericht")
            return self.result("INFO", "PASS", "No Donut result")
        rejected = {
            name: entry["checks"]
            for name, entry in report["fields"].items()
            if entry["decision"] == "rejected"
        }
        if not rejected:
            return self.result("INFO", "PASS", "Donut values plausible")
        return self.result(
            self.severity,
            "FAIL",
            "Donut-Werte unplausibel: " + ", ".join(sorted(rejected)),
            evidence=rejected,
        )


class DonutDisagreementRule(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_DONUT_DISAGREEMENT",
            name="donut_disagreement",
            description=(
                "Donut-Werte bestätigt (Konfidenz oder Tesseract-Text) und widerspruchsfrei"
            ),
        )

    async def evaluate(self, context: PipelineContext) -> Any:
        report = _report(context)
        if report is None:
            return self.result("INFO", "PASS", "No Donut result")
        open_fields = {
            name: entry["decision"]
            for name, entry in report["fields"].items()
            if entry["decision"] in {"disagreement", "unconfirmed"}
        }
        if not open_fields:
            return self.result("INFO", "PASS", "Donut values confirmed")
        return self.result(
            self.severity,
            "REVIEW",
            "Donut-Werte unbestätigt oder widersprüchlich: " + ", ".join(sorted(open_fields)),
            evidence=open_fields,
        )


def donut_rules() -> list[ValidationRule]:
    return [DonutPlausibilityRule(), DonutDisagreementRule()]
