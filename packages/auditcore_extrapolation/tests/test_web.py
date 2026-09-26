"""REST contract auditcore_extrapolation.evaluation/1 (functions, Starlette, FastAPI)."""

from __future__ import annotations

import json
from typing import cast

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from auditcore_extrapolation.web import (
    CONTRACT,
    ContractError,
    catalogue,
    create_app,
    create_router,
    evaluate,
    export_evaluation,
    residual,
)
from auditcore_extrapolation.web.export import _cell

PPS_REQUEST: dict[str, object] = {
    "method": "nonstatistical.pps",
    "strata": [{"name": "alle", "book_value": 22_031_228, "population_size": 36}],
    "units": [
        {
            "id": "h1",
            "stratum": "alle",
            "book_value": 3_102_991.25,
            "random_error": 50_000,
            "exhaustive": True,
        },
        {
            "id": "h2",
            "stratum": "alle",
            "book_value": 3_102_991.25,
            "random_error": 30_028,
            "exhaustive": True,
        },
        {"id": "h3", "stratum": "alle", "book_value": 3_102_991.25, "exhaustive": True},
        {"id": "h4", "stratum": "alle", "book_value": 3_102_991.25, "exhaustive": True},
        {"id": "s1", "stratum": "alle", "book_value": 500_000, "random_error": 10_000},
        {"id": "s2", "stratum": "alle", "book_value": 500_000, "random_error": 3_600},
        {"id": "s3", "stratum": "alle", "book_value": 500_000},
        {"id": "s4", "stratum": "alle", "book_value": 500_000},
    ],
}

MUS_REQUEST: dict[str, object] = {
    "method": "mus.standard",
    "confidence_level": 0.9,
    "factor_profile": "kom_2017_tables",
    "strata": [{"name": "P", "book_value": 1_000_000, "systemic_error": 2_000}],
    "units": [
        {"id": "a", "stratum": "P", "book_value": 20_000, "random_error": 1_000},
        {"id": "b", "stratum": "P", "book_value": 10_000, "systemic_error": 500},
        {"id": "c", "stratum": "P", "book_value": 5_000},
        {
            "id": "d",
            "stratum": "P",
            "book_value": 8_000,
            "anomalous_error": 800,
            "anomalous_reason": "Einmaliger Übertragungsfehler, bereits korrigiert",
            "anomalous_corrected": True,
        },
        {
            "id": "e",
            "stratum": "P",
            "book_value": 200_000,
            "random_error": 4_000,
            "exhaustive": True,
        },
    ],
}


def test_catalogue_lists_all_methods_without_preselection() -> None:
    data = catalogue()
    assert data["contract"] == CONTRACT
    methods = cast(list[dict[str, object]], data["methods"])
    assert {m["id"] for m in methods} >= {"srs.ratio", "mus.conservative", "nonstatistical.pps"}
    assert data["materiality"] == {"default": 0.02, "maximum": 0.02}
    levels = cast(dict[str, list[float]], data["confidence_levels"])
    assert levels["z"] == [0.6, 0.7, 0.8, 0.9, 0.95]


def test_evaluate_nonstatistical_pps_reproduces_the_guidance_example() -> None:
    result = evaluate(PPS_REQUEST)
    ter = cast(dict[str, object], result["total_error_rate"])
    assert ter["total_error"] == pytest.approx(145_439, abs=1)
    assert ter["upper_limit"] is None
    assert ter["conclusion"] == "not_material"
    assert len(cast(str, result["fingerprint"])) == 64


def test_evaluate_separates_error_classes() -> None:
    result = evaluate(MUS_REQUEST)
    ter = cast(dict[str, float], result["total_error_rate"])
    assert ter["systemic_errors"] == 2_000
    assert ter["anomalous_corrected_excluded"] == 800
    assert ter["anomalous_uncorrected"] == 0
    assert ter["total_error"] == pytest.approx(ter["projected_random_error"] + 2_000)


