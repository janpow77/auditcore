"""Einzelfälle der Pipeline gegen die Aufzeichnung (Regeln, Hashing, Modelle, Aufbewahrung)."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from test_pipeline_replay import jsonable, mask

from auditcore_documents.pipeline import (
    AnalysisModules,
    ComputeProfile,
    ComputeProfileEnforcer,
    HashingService,
    OcrMetrics,
    PipelineArtifacts,
    PipelineContext,
    PipelineValueError,
    RetentionPolicyConfig,
    RetentionSweeper,
    RunStatus,
)
from auditcore_documents.pipeline import context as cmod
from auditcore_documents.pipeline.retention import FINISHED_STATUSES, SWEEP_LIMIT, is_expired_run
from auditcore_documents.pipeline.stages.export import FileExport
from auditcore_documents.pipeline.stages.postprocess import (
    cleanup_text,
    extract_fields,
    normalize_fields,
)
from auditcore_documents.pipeline.stages.validation import (
    FraudDetectionRule,
    IbanChecksumRule,
    OcrConfidenceRule,
    TotalSumPlausibilityRule,
    VatIdFormatRule,
)

DATA = json.loads(
    (Path(__file__).parent / "fixtures" / "pipeline_observed.json").read_text(encoding="utf-8")
)
UNITS = DATA["units"]


@pytest.mark.parametrize("entry", UNITS["postprocess"], ids=lambda e: repr(e["text"])[:25])
def test_postprocess(entry: dict[str, Any]) -> None:
    cleaned = cleanup_text(entry["text"])
    assert cleaned == entry["cleaned"]
    extracted = extract_fields(cleaned)
    assert extracted == entry["extracted"]
    assert normalize_fields(extracted) == entry["normalized"]


async def evaluate(rule: Any, fields: dict[str, Any], ocr: float | None = None) -> dict[str, Any]:
    context = PipelineContext(document_id="d", artifacts=PipelineArtifacts(normalized_json=fields))
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
    except Exception as exc:  # noqa: BLE001
        return {"raises": type(exc).__name__}
    data = jsonable(result.to_dict())
    data.pop("evaluated_at")
    return data


def strip(entry: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {k: v for k, v in entry.items() if k not in keys}


@pytest.mark.parametrize("entry", UNITS["iban"], ids=lambda e: e["iban"])
def test_iban_rule(entry: dict[str, Any]) -> None:
    assert asyncio.run(evaluate(IbanChecksumRule(), {"iban": entry["iban"]})) == strip(
        entry, "iban"
    )


@pytest.mark.parametrize("entry", UNITS["vat_id"], ids=lambda e: e["vat_id"])
def test_vat_id_rule(entry: dict[str, Any]) -> None:
    result = asyncio.run(evaluate(VatIdFormatRule(), {"vat_id": entry["vat_id"]}))
    assert result == strip(entry, "vat_id")


@pytest.mark.parametrize("entry", UNITS["amounts"], ids=lambda e: repr(e["fields"])[:30])
def test_total_plausibility_rule(entry: dict[str, Any]) -> None:
    result = asyncio.run(evaluate(TotalSumPlausibilityRule(), entry["fields"]))
    assert result == strip(entry, "fields")


@pytest.mark.parametrize("entry", UNITS["ocr_confidence"], ids=lambda e: str(e["avg"]))
def test_ocr_confidence_rule(entry: dict[str, Any]) -> None:
    assert asyncio.run(evaluate(OcrConfidenceRule(), {}, entry["avg"])) == strip(entry, "avg")
    assert asyncio.run(evaluate(OcrConfidenceRule(), {})) == UNITS["ocr_confidence_none"]


@pytest.mark.parametrize("index", range(len(UNITS["fraud"])))
def test_fraud_rule_without_checker(index: int) -> None:
    entry = UNITS["fraud"][index]
    result = asyncio.run(evaluate(FraudDetectionRule(), entry["fields"]))
    expected = strip(entry, "fields")
    if expected.get("message") == "Fraud detection service not available":
        # Original: ImportError des FraudDetectionManagers in der Aufzeichnungsumgebung;
        # ohne Port meldet die Bibliothek wie das Original ohne DB-Sitzung (PL-L10).
        expected["message"] = "No database session for fraud detection"
    assert result == expected


def test_fraud_rule_disabled() -> None:
    context = PipelineContext(
        document_id="d", analysis_modules=AnalysisModules(fraud_detection=False)
    )
    data = jsonable(asyncio.run(FraudDetectionRule().evaluate(context)).to_dict())
    data.pop("evaluated_at")
    assert data == UNITS["fraud_disabled"]


def test_compute_enforcer_matrix() -> None:
    class Quota:
        def __init__(self, ok: bool) -> None:
            self.ok = ok

        async def check_gpu_quota(self, user_id: str) -> bool:
            return self.ok

    for entry in UNITS["compute"]:
        if "quota_ok" in entry:
            enforcer = ComputeProfileEnforcer(True, 2, Quota(entry["quota_ok"]))
            user = entry["user"]
        else:
            enforcer = ComputeProfileEnforcer(entry["gpu_available"], entry["gpu_count"])
            user = "u"
        accepted, reason = asyncio.run(enforcer.enforce(user, ComputeProfile(entry["requested"])))
        assert (accepted.value, reason) == (entry["accepted"], entry["reason"]), entry


def test_hashing() -> None:
    hashing = HashingService()
    recorded = UNITS["hashing"]
    for text, digest in recorded["bytes"].items():
        assert hashing.hash_bytes(text.encode()) == digest
    for case in recorded["json"]:
        assert hashing.hash_json(case["obj"]) == case["hash"]
    chain = recorded["chain"]
    assert hashing.compute_chain_hash([]) == chain["empty"]
    assert hashing.compute_chain_hash(["a", "b", "c"]) == chain["abc"]
    assert hashing.verify_chain([], chain["empty"]) is chain["verify_empty"]
    assert [hashing.short_hash("abcdef", 8), hashing.short_hash("abcdefghij", 4)] == chain["short"]


@pytest.mark.parametrize("index", range(len(UNITS["artifacts_json"])))
def test_artifacts_json_equals_pydantic(index: int) -> None:
    entry = UNITS["artifacts_json"][index]
    artifacts = PipelineArtifacts(**entry["input"])
    if index == 1:
        # JSON-Eingaben verlieren Float-Details (1e-7/1e20); Originalobjekt nachbauen.
        artifacts.ocr_raw_json = {"n": 1e-7, "m": 1e20, "f": 0.1 + 0.2, "l": [1, 2.5, None, True]}
        artifacts.ocr_text = 'Grüße\n"x"\\  '
        artifacts.deskew_angles = [0.0, -0.0, 1.5]
    if index == 2:
        # Aufgezeichnete Eingaben haben sortierte Schlüssel; Reihenfolge wie im Original.
        artifacts.ocr_pages = [{"page": 1, "text": "", "confidence": None}]
        artifacts.normalized_json = {"total": 1234.56, "iban": "DE00"}
    assert artifacts.to_json() == entry["json"]


def test_context_defaults_coercion_and_flags() -> None:
    ctx = PipelineContext(
        document_id="d",
        run_id="r",
        status="running",
        compute_profile_requested="gpu_2",  # type: ignore[arg-type]
        validation_flags=["A"],
    )
    recorded = UNITS["context_coerced"]
    assert ctx.status.value == recorded["status"]
    assert ctx.compute_profile_requested.value == recorded["compute"]
    assert ctx.needs_review() is recorded["needs_review"]
    details = ctx.to_audit_details()
    ctx.add_validation_flag("A")
    ctx.add_validation_flag("B")
    # Wie im Original verweisen die Details auf die Listen des Kontexts (PL-L11).
    assert details == recorded["audit"]
    assert ctx.validation_flags == UNITS["context_flags"]


def test_context_state_transitions() -> None:
    state = PipelineContext(document_id="d", run_id="r")
    state.start_stage("a")
    state.complete_stage("a", success=True, stage_hash="h1")
    state.start_stage("b")
    state.complete_stage("b", success=False, error=ValueError("x"))
    state.fail(ValueError("x"), error_code="E1", retryable=True)
    assert mask(jsonable(state.to_dict())) == UNITS["context_state"]
    review = PipelineContext(document_id="d", run_id="r")
    review.complete(RunStatus.REVIEW_NEEDED)
    assert {"status": review.status.value, "total": review.total_duration_ms} == UNITS[
        "context_complete_review"
    ]


def test_model_defaults() -> None:
    for name, expected in UNITS["defaults"].items():
        assert jsonable(getattr(cmod, name)().to_dict()) == expected, name


@pytest.mark.parametrize(
    "entry", UNITS["model_bounds"], ids=lambda e: f"{e['model']}.{e['field']}={e['value']}"
)
def test_model_bounds(entry: dict[str, Any]) -> None:
    kwargs: dict[str, Any] = {entry["field"]: entry["value"]}
    if entry["model"] == "OcrMetrics":
        kwargs = {
            "engine": "e",
            "avg_confidence": 0.5,
            "min_confidence": 0.5,
            "pages_processed": 1,
            "duration_ms": 1,
            **kwargs,
        }
    try:
        getattr(cmod, entry["model"])(**kwargs)
        valid = True
    except PipelineValueError:
        valid = False
    assert valid is entry["valid"]


# --------------------------------------------------------------------------- Aufbewahrung

RETENTION = DATA["retention"]


class Item:
    def __init__(self, index: int, **extra: Any) -> None:
        self.run_id = f"run-{index}"
        self.document_id = f"doc-{index}"
        self.user_id = "u"
        self.error = "Fehler" if index % 2 else None
        self.ocr_metrics: Any = {"x": 1}
        self.validation_results: Any = [1]
        self.status = "ok"
        self.input_uri: str | None = None
        self.output_uri: str | None = None
        for key, value in extra.items():
            setattr(self, key, value)

    def snapshot(self) -> dict[str, Any]:
        return {
            k: (v if not isinstance(v, datetime) else "<datum>")
            for k, v in sorted(vars(self).items())
            if not k.startswith("_")
        }


class Broken(Item):
    def __init__(self, index: int) -> None:
        super().__init__(index)
        self._armed = True

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "user_id" and getattr(self, "_armed", False):
            raise PermissionError("gesperrt")
        super().__setattr__(name, value)


class Store:
    def __init__(self, items: list[Any]) -> None:
        self.items = items
        self.deleted: list[str] = []
        self.commits = 0
        self.queries: list[tuple[datetime, tuple[str, ...], int]] = []

    async def find_expired_runs(
        self, cutoff: datetime, statuses: tuple[str, ...], limit: int
    ) -> list[Any]:
        self.queries.append((cutoff, statuses, limit))
        return self.items

    async def delete_record(self, item: Any) -> None:
        self.deleted.append(item.run_id)

    async def commit(self) -> None:
        self.commits += 1


class Audit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def log_event(self, **kwargs: Any) -> None:
        self.events.append(kwargs)


@pytest.mark.parametrize("entry", RETENTION["cases"], ids=lambda e: e["name"])
def test_retention_cases(entry: dict[str, Any], tmp_path: Path) -> None:
    file_a = tmp_path / "a.pdf"
    file_a.write_bytes(b"x" * 123)
    factories = {
        "dry_run": lambda: [Item(1), Item(2)],
        "anonymize": lambda: [Item(1), Item(2), Broken(3)],
        "soft_status": lambda: [Item(1)],
        "soft_deleted_at": lambda: [Item(1, deleted_at=None)],
        "hard": lambda: [Item(1, input_uri=str(file_a), output_uri="/nicht/da.json"), Item(2)],
    }
    items = factories[entry["name"]]()
    store, audit = Store(items), Audit()
    now = datetime(2026, 9, 23, 12, tzinfo=UTC)
    sweeper = RetentionSweeper(store, audit, clock=lambda: now)
    policy = RetentionPolicyConfig(name="Test", processing_logs_days=90, **entry["config"])
    outcome = asyncio.run(sweeper.process(policy, dry_run=entry["dry_run"]))
    assert vars(outcome) == entry["outcome"]
    snapshots = [i.snapshot() for i in items]
    for snapshot, expected in zip(snapshots, entry["items"], strict=True):
        if (expected.get("input_uri") or "").endswith("/a.pdf"):
            expected = {**expected, "input_uri": str(file_a)}
        assert snapshot == expected
    assert store.deleted == entry["deleted"]
    assert store.commits == entry["commits"]
    assert [
        {
            k: v
            for k, v in e.items()
            if k in {"event_type", "document_id", "actor_type", "actor_id", "details"}
        }
        for e in audit.events
    ] == [
        {
            k: v
            for k, v in e.items()
            if k in {"event_type", "document_id", "actor_type", "actor_id", "details"}
        }
        for e in entry["audit"]
    ]
    assert file_a.exists() is entry["file_a_exists"]
    cutoff, statuses, limit = store.queries[0]
    assert (cutoff, statuses, limit) == (now - timedelta(days=90), FINISHED_STATUSES, SWEEP_LIMIT)
    sql = entry["queries"][0]
    assert "WHERE pipeline_runs.created_at < " in sql and "pipeline_runs.status IN" in sql
    assert sql.rstrip().endswith("LIMIT %(param_1)s")


def test_retention_policy_defaults_and_criteria() -> None:
    policy = RetentionPolicyConfig(name="D")
    assert vars(policy) == RETENTION["defaults"]
    assert RETENTION["invalid_strategy"] == "ValidationError"
    with pytest.raises(PipelineValueError):
        RetentionPolicyConfig(name="X", deletion_strategy="shred")  # type: ignore[arg-type]
    now = datetime(2026, 9, 23, tzinfo=UTC)
    assert is_expired_run(now - timedelta(days=91), "ok", policy, now)
    assert not is_expired_run(now - timedelta(days=89), "ok", policy, now)
    assert not is_expired_run(now - timedelta(days=91), "running", policy, now)


def test_retention_job_contract() -> None:
    sweeper = RetentionSweeper(Store([Item(1)]))
    job = asyncio.run(sweeper.run(RetentionPolicyConfig(name="P"), dry_run=True))
    assert job["status"] == "completed" and job["artifacts_deleted"] == 1 and job["errors"] is None
    with pytest.raises(ValueError, match="No retention policy found"):
        asyncio.run(sweeper.run(None))

    class FailingStore(Store):
        async def find_expired_runs(self, *args: Any) -> list[Any]:
            raise RuntimeError("DB weg")

    failed = asyncio.run(RetentionSweeper(FailingStore([])).run(RetentionPolicyConfig(name="P")))
    assert failed["status"] == "failed" and failed["errors"] == [{"error": "DB weg"}]


@pytest.mark.parametrize("fmt", ["json", "csv", "xml"])
def test_file_export_units(fmt: str, tmp_path: Path) -> None:
    context = PipelineContext(document_id="d", run_id="r", status=RunStatus.OK)
    context.artifacts.extracted_fields = {"invoice_number": "R1", "total": "1,00", "leer": None}
    result = asyncio.run(FileExport(tmp_path, fmt).export(context))
    recorded = DATA["export_units"][fmt]
    assert {k: (Path(v).name if k == "path" else v) for k, v in result.items()} == recorded[
        "result"
    ]
    path = tmp_path / f"r.{fmt}"
    assert (path.read_text(encoding="utf-8") if path.exists() else None) == recorded["content"]
    missing = asyncio.run(FileExport(tmp_path / "fehlt", "json").export(context))
    assert missing["success"] is False and Path(missing["path"]).name == "r.json"
