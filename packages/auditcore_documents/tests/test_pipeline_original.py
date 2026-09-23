"""Originaltests aus flowinvoice (tests/pipeline/test_postprocess.py, test_validation.py).

Aussagen unverändert, umgestellt auf die Bibliothek (asyncio.run statt pytest-asyncio).
"""

from __future__ import annotations

import asyncio

from auditcore_documents.pipeline import (
    CORRECTED_PIPELINE,
    OcrMetrics,
    PipelineContext,
    RunStatus,
    ValidationResult,
    ValidationStage,
)
from auditcore_documents.pipeline.stages.postprocess import extract_fields, normalize_fields
from auditcore_documents.pipeline.stages.validation import (
    TotalSumPlausibilityRule,
    ValidationRule,
)

RECHNUNG_DE = """
RECHNUNG

Rechnungsnummer: 2025-001
Rechnungsdatum: 15.12.2025

Mustermann GmbH
USt-IdNr.: DE123456789

Leistungsbeschreibung: Softwareentwicklung

Nettobetrag:                1.000,00 EUR
MwSt. 19%:                    190,00 EUR
Bruttobetrag:               1.190,00 EUR

IBAN: DE89 3704 0044 0532 0130 00
"""


def fields(text: str) -> dict[str, object]:
    return normalize_fields(extract_fields(text))


def test_netto_steuer_und_brutto_werden_extrahiert() -> None:
    f = fields(RECHNUNG_DE)
    assert (f["net_amount"], f["vat_amount"], f["total"]) == (1000.0, 190.0, 1190.0)


def test_betraege_sind_zahlen_kein_text() -> None:
    f = fields(RECHNUNG_DE)
    assert all(isinstance(f[k], float) for k in ("net_amount", "vat_amount", "total"))


def test_englische_schreibweise() -> None:
    text = """
    Invoice No: INV-2025-77
    Date: 15.12.2025
    Net amount: 500,00 EUR
    VAT 19%: 95,00 EUR
    Total: 595,00 EUR
    """
    f = fields(text)
    assert (f["net_amount"], f["vat_amount"], f["total"]) == (500.0, 95.0, 595.0)


def test_fehlende_betraege_bleiben_none() -> None:
    f = fields("RECHNUNG\nRechnungsdatum: 15.12.2025\n")
    assert (f["net_amount"], f["vat_amount"], f["total"]) == (None, None, None)


def test_rechnungsnummer_datum_ust_id_iban() -> None:
    f = fields(RECHNUNG_DE)
    assert f["invoice_number"] == "2025-001"
    assert fields("Rechnungs-Nr.: 2025-042")["invoice_number"] == "2025-042"
    assert f["date"] == "2025-12-15"
    assert f["vat_id"] == "DE123456789"
    assert f["iban"] == "DE89370400440532013000"


def test_regel_rechnet_mit_den_extrahierten_feldern() -> None:
    context = PipelineContext(document_id="doc-1", run_id="run-1")
    context.artifacts.normalized_json = fields(RECHNUNG_DE)
    result = asyncio.run(TotalSumPlausibilityRule(threshold=0.01).evaluate(context))
    assert result.outcome == "PASS" and "Not all amount fields" not in result.message
    context.artifacts.normalized_json = fields(RECHNUNG_DE.replace("1.190,00 EUR", "1.290,00 EUR"))
    assert asyncio.run(TotalSumPlausibilityRule(threshold=0.01).evaluate(context)).outcome == "FAIL"


def base_context() -> PipelineContext:
    context = PipelineContext(document_id="doc-123")
    context.artifacts.normalized_json = {}
    context.status = RunStatus.RUNNING
    return context


def test_all_pass_results_in_ok() -> None:
    context = base_context()
    context.artifacts.normalized_json = {"iban": "DE89370400440532013000", "vat_id": "DE123456789"}
    context.ocr_metrics = OcrMetrics(
        engine="chandra",
        avg_confidence=0.95,
        min_confidence=0.90,
        pages_processed=1,
        duration_ms=100,
    )
    assert asyncio.run(ValidationStage().execute(context)).status == RunStatus.OK


def test_warn_results_in_review_needed() -> None:
    context = base_context()
    context.ocr_metrics = OcrMetrics(
        engine="tesseract",
        avg_confidence=0.70,
        min_confidence=0.60,
        pages_processed=1,
        duration_ms=100,
    )
    result = asyncio.run(ValidationStage().execute(context))
    assert result.status == RunStatus.REVIEW_NEEDED
    assert any("REVIEW" in flag for flag in result.validation_flags)


def test_critical_results_in_rejected() -> None:
    context = base_context()
    context.artifacts.normalized_json = {"iban": "DE00000000000000000000"}
    result = asyncio.run(ValidationStage().execute(context))
    assert result.status == RunStatus.REJECTED
    assert any("CRITICAL" in flag for flag in result.validation_flags)


def test_validation_results_are_collected() -> None:
    assert len(asyncio.run(ValidationStage().execute(base_context())).validation_results) > 0


def test_custom_rules_can_be_added() -> None:
    class AlwaysFailRule(ValidationRule):
        def __init__(self) -> None:
            super().__init__(rule_id="TEST_ALWAYS_FAIL", name="always_fail", severity="WARN")

        async def evaluate(self, ctx: PipelineContext) -> ValidationResult:
            return ValidationResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity="WARN",
                outcome="FAIL",
                message="This rule always fails",
            )

    result = asyncio.run(ValidationStage(rules=[AlwaysFailRule()]).execute(base_context()))
    assert result.status == RunStatus.REVIEW_NEEDED
    assert [r.rule_id for r in result.validation_results] == ["TEST_ALWAYS_FAIL"]


def test_corrected_iban_pattern_stops_at_line_end() -> None:
    """PL-C02: Im Original frisst das Muster die Folgezeile (gültige IBAN wird ungültig)."""
    text = "IBAN: DE89 3704 0044 0532 0130 00\nNettobetrag: 1.000,00 EUR\n"
    legacy = fields(text)["iban"]
    corrected = normalize_fields(extract_fields(text, CORRECTED_PIPELINE.field_patterns))["iban"]
    assert legacy == "DE89370400440532013000NETTOB"
    assert corrected == "DE89370400440532013000"
