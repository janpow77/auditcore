"""Donut-Port, DonutFieldMergeStage und DONUT_PIPELINE mit FakeDonut und synthetischen Belegen.

Die Belege unter ``fixtures/donut`` stammen aus ``auditcore_invoicesynth``
(``tools/build_donut_fixtures.py``), sind sichtbar als SYNTHETISCH markiert und
enthalten nur fiktive, prüfziffer-gültige Kennungen (Entscheidungen E4/E5).
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from auditcore_documents.pipeline import (
    CORRECTED_PIPELINE,
    DONUT_PIPELINE,
    LEGACY_PIPELINE,
    PIPELINE_PROFILES,
    DonutFieldMergeStage,
    DonutResult,
    FakeDonut,
    HttpDonut,
    InMemoryAuditLog,
    LocalDonut,
    OcrSettings,
    OcrStage,
    ParsedDocument,
    ParsedPage,
    PipelineContext,
    StageError,
    build_pipeline,
    flowagent_donut,
    parse_donut_sequence,
    verify_model_dir,
)
from auditcore_documents.pipeline.donut import field_confidences
from auditcore_documents.pipeline.stages.donut_merge import (
    amount,
    combine_pages,
    iso_date,
    vat_id_check,
)

FIXTURES = Path(__file__).parent / "fixtures" / "donut"
CASES = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))["cases"]
TODAY = date(2026, 9, 24)


def case(layout: str) -> dict[str, Any]:
    return next(c for c in CASES if c["meta"]["layout"] == layout)


def printed_text(gt: dict[str, Any]) -> str:
    """Unabhängige Lesung (Tesseract-Ersatz): gedruckte Werte mit Beschriftungen."""
    lines = [f"Rechnungsnummer: {gt['invoice_number']}"] if "invoice_number" in gt else []
    if "invoice_date" in gt:
        lines.append(f"Rechnungsdatum: {gt['invoice_date']}")
    supplier = gt.get("supplier", {})
    if supplier.get("vat_id"):
        lines.append(f"USt-IdNr.: {supplier['vat_id']}")
    if "net_amount" in gt:
        lines.append(f"Nettobetrag: {gt['net_amount']}")
    for line in gt.get("vat_lines", []):
        lines.append(f"USt {line.get('rate', '')}: {line['amount']}")
    if "total" in gt:
        lines.append(f"Gesamtbetrag: {gt['total']}")
    if "iban" in gt:
        lines.append(f"IBAN: {gt['iban']}")
    return "\n".join(lines)


class FakeTesseract:
    def __init__(self, text: str, confidence: float = 0.93) -> None:
        self.text = text
        self.confidence = confidence

    def parse(self, path: Path) -> ParsedDocument:
        return ParsedDocument(self.text, [ParsedPage(self.text, self.confidence)], None, None)


def result(gt: dict[str, Any], confidence: float = 0.98) -> DonutResult:
    keys = ["invoice_number", "invoice_date", "total", "iban", "net_amount", "supplier.vat_id"]
    keys += [
        f"vat_lines.{i}.{k}"
        for i, _ in enumerate(gt.get("vat_lines", []))
        for k in ("rate", "amount")
    ]
    return DonutResult(
        fields=gt,
        field_confidence=dict.fromkeys(keys, confidence),
        model_id="auditcore-donut-invoice-de@test",
        model_sha256="a" * 64,
        device="cpu",
    )


def run(
    file_name: str,
    donut: FakeDonut | None,
    *,
    text: str | None = None,
    profile: Any = DONUT_PIPELINE,
    rasterizer: Callable[[bytes], list[tuple[int, bytes]] | None] | None = None,
) -> PipelineContext:
    audit = InMemoryAuditLog()
    ocr = OcrStage(
        audit_service=audit,
        donut=donut,
        tesseract=FakeTesseract(text) if text is not None else None,
        rasterizer=rasterizer,
    )
    merge = DonutFieldMergeStage(
        audit_service=audit, min_field_confidence=0.90, today=lambda: TODAY
    )
    pipeline = build_pipeline(profile=profile, audit=audit, ocr=ocr, donut_merge=merge)
    source = FIXTURES / file_name
    context = PipelineContext(
        document_id="doc-1",
        run_id="run-1",
        input_uri=str(source),
        hash_original=hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    return asyncio.run(pipeline.run(context))


def flags(context: PipelineContext) -> list[str]:
    return list(context.validation_flags)


def decisions(context: PipelineContext) -> dict[str, str]:
    fields = (context.artifacts.normalized_json or {})["donut_merge"]["fields"]
    return {name: entry["decision"] for name, entry in fields.items()}


# --------------------------------------------------------------------------- Profil/Vertrag
def test_profile_is_explicit_and_legacy_unchanged() -> None:
    assert PIPELINE_PROFILES["auditcore.pipeline.donut"] is DONUT_PIPELINE
    assert DONUT_PIPELINE.status == "EXPERIMENTAL" and DONUT_PIPELINE.ocr_backend == "donut"
    assert LEGACY_PIPELINE.ocr_backend is None and CORRECTED_PIPELINE.ocr_backend is None
    assert LEGACY_PIPELINE.fingerprint == (
        "aaec1633e2ec3561ed402c8eefa6c6f3a8a914d8e1c08c4e7997c718ab1d5455"
    )
    assert CORRECTED_PIPELINE.fingerprint == (
        "4b7edabdc5c34a9410ae27d9a4c409cff470372f8698bb7dee9d68a7091af753"
    )
    legacy = [s.name for s in build_pipeline(profile=LEGACY_PIPELINE).stages]
    assert "donut_merge" not in legacy
    donut = build_pipeline(profile=DONUT_PIPELINE)
    names = [s.name for s in donut.stages]
    assert names.index("donut_merge") == names.index("postprocess") + 1
    rules = {r.rule_id for r in donut.stages[names.index("validation")].rules}  # type: ignore[attr-defined]
    assert {"VAL_DONUT_PLAUSIBILITY", "VAL_DONUT_DISAGREEMENT"} <= rules
    assert OcrSettings(backend="donut").backend == "donut"  # type: ignore[arg-type]


def test_fixtures_are_synthetic_and_marked() -> None:
    assert {c["meta"]["layout"] for c in CASES} >= {"kopf_links", "mehrseitig", "kleinunternehmer"}
    for item in CASES:
        assert item["meta"]["synthetic"] is True
        assert (FIXTURES / item["file_name"]).read_bytes().startswith(b"\x89PNG")


# --------------------------------------------------------------------------- Ablauf
@pytest.mark.parametrize("layout", ["summen_unten", "holdout_briefkopf", "kopf_links"])
def test_confirmed_donut_values_are_taken(layout: str) -> None:
    item = case(layout)
    gt = item["gt_parse"]
    context = run(item["file_name"], FakeDonut([result(gt)]), text=printed_text(gt))
    assert context.status.value == "ok", (flags(context), decisions(context))
    normalized = context.artifacts.normalized_json or {}
    assert normalized["total"] == float(amount(gt["total"]))  # type: ignore[arg-type]
    assert normalized["iban"] == gt["iban"].replace(" ", "")
    assert normalized["vat_id"] == gt["supplier"]["vat_id"]
    assert normalized["date"] == iso_date(gt["invoice_date"])
    core = {"invoice_number", "date", "net_amount", "vat_amount", "total", "iban", "vat_id"}
    assert {decisions(context)[k] for k in core & set(decisions(context))} == {"accepted"}
    extra = {k: v for k, v in decisions(context).items() if k not in core | {"vat_rates"}}
    assert set(extra.values()) <= {"not_taken"}  # Zusatzfelder ohne Konfidenz: nicht übernommen
    assert context.ocr_metrics is not None and context.ocr_metrics.engine == "donut"
    raw = context.artifacts.ocr_raw_json or {}
    assert raw["engine"] == "donut" and raw["model_sha256"] == "a" * 64


def test_hallucinated_amount_fails_sum_check_and_keeps_regex_value() -> None:
    item = case("summen_unten")
    gt = item["gt_parse"]
    wrong = copy.deepcopy(gt)
    wrong["total"] = gt["total"].replace(",", "0,", 1)  # eingefügte Ziffer wie in der Probe
    context = run(item["file_name"], FakeDonut([result(wrong, 0.99)]), text=printed_text(gt))
    assert context.status.value == "review_needed"
    assert "FAIL_VAL_DONUT_PLAUSIBILITY" in flags(context)
    assert decisions(context)["total"] == "rejected"
    assert (context.artifacts.normalized_json or {})["total"] == float(amount(gt["total"]))  # type: ignore[arg-type]


def test_invalid_iban_vat_id_and_rate_are_rejected() -> None:
    item = case("summen_unten")
    gt = copy.deepcopy(item["gt_parse"])
    gt["iban"] = gt["iban"][:-1] + str((int(gt["iban"][-1]) + 1) % 10)
    vat_id = gt["supplier"]["vat_id"]
    gt["supplier"]["vat_id"] = vat_id[:-1] + str((int(vat_id[-1]) + 1) % 10)
    gt["vat_lines"][0]["rate"] = "16 %"
    context = run(item["file_name"], FakeDonut([result(gt)]), text="")
    result_decisions = decisions(context)
    assert result_decisions["iban"] == result_decisions["vat_id"] == "rejected"
    assert result_decisions["vat_rates"] == "rejected"
    assert context.status.value in {"review_needed", "rejected"}
    assert "FAIL_VAL_DONUT_PLAUSIBILITY" in flags(context)


def test_low_confidence_without_text_match_stays_unconfirmed() -> None:
    item = case("holdout_briefkopf")
    gt = item["gt_parse"]
    context = run(item["file_name"], FakeDonut([result(gt, 0.7)]), text="")
    assert context.status.value == "review_needed"
    assert "REVIEW_VAL_DONUT_DISAGREEMENT" in flags(context)
    assert "LOW_OCR_CONFIDENCE" in flags(context)
    assert set(decisions(context).values()) <= {"unconfirmed", "not_taken"}
    very_low = run(item["file_name"], FakeDonut([result(gt, 0.3)]), text="")
    assert very_low.status.value == "rejected"  # OCR-Qualität wie bei allen Motoren
    assert (
        "total" not in (context.artifacts.normalized_json or {})
        or (context.artifacts.normalized_json or {})["total"] is None
    )


def test_total_without_sum_check_needs_the_text() -> None:
    item = case("kleinunternehmer")
    gt = item["gt_parse"]
    confirmed = run(item["file_name"], FakeDonut([result(gt)]), text=printed_text(gt))
    assert decisions(confirmed)["total"] == "accepted"
    no_text = run(item["file_name"], FakeDonut([result(gt)]), text=None)
    assert decisions(no_text)["total"] == "unconfirmed"
    assert no_text.status.value == "review_needed"


def test_disagreement_with_tesseract_keeps_the_regex_value() -> None:
    item = case("summen_unten")
    gt = item["gt_parse"]
    other = copy.deepcopy(gt)
    other["invoice_number"] = "RE-999999"
    context = run(item["file_name"], FakeDonut([result(other)]), text=printed_text(gt))
    assert decisions(context)["invoice_number"] == "disagreement"
    assert (context.artifacts.normalized_json or {})["invoice_number"] == gt["invoice_number"]
    assert context.status.value == "review_needed"


def test_multi_page_header_first_sums_last() -> None:
    pages = [c for c in CASES if c["meta"]["layout"] == "mehrseitig"]
    assert len(pages) == 2
    combined = combine_pages([{"fields": p["gt_parse"]} for p in pages])
    assert combined["invoice_date"] == pages[0]["gt_parse"]["invoice_date"]
    assert combined["total"] == pages[1]["gt_parse"]["total"]
    assert combined["supplier"]["vat_id"] == pages[1]["gt_parse"]["supplier"]["vat_id"]
    pngs = [(i + 1, (FIXTURES / p["file_name"]).read_bytes()) for i, p in enumerate(pages)]
    donut = FakeDonut(lambda png: result(pages[[b for _, b in pngs].index(png)]["gt_parse"]))
    text = printed_text(combined)
    pdf = FIXTURES.parent / "pipeline" / "invoice_1.pdf"
    audit = InMemoryAuditLog()
    ocr = OcrStage(
        audit_service=audit,
        donut=donut,
        tesseract=FakeTesseract(text),
        rasterizer=lambda data: pngs,
    )
    merge = DonutFieldMergeStage(audit_service=audit, today=lambda: TODAY)
    pipeline = build_pipeline(profile=DONUT_PIPELINE, audit=audit, ocr=ocr, donut_merge=merge)
    context = asyncio.run(
        pipeline.run(PipelineContext(document_id="d", run_id="r", input_uri=str(pdf)))
    )
    assert len(donut.calls) == 2
    assert context.status.value == "ok", (flags(context), decisions(context))
    assert (context.artifacts.normalized_json or {})["total"] == float(amount(combined["total"]))  # type: ignore[arg-type]


def test_missing_donut_port_fails_clearly() -> None:
    context = run(case("kopf_links")["file_name"], None, text="x")
    assert context.status.value == "failed"
    assert context.error_code == "DONUT_NOT_CONFIGURED"


# --------------------------------------------------------------------------- Ports
def test_sequence_parsing_and_field_confidence() -> None:
    sequence = (
        "<s_auditcore_invoice_v1><s_invoice_number>RE-1</s_invoice_number>"
        "<s_supplier><s_vat_id>DE136695976</s_vat_id></s_supplier>"
        "<s_vat_lines><s_rate>19 %</s_rate></s_vat_lines><s_total>1,00</s_total></s>"
    )
    assert parse_donut_sequence(sequence) == {
        "invoice_number": "RE-1",
        "supplier": {"vat_id": "DE136695976"},
        "vat_lines": [{"rate": "19 %"}],
        "total": "1,00",
    }
    tokens = [
        "<s_total>",
        "1",
        ",",
        "00",
        "</s_total>",
        "<s_vat_lines>",
        "<s_rate>",
        "19",
        "</s_rate>",
        "<sep/>",
        "<s_rate>",
        "7",
        "</s_rate>",
        "</s_vat_lines>",
    ]
    probs = [1, 0.9, 0.8, 0.95, 1, 1, 1, 0.7, 1, 1, 1, 0.6, 1, 1]
    assert field_confidences(tokens, probs) == {
        "total": 0.8,
        "vat_lines.0.rate": 0.7,
        "vat_lines.1.rate": 0.6,
    }


def test_http_donut_contract() -> None:
    assert not HttpDonut(None, "http://x").available()
    with pytest.raises(StageError) as error:
        HttpDonut(None, "http://x").parse(b"png")
    assert error.value.error_code == "DONUT_NOT_CONFIGURED"
    calls: list[tuple[str, dict[str, Any]]] = []

    def post(url: str, *, files: Any, data: Any, timeout: float) -> tuple[int, bytes]:
        calls.append((url, dict(data)))
        payload = {
            "raw": "<s_auditcore_invoice_v1><s_total>9,99 €</s_total></s>",
            "model": "donut-invoice-de",
            "model_sha256": "b" * 64,
            "field_confidence": {"total": 0.97},
            "duration_ms": 12,
            "device": "cuda",
        }
        return 200, json.dumps(payload).encode()

    donut = HttpDonut(post, "http://vision:8005/", expected_model_sha256="b" * 64)
    parsed = donut.parse(b"png")
    assert parsed.fields == {"total": "9,99 €"} and parsed.field_confidence == {"total": 0.97}
    assert calls[0] == ("http://vision:8005/v1/vision/parse", {"model": "donut-invoice-de"})
    with pytest.raises(StageError) as mismatch:
        HttpDonut(post, "http://v", expected_model_sha256="c" * 64).parse(b"png")
    assert mismatch.value.error_code == "DONUT_MODEL_HASH_MISMATCH"
    platform = flowagent_donut(post, "https://agent.example")
    platform.parse(b"png")
    assert calls[-1][0] == "https://agent.example/api/v1/ai/apps/flowinvoice/v1/vision/parse"

    def unavailable(url: str, **kwargs: Any) -> tuple[int, bytes]:
        return 503, b""

    with pytest.raises(StageError) as outage:
        HttpDonut(unavailable, "http://v").parse(b"png")
    assert outage.value.error_code == "DONUT_UNAVAILABLE" and outage.value.recoverable


def test_local_donut_verifies_hash_before_loading(tmp_path: Path) -> None:
    with pytest.raises(StageError) as missing:
        verify_model_dir(tmp_path, "0" * 64)
    assert missing.value.error_code == "DONUT_MODEL_MISSING"
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    with pytest.raises(StageError) as mismatch:
        LocalDonut(tmp_path, "0" * 64).parse(b"png")
    assert mismatch.value.error_code == "DONUT_MODEL_HASH_MISMATCH"
    good = hashlib.sha256(b"weights").hexdigest()
    assert verify_model_dir(tmp_path, good) == good


def test_plausibility_helpers() -> None:
    assert vat_id_check("DE136695976") is None
    assert vat_id_check("DE136695975") == "USt-IdNr.-Prüfziffer ungültig"
    assert vat_id_check("ATU13585627") is None
    assert vat_id_check("ATU13585626") == "UID-Prüfziffer ungültig"
    assert amount("EUR 1 835,24") == amount("1.835,24 €") == amount("1,835.24")
    assert amount("1.835") is None
    assert iso_date("5. Jänner 2026") == "2026-01-05" == iso_date("January 5, 2026")
    assert iso_date("1.3.26") == "2026-03-01"
