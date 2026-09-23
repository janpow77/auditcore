"""Führt die flowinvoice-Dokumentpipeline tatsächlich aus und zeichnet sie auf.

Aufruf im Wegwerf-Container mit den flowinvoice-Produktionsabhängigkeiten
(``requirements-production.txt``, pydantic 2.11.9, SQLAlchemy 2.0.43,
python-magic/libmagic, pypdf 6.16.2, pypdfium2 4.30.0)::

    python tools/capture_pipeline.py --source <flowinvoice-Checkout@fb2d185>/backend \
        --output tests/fixtures/pipeline_observed.json

Die unveränderten Module ``app.pipeline.*`` laufen mit aufzeichnenden
Stellvertretern an den Anwendungsgrenzen: Gateway-OCR (``safe_call_ocr``),
Chandra, Tesseract-Parser, Audit-Dienst (statt DB), Einstellungen,
``asyncio.sleep``. Laufzeiten, Zeitstempel und Datumsanteile des
Speicherschlüssels hängen vom Lauf ab und werden maskiert; Stufen-Hashes,
Status, Flags, Artefakte und Ereignisse bleiben exakt.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import re
import sys
import tempfile
import types
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "pipeline"
REPOSITORY = "janpow77/flowinvoice"
COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
BLOBS = {
    "app/pipeline/context.py": "9d3af1d6ed8317e54f7a23285505ce56eebb3b06",
    "app/pipeline/hashing.py": "f08e18530bb64492ea5b9f3f45ec28760ecd60a9",
    "app/pipeline/audit.py": "922d061585a1f4b46a323cedcf7d3df285296211",
    "app/pipeline/retention.py": "68b7b0e0d4dc5b76432a834b5a9e718b78827ccd",
    "app/pipeline/orchestrator.py": "dad63a5e8bffc04b18693331a7446ce868841807",
    "app/pipeline/stages/base.py": "92d6c3c7280c297e7ab4bdfa0ce9bf63e58c1d35",
    "app/pipeline/stages/ingestion.py": "9327abd953df8c6ec94c75318a6c8b52751dd571",
    "app/pipeline/stages/preprocess.py": "942d411f49906f4368d14b550137cc10e08fa2d4",
    "app/pipeline/stages/ocr.py": "5fae527f85f5ac27e17b4b322c7c64fe339b6994",
    "app/pipeline/stages/postprocess.py": "d858e7055d29c1024518f07508fb6fed9823883b",
    "app/pipeline/stages/validation.py": "679954a2396984ad4ae05a4244f5e38e11dda2c6",
    "app/pipeline/stages/persist.py": "7d292b0bf5a35dd05fad83fc64f9afab3ab7779e",
    "app/pipeline/stages/export.py": "381dcf647ca44b6c6fd51320268c23faef5f671a",
    "app/models/pipeline_profile.py": "047effcc4730617028e1aacf335b6f9e4b807124",
}


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324 - Git-ID


def jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return jsonable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    return value


VOLATILE_KEYS = {
    "started_at",
    "completed_at",
    "updated_at",
    "created_at",
    "evaluated_at",
    "duration_ms",
    "total_duration_ms",
    "timestamp",
}


def mask(value: Any) -> Any:
    """Laufabhängige Zeiten maskieren (Werte, nicht Schlüssel)."""
    if isinstance(value, dict):
        return {
            k: ("<volatil>" if k in VOLATILE_KEYS and v is not None else mask(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [mask(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"^\d{4}/\d{2}/\d{2}/", "<datum>/", value)
    return value


class RecordingAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def log_event(self, **kwargs: Any) -> None:
        self.events.append(mask(jsonable(copy.deepcopy(kwargs))))


# --------------------------------------------------------------------------- Stellvertreter

OCR_DATA = json.loads((FIXTURES / "ocr_texts.json").read_text(encoding="utf-8"))


class RouterScript:
    """Gateway-Stellvertreter; Antwort je Szenario."""

    def __init__(self) -> None:
        self.mode = "ok"
        self.confidence: float | None = 0.95
        self.text_override: str | None = None
        self.calls: list[dict[str, Any]] = []
        self.current_file = ""

    async def __call__(self, data: bytes, filename: str, **kwargs: Any) -> Any:
        from app.clients.ai_router_client import OcrResult

        self.calls.append({"filename": filename, **kwargs, "png": data[:8] == b"\x89PNG\r\n\x1a\n"})
        if self.mode == "down":
            return None, "Gateway nicht erreichbar"
        if self.mode == "fail_page_2" and filename.endswith("-2.png"):
            return None, "Timeout"
        page_match = re.search(r"-(\d+)\.png$", filename)
        pages = OCR_DATA["invoice_pages"].get(self.current_file, [""])
        if self.text_override is not None:
            text = self.text_override
        elif page_match:
            text = pages[int(page_match.group(1)) - 1]
        else:
            text = "\n".join(pages)
        if self.mode == "single_pages":
            return (
                OcrResult(
                    text=text,
                    pages=[{"page": 1, "confidence": 0.9}, {"page": 2, "confidence": 0.7}, "x"],
                    spoke="vision",
                    model="m-ocr",
                    duration_ms=0,
                    confidence=None,
                    fields={"a": 1},
                ),
                None,
            )
        return (
            OcrResult(
                text=text,
                pages=[],
                spoke="",
                model="m-ocr",
                duration_ms=0,
                confidence=self.confidence,
            ),
            None,
        )


class ChandraScript:
    def __init__(self) -> None:
        self.available = False
        self.service_none = False
        self.result: dict[str, Any] = {}
        self.raise_error = False
        self.calls: list[dict[str, Any]] = []

    def get_chandra_service(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.service_none:
            return None
        script = self

        class Service:
            def process_pdf(self, path: Path) -> dict[str, Any]:
                if script.raise_error:
                    raise RuntimeError("GPU-Speicher erschöpft")
                return dict(script.result)

        return Service()


class ParserScript:
    def __init__(self) -> None:
        self.pages: list[tuple[str, float | None]] = []
        self.raise_error = False

    def get_parser(self) -> Any:
        script = self

        class Page:
            def __init__(self, text: str, confidence: float | None) -> None:
                self.text, self.confidence = text, confidence

        class Parsed:
            def __init__(self) -> None:
                self.pages = [Page(t, c) for t, c in script.pages]
                self.raw_text = "\n".join(t for t, _ in script.pages)
                self.extracted = {"quelle": "tesseract"}
                self.timings_ms = {"ocr": 1}

        class Parser:
            def parse(self, path: Path) -> Parsed:
                if script.raise_error:
                    raise OSError("tesseract fehlt")
                return Parsed()

        return Parser()


def install_stubs(
    settings: types.SimpleNamespace,
) -> tuple[RouterScript, ChandraScript, ParserScript]:
    router, chandra, parser = RouterScript(), ChandraScript(), ParserScript()
    ai_router = importlib.import_module("app.clients.ai_router_client")
    ai_router.safe_call_ocr = router  # type: ignore[attr-defined]
    chandra_module = types.ModuleType("app.services.chandra_ocr")
    chandra_module.is_chandra_available = lambda: chandra.available  # type: ignore[attr-defined]
    chandra_module._check_gpu_available = lambda: False  # type: ignore[attr-defined]
    chandra_module.get_chandra_service = chandra.get_chandra_service  # type: ignore[attr-defined]
    sys.modules["app.services.chandra_ocr"] = chandra_module
    parser_module = types.ModuleType("app.services.parser")
    parser_module.get_parser = parser.get_parser  # type: ignore[attr-defined]
    sys.modules["app.services.parser"] = parser_module
    config = importlib.import_module("app.config")
    config.get_settings = lambda: settings  # type: ignore[attr-defined]
    ocr = importlib.import_module("app.pipeline.stages.ocr")
    ocr.get_settings = lambda: settings  # type: ignore[attr-defined]
    return router, chandra, parser


# --------------------------------------------------------------------------- Szenarien

SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "router_ok",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
    },
    {
        "name": "router_review",
        "file": "invoice_2.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.7,
    },
    {
        "name": "router_reject",
        "file": "invoice_3.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.3,
    },
    {"name": "router_down", "file": "invoice_1.pdf", "ocr_backend": "router", "router": "down"},
    {
        "name": "router_page_error",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "fail_page_2",
        "confidence": 0.9,
    },
    {
        "name": "router_image_single",
        "file": "pixel.png",
        "ocr_backend": "router",
        "router": "single_pages",
        "text": "de_gueltig",
    },
    {
        "name": "de_valid",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.97,
        "text": "de_gueltig",
    },
    {
        "name": "de_iban_invalid",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.97,
        "text": "de_iban_falsch",
    },
    {
        "name": "de_sum_mismatch",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.97,
        "text": "de_summe_falsch",
    },
    {
        "name": "de_unknown_country",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.97,
        "text": "de_land_unbekannt",
    },
    {
        "name": "de_bad_values",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.97,
        "text": "de_datum_unlesbar",
    },
    {
        "name": "auto_gateway_no_chandra",
        "file": "invoice_1.pdf",
        "ocr_backend": "auto",
        "gateway": "http://gateway",
        "router": "ok",
        "confidence": 0.95,
    },
    {
        "name": "local_chandra_ok",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "chandra": {
            "available": True,
            "result": {
                "text": "Invoice: C-1\nTotal: 5.00",
                "pages": 1,
                "success": True,
                "error_count": 0,
                "token_count": 12,
            },
        },
    },
    {
        "name": "local_chandra_errors",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "chandra": {"available": True, "result": {"text": "x", "success": True, "error_count": 2}},
    },
    {
        "name": "local_chandra_service_none",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "chandra": {"available": True, "service_none": True},
        "parser": {"pages": [["Seite eins", 0.91], ["Seite zwei", 0.83]]},
    },
    {
        "name": "local_chandra_raises",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "chandra": {"available": True, "raise": True},
    },
    {
        "name": "local_tesseract_no_conf",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "chandra": {"available": False},
        "parser": {"pages": [["Invoice: T-7", None]]},
    },
    {
        "name": "local_tesseract_fails",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "chandra": {"available": False},
        "parser": {"raise": True},
    },
    {
        "name": "local_backend_none",
        "file": "invoice_1.pdf",
        "ocr_backend": "local",
        "stage_backend": "none",
    },
    {"name": "invalid_mime", "file": "notiz.txt", "ocr_backend": "router", "router": "ok"},
    {
        "name": "missing_file",
        "file": "/nicht/vorhanden.pdf",
        "ocr_backend": "router",
        "router": "ok",
    },
    {
        "name": "unsupported_uri",
        "file": "relativ/beleg.pdf",
        "ocr_backend": "router",
        "router": "ok",
    },
    {"name": "s3_uri", "file": "s3://bucket/beleg.pdf", "ocr_backend": "router", "router": "ok"},
    {
        "name": "http_uri_recovery",
        "file": "http://127.0.0.1:9/beleg.pdf",
        "ocr_backend": "router",
        "router": "ok",
    },
    {
        "name": "stop_after_ocr",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
        "stop_after": "ocr",
    },
    {
        "name": "start_from_postprocess",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
        "start_from": "postprocess",
        "stop_after": "validation",
    },
    {
        "name": "unknown_filter_names",
        "file": "invoice_2.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
        "start_from": "gibt-es-nicht",
        "stop_after": "auch-nicht",
    },
    {
        "name": "llm_unavailable_recovery",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
        "llm_stage": True,
    },
    {
        "name": "unexpected_stage_error",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
        "boom_stage": True,
    },
    {
        "name": "export_targets",
        "file": "invoice_1.pdf",
        "ocr_backend": "router",
        "router": "ok",
        "confidence": 0.95,
        "export": True,
    },
]


async def run_scenario(scenario: dict[str, Any], workdir: Path) -> dict[str, Any]:
    from app.pipeline.context import AnalysisModules, ComputeProfile, PipelineContext
    from app.pipeline.hashing import HashingService
    from app.pipeline.orchestrator import ComputeProfileEnforcer, PipelineOrchestrator
    from app.pipeline.stages import (
        ExportStage,
        IngestionStage,
        OcrStage,
        PersistStage,
        PostprocessStage,
        PreprocessStage,
        ValidationStage,
    )
    from app.pipeline.stages.base import PipelineStage, StageError
    from app.pipeline.stages.export import FileExport

    exports = workdir / "exports"
    settings = types.SimpleNamespace(
        ocr_backend=scenario["ocr_backend"],
        flow_agent_url="",
        llm_router_url=scenario.get("gateway", ""),
        parser_tesseract_languages="deu+eng",
        exports_path=exports,
    )
    router, chandra, parser = install_stubs(settings)
    router.mode = scenario.get("router", "ok")
    router.confidence = scenario.get("confidence", 0.95)
    router.text_override = OCR_DATA["german"][scenario["text"]] if "text" in scenario else None
    router.current_file = scenario["file"]
    ch = scenario.get("chandra", {})
    chandra.available = ch.get("available", False)
    chandra.service_none = ch.get("service_none", False)
    chandra.result = ch.get("result", {})
    chandra.raise_error = ch.get("raise", False)
    pa = scenario.get("parser", {})
    parser.pages = [tuple(p) for p in pa.get("pages", [])]
    parser.raise_error = pa.get("raise", False)

    sleeps: list[float] = []

    async def no_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    audit = RecordingAudit()
    hashing = HashingService()
    source = scenario["file"]
    input_uri = str(FIXTURES / source) if "/" not in source and ":" not in source else source

    class LlmStage(PipelineStage):
        name = "enrichment"
        attempts = 0

        async def execute(self, context: Any) -> Any:
            type(self).attempts += 1
            raise StageError(
                stage=self.name, error_code="LLM_UNAVAILABLE", message="LLM aus", recoverable=True
            )

    class BoomStage(PipelineStage):
        name = "boom"

        async def execute(self, context: Any) -> Any:
            raise KeyError("kaputt")

    stages: list[Any] = [
        IngestionStage(audit_service=audit, hashing_service=hashing),
        PreprocessStage(audit_service=audit, hashing_service=hashing),
        OcrStage(
            audit_service=audit,
            hashing_service=hashing,
            backend=scenario.get("stage_backend", "auto"),
        ),
        PostprocessStage(audit_service=audit, hashing_service=hashing),
    ]
    if scenario.get("llm_stage"):
        stages.append(LlmStage(audit_service=audit, hashing_service=hashing))
    if scenario.get("boom_stage"):
        stages.append(BoomStage(audit_service=audit, hashing_service=hashing))
    stages += [
        ValidationStage(audit_service=audit, hashing_service=hashing, db_session=None),
        PersistStage(audit_service=audit, hashing_service=hashing, db_session=None),
    ]
    if scenario.get("export"):
        out = workdir / "out"
        out.mkdir()

        class FailingTarget:
            name = "kaputt"
            enabled = True

            async def export(self, context: Any) -> dict[str, Any]:
                raise ValueError("Ziel nicht erreichbar")

        class DisabledTarget:
            name = "aus"
            enabled = False

        stages.append(
            ExportStage(
                audit_service=audit,
                hashing_service=hashing,
                targets=[
                    FileExport(str(out), "json"),
                    FileExport(str(out), "csv"),
                    FileExport(str(out), "xml"),
                    FailingTarget(),
                    DisabledTarget(),
                ],
            )
        )
    orchestrator = PipelineOrchestrator(
        stages=stages,
        audit_service=audit,
        hashing_service=hashing,
        compute_enforcer=ComputeProfileEnforcer(),
    )
    real_sleep = asyncio.sleep
    asyncio.sleep = no_sleep  # type: ignore[assignment]
    try:
        context = PipelineContext(
            document_id="doc-1",
            run_id="run-1",
            project_id="proj-1",
            user_id="user-1",
            input_uri=input_uri,
            compute_profile_requested=ComputeProfile.GPU_1,
            analysis_modules=AnalysisModules(),
        )
        error = None
        try:
            context = await orchestrator.run(
                context,
                start_from_stage=scenario.get("start_from"),
                stop_after_stage=scenario.get("stop_after"),
            )
        except Exception as exc:  # noqa: BLE001
            error = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        asyncio.sleep = real_sleep  # type: ignore[assignment]
    stored = {}
    base = exports / "pipeline_artifacts"
    if base.exists():
        for path in sorted(base.rglob("*")):
            if path.is_file():
                rel = mask(str(path.relative_to(base)))
                content = path.read_text(encoding="utf-8")
                stored[rel] = mask(json.loads(content)) if path.suffix == ".json" else content
    exported = {}
    if scenario.get("export"):
        for path in sorted((workdir / "out").iterdir()):
            text = path.read_text()
            exported[path.name] = mask(json.loads(text)) if path.suffix == ".json" else text
    context_dump = mask(jsonable(context.model_dump(mode="json")))
    context_dump["input_uri"] = (
        scenario["file"]
        if context_dump.get("input_uri", "").startswith(str(FIXTURES))
        else context_dump.get("input_uri")
    )
    return {
        "scenario": scenario,
        "error": error,
        "context": context_dump,
        "artifacts_json": context.artifacts.model_dump_json(),
        "audit": audit.events,
        "router_calls": router.calls,
        "chandra_calls": chandra.calls,
        "sleeps": sleeps,
        "stored_artifacts": stored,
        "exported": exported,
        "ocr_backend_after": getattr(stages[2], "backend", None),
    }


# --------------------------------------------------------------------------- Einheiten

POSTPROCESS_TEXTS = [
    "",
    "Rechnungsnummer:   RE-1\n\n\n\n\nDatum: 1.2.2026",
    "Rechnungs-Nr. AB/12-3 Rechnungsdatum 01/02/26 Bruttobetrag 1.234,56 € Netto 1.037,44 "
    "MwSt. 19,5 % 197,12",
    "Invoice Number: X9 Date: 2026-02-01 Total: 12.345 Subtotal 10.000 VAT 2.345",
    "IBAN: de89 3704 0044 0532 0130 00 USt-IdNr. de123456789",
    "Re.-Nr.: 5 Summe: 1,5 Nettosumme: 1,0 Mehrwertsteuer 0,5",
    "Total: 1.234.567,89 Net amount: abc VAT: 1.2.3",
    "Datum: 32.13.2026 Rechnungsnummer: -",
]

IBANS = [
    "DE89370400440532013000",
    "DE89370400440532013001",
    "DE8937040044053201300",
    "AT611904300234573201",
    "GB82WEST12345698765432",
    "XX12345678901234567",
    "DE89 3704 0044 0532 0130 00",
    "de89370400440532013000",
    "DE89370400440532O13000",
    "12",
]
VAT_IDS = [
    "DE123456789",
    "DE12345678",
    "ATU12345678",
    "FRAB123456789",
    "IT12345678901",
    "ESA1234567B",
    "NL123456789B01",
    "BE0123456789",
    "GB123456789",
    "GBGD001",
    "XX1",
    "de123456789",
]
AMOUNTS = [
    {"total": 119.0, "net_amount": 100.0, "vat_amount": 19.0},
    {"total": 119.01, "net_amount": 100.0, "vat_amount": 19.0},
    {"total": 119.02, "net_amount": 100.0, "vat_amount": 19.0},
    {"total": 0.0, "net_amount": 0.0, "vat_amount": 0.0},
    {"total": "abc", "net_amount": 1.0, "vat_amount": 1.0},
    {"total": 10.0, "net_amount": None, "vat_amount": 1.0},
]


async def capture_units() -> dict[str, Any]:
    from app.pipeline.context import (
        AnalysisModules,
        OcrMetrics,
        PipelineArtifacts,
        PipelineContext,
        RunStatus,
    )
    from app.pipeline.hashing import HashingService
    from app.pipeline.orchestrator import ComputeProfileEnforcer
    from app.pipeline.stages.postprocess import PostprocessStage
    from app.pipeline.stages.validation import (
        FraudDetectionRule,
        IbanChecksumRule,
        OcrConfidenceRule,
        TotalSumPlausibilityRule,
        VatIdFormatRule,
    )

    out: dict[str, Any] = {}
    stage = PostprocessStage()
    out["postprocess"] = []
    for text in POSTPROCESS_TEXTS:
        cleaned = stage._cleanup_text(text)
        extracted = stage._extract_fields(cleaned)
        out["postprocess"].append(
            {
                "text": text,
                "cleaned": cleaned,
                "extracted": extracted,
                "normalized": stage._normalize_fields(extracted),
            }
        )

    async def rule_eval(
        rule: Any, fields: dict[str, Any], ocr: float | None = None
    ) -> dict[str, Any]:
        context = PipelineContext(
            document_id="d", artifacts=PipelineArtifacts(normalized_json=fields)
        )
        if ocr is not None:
            context.ocr_metrics = OcrMetrics(
                engine="x",
                avg_confidence=ocr,
                min_confidence=min(ocr, 0.5),
                pages_processed=1,
                duration_ms=1,
            )
        try:
            result = await rule.evaluate(context)
        except Exception as exc:  # noqa: BLE001 - Fehlervertrag wird aufgezeichnet
            return {"raises": type(exc).__name__}
        data = jsonable(result.model_dump(mode="json"))
        data.pop("evaluated_at")
        return data

    out["iban"] = [{"iban": i, **(await rule_eval(IbanChecksumRule(), {"iban": i}))} for i in IBANS]
    out["vat_id"] = [
        {"vat_id": v, **(await rule_eval(VatIdFormatRule(), {"vat_id": v}))} for v in VAT_IDS
    ]
    out["amounts"] = [
        {"fields": a, **(await rule_eval(TotalSumPlausibilityRule(), a))} for a in AMOUNTS
    ]
    out["ocr_confidence"] = [
        {"avg": c, **(await rule_eval(OcrConfidenceRule(), {}, c))}
        for c in (0.99, 0.85, 0.849, 0.2)
    ]
    out["ocr_confidence_none"] = await rule_eval(OcrConfidenceRule(), {})
    out["fraud"] = []
    for fields in (
        {},
        {"invoice_number": "R1"},
        {"invoice_number": "R1", "supplier_name": "S", "total": "1.234,5", "date": "2026-02-01"},
        {"invoice_number": "R1", "vendor_name": "S", "total_amount": 5},
    ):
        out["fraud"].append(
            {"fields": fields, **(await rule_eval(FraudDetectionRule(db_session=None), fields))}
        )
    disabled = PipelineContext(
        document_id="d", analysis_modules=AnalysisModules(fraud_detection=False)
    )
    result = await FraudDetectionRule().evaluate(disabled)
    out["fraud_disabled"] = {
        k: v for k, v in jsonable(result.model_dump(mode="json")).items() if k != "evaluated_at"
    }

    out["compute"] = []
    for gpu_available, gpu_count in ((False, 0), (True, 1), (True, 2)):
        enforcer = ComputeProfileEnforcer(gpu_available=gpu_available, gpu_count=gpu_count)
        for requested in ("cpu", "auto", "gpu_1", "gpu_2"):
            from app.pipeline.context import ComputeProfile

            accepted, reason = await enforcer.enforce("u", ComputeProfile(requested))
            out["compute"].append(
                {
                    "gpu_available": gpu_available,
                    "gpu_count": gpu_count,
                    "requested": requested,
                    "accepted": accepted.value,
                    "reason": reason,
                }
            )

    class Quota:
        def __init__(self, ok: bool) -> None:
            self.ok = ok

        async def check_gpu_quota(self, user_id: str) -> bool:
            return self.ok

    for ok in (True, False):
        enforcer = ComputeProfileEnforcer(gpu_available=True, gpu_count=2, quota_service=Quota(ok))
        from app.pipeline.context import ComputeProfile

        for user in ("u", None):
            accepted, reason = await enforcer.enforce(user, ComputeProfile.GPU_2)
            out["compute"].append(
                {
                    "quota_ok": ok,
                    "user": user,
                    "requested": "gpu_2",
                    "accepted": accepted.value,
                    "reason": reason,
                }
            )

    hashing = HashingService()
    out["hashing"] = {
        "bytes": {v: hashing.hash_bytes(v.encode()) for v in ("", "abc", "Prüfung")},
        "json": [
            {"obj": o, "hash": hashing.hash_json(o)}
            for o in ({"b": 1, "a": [1, 2.5, None]}, [{"z": "ä"}], {"d": "2026-01-01", "n": 1e-7})
        ],
        "chain": {
            "empty": hashing.compute_chain_hash([]),
            "abc": hashing.compute_chain_hash(["a", "b", "c"]),
            "verify_empty": hashing.verify_chain([], hashing.compute_chain_hash([])),
            "short": [hashing.short_hash("abcdef", 8), hashing.short_hash("abcdefghij", 4)],
        },
    }
    artifacts_cases = [
        PipelineArtifacts(),
        PipelineArtifacts(
            ocr_text='Grüße\n"x"\\  ',
            ocr_raw_json={"n": 1e-7, "m": 1e20, "f": 0.1 + 0.2, "l": [1, 2.5, None, True]},
            deskew_angles=[0.0, -0.0, 1.5],
            page_count=2,
            file_size_bytes=10,
            mime_type="application/pdf",
        ),
        PipelineArtifacts(
            ocr_pages=[{"page": 1, "text": "", "confidence": None}],
            extracted_fields={"a": None},
            normalized_json={"total": 1234.56, "iban": "DE00"},
        ),
    ]
    out["artifacts_json"] = [
        {"input": jsonable(a.model_dump(mode="json")), "json": a.model_dump_json()}
        for a in artifacts_cases
    ]
    ctx = PipelineContext(
        document_id="d",
        run_id="r",
        status="running",
        compute_profile_requested="gpu_2",
        validation_flags=["A"],
    )
    out["context_defaults"] = mask(
        jsonable(PipelineContext(document_id="d", run_id="r").model_dump(mode="json"))
    )
    out["context_coerced"] = {
        "status": ctx.status.value,
        "compute": ctx.compute_profile_requested.value,
        "needs_review": ctx.needs_review(),
        "audit": ctx.to_audit_details(),
    }
    ctx.add_validation_flag("A")
    ctx.add_validation_flag("B")
    out["context_flags"] = ctx.validation_flags
    out["model_bounds"] = []
    from app.pipeline import context as cmod

    for model, fieldname, values in (
        ("OcrMetrics", "avg_confidence", [-0.1, 0.0, 1.0, 1.1]),
        ("OcrSettings", "chandra_image_size", [399, 400, 2400, 2401]),
        ("OcrSettings", "tesseract_psm", [-1, 0, 13, 14]),
        ("ParserSettings", "max_pages", [0, 1, 500, 501]),
        ("LlmSettings", "temperature", [-0.1, 0.0, 2.0, 2.1]),
        ("PostProcessingSettings", "confidence_threshold", [-0.01, 1.0, 1.01]),
        ("RagConfig", "top_k", [0, 1, 20, 21]),
    ):
        for value in values:
            kwargs = {fieldname: value}
            if model == "OcrMetrics":
                kwargs = {
                    "engine": "e",
                    "avg_confidence": 0.5,
                    "min_confidence": 0.5,
                    "pages_processed": 1,
                    "duration_ms": 1,
                    fieldname: value,
                }
            try:
                getattr(cmod, model)(**kwargs)
                ok = True
            except Exception:  # noqa: BLE001
                ok = False
            out["model_bounds"].append(
                {"model": model, "field": fieldname, "value": value, "valid": ok}
            )
    out["defaults"] = {
        name: jsonable(getattr(cmod, name)().model_dump(mode="json"))
        for name in (
            "OcrSettings",
            "ParserSettings",
            "LlmSettings",
            "PostProcessingSettings",
            "RagConfig",
            "AnalysisModules",
        )
    }
    # Kontextzustände (start/complete/fail) ohne Uhrzeiten
    state = PipelineContext(document_id="d", run_id="r")
    state.start_stage("a")
    state.complete_stage("a", success=True, stage_hash="h1")
    state.start_stage("b")
    state.complete_stage("b", success=False, error=ValueError("x"))
    state.fail(ValueError("x"), error_code="E1", retryable=True)
    out["context_state"] = mask(jsonable(state.model_dump(mode="json")))
    state2 = PipelineContext(document_id="d", run_id="r")
    state2.complete(RunStatus.REVIEW_NEEDED)
    out["context_complete_review"] = {
        "status": state2.status.value,
        "total": state2.total_duration_ms,
    }
    return out


async def capture_retention() -> dict[str, Any]:
    from app.pipeline.retention import RetentionPolicyConfig, RetentionService
    from sqlalchemy.dialects import postgresql

    class Item:
        def __init__(self, index: int, **extra: Any) -> None:
            self.run_id = f"run-{index}"
            self.document_id = f"doc-{index}"
            self.user_id = "u"
            self.error = "Fehler" if index % 2 else None
            self.ocr_metrics = {"x": 1}
            self.validation_results = [1]
            self.status = "ok"
            self.input_uri = None
            self.output_uri = None
            for k, v in extra.items():
                setattr(self, k, v)

        def snapshot(self) -> dict[str, Any]:
            return {
                k: (v if not isinstance(v, datetime) else "<datum>")
                for k, v in sorted(vars(self).items())
            }

    class Broken(Item):
        def __init__(self, index: int) -> None:
            super().__init__(index)
            self._armed = True

        def __setattr__(self, name: str, value: Any) -> None:
            if name == "user_id" and getattr(self, "_armed", False):
                raise PermissionError("gesperrt")
            super().__setattr__(name, value)

        def snapshot(self) -> dict[str, Any]:
            data = super().snapshot()
            data.pop("_armed", None)
            return data

    class Result:
        def __init__(self, items: list[Any]) -> None:
            self.items = items

        def scalars(self) -> Any:
            return self

        def all(self) -> list[Any]:
            return self.items

    class FakeDb:
        def __init__(self, items: list[Any]) -> None:
            self.items = items
            self.queries: list[str] = []
            self.deleted: list[str] = []
            self.commits = 0

        async def execute(self, query: Any) -> Result:
            compiled = query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}
            )
            self.queries.append(re.sub(r"\s+", " ", str(compiled)))
            return Result(self.items)

        async def delete(self, item: Any) -> None:
            self.deleted.append(item.run_id)

        async def commit(self) -> None:
            self.commits += 1

    audit = RecordingAudit()
    results = []
    with tempfile.TemporaryDirectory() as temporary:
        file_a = Path(temporary) / "a.pdf"
        file_a.write_bytes(b"x" * 123)
        cases = [
            ("dry_run", {}, True, lambda: [Item(1), Item(2)]),
            (
                "anonymize",
                {"anonymize_instead_of_delete": True},
                False,
                lambda: [Item(1), Item(2), Broken(3)],
            ),
            ("soft_status", {}, False, lambda: [Item(1)]),
            (
                "soft_deleted_at",
                {"soft_delete_grace_days": 5},
                False,
                lambda: [Item(1, deleted_at=None)],
            ),
            (
                "hard",
                {"deletion_strategy": "hard"},
                False,
                lambda: [Item(1, input_uri=str(file_a), output_uri="/nicht/da.json"), Item(2)],
            ),
        ]
        for name, config, dry_run, factory in cases:
            items = factory()
            db = FakeDb(items)
            audit.events.clear()
            service = RetentionService(db, audit_service=audit)
            policy = RetentionPolicyConfig(name="Test", processing_logs_days=90, **config)
            outcome = await service._process_artifacts(policy, dry_run=dry_run)
            results.append(
                {
                    "name": name,
                    "config": config,
                    "dry_run": dry_run,
                    "outcome": outcome,
                    "items": [i.snapshot() for i in items],
                    "deleted": db.deleted,
                    "commits": db.commits,
                    "queries": db.queries,
                    "audit": copy.deepcopy(audit.events),
                    "file_a_exists": file_a.exists(),
                }
            )
    defaults = RetentionPolicyConfig(name="D").model_dump()
    try:
        RetentionPolicyConfig(name="X", deletion_strategy="shred")
        strategy_error = None
    except Exception as exc:  # noqa: BLE001
        strategy_error = type(exc).__name__
    return {"cases": results, "defaults": defaults, "invalid_strategy": strategy_error}


async def capture_export_units() -> dict[str, Any]:
    from app.pipeline.context import PipelineContext
    from app.pipeline.stages.export import FileExport

    context = PipelineContext(document_id="d", run_id="r", status="ok")
    context.artifacts.extracted_fields = {"invoice_number": "R1", "total": "1,00", "leer": None}
    out = {}
    with tempfile.TemporaryDirectory() as temporary:
        for fmt in ("json", "csv", "xml"):
            result = await FileExport(temporary, fmt).export(context)
            path = Path(temporary) / f"r.{fmt}"
            out[fmt] = {
                "result": {k: (Path(v).name if k == "path" else v) for k, v in result.items()},
                "content": path.read_text() if path.exists() else None,
            }
        missing = await FileExport(str(Path(temporary) / "fehlt"), "json").export(context)
        out["missing_dir"] = {k: (Path(v).name if k == "path" else v) for k, v in missing.items()}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, required=True, help="flowinvoice backend-Verzeichnis"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "tests" / "fixtures" / "pipeline_observed.json"
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output_path = args.output.resolve()
    blobs = {}
    for relative, expected in BLOBS.items():
        actual = git_blob(source / relative)
        if actual != expected:
            raise SystemExit(f"Blob-Abweichung {relative}: {actual} != {expected}")
        blobs[relative] = actual
    sys.path.insert(0, str(source))
    os.chdir(tempfile.mkdtemp())
    scenarios = []
    for scenario in SCENARIOS:
        with tempfile.TemporaryDirectory() as temporary:
            scenarios.append(asyncio.run(run_scenario(scenario, Path(temporary))))
    output = {
        "schema_version": 1,
        "source": {"repository": REPOSITORY, "commit": COMMIT, "blobs": blobs},
        "environment": {
            "python": platform.python_version(),
            "packages": {
                n: importlib.metadata.version(n)
                for n in ("pydantic", "SQLAlchemy", "python-magic", "pypdf", "pypdfium2", "pillow")
            },
        },
        "fixtures": json.loads((FIXTURES / "ocr_texts.json").read_text())["sha256"],
        "scenarios": scenarios,
        "units": asyncio.run(capture_units()),
        "retention": asyncio.run(capture_retention()),
        "export_units": asyncio.run(capture_export_units()),
    }
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"scenarios": len(scenarios), "written": str(output_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
