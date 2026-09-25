"""Refaktorierung 0.2.1: bisherige Importpfade bleiben gültig, neue Bausteine sind geprüft."""

from __future__ import annotations

import importlib
from decimal import Decimal

import pytest

#: Bisheriger Modulpfad → (neues Modul, Namen, die dort definiert und hier re-exportiert sind).
MOVED = {
    "auditcore_documents.pipeline.context": (
        "auditcore_documents.pipeline.settings_models",
        [
            "OcrSettings",
            "ParserSettings",
            "LlmSettings",
            "RagConfig",
            "AnalysisModules",
            "PostProcessingSettings",
            "PipelineProfileSettings",
            "OcrBackend",
            "ExtractionMethod",
        ],
    ),
    "auditcore_documents.pipeline.stages.ocr": (
        "auditcore_documents.pipeline.stages.ocr_results",
        [
            "OcrRouting",
            "RouterResult",
            "ParsedDocument",
            "ParsedPage",
            "pdfium_rasterizer",
            "combine_router_pages",
            "single_router_result",
            "chandra_result",
            "tesseract_result",
            "donut_result",
            "donut_text",
            "should_use_router",
            "looks_like_pdf",
            "RouterCall",
        ],
    ),
    "auditcore_documents.pipeline.stages.validation": (
        "auditcore_documents.pipeline.stages.validation_rules",
        [
            "IbanChecksumRule",
            "VatIdFormatRule",
            "TotalSumPlausibilityRule",
            "OcrConfidenceRule",
            "AmountFormatRule",
        ],
    ),
    "auditcore_documents.pipeline.stages.donut_merge": (
        "auditcore_documents.pipeline.stages.donut_values",
        [
            "amount",
            "iso_date",
            "rate",
            "clean_amount",
            "combine_pages",
            "combine_confidence",
            "vat_id_check",
            "confirmed_in_text",
            "text_amounts",
            "text_dates",
            "MONTHS",
        ],
    ),
}


@pytest.mark.parametrize("old_path", sorted(MOVED))
def test_previous_import_paths_re_export_the_same_objects(old_path: str) -> None:
    new_path, names = MOVED[old_path]
    old, new = importlib.import_module(old_path), importlib.import_module(new_path)
    for name in names:
        assert getattr(old, name) is getattr(new, name), name
        assert name in old.__all__, name


def test_validation_module_keeps_fraud_names() -> None:
    from auditcore_documents.pipeline.stages import fraud_rule, validation

    for name in ("FraudAssessment", "FraudChecker", "FraudDetectionRule", "fraud_invoice_date"):
        assert getattr(validation, name) is getattr(fraud_rule, name)


def test_watchdog_package_exports() -> None:
    from auditcore_documents.pipeline import watchdog
    from auditcore_documents.pipeline.watchdog import model

    for name in watchdog.__all__:
        assert hasattr(watchdog, name), name
    assert watchdog.WatchdogFinding is model.WatchdogFinding


def test_watchdog_issue_helpers() -> None:
    from auditcore_documents.pipeline.watchdog.document_checks import (
        invoice_number_issues,
        supplier_name_issues,
    )

    assert invoice_number_issues("RE-2026-001") == []
    assert invoice_number_issues("Rechnung über Steuer und viele weitere Worte") == [
        "zu lang (44 > 30 Zeichen)",
        "sieht nach Fließtext aus, nicht nach Rechnungsnummer",
        "verdächtiger Inhalt (enthält 'steuer')",
    ]
    assert supplier_name_issues("12") == ["zu kurz (2 Zeichen)", "besteht nur aus Zahlen"]
    assert supplier_name_issues("ACME GmbH") == []


def test_article_law_handler_table_covers_every_pattern() -> None:
    from auditcore_documents.article_law import COMMAND_HANDLERS, COMMAND_PATTERNS

    assert [kind for kind, _pattern in COMMAND_PATTERNS] == list(COMMAND_HANDLERS)


def test_donut_candidates_are_typed_by_field() -> None:
    from auditcore_documents.pipeline.stages.donut_checks import donut_candidates, vat_lines

    values = donut_candidates(
        {
            "invoice_number": " RE  7 ",
            "invoice_date": "01.02.2026",
            "total": "119,00",
            "iban": "DE89 3704 0044 0532 0130 00",
            "vat_lines": [{"rate": "19%", "amount": "19,00", "base": "100,00"}],
        }
    )
    assert values["invoice_number"] == (" RE  7 ", "RE 7")
    assert values["date"] == ("01.02.2026", "2026-02-01")
    assert values["total"] == ("119,00", Decimal("119.00"))
    assert values["iban"][1] == "DE89370400440532013000"
    assert values["vat_amount"] == ("19,00", Decimal("19.00"))
    assert vat_lines(values) == [(Decimal(19), Decimal("100.00"), Decimal("19.00"))]


def test_docx_style_bounds_layout_values() -> None:
    from auditcore_documents.docx_parts import NAVY, DocxStyle

    style = DocxStyle.from_layout(
        {"body_font_size_pt": 99, "accent_color": "#zzzzzz", "font_family": ""}, None
    )
    assert style.body_size == 18.0
    assert style.accent_color == NAVY
    assert style.font_family == "Hessen Gellix"
    assert style.header_text == "Vermerk"
    with pytest.raises(ValueError):
        DocxStyle.from_layout({"line_spacing": "breit"}, None)
