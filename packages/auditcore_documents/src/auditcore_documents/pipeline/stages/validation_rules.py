"""Einzelregeln der Validierungsstufe: IBAN, USt-IdNr., Summen, OCR-Konfidenz, Betragsformat."""

from __future__ import annotations

import re

from auditcore_documents.pipeline.context import PipelineContext, ValidationResult
from auditcore_documents.pipeline.stages.validation_base import (
    VAT_ID_PATTERNS,
    ValidationRule,
    validate_iban,
)


class IbanChecksumRule(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_IBAN_CHECKSUM",
            name="iban_checksum",
            description="Validiert IBAN-Prüfsumme nach ISO 13616",
            severity="CRITICAL",
            action_on_fail="REJECTED",
        )

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        iban = (context.artifacts.normalized_json or {}).get("iban")
        if not iban:
            return self.result("INFO", "PASS", "No IBAN found, skipping validation")
        valid, message = validate_iban(iban)
        if valid:
            return self.result(
                self.severity, "PASS", f"IBAN checksum valid: {iban[:4]}...{iban[-4:]}"
            )
        return self.result(self.severity, "FAIL", message, evidence={"iban": iban})


class VatIdFormatRule(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_VAT_ID_FORMAT",
            name="vat_id_format",
            description="Validiert USt-ID Format nach EU-Vorgaben",
            severity="WARN",
            action_on_fail="REVIEW_NEEDED",
        )

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        vat_id = (context.artifacts.normalized_json or {}).get("vat_id")
        if not vat_id:
            return self.result("INFO", "PASS", "No VAT ID found, skipping validation")
        country = vat_id[:2].upper()
        pattern = VAT_ID_PATTERNS.get(country)
        if not pattern:
            return self.result(
                "INFO",
                "REVIEW",
                f"Unknown VAT ID country: {country}",
                evidence={"vat_id": vat_id, "country": country},
            )
        if re.match(pattern, vat_id):
            return self.result(self.severity, "PASS", f"VAT ID format valid: {vat_id}")
        return self.result(
            self.severity,
            "FAIL",
            f"VAT ID format invalid for country {country}",
            evidence={"vat_id": vat_id, "expected_pattern": pattern},
        )


class TotalSumPlausibilityRule(ValidationRule):
    def __init__(self, threshold: float = 0.01) -> None:
        super().__init__(
            rule_id="VAL_TOTAL_PLAUSIBILITY",
            name="total_sum_plausibility",
            description="Prüft ob Gesamtsumme = Netto + MwSt",
            severity="WARN",
            action_on_fail="REVIEW_NEEDED",
            threshold=threshold,
        )

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        fields = context.artifacts.normalized_json or {}
        total, net, vat = fields.get("total"), fields.get("net_amount"), fields.get("vat_amount")
        # Original: ``all([...])`` – ein Betrag 0 gilt als fehlend (PL-L06).
        if not all([total, net, vat]):
            return self.result(
                "INFO", "PASS", "Not all amount fields available for plausibility check"
            )
        try:
            total_f, net_f, vat_f = float(total), float(net), float(vat)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return self.result(
                "INFO",
                "REVIEW",
                "Could not parse amount fields as numbers",
                evidence={"total": total, "net": net, "vat": vat},
            )
        calculated = net_f + vat_f
        diff = abs(total_f - calculated)
        assert self.threshold is not None
        if diff <= self.threshold:
            return self.result(
                self.severity,
                "PASS",
                f"Sum plausible: {net_f} + {vat_f} = {calculated} (total: {total_f})",
            )
        return self.result(
            self.severity,
            "FAIL",
            f"Sum mismatch: {net_f} + {vat_f} = {calculated}, but total is {total_f}",
            evidence={
                "total": total_f,
                "net": net_f,
                "vat": vat_f,
                "calculated": calculated,
                "difference": diff,
                "threshold": self.threshold,
            },
        )


class OcrConfidenceRule(ValidationRule):
    def __init__(self, threshold: float = 0.85) -> None:
        super().__init__(
            rule_id="VAL_OCR_CONFIDENCE",
            name="ocr_confidence",
            description="Mindest-OCR-Confidence prüfen",
            severity="WARN",
            action_on_fail="REVIEW_NEEDED",
            threshold=threshold,
        )

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        if not context.ocr_metrics:
            return self.result("INFO", "PASS", "No OCR metrics available")
        avg = context.ocr_metrics.avg_confidence
        assert self.threshold is not None
        if avg >= self.threshold:
            return self.result(
                self.severity, "PASS", f"OCR confidence OK: {avg:.2%} >= {self.threshold:.2%}"
            )
        return self.result(
            self.severity,
            "REVIEW",
            f"OCR confidence low: {avg:.2%} < {self.threshold:.2%}",
            evidence={
                "avg_confidence": avg,
                "min_confidence": context.ocr_metrics.min_confidence,
                "threshold": self.threshold,
            },
        )


class AmountFormatRule(ValidationRule):
    """Mehrdeutige oder ungültige Beträge führen zur Prüfung statt zu geratenen Werten (D5)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_AMOUNT_FORMAT",
            name="amount_format",
            description="Beträge eindeutig lesbar (Dezimal-/Tausendertrennzeichen)",
            severity="WARN",
            action_on_fail="REVIEW_NEEDED",
        )

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        from auditcore_documents.pipeline.stages.postprocess import AMOUNT_FIELDS, parse_amount

        raw = context.artifacts.extracted_fields or {}
        unclear = {}
        for name in AMOUNT_FIELDS:
            value = raw.get(name)
            if isinstance(value, str):
                parsed, state = parse_amount(value)
                if parsed is None:
                    unclear[name] = {"raw": value, "state": state}
        if not unclear:
            return self.result("INFO", "PASS", "All amounts unambiguous")
        return self.result(
            self.severity,
            "REVIEW",
            "Ambiguous or invalid amounts: " + ", ".join(sorted(unclear)),
            evidence=unclear,
        )
