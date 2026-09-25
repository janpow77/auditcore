"""Entscheidungen D1 bis D8 vom 2026-09-23 (Nutzerzitat „alle empfehlungen“)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from test_pipeline_contract import scenario
from test_pipeline_replay import run

import auditcore_documents as ad
from auditcore_documents.article_law import LawParagraph, apply_commands
from auditcore_documents.pipeline import (
    ALL_CATEGORIES,
    CORRECTED_PIPELINE,
    LEGACY_PIPELINE,
    RECOMMENDED_PIPELINE,
    AmountFormatRule,
    InMemoryAuditLog,
    PipelineContext,
    RetentionPolicyConfig,
    RetentionSweeper,
    RunStatus,
    build_retention_sweeper,
    parse_amount,
)
from auditcore_documents.pipeline.stages.postprocess import (
    FIELD_PATTERNS,
    corrected_patterns,
    extract_fields,
    normalize_fields,
)

NOW = datetime(2026, 9, 23, tzinfo=UTC)


def test_legacy_fingerprints_are_stable() -> None:
    """Werte von origin/main vor den Entscheidungen (Profile 1.1.0 / 1.0.0)."""
    assert ad.LEGACY.fingerprint == (
        "ce48c658863ef27f8b49eb4100e494e18803fa573e27476a09385d6abb1d0017"
    )
    assert ad.LEGACY_DIFFLIB.fingerprint == (
        "5b0eb5966dcfea37fbf323662c4571d1fc737d6cf19f10e02899517d5e988836"
    )
    assert LEGACY_PIPELINE.fingerprint == (
        "aaec1633e2ec3561ed402c8eefa6c6f3a8a914d8e1c08c4e7997c718ab1d5455"
    )


def test_d1_corrected_is_the_recommended_compare_profile() -> None:
    assert ad.RECOMMENDED is ad.CORRECTED
    assert ad.CORRECTED.status == "DECIDED_RECOMMENDED"
    assert ad.CORRECTED.version == "2026.09.2"
    assert ad.CORRECTED.renumber_after_insert and not ad.LEGACY.renumber_after_insert


def _paragraphs() -> list[LawParagraph]:
    return [
        LawParagraph("§ 3", 1, "Erster Absatz."),
        LawParagraph("§ 3", 2, "Zweiter Absatz mit Frist und Frist."),
        LawParagraph("§ 3", 3, "Dritter Absatz."),
        LawParagraph("§ 4", 1, "Anderer Paragraf."),
    ]


COMMANDS = [
    "Nach § 3 Absatz 1 wird folgender Absatz 2 eingefügt:",
    "„(2) Neuer Absatz.“",
    "In § 3 Absatz 3 werden die Wörter „Frist“ durch die Wörter „Zeitraum“ ersetzt.",
]


def test_d2_insert_renumbers_following_paragraphs() -> None:
    paragraphs, open_commands, recognised = apply_commands(
        _paragraphs(), list(COMMANDS), renumber_after_insert=True
    )
    assert not open_commands and recognised == 2
    by_text = {p.text: p for p in paragraphs}
    moved = by_text["Zweiter Absatz mit Frist und Frist."]
    assert moved.paragraph == 3
    # Ersetzungen treffen alle Vorkommen im Absatz.
    assert moved.new_text == "Zweiter Absatz mit Zeitraum und Zeitraum."
    assert by_text["Dritter Absatz."].paragraph == 4
    assert by_text["Anderer Paragraf."].paragraph == 1
    assert [p.paragraph for p in paragraphs if p.section == "§ 3"] == [1, 2, 3, 4]


def test_d2_legacy_keeps_the_original_numbering() -> None:
    """DC-L01: ohne Umnummerierung trifft „Absatz 3“ den bisherigen dritten Absatz."""
    paragraphs, open_commands, recognised = apply_commands(_paragraphs(), list(COMMANDS))
    assert recognised == 1
    assert open_commands == [COMMANDS[2] + " [zu ersetzender Wortlaut nicht gefunden]"]
    assert [p.paragraph for p in paragraphs if p.section == "§ 3"] == [1, 2, 2, 3]


def test_d4_recommended_pipeline() -> None:
    assert RECOMMENDED_PIPELINE is CORRECTED_PIPELINE
    assert CORRECTED_PIPELINE.status == "DECIDED_RECOMMENDED"
    assert CORRECTED_PIPELINE.version == "2026.09.2"
    assert CORRECTED_PIPELINE.amount_mode == "locale-aware"
    assert CORRECTED_PIPELINE.retention_categories == ALL_CATEGORIES


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("18251.04", (18251.04, "ok")),
        ("1.000,00", (1000.0, "ok")),
        ("1,234.56", (1234.56, "ok")),
        ("1.234.567", (1234567.0, "ok")),
        ("1.234.567,89", (1234567.89, "ok")),
        ("3467,70", (3467.7, "ok")),
        ("42", (42.0, "ok")),
        ("1.234", (None, "ambiguous")),
        ("1,234", (None, "ambiguous")),
        ("1.2.3", (None, "invalid")),
        ("1,234,5", (None, "invalid")),
        ("", (None, "invalid")),
    ],
)
def test_d5_amounts_are_read_locale_aware(raw: str, expected: tuple[Any, str]) -> None:
    assert parse_amount(raw) == expected


def test_d5_corrected_patterns_do_not_cross_lines_or_start_inside_words() -> None:
    text = "INVOICE\nDocument: D-1\nSubtotal: 100.00\nTotal: 119.00\n"
    legacy = extract_fields(text, FIELD_PATTERNS)
    corrected = extract_fields(text, corrected_patterns(FIELD_PATTERNS))
    assert legacy.get("invoice_number") == "Document"
    assert corrected.get("invoice_number") != "Document"
    assert normalize_fields(corrected, "locale-aware")["total"] == 119.0
    assert normalize_fields(legacy)["total"] == 10000.0


def test_d5_invoice_amounts_are_kept_and_no_false_plausibility_finding(tmp_path: Path) -> None:
    legacy = asyncio.run(run(scenario("router_ok"), tmp_path / "a"))
    corrected = asyncio.run(run(scenario("router_ok"), tmp_path / "b", CORRECTED_PIPELINE))
    assert "FAIL_VAL_TOTAL_PLAUSIBILITY" in legacy["context"]["validation_flags"]
    assert corrected["context"]["validation_flags"] == []
    assert corrected["context"]["status"] == "ok"


def test_d5_ambiguous_amount_requires_review() -> None:
    context = PipelineContext(document_id="d")
    context.artifacts.extracted_fields = {"total": "1.234", "net_amount": "1.000,00"}
    result = asyncio.run(AmountFormatRule().evaluate(context))
    assert result.outcome == "REVIEW" and result.rule_id == "VAL_AMOUNT_FORMAT"
    assert result.evidence == {"total": {"raw": "1.234", "state": "ambiguous"}}
    context.artifacts.extracted_fields = {"total": "1.234,00"}
    assert asyncio.run(AmountFormatRule().evaluate(context)).outcome == "PASS"


def test_d6_gateway_outage_is_a_retryable_error(tmp_path: Path) -> None:
    legacy = asyncio.run(run(scenario("router_down"), tmp_path / "a"))
    corrected = asyncio.run(run(scenario("router_down"), tmp_path / "b", CORRECTED_PIPELINE))
    assert legacy["context"]["status"] == "rejected"
    context = corrected["context"]
    assert context["status"] == RunStatus.FAILED.value
    assert context["error_code"] == "OCR_GATEWAY_UNAVAILABLE" and context["retryable"] is True
    assert corrected["sleeps"] == [5, 10, 15]
    assert len(corrected["router_calls"]) == 4


class _Store:
    def __init__(self, items: dict[str, list[Any]], *, artifacts: bool = True) -> None:
        self.items = items
        self.deleted: list[Any] = []
        self.queries: list[tuple[str, datetime]] = []
        if artifacts:
            self.find_expired_artifacts = self._find_artifacts

    async def find_expired_runs(
        self, cutoff: datetime, statuses: tuple[str, ...], limit: int
    ) -> list[Any]:
        self.queries.append(("processing_logs", cutoff))
        return self.items.get("processing_logs", [])

    async def _find_artifacts(self, category: str, cutoff: datetime, limit: int) -> list[Any]:
        self.queries.append((category, cutoff))
        return self.items.get(category, [])

    async def delete_record(self, item: Any) -> None:
        self.deleted.append(item)

    async def commit(self) -> None:
        return None


def test_d7_all_five_retention_periods_are_enforced(tmp_path: Path) -> None:
    items = {c: [SimpleNamespace(document_id=c, id=c)] for c in ALL_CATEGORIES}
    store = _Store(items)
    audit = InMemoryAuditLog(clock=lambda: NOW)
    sweeper = build_retention_sweeper(profile=CORRECTED_PIPELINE, store=store, audit=audit)
    sweeper.clock = lambda: NOW
    policy = RetentionPolicyConfig(name="p", deletion_strategy="hard")
    outcome = asyncio.run(sweeper.process(policy))
    assert outcome.processed == 5 and outcome.deleted == 5 and not outcome.errors
    assert dict(store.queries) == {
        "original_documents": NOW - timedelta(days=2555),
        "ocr_raw_output": NOW - timedelta(days=365),
        "structured_extraction": NOW - timedelta(days=2555),
        "processing_logs": NOW - timedelta(days=90),
        "audit_events": NOW - timedelta(days=3650),
    }
    kinds = sorted(e.details_dict()["artifact_type"] for e in audit)
    assert kinds == sorted(ALL_CATEGORIES)


def test_d7_missing_store_port_is_reported_and_legacy_default_unchanged() -> None:
    store = _Store({}, artifacts=False)
    outcome = asyncio.run(
        RetentionSweeper(store, categories=ALL_CATEGORIES).process(RetentionPolicyConfig(name="p"))
    )
    assert sorted(e["artifact_type"] for e in outcome.errors) == sorted(
        c for c in ALL_CATEGORIES if c != "processing_logs"
    )
    legacy_store = _Store({})
    asyncio.run(RetentionSweeper(legacy_store).process(RetentionPolicyConfig(name="p")))
    assert [q[0] for q in legacy_store.queries] == ["processing_logs"]
    with pytest.raises(ValueError, match="Aufbewahrungskategorie"):
        RetentionSweeper(legacy_store, categories=("unbekannt",))


def test_locale_aware_amounts_report_ambiguity_instead_of_dropping_it() -> None:
    from auditcore_documents.pipeline.stages.postprocess import (
        amount_findings,
        normalize_fields_checked,
    )

    fields = {"total": "1.234", "net_amount": "12,5,0", "vat_amount": "19,00", "iban": None}
    values, findings = normalize_fields_checked(fields, "locale-aware")
    assert values["total"] is None and values["net_amount"] is None
    assert values["vat_amount"] == 19.0
    assert findings == {
        "total": {"raw": "1.234", "state": "ambiguous"},
        "net_amount": {"raw": "12,5,0", "state": "invalid"},
    }
    assert values == normalize_fields(fields, "locale-aware"), "values unchanged"
    legacy_values, legacy_findings = normalize_fields_checked(fields)
    assert legacy_findings == {} and legacy_values["total"] == 1234.0
    assert amount_findings({"total": 5}) == {}, "non-text values are not re-parsed"


def test_postprocess_stage_flags_ambiguous_amounts() -> None:
    import asyncio

    from auditcore_documents.pipeline.context import PipelineContext
    from auditcore_documents.pipeline.stages.postprocess import PostprocessStage

    stage = PostprocessStage()
    stage.amount_mode = "locale-aware"
    context = PipelineContext(document_id="d1")
    context.artifacts.ocr_text = "Gesamtbetrag: 1.234 EUR"
    asyncio.run(stage.execute(context))
    assert context.artifacts.extracted_fields is not None
    assert context.artifacts.extracted_fields.get("total") == "1.234"
    assert context.artifacts.normalized_json is not None
    assert context.artifacts.normalized_json["total"] is None
    assert "AMOUNT_AMBIGUOUS_TOTAL" in context.validation_flags
    legacy = PostprocessStage()
    legacy_context = PipelineContext(document_id="d2")
    legacy_context.artifacts.ocr_text = "Gesamtbetrag: 1.234 EUR"
    asyncio.run(legacy.execute(legacy_context))
    assert not [f for f in legacy_context.validation_flags if f.startswith("AMOUNT_")]
