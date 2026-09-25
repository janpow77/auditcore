"""Betrugsprüfungsregel über den ``FraudChecker``-Port (aus ``stages/validation.py``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from auditcore_documents.pipeline.context import PipelineContext, ValidationResult
from auditcore_documents.pipeline.stages.validation_base import ValidationRule


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


def _total_amount(total_str: object) -> Decimal:
    try:
        return Decimal(str(total_str).replace(",", ".")) if total_str else Decimal("0")
    except (ValueError, TypeError):
        # decimal.InvalidOperation ist kein ValueError: sie verlässt die Regel wie im
        # Original und wird von der Stufe als ERROR_VAL_FRAUD_DETECTION gewertet.
        return Decimal("0")


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
        total_amount = _total_amount(total_str)
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
        return self._assessment_result(result)

    def _assessment_result(self, result: FraudAssessment) -> ValidationResult:
        """Risikostufe des Ports → Regelergebnis (kritisch, hoch/mittel, sonst bestanden)."""
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


FraudCall = Callable[..., Awaitable[FraudAssessment]]
