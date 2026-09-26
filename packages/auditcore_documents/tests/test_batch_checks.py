"""Bestandsprüfung ``documents_batch_checks/1``: Dienst, Export, Starlette und FastAPI.

Bestand: ``fixtures/batch/bestand.csv`` – zehn synthetische Belege erfundener
Lieferanten mit je einem gezielt eingebauten Mangel (keine echten Daten).
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from auditcore_documents.web import (
    BATCH_CHECKS_CONTRACT,
    BatchCheckError,
    BatchCheckService,
    BatchCheckSettings,
    batch_check_routes,
    create_batch_check_app,
    create_batch_check_router,
)
from auditcore_documents.web.batch_input import FIELDS
from auditcore_documents.web.batch_rules import RULES

CSV_FILE = Path(__file__).parent / "fixtures" / "batch" / "bestand.csv"
NOW = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)


def inventory() -> list[dict[str, Any]]:
    """CSV mit Spaltenzuordnung über die Spaltennamen des Katalogs (wie die Oberfläche)."""
    rows = list(csv.reader(CSV_FILE.open(encoding="utf-8"), delimiter=";"))
    header = [name.strip().lower() for name in rows[0]]
    columns = {f.name: header.index(a) for f in FIELDS for a in f.aliases if a in header}
    return [{name: row[i] or None for name, i in columns.items()} for row in rows[1:]]


def service(**settings: Any) -> BatchCheckService:
    return BatchCheckService(BatchCheckSettings(**settings), clock=lambda: NOW)


def answer(**options: Any) -> dict[str, Any]:
    return service().check({"documents": inventory(), "options": options})


def rules_by_code(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rule["code"]: rule for rule in result["rules"]}


def findings_of(result: dict[str, Any], code: str) -> list[dict[str, Any]]:
    return [f for f in result["findings"] if f["rule"] == code]


def test_catalogue_lists_all_rules_fields_and_defaults() -> None:
    data = service(max_documents=10).catalogue()
    assert data["contract"] == BATCH_CHECKS_CONTRACT == "documents_batch_checks/1"
    codes = [rule["code"] for rule in data["rules"]]
    assert codes[:13] == [f"C-{n:02d}" for n in range(1, 14)]
    assert codes[13:] == ["A-07", "B-12", "ERG-01", "ERG-02"]
    assert {f["name"] for f in data["fields"]} >= {"ref", "invoice_number", "gross_amount"}
    assert data["defaults"] == {
        "total_volume": None,
        "tolerance": 0.02,
        "concentration_threshold": 0.3,
        "block_threshold": 0.2,
        "supplementary": True,
    }
    assert data["limits"]["max_documents"] == 10
    assert data["export_formats"] == ["json", "csv"]
    assert json.dumps(data, ensure_ascii=False)


def test_every_rule_reports_status_and_affected_documents() -> None:
    result = answer(total_volume="48.500,00")
    rules = rules_by_code(result)
    assert result["summary"]["documents"] == 10
    assert result["summary"]["escalation_level"] == "blocker"
    assert result["summary"]["report_blocked"] is True
    assert result["summary"]["timestamp"] == NOW.isoformat()
    for code in ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08", "C-09"):
        assert rules[code]["status"] == "findings", code
    assert {rules[c]["status"] for c in ("C-10", "C-11", "C-12")} == {"result"}
    assert "Blockade" in rules["C-10"]["note"]
    assert rules["C-13"]["findings"] == 2 and rules["C-13"]["level"] == "info"
    assert findings_of(result, "C-09")[0]["documents"] == [2, 3]
    assert findings_of(result, "C-07")[0]["documents"] == [0, 1, 2, 3]
    assert findings_of(result, "C-08")[0]["documents"] == []
    assert findings_of(result, "B-12")[0]["documents"] == [5, 6, 7, 8, 9]
    assert "RE-2026-0103 bis RE-2026-0105" in findings_of(result, "ERG-01")[0]["message"]
    assert findings_of(result, "ERG-02")[0]["level"] == "warning"


def test_findings_are_numbered_in_rule_order_and_documents_carry_refs() -> None:
    result = answer()
    order = [rule.code for rule in RULES]
    positions = [order.index(f["rule"]) for f in result["findings"]]
    assert positions == sorted(positions)
    assert [f["id"] for f in result["findings"]][:2] == ["B-0001", "B-0002"]
    documents = result["documents"]
    assert documents[3]["ref"] == "B-004"
    assert documents[3]["rules"] == ["C-07", "C-09", "ERG-01", "ERG-02"]
    assert documents[0]["level"] == "warning"


def test_missing_inputs_are_not_checked_and_supplement_can_be_switched_off() -> None:
    documents = [{k: v for k, v in d.items() if k != "ocr_confidence"} for d in inventory()]
    result = service().check({"documents": documents, "options": {"supplementary": False}})
    rules = rules_by_code(result)
    assert rules["C-08"]["status"] == "not_checked"
    assert "Gesamtvolumen" in rules["C-08"]["note"]
    assert rules["C-13"]["status"] == "not_checked"
    assert rules["ERG-01"]["status"] == rules["ERG-02"]["status"] == "not_checked"
    assert not findings_of(result, "ERG-01")


def test_extraction_runs_are_accepted_as_inventory() -> None:
    run = {
        "contract": "documents_extraction/1",
        "document": {"filename": "rechnung.pdf"},
        "ocr": {"avg_confidence": 0.5},
        "fields": [
            {"name": "invoice_number", "value": "A-1"},
            {"name": "date", "value": "2026-01-02"},
            {"name": "supplier_name", "value": "Muster Bau GmbH"},
            {"name": "total", "value": "119.00"},
            {"name": "vat_id", "value": "DE100000001"},
        ],
    }
    result = service().check({"documents": [run, {**run, "document": {}}]})
    assert [d["ref"] for d in result["documents"]] == ["rechnung.pdf", "Beleg 2"]
    assert result["documents"][0]["gross_amount"] == "119.00"
    assert result["documents"][0]["ocr_confidence"] == 0.5
    assert findings_of(result, "C-09")


@pytest.mark.parametrize(
    ("payload", "status", "text"),
    [
        ({}, 422, "'documents' muss eine nicht leere Liste sein."),
        ({"documents": []}, 422, "nicht leere Liste"),
        ({"documents": [1]}, 422, "JSON-Objekt"),
        ({"documents": [{"net_amount": [1]}]}, 422, "Beleg 1: 'net_amount'"),
        ({"documents": [{"ocr_confidence": 3}]}, 422, "zwischen 0 und 1"),
        ({"documents": [{}], "options": {"block_threshold": 2}}, 422, "höchstens 1"),
        ({"documents": [{}], "options": {"supplementary": "ja"}}, 422, "true oder false"),
        ({"documents": [{}], "options": {"total_volume": "viel"}}, 422, "Zahl"),
        ({"documents": [{}, {}, {}]}, 413, "Höchstens 2 Belege"),
    ],
)
def test_contract_errors(payload: dict[str, Any], status: int, text: str) -> None:
    with pytest.raises(BatchCheckError) as error:
        service(max_documents=2).check(payload)
    assert error.value.status == status
    assert text in str(error.value)


def test_export_csv_and_json() -> None:
    body = {"documents": inventory(), "format": "csv"}
    exported = service().export(body)
    assert exported.filename == "befunde-bestand-2026-09-26.csv"
    text = exported.content.decode("utf-8")
    assert text.startswith("\ufeffBefund;Regel;Prüfung;Stufe;Beleg-Nr.;Beleg;")
    assert "B-0001;C-01;Pflichtangaben;Warnung;6;B-006;" in text
    risky = service().export({"documents": [{"ref": "=HYPERLINK(1)"}], "format": "csv"})
    assert ";'=HYPERLINK(1);" in risky.content.decode("utf-8")
    as_json = service().export({**body, "format": "json"})
    assert json.loads(as_json.content)["contract"] == BATCH_CHECKS_CONTRACT
    with pytest.raises(BatchCheckError):
        service().export({**body, "format": "xlsx"})


def test_starlette_endpoints_and_errors() -> None:
    client = TestClient(create_batch_check_app(service(max_body_bytes=200_000)))
    assert client.get("/catalogue").json()["contract"] == BATCH_CHECKS_CONTRACT
    ok = client.post("/runs", json={"documents": inventory()})
    assert ok.status_code == 200 and ok.json()["summary"]["documents"] == 10
    exported = client.post("/export", json={"documents": inventory(), "format": "csv"})
    assert exported.headers["content-disposition"].endswith('.csv"')
    assert exported.headers["content-type"].startswith("text/csv")
    bad = client.post("/runs", content=b"{", headers={"content-type": "application/json"})
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_json"
    big = client.post("/runs", content=b" " * 200_001)
    assert big.status_code == 413
    empty = client.post("/runs", json={"documents": []})
    assert empty.status_code == 422 and empty.json()["error"]["code"] == "invalid_input"


def test_mounted_routes_and_fastapi_router_match() -> None:
    from fastapi import FastAPI
    from starlette.applications import Starlette

    starlette_app = Starlette(routes=batch_check_routes(service(), prefix="/api/batch-checks"))
    fastapi_app = FastAPI()
    fastapi_app.include_router(create_batch_check_router(service(), prefix="/api/batch-checks"))
    body = {"documents": inventory(), "options": {"total_volume": 48009}}
    left = TestClient(starlette_app).post("/api/batch-checks/runs", json=body)
    right = TestClient(fastapi_app).post("/api/batch-checks/runs", json=body)
    assert left.status_code == right.status_code == 200
    assert left.content == right.content
    assert rules_by_code(left.json())["C-08"]["status"] == "passed"
