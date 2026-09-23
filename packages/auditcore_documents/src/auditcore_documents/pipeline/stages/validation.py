"""Geschäftsregeln und Plausibilität (aus ``stages/validation.py``).

Regeln, Schweregrade, Meldungen und Statuslogik wie im Original. Die
Betrugsprüfung ist ein Port (``FraudChecker``); der FraudDetectionManager
mit Datenbank bleibt in der Anwendung. Datumsangaben ohne Zuordnung fallen
wie im Original auf „heute“ zurück (Uhr injizierbar).
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

from auditcore_documents.pipeline.context import PipelineContext, RunStatus, ValidationResult
from auditcore_documents.pipeline.stages.base import PipelineStage

IBAN_COUNTRY_LENGTHS = {
    "DE": 22,
    "AT": 20,
    "CH": 21,
    "FR": 27,
    "IT": 27,
    "ES": 24,
    "NL": 18,
    "BE": 16,
    "GB": 22,
}
VAT_ID_PATTERNS = {
    "DE": r"^DE\d{9}$",
    "AT": r"^ATU\d{8}$",
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "IT": r"^IT\d{11}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "NL": r"^NL\d{9}B\d{2}$",
    "BE": r"^BE0?\d{9,10}$",
    "GB": r"^GB\d{9}$|^GB\d{12}$|^GBGD\d{3}$|^GBHA\d{3}$",
}


def validate_iban(iban: str) -> tuple[bool, str]:
    """Längen- und Modulo-97-Prüfung nach ISO 13616 (Meldungen wie im Original)."""
    iban = iban.replace(" ", "").upper()
    if len(iban) < 15 or len(iban) > 34:
        return False, f"Invalid IBAN length: {len(iban)}"
    country = iban[:2]
    expected = IBAN_COUNTRY_LENGTHS.get(country)
    if expected is not None and len(iban) != expected:
        return False, f"Invalid IBAN length for {country}: expected {expected}, got {len(iban)}"
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(char if char.isdigit() else str(ord(char) - 55) for char in rearranged)
    try:
        if int(numeric) % 97 != 1:
            return False, "IBAN checksum invalid"
    except ValueError:
        return False, "IBAN contains invalid characters"
    return True, ""


class ValidationRule:
    rule_id: str
    name: str
    description: str
    severity: str = "WARN"
    action_on_fail: str = "REVIEW_NEEDED"

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str = "",
        severity: str = "WARN",
        action_on_fail: str = "REVIEW_NEEDED",
        threshold: float | None = None,
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity
        self.action_on_fail = action_on_fail
        self.threshold = threshold

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        raise NotImplementedError

    def result(self, severity: Any, outcome: Any, message: str, **extra: Any) -> ValidationResult:
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=severity,
            outcome=outcome,
            message=message,
            **extra,
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


@dataclass
class FraudAssessment:
    """Ergebnis des Betrugsprüfungs-Ports (Auszug aus ``FraudAnalysisResult``)."""

    risk_level: str
    risk_factors: list[str] = field(default_factory=list)
    risk_score: float | None = None
    duplicate_found: bool = False
    sanctions_hit: bool = False


class FraudChecker(Protocol):
    def __call__(
        self,
        *,
        invoice_number: str,
        supplier_name: str,
        supplier_vat_id: str | None,
        total_amount: Decimal,
        invoice_date: date,
        project_id: str | None,
        exclude_document_id: str,
    ) -> Awaitable[FraudAssessment]: ...


def fraud_invoice_date(value: str | None, today: date) -> date:
    """Datumslogik des Originals (einschließlich Rückfall auf „heute“)."""
    if not value:
        return today
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            parsed = date.fromisoformat(value) if "-" in value else None
            if not parsed:
                parsed = datetime.strptime(value, fmt).date()
            return parsed
        except ValueError:
            continue
    return today


class FraudDetectionRule(ValidationRule):
    def __init__(
        self,
        fraud_checker: FraudChecker | None = None,
        today: Callable[[], date] = date.today,
    ) -> None:
        super().__init__(
            rule_id="VAL_FRAUD_DETECTION",
            name="fraud_detection",
            description="Betrugserkennungsprüfungen (Duplikate, Sanktionen, Benford)",
            severity="CRITICAL",
            action_on_fail="REVIEW_NEEDED",
        )
        self.fraud_checker = fraud_checker
        self.today = today

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        if context.analysis_modules and not context.analysis_modules.fraud_detection:
            return self.result("INFO", "PASS", "Fraud detection disabled in analysis modules")
        fields = context.artifacts.normalized_json or {}
        invoice_number = fields.get("invoice_number")
        supplier_name = fields.get("supplier_name") or fields.get("vendor_name")
        supplier_vat_id = fields.get("vat_id") or fields.get("supplier_vat_id")
        total_str = fields.get("total") or fields.get("total_amount")
        if not invoice_number or not supplier_name:
            return self.result(
                "INFO",
                "PASS",
                "Insufficient data for fraud detection (missing invoice_number or supplier_name)",
            )
        try:
            total_amount = Decimal(str(total_str).replace(",", ".")) if total_str else Decimal("0")
        except (ValueError, TypeError):
            # decimal.InvalidOperation ist kein ValueError: sie verlässt die Regel wie im
            # Original und wird von der Stufe als ERROR_VAL_FRAUD_DETECTION gewertet.
            total_amount = Decimal("0")
        invoice_date = fraud_invoice_date(
            fields.get("date") or fields.get("invoice_date"), self.today()
        )
        if self.fraud_checker is None:
            # Meldung des Originals, wenn keine DB-Sitzung übergeben wurde.
            return self.result("INFO", "PASS", "No database session for fraud detection")
        try:
            result = await self.fraud_checker(
                invoice_number=invoice_number,
                supplier_name=supplier_name,
                supplier_vat_id=supplier_vat_id,
                total_amount=total_amount,
                invoice_date=invoice_date,
                project_id=context.project_id,
                exclude_document_id=context.document_id,
            )
        except Exception as exc:  # noqa: BLE001 - Originalvertrag
            return self.result("WARN", "REVIEW", f"Fraud detection error: {exc}")
        level = str(result.risk_level)
        factors = ", ".join(result.risk_factors)
        if level == "critical":
            return self.result(
                "CRITICAL",
                "FAIL",
                f"CRITICAL fraud risk detected: {factors}",
                evidence={
                    "risk_level": level,
                    "risk_factors": result.risk_factors,
                    "risk_score": result.risk_score,
                    "duplicate_found": result.duplicate_found,
                    "sanctions_hit": result.sanctions_hit,
                },
            )
        if level in ("high", "medium"):
            return self.result(
                "WARN" if level == "high" else "INFO",
                "REVIEW",
                f"{'High' if level == 'high' else 'Medium'} fraud risk: {factors}",
                evidence={
                    "risk_level": level,
                    "risk_factors": result.risk_factors,
                    "risk_score": result.risk_score,
                },
            )
        return self.result(
            "INFO",
            "PASS",
            f"Fraud detection passed (risk level: {level})",
            evidence={"risk_level": level, "risk_score": result.risk_score},
        )


def default_rules(fraud_checker: FraudChecker | None = None) -> list[ValidationRule]:
    return [
        IbanChecksumRule(),
        VatIdFormatRule(),
        TotalSumPlausibilityRule(),
        OcrConfidenceRule(),
        FraudDetectionRule(fraud_checker=fraud_checker),
    ]


def summarize(results: list[ValidationResult]) -> dict[str, int]:
    return {
        "results_count": len(results),
        "pass_count": sum(1 for r in results if r.outcome == "PASS"),
        "fail_count": sum(1 for r in results if r.outcome == "FAIL"),
        "review_count": sum(1 for r in results if r.outcome == "REVIEW"),
    }


class ValidationStage(PipelineStage):
    name = "validation"
    description = "Business rules validation and plausibility checks"

    def __init__(
        self,
        *args: object,
        rules: list[ValidationRule] | None = None,
        fraud_checker: FraudChecker | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.rules = rules or default_rules(fraud_checker)

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        has_critical_fail = False
        has_review = False
        for rule in self.rules:
            try:
                result = await rule.evaluate(context)
                context.validation_results.append(result)
                if result.outcome == "FAIL":
                    if result.severity == "CRITICAL":
                        has_critical_fail = True
                        context.add_validation_flag(f"CRITICAL_{rule.rule_id}")
                    else:
                        has_review = True
                        context.add_validation_flag(f"FAIL_{rule.rule_id}")
                elif result.outcome == "REVIEW":
                    has_review = True
                    context.add_validation_flag(f"REVIEW_{rule.rule_id}")
            except Exception:  # noqa: BLE001 - Originalvertrag: Regelfehler → Review
                context.add_validation_flag(f"ERROR_{rule.rule_id}")
                has_review = True
        if has_critical_fail:
            context.status = RunStatus.REJECTED
        elif has_review:
            context.status = RunStatus.REVIEW_NEEDED
        elif context.status == RunStatus.RUNNING:
            context.status = RunStatus.OK
        if self.audit:
            await self.audit.log_event(
                event_type="VALIDATION_COMPLETE",
                document_id=context.document_id,
                run_id=context.run_id,
                hash_original=context.hash_original,
                details={
                    "status": context.status.value,
                    "flags": context.validation_flags,
                    **summarize(context.validation_results),
                },
            )
        return context


FraudCall = Callable[..., Awaitable[FraudAssessment]]