def test_residual_uses_exact_decimals() -> None:
    result = residual(
        {"audit_population": 1000, "total_error_rate": 0.025, "financial_corrections": 2.1}
    )
    rer = cast(dict[str, object], result["residual_error_rate"])
    assert rer["exceeds_materiality"] is True
    assert rer["rate_after_correction"] == pytest.approx(0.02)
    rows = cast(list[dict[str, object]], rer["rows"])
    assert rows[8] == {
        "row": "J=G-H",
        "label": "Verbleibender Risikobetrag",
        "value": 22.9,
        "exact": "22.900",
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"method": "x", "strata": [], "units": []}, "Unbekannte Methode"),
        (
            {**PPS_REQUEST, "units": [{"id": "z", "stratum": "fremd", "book_value": 1}]},
            "unbekannte Schichten",
        ),
        ({**MUS_REQUEST, "confidence_level": 0.85}, "Tabelle 3"),
        ({**MUS_REQUEST, "materiality_rate": 0.03}, "2 %"),
        ({**PPS_REQUEST, "units": "nein"}, "nicht leere Liste"),
    ],
)
def test_contract_errors(payload: dict[str, object], message: str) -> None:
    with pytest.raises(ContractError, match=message):
        evaluate(payload)


def test_export_csv_and_json() -> None:
    csv_file = export_evaluation({**PPS_REQUEST, "format": "csv"})
    text = csv_file.content.decode("utf-8")
    assert text.startswith("﻿Hochrechnung und Gesamtfehlerquote;")
    assert "Gesamtfehlerquote (TER);0,0066" in text
    assert "Ergebnis;Kein wesentlicher Fehler" in text
    assert csv_file.filename.startswith("hochrechnung-nonstatistical.pps-")
    json_file = export_evaluation({**PPS_REQUEST, "format": "json"})
    assert json.loads(json_file.content)["contract"] == CONTRACT
    with pytest.raises(ContractError, match="csv oder json"):
        export_evaluation({**PPS_REQUEST, "format": "xlsx"})


def test_export_neutralises_formulas() -> None:
    assert _cell("=HYPERLINK(1)") == "'=HYPERLINK(1)"
    assert _cell(-5.5) == "-5,5"
    assert _cell(None) == ""


@pytest.fixture(params=["starlette", "fastapi"])
def client(request: pytest.FixtureRequest) -> TestClient:
    if request.param == "starlette":
        return TestClient(create_app("/api/extrapolation"))
    app = FastAPI()
    app.include_router(create_router("/api/extrapolation"))
    return TestClient(app)


def test_http_routes(client: TestClient) -> None:
    profiles = client.get("/api/extrapolation/profiles")
    assert profiles.status_code == 200 and profiles.headers["cache-control"] == "no-store"
    evaluated = client.post("/api/extrapolation/evaluate", json=PPS_REQUEST)
    assert evaluated.status_code == 200
    assert evaluated.json()["total_error_rate"]["conclusion"] == "not_material"
    rer = client.post(
        "/api/extrapolation/residual", json={"audit_population": 1000, "total_error_rate": 0.022}
    )
    assert rer.json()["residual_error_rate"]["rate"] == pytest.approx(0.022)
    exported = client.post(
        "/api/extrapolation/evaluate/export", json={**PPS_REQUEST, "format": "csv"}
    )
    assert exported.headers["content-disposition"].startswith("attachment; filename=")
    assert exported.headers["content-type"].startswith("text/csv")


def test_http_errors(client: TestClient) -> None:
    bad = client.post("/api/extrapolation/evaluate", content=b"{kaputt")
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_json"
    invalid = client.post("/api/extrapolation/evaluate", json={"method": "srs.ratio"})
    assert invalid.status_code == 422 and invalid.json()["error"]["code"] == "invalid_input"


def test_body_limit() -> None:
    small = TestClient(create_app(max_body_bytes=10))
    response = small.post("/evaluate", json=PPS_REQUEST)
    assert response.status_code == 413
