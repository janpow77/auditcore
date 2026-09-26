"""Belegerkennung ``documents_extraction/1``: Dienst, Starlette und FastAPI mit Attrappen-Ports.

Belege: synthetische, sichtbar markierte Rechnungsbilder aus
``fixtures/donut`` (``auditcore_invoicesynth``); OCR und Donut sind
Attrappen, es gibt keinen Netzwerkzugriff.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from auditcore_documents.pipeline import DonutResult, FakeDonut, ParsedDocument, ParsedPage
from auditcore_documents.web import (
    EXTRACTION_CONTRACT,
    ExtractionEngines,
    ExtractionError,
    ExtractionService,
    ExtractionSettings,
    Thresholds,
    create_extraction_app,
    create_extraction_router,
    extraction_routes,
)

FIXTURES = Path(__file__).parent / "fixtures" / "donut"
CASE = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))["cases"][0]
IMAGE = (FIXTURES / CASE["file_name"]).read_bytes()
GT = CASE["gt_parse"]
TEXT = "\n".join(
    [
        f"Rechnungsnummer: {GT['invoice_number']}",
        f"USt-IdNr.: {GT['supplier']['vat_id']}",
        f"IBAN: {GT['iban']}",
        f"Gesamtbetrag: {GT['total']}",
    ]
)


class FakeTesseract:
    def __init__(self, text: str = TEXT, confidence: float = 0.93) -> None:
        self.text = text
        self.confidence = confidence

    def parse(self, path: Path) -> ParsedDocument:
        assert path.is_file()
        return ParsedDocument(self.text, [ParsedPage(self.text, self.confidence)], None, None)


def donut(confidence: float = 0.98) -> FakeDonut:
    keys = ["invoice_number", "invoice_date", "total", "iban", "net_amount", "supplier.vat_id"]
    return FakeDonut(
        [
            DonutResult(
                fields=GT,
                field_confidence=dict.fromkeys(keys, confidence),
                model_id="donut@test",
                model_sha256="a" * 64,
            )
        ]
    )


def service(**engines: Any) -> ExtractionService:
    return ExtractionService(ExtractionEngines(rasterizer=None, **engines))


def test_catalogue_without_engines_is_disabled() -> None:
    catalogue = ExtractionService().catalogue()
    assert catalogue["contract"] == EXTRACTION_CONTRACT == "documents_extraction/1"
    assert catalogue["enabled"] is False and catalogue["default_profile"] is None
    assert catalogue["engines"] == dict.fromkeys(("router", "chandra", "tesseract", "donut"), False)
    retention = catalogue["retention"]
    assert isinstance(retention, dict) and retention["stored"] is False
    assert retention["days"]["processing_logs"] == 90
    with pytest.raises(ExtractionError) as caught:
        ExtractionService().run("beleg.png", IMAGE, None)
    assert (caught.value.status, caught.value.code) == (404, "extraction_disabled")


def test_catalogue_marks_profiles_by_engine() -> None:
    catalogue = service(tesseract=FakeTesseract()).catalogue()
    profiles = {p["id"]: p for p in catalogue["profiles"]}  # type: ignore[attr-defined]
    assert catalogue["default_profile"] == "auditcore.pipeline"
    assert profiles["auditcore.pipeline"]["recommended"] is True
    assert profiles["auditcore.pipeline.donut"]["available"] is False
    assert profiles["auditcore.pipeline.donut"]["min_field_confidence"] == 0.9
    assert len(profiles["auditcore.pipeline"]["retention_categories"]) == 5


def test_recommended_run_returns_fields_and_findings() -> None:
    result = service(tesseract=FakeTesseract()).run("beleg.png", IMAGE, None)
    assert result["profile"]["id"] == "auditcore.pipeline"  # type: ignore[index]
    run = result["run"]
    assert run["status"] == "ok" and run["error_code"] is None  # type: ignore[index]
    assert result["ocr"]["engine"] == "tesseract" and result["ocr"]["quality"] == "ok"  # type: ignore[index]
    fields = {f["name"]: f for f in result["fields"]}  # type: ignore[attr-defined]
    assert fields["invoice_number"]["value"] == GT["invoice_number"]
    assert fields["iban"]["value"] == GT["iban"].replace(" ", "")
    assert fields["iban"]["confidence"] is None
    rules = {f["rule_id"]: f["outcome"] for f in result["findings"]}  # type: ignore[attr-defined]
    assert rules["VAL_IBAN_CHECKSUM"] == "PASS"
    assert result["document"]["mime_type"] == "image/png"  # type: ignore[index]
    assert result["stored"] is False
    json.dumps(result)


def test_donut_run_reports_field_confidence_and_decision() -> None:
    engines = {"tesseract": FakeTesseract(), "donut": donut()}
    result = service(**engines).run("beleg.png", IMAGE, "auditcore.pipeline.donut")
    fields = {f["name"]: f for f in result["fields"]}  # type: ignore[attr-defined]
    assert fields["invoice_number"]["confidence"] == 0.98
    assert fields["invoice_number"]["decision"] == "accepted"
    assert fields["bic"]["decision"] == "not_taken" and fields["bic"]["value"] is None
    assert result["ocr"]["engine"] == "donut"  # type: ignore[index]


def test_low_confidence_needs_review() -> None:
    result = service(tesseract=FakeTesseract(confidence=0.7)).run("b.png", IMAGE, None)
    assert result["run"]["status"] == "review_needed"  # type: ignore[index]
    assert result["ocr"]["quality"] == "review"  # type: ignore[index]
    assert "LOW_OCR_CONFIDENCE" in result["flags"]  # type: ignore[operator]


def test_unsupported_file_is_a_failed_run_not_a_contract_error() -> None:
    result = service(tesseract=FakeTesseract()).run("notiz.txt", b"nur Text", None)
    assert result["run"]["status"] == "failed"  # type: ignore[index]
    assert result["run"]["error_code"] == "INVALID_MIME_TYPE"  # type: ignore[index]


@pytest.mark.parametrize(
    ("profile", "content", "code"),
    [
        ("unbekannt", IMAGE, "unknown_profile"),
        ("auditcore.pipeline.donut", IMAGE, "profile_unavailable"),
        (None, b"", "empty_file"),
    ],
)
def test_contract_errors(profile: str | None, content: bytes, code: str) -> None:
    with pytest.raises(ExtractionError) as caught:
        service(tesseract=FakeTesseract()).run("b.png", content, profile)
    assert caught.value.code == code and caught.value.status == 422


def test_limits_and_unknown_settings() -> None:
    small = ExtractionService(
        ExtractionEngines(tesseract=FakeTesseract()),
        ExtractionSettings(max_upload_bytes=10, thresholds=Thresholds(ok=0.9, review=0.5)),
    )
    assert small.catalogue()["thresholds"] == {"ok": 0.9, "review": 0.5}
    with pytest.raises(ExtractionError) as caught:
        small.run("b.png", IMAGE, None)
    assert caught.value.status == 413
    with pytest.raises(ValueError, match="Unbekannte"):
        ExtractionService(settings=ExtractionSettings(profiles=("gibt.es.nicht",)))


def test_starlette_endpoints() -> None:
    client = TestClient(create_extraction_app(service(tesseract=FakeTesseract())))
    assert client.get("/profile").json()["enabled"] is True
    answer = client.post("/runs", files={"file": ("beleg.png", IMAGE, "image/png")})
    assert answer.status_code == 200 and answer.json()["run"]["status"] == "ok"
    missing = client.post("/runs", data={"profile": "auditcore.pipeline"})
    assert missing.status_code == 422 and missing.json()["error"]["code"] == "missing_file"
    wrong = client.post(
        "/runs", files={"file": ("b.png", IMAGE, "image/png")}, data={"profile": "x"}
    )
    assert wrong.json()["error"]["code"] == "unknown_profile"


def test_starlette_disabled_and_mounting() -> None:
    from starlette.applications import Starlette

    app = Starlette(routes=extraction_routes(ExtractionService(), "/api/extraction"))
    client = TestClient(app)
    assert client.get("/api/extraction/profile").json()["enabled"] is False
    answer = client.post("/api/extraction/runs", files={"file": ("b.png", IMAGE, "image/png")})
    assert answer.status_code == 404
    assert answer.json() == {
        "error": {
            "code": "extraction_disabled",
            "message": "Belegerkennung ist abgeschaltet (keine OCR-Engine angeschlossen).",
        }
    }


def test_fastapi_router_matches_starlette() -> None:
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(
        create_extraction_router(service(tesseract=FakeTesseract()), prefix="/api/extraction")
    )
    client = TestClient(app)
    starlette = TestClient(create_extraction_app(service(tesseract=FakeTesseract())))
    assert client.get("/api/extraction/profile").json() == starlette.get("/profile").json()
    answer = client.post("/api/extraction/runs", files={"file": ("b.png", IMAGE, "image/png")})
    assert answer.status_code == 200 and answer.json()["contract"] == "documents_extraction/1"
