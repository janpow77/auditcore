"""Wiederholung der aufgezeichneten flowinvoice-Pipeline gegen die Bibliothek.

Grundlage: ``tests/fixtures/pipeline_observed.json`` aus
``tools/capture_pipeline.py`` (flowinvoice@fb2d185). Die Ports der Bibliothek
erhalten dieselben Antworten wie die Stellvertreter der Aufzeichnung.
Verglichen werden Kontext (inklusive Stufen-Hashes), Audit-Ereignisse,
Gateway-Aufrufe, Wartezeiten, abgelegte Artefakte und Exporte; Zeiten sind
wie in der Aufzeichnung maskiert.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import fields as dc_fields
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from auditcore_documents.pipeline import (
    LEGACY_PIPELINE,
    AnalysisModules,
    ComputeProfile,
    ComputeProfileEnforcer,
    ExportStage,
    FileArtifactStore,
    FileExport,
    HashingService,
    IngestionStage,
    OcrRouting,
    OcrStage,
    ParsedDocument,
    ParsedPage,
    PersistStage,
    PipelineContext,
    PipelineProfile,
    PipelineStage,
    RouterResult,
    StageError,
    ValidationStage,
    build_pipeline,
    sniff_mime,
)

FIXTURES = Path(__file__).parent / "fixtures"
PIPELINE_FIXTURES = FIXTURES / "pipeline"
DATA = json.loads((FIXTURES / "pipeline_observed.json").read_text(encoding="utf-8"))
OCR = json.loads((PIPELINE_FIXTURES / "ocr_texts.json").read_text(encoding="utf-8"))
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


def jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return jsonable(value.to_dict())
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def mask(value: Any) -> Any:
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
        self.events.append(mask(jsonable(kwargs)))


class Router:
    def __init__(self, scenario: dict[str, Any]) -> None:
        self.mode = scenario.get("router", "ok")
        self.confidence = scenario.get("confidence", 0.95)
        self.text = OCR["german"][scenario["text"]] if "text" in scenario else None
        self.file = scenario["file"]
        self.calls: list[dict[str, Any]] = []

    async def __call__(
        self, data: bytes, *, filename: str, model: str, language: str
    ) -> tuple[RouterResult | None, str | None]:
        self.calls.append(
            {
                "filename": filename,
                "language": language,
                "model": model,
                "png": data[:8] == b"\x89PNG\r\n\x1a\n",
            }
        )
        if self.mode == "down":
            return None, "Gateway nicht erreichbar"
        if self.mode == "fail_page_2" and filename.endswith("-2.png"):
            return None, "Timeout"
        match = re.search(r"-(\d+)\.png$", filename)
        pages = OCR["invoice_pages"].get(self.file, [""])
        if self.text is not None:
            text = self.text
        elif match:
            text = pages[int(match.group(1)) - 1]
        else:
            text = "\n".join(pages)
        if self.mode == "single_pages":
            return (
                RouterResult(
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
            RouterResult(
                text=text,
                pages=[],
                spoke="",
                model="m-ocr",
                duration_ms=0,
                confidence=self.confidence,
            ),
            None,
        )


class Chandra:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.calls: list[dict[str, Any]] = []

    def available(self) -> bool:
        return bool(self.spec.get("available"))

    def service(self, *, max_output_tokens: int, max_image_size: int) -> Any:
        self.calls.append(
            {"max_output_tokens": max_output_tokens, "max_image_size": max_image_size}
        )
        if self.spec.get("service_none"):
            return None
        spec = self.spec

        class Service:
            def process_pdf(self, path: Path) -> dict[str, Any]:
                if spec.get("raise"):
                    raise RuntimeError("GPU-Speicher erschöpft")
                return dict(spec.get("result", {}))

        return Service()


class Tesseract:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec

    def parse(self, path: Path) -> ParsedDocument:
        if self.spec.get("raise"):
            raise OSError("tesseract fehlt")
        pages = [ParsedPage(text, conf) for text, conf in self.spec.get("pages", [])]
        return ParsedDocument(
            raw_text="\n".join(p.text for p in pages),
            pages=pages,
            extracted={"quelle": "tesseract"},
            timings_ms={"ocr": 1},
        )


def legacy_mime(data: bytes) -> str:
    """sniff_mime, für die unzulässige Textdatei das libmagic-Ergebnis des Originals."""
    return "text/plain" if data.startswith(b"Kein Beleg") else sniff_mime(data)


class LlmStage(PipelineStage):
    name = "enrichment"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise StageError(
            stage=self.name, error_code="LLM_UNAVAILABLE", message="LLM aus", recoverable=True
        )


class BoomStage(PipelineStage):
    name = "boom"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise KeyError("kaputt")


class FailingTarget:
    name = "kaputt"
    enabled = True

    async def export(self, context: PipelineContext) -> dict[str, Any]:
        raise ValueError("Ziel nicht erreichbar")


class DisabledTarget:
    name = "aus"
    enabled = False

    async def export(self, context: PipelineContext) -> dict[str, Any]:  # pragma: no cover
        raise AssertionError("deaktiviert")


async def fetch_refused(url: str) -> bytes:
    raise ConnectionRefusedError("All connection attempts failed")


async def run(
    scenario: dict[str, Any], workdir: Path, profile: PipelineProfile = LEGACY_PIPELINE
) -> dict[str, Any]:
    audit = RecordingAudit()
    hashing = HashingService()
    router = Router(scenario)
    chandra = Chandra(scenario.get("chandra", {}))
    routing = OcrRouting(mode=scenario["ocr_backend"], gateway_url=scenario.get("gateway", ""))
    sleeps: list[float] = []

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    ocr = OcrStage(
        audit_service=audit,
        hashing_service=hashing,
        backend=scenario.get("stage_backend", "auto"),
        routing=routing,
        router=router,
        chandra=chandra,
        tesseract=Tesseract(scenario.get("parser", {})),
    )
    extra: list[PipelineStage] = []
    if scenario.get("llm_stage"):
        extra.append(LlmStage(audit_service=audit, hashing_service=hashing))
    if scenario.get("boom_stage"):
        extra.append(BoomStage(audit_service=audit, hashing_service=hashing))
    exports = workdir / "exports"
    orchestrator = build_pipeline(
        profile=profile,
        audit=audit,
        hashing=hashing,
        ocr=ocr,
        ingestion=IngestionStage(
            audit_service=audit,
            hashing_service=hashing,
            mime_detector=legacy_mime,
            fetch_url=fetch_refused,
        ),
        validation=ValidationStage(audit_service=audit, hashing_service=hashing),
        persist=PersistStage(
            audit_service=audit, hashing_service=hashing, store=FileArtifactStore(exports)
        ),
        compute_enforcer=ComputeProfileEnforcer(),
        sleep=sleep,
    )
    # Zusatzstufen stehen im Original vor Validierung und Persistenz.
    if extra:
        stages = orchestrator.stages
        orchestrator.stages = [*stages[:4], *extra, *stages[4:]]
        for stage in extra:
            stage.audit, stage.hashing = audit, hashing
    if scenario.get("export"):
        out = workdir / "out"
        out.mkdir()
        orchestrator.stages.append(
            ExportStage(
                audit_service=audit,
                hashing_service=hashing,
                targets=[
                    FileExport(out, "json"),
                    FileExport(out, "csv"),
                    FileExport(out, "xml"),
                    FailingTarget(),
                    DisabledTarget(),
                ],
            )
        )
    source = scenario["file"]
    input_uri = (
        str(PIPELINE_FIXTURES / source) if "/" not in source and ":" not in source else source
    )
    context = PipelineContext(
        document_id="doc-1",
        run_id="run-1",
        project_id="proj-1",
        user_id="user-1",
        input_uri=input_uri,
        compute_profile_requested=ComputeProfile.GPU_1,
        analysis_modules=AnalysisModules(),
    )
    context = await orchestrator.run(
        context,
        start_from_stage=scenario.get("start_from"),
        stop_after_stage=scenario.get("stop_after"),
    )
    stored = {}
    base = exports / "pipeline_artifacts"
    if base.exists():
        for path in sorted(base.rglob("*")):
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                stored[mask(str(path.relative_to(base)))] = (
                    mask(json.loads(content)) if path.suffix == ".json" else content
                )
    exported = {}
    if scenario.get("export"):
        for path in sorted((workdir / "out").iterdir()):
            text = path.read_text(encoding="utf-8")
            exported[path.name] = mask(json.loads(text)) if path.suffix == ".json" else text
    dump = mask(jsonable(context.to_dict()))
    if dump.get("input_uri", "").startswith(str(PIPELINE_FIXTURES)):
        dump["input_uri"] = scenario["file"]
    return {
        "context": dump,
        "artifacts_json": context.artifacts_json(),
        "audit": audit.events,
        "router_calls": router.calls,
        "chandra_calls": chandra.calls,
        "sleeps": sleeps,
        "stored_artifacts": stored,
        "exported": exported,
        "ocr_backend_after": ocr.backend,
    }


def paths_as_names(value: Any) -> Any:
    """Exportpfade hängen vom temporären Verzeichnis ab; verglichen wird der Dateiname."""
    if isinstance(value, dict):
        return {
            k: (Path(v).name if k == "path" and isinstance(v, str) else paths_as_names(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [paths_as_names(v) for v in value]
    return value


def test_source_is_bound() -> None:
    assert DATA["source"]["repository"] == "janpow77/flowinvoice"
    assert DATA["source"]["commit"] == "fb2d18568d2eaf64574d131ceae51a936b9aac02"
    import hashlib

    for name, digest in DATA["fixtures"].items():
        assert hashlib.sha256((PIPELINE_FIXTURES / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("entry", DATA["scenarios"], ids=lambda e: e["scenario"]["name"])
def test_pipeline_scenario(entry: dict[str, Any], tmp_path: Path) -> None:
    observed = asyncio.run(run(entry["scenario"], tmp_path))
    assert entry["error"] is None
    # Maskierte Kontexte vergleichen; Zeitfelder sind in beiden Fällen maskiert.
    assert observed["context"] == entry["context"]
    assert observed["artifacts_json"] == entry["artifacts_json"]
    assert paths_as_names(observed["audit"]) == paths_as_names(entry["audit"])
    assert observed["router_calls"] == entry["router_calls"]
    assert observed["chandra_calls"] == entry["chandra_calls"]
    # Das Original schläft zusätzlich 0 s in httpx; fachlich zählen die Wartezeiten.
    assert observed["sleeps"] == [s for s in entry["sleeps"] if s]
    assert observed["stored_artifacts"] == entry["stored_artifacts"]
    assert observed["exported"] == entry["exported"]
    assert observed["ocr_backend_after"] == entry["ocr_backend_after"]


def test_mime_sniffing_matches_libmagic_for_allowed_fixtures() -> None:
    by_name = {e["scenario"]["file"]: e for e in DATA["scenarios"]}
    for name in ("invoice_1.pdf", "pixel.png"):
        recorded = by_name[name]["context"]["artifacts"]["mime_type"]
        assert sniff_mime((PIPELINE_FIXTURES / name).read_bytes()) == recorded


def test_context_fields_match_the_original_model() -> None:
    recorded = DATA["units"]["context_defaults"]
    ours = mask(jsonable(PipelineContext(document_id="d", run_id="r").to_dict()))
    assert set(ours) == set(recorded)
    assert ours == recorded
    assert [f.name for f in dc_fields(PipelineContext) if f.name != "clock"] == list(
        PipelineContext(document_id="x").to_dict()
    )
