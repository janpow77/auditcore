"""Vertragstests der Pipeline: Profile, Korrekturen PL-C01 bis PL-C07, Ports."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from test_pipeline_replay import DATA, run

from auditcore_documents.pipeline import (
    CORRECTED_PIPELINE,
    LEGACY_PIPELINE,
    PIPELINE_PROFILES,
    FileArtifactStore,
    HashingService,
    IngestionStage,
    InMemoryAuditLog,
    OcrStage,
    PersistStage,
    PipelineContext,
    RunStatus,
    StageError,
    WebhookExport,
    sniff_mime,
)
from auditcore_documents.pipeline.jsonfmt import dumps_compact
from auditcore_documents.pipeline.stages.export import WebhookError
from auditcore_documents.pipeline.stages.ocr import OcrRouting, pdfium_rasterizer

FIXTURES = Path(__file__).parent / "fixtures" / "pipeline"


def scenario(name: str) -> dict[str, Any]:
    return next(e["scenario"] for e in DATA["scenarios"] if e["scenario"]["name"] == name)


def test_profiles_are_versioned_and_fingerprinted() -> None:
    assert set(PIPELINE_PROFILES) == {"flowinvoice.pipeline", "auditcore.pipeline"}
    assert LEGACY_PIPELINE.fingerprint != CORRECTED_PIPELINE.fingerprint
    assert "fb2d18568d2eaf64574d131ceae51a936b9aac02" in LEGACY_PIPELINE.source
    assert LEGACY_PIPELINE.preserve_review is False and CORRECTED_PIPELINE.preserve_review is True
    assert CORRECTED_PIPELINE.identity()["id"] == "auditcore.pipeline"


def test_pl_c01_review_status_is_lost_in_legacy_and_kept_when_corrected(tmp_path: Path) -> None:
    """Original: OCR-Konfidenz 0,7 und Regelbefund enden trotzdem mit ``ok``."""
    legacy = asyncio.run(run(scenario("router_review"), tmp_path / "a"))
    assert legacy["context"]["status"] == "ok"
    assert "LOW_OCR_CONFIDENCE" in legacy["context"]["validation_flags"]
    corrected = asyncio.run(run(scenario("router_review"), tmp_path / "b", CORRECTED_PIPELINE))
    assert corrected["context"]["status"] == "review_needed"
    assert corrected["audit"][-1]["details"]["status"] == "review_needed"


def test_pl_c03_ingestion_checks_size_before_reading(tmp_path: Path) -> None:
    big = tmp_path / "gross.pdf"
    big.write_bytes(b"%PDF-" + b"0" * 64)
    stage = IngestionStage(hashing_service=HashingService())
    stage.MAX_FILE_SIZE = 10
    context = PipelineContext(document_id="d", input_uri=str(big))
    with pytest.raises(StageError) as caught:
        asyncio.run(stage.execute(context))
    assert caught.value.error_code == "FILE_TOO_LARGE" and not caught.value.recoverable


def test_pl_c04_mime_sniffing() -> None:
    assert sniff_mime(b"%PDF-1.7") == "application/pdf"
    assert sniff_mime((FIXTURES / "pixel.png").read_bytes()) == "image/png"
    assert sniff_mime(b"\xff\xd8\xff\xe0") == "image/jpeg"
    assert sniff_mime(b"II*\x00") == "image/tiff"
    assert sniff_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert sniff_mime(b"Kein Beleg") == "application/octet-stream"


def test_http_requires_a_fetch_port() -> None:
    stage = IngestionStage()
    context = PipelineContext(document_id="d", input_uri="https://example.invalid/a.pdf")
    with pytest.raises(StageError) as caught:
        asyncio.run(stage.execute(context))
    assert caught.value.error_code == "HTTP_NOT_CONFIGURED"


def test_pl_c06_artifact_store_rejects_escapes(tmp_path: Path) -> None:
    store = FileArtifactStore(tmp_path)
    asyncio.run(store.store("2026/09/23/doc/run/ocr_text.txt", b"x"))
    assert (tmp_path / "pipeline_artifacts/2026/09/23/doc/run/ocr_text.txt").read_bytes() == b"x"
    with pytest.raises(ValueError, match="verlässt"):
        asyncio.run(store.store("../../boese.txt", b"x"))


def test_persist_reports_port_errors_without_failing(tmp_path: Path) -> None:
    errors: list[str] = []

    class BrokenRepository:
        async def upsert(self, run_id: str, create: dict[str, Any], update: dict[str, Any]) -> None:
            raise RuntimeError("DB weg")

    stage = PersistStage(
        repository=BrokenRepository(),
        store=FileArtifactStore(tmp_path),
        on_error=lambda where, exc: errors.append(f"{where}:{exc}"),
    )
    context = PipelineContext(document_id="d", storage_key="../ausbruch")
    context.artifacts.ocr_text = "Text"
    asyncio.run(stage.execute(context))
    assert errors[0] == "run:DB weg" and errors[1].startswith("ocr_text.txt:")


def test_ocr_without_router_port_fails_clearly(tmp_path: Path) -> None:
    stage = OcrStage(routing=OcrRouting(mode="router"))
    context = PipelineContext(document_id="d", input_uri=str(FIXTURES / "invoice_1.pdf"))
    with pytest.raises(StageError) as caught:
        asyncio.run(stage.execute(context))
    assert caught.value.error_code == "ROUTER_NOT_CONFIGURED"


def test_pdfium_rasterizer_renders_pages() -> None:
    pytest.importorskip("pypdfium2")
    pytest.importorskip("PIL")
    pages = pdfium_rasterizer((FIXTURES / "invoice_1.pdf").read_bytes())
    assert pages is not None and pages[0][0] == 1 and pages[0][1][:8] == b"\x89PNG\r\n\x1a\n"
    assert pdfium_rasterizer(b"kein pdf") is None


def test_in_memory_audit_log_is_append_only() -> None:
    log = InMemoryAuditLog(clock=lambda: datetime(2026, 9, 23, tzinfo=UTC), id_factory=lambda: "e1")
    details = {"a": [1, {"b": 2}]}
    event = asyncio.run(log.log_event(event_type="X", document_id="d", details=details))
    details["a"].append(3)
    assert event.details_dict() == {"a": [1, {"b": 2}]}
    with pytest.raises(TypeError):
        event.details["a"] = 1  # type: ignore[index]
    with pytest.raises(AttributeError):
        event.event_type = "Y"  # type: ignore[misc]
    assert [e.id for e in log] == ["e1"] and len(log.events(document_id="d")) == 1


def test_pl_c05_linked_chain_detects_reordering() -> None:
    hashing = HashingService()
    chain = hashing.linked_chain(["a", "b"])
    assert chain != hashing.linked_chain(["b", "a"])
    # Original: die Einzelhashes hängen nicht voneinander ab.
    assert hashing.compute_chain_hash(["a", "b"]) != hashing.compute_chain_hash(["b", "a"])


def test_webhook_export_uses_the_port() -> None:
    calls: list[Any] = []

    async def post(
        url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float
    ) -> tuple[int, str]:
        calls.append((url, payload["event"], headers["Content-Type"], timeout))
        return 202, "x" * 600

    context = PipelineContext(document_id="d", run_id="r", status=RunStatus.OK)
    result = asyncio.run(WebhookExport("https://ziel.invalid/hook", post).export(context))
    assert result == {"success": True, "status_code": 202, "response": "x" * 500}
    assert calls == [("https://ziel.invalid/hook", "pipeline_completed", "application/json", 30.0)]

    async def failing(*_: Any) -> tuple[int, str]:
        raise WebhookError("503")

    failed = asyncio.run(WebhookExport("https://ziel.invalid/hook", failing).export(context))
    assert failed == {"success": False, "error": "503", "url": "https://ziel.invalid/hook"}


def test_compact_json_float_formatting() -> None:
    assert dumps_compact({"a": 1e-7, "b": 1e20, "c": float("nan"), "d": [True, None, "ä"]}) == (
        '{"a":1e-7,"b":1e20,"c":null,"d":[true,null,"ä"]}'
    )
    with pytest.raises(TypeError):
        dumps_compact({"x": object()})


def test_corrected_profile_keeps_valid_iban_on_real_text(tmp_path: Path) -> None:
    """PL-C02 im Ablauf: ``de_valid`` wird im Original wegen der IBAN abgelehnt."""
    legacy = next(e for e in DATA["scenarios"] if e["scenario"]["name"] == "de_valid")
    assert legacy["context"]["status"] == "rejected"
    corrected = asyncio.run(run(scenario("de_valid"), tmp_path, CORRECTED_PIPELINE))
    assert corrected["context"]["artifacts"]["normalized_json"]["iban"] == "DE89370400440532013000"
    assert corrected["context"]["status"] == "ok"
    assert json.loads(corrected["artifacts_json"])["normalized_json"]["total"] == 1190.0


def test_empty_in_memory_audit_log_is_used_as_sink() -> None:
    """Regression: ein leeres Protokoll ist „falsy“ (``__len__``), zählt aber als Senke."""
    from auditcore_documents.pipeline import PipelineOrchestrator, PostprocessStage

    audit = InMemoryAuditLog()
    context = PipelineContext(document_id="d", run_id="r")
    context.artifacts.ocr_text = "Rechnungsnummer: RE-1\nGesamtbetrag: 1,00\n"
    asyncio.run(PipelineOrchestrator([PostprocessStage()], audit_service=audit).run(context))
    assert [e.event_type for e in audit] == [
        "PIPELINE_STARTED",
        "POSTPROCESS_STARTED",
        "POSTPROCESS_DONE",
        "PIPELINE_COMPLETED",
    ]
