"""Geschäftsregeln und Plausibilität (aus ``stages/validation.py``).

Regeln, Schweregrade, Meldungen und Statuslogik wie im Original. Die
Betrugsprüfung ist ein Port (``FraudChecker``); der FraudDetectionManager
mit Datenbank bleibt in der Anwendung. Datumsangaben ohne Zuordnung fallen
wie im Original auf „heute“ zurück (Uhr injizierbar).
"""

from __future__ import annotations

from auditcore_documents.pipeline.context import PipelineContext, RunStatus, ValidationResult
from auditcore_documents.pipeline.stages.base import PipelineStage
from auditcore_documents.pipeline.stages.fraud_rule import (
    FraudAssessment,
    FraudCall,
    FraudChecker,
    FraudDetectionRule,
    fraud_invoice_date,
)
from auditcore_documents.pipeline.stages.validation_base import (
    IBAN_COUNTRY_LENGTHS,
    VAT_ID_PATTERNS,
    ValidationRule,
    validate_iban,
)
from auditcore_documents.pipeline.stages.validation_rules import (
    AmountFormatRule,
    IbanChecksumRule,
    OcrConfidenceRule,
    TotalSumPlausibilityRule,
    VatIdFormatRule,
)

__all__ = [
    "IBAN_COUNTRY_LENGTHS",
    "VAT_ID_PATTERNS",
    "AmountFormatRule",
    "FraudAssessment",
    "FraudCall",
    "FraudChecker",
    "FraudDetectionRule",
    "IbanChecksumRule",
    "OcrConfidenceRule",
    "TotalSumPlausibilityRule",
    "ValidationRule",
    "ValidationStage",
    "VatIdFormatRule",
    "default_rules",
    "fraud_invoice_date",
    "summarize",
    "validate_iban",
]


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
        if self.audit is not None:
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
