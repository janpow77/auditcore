"""REST interface ``auditcore_risk.web`` (contract ``docs/ui/risk-rest.md`` im Monorepo)."""

from __future__ import annotations

import json
import math
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.testclient import TestClient  # noqa: E402

from auditcore_risk import load_profile  # noqa: E402
from auditcore_risk.errors import DependencyError, InputError, ProfileError  # noqa: E402
from auditcore_risk.web import (  # noqa: E402
    ApiError,
    create_app,
    handle_evaluate,
    json_safe,
    library_error,
    profile_fields,
    rule_parameters,
)

YEAR_BOUND = {"id": "riskanalysis.year_bound", "version": "2026.09.5"}
NETTO_FEHLT = "Nettobetrag fehlt in der Quelle"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _beleg(**fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "belegnummer": "B1",
        "bruttobetrag": 40_000.0,
        "nettobetrag": 33_613.45,
        "vergabenummer": "0=ni",
        "Name": "Alpha GmbH",
        "zahlungsempfaenger": "Beta KG",
        "rechnungsdatum_dt": "2025-03-01",
    }
    base.update(fields)
    return base


def test_profiles_lists_every_packaged_profile(client: TestClient) -> None:
    answer = client.get("/risk/profiles")
    assert answer.status_code == 200
    entries = answer.json()["profiles"]
    keys = {(e["id"], e["version"]) for e in entries}
    assert ("riskanalysis.year_bound", "2026.09.5") in keys
    entry = next(e for e in entries if e["version"] == "2026.09.5")
    assert entry["status"] == "APPROVED"
    assert entry["rule_count"] == 10
    assert entry["field_count"] == 17
    assert len(entry["fingerprint"]) == 64


def test_profile_detail_has_rules_parameters_and_fields(client: TestClient) -> None:
    answer = client.get("/risk/profiles/riskanalysis.year_bound/2026.09.5")
    assert answer.status_code == 200
    detail = answer.json()
    rules = {r["code"]: r for r in detail["rules"]}
    assert list(rules)[:3] == ["RF01", "RF02", "RF08"]
    assert rules["RF02"]["inputs"] == ["nettobetrag", "rechnungsdatum_dt"]
    assert rules["RF02"]["when_missing_columns"] == "undetermined"
    assert rules["RF08"]["parameters"] == {"amount_gt": 25000.0}
    assert rules["RF01"]["parameters"] == {"multiple": 1000}
    fields = {f["name"]: f for f in detail["fields"]}
    netto = fields["nettobetrag"]
    assert netto["requirement"] == "optional"
    assert {u["code"] for u in netto["uses"]} == {"RF02", "RF08"}
    assert all(NETTO_FEHLT in u["empty"] for u in netto["uses"])
    assert fields["Name"]["requirement"] == "required"
    assert detail["source"]["repository"] == "janpow77/riskanalysis"


def test_unknown_profile_is_404_not_a_default(client: TestClient) -> None:
    answer = client.get("/risk/profiles/riskanalysis.year_bound/0.0.0")
    assert answer.status_code == 404
    assert answer.json()["error"]["code"] == "profile_not_found"


def test_check_columns_names_consequences(client: TestClient) -> None:
    answer = client.post(
        "/risk/profiles/riskanalysis.year_bound/2026.09.5/check-columns",
        json={"columns": ["bruttobetrag", "Name", "zahlungsempfaenger"]},
    )
    assert answer.status_code == 200
    data = answer.json()
    rules = {r["code"]: r for r in data["rules"]}
    assert rules["RF02"]["missing"] == ["nettobetrag"]
    assert rules["RF02"]["when_missing_columns"] == "undetermined"
    assert rules["RF11"]["when_missing_columns"] == "all_false"
    assert data["complete"] is False
    assert data["aborts"] is False
    bad = client.post(
        "/risk/profiles/riskanalysis.year_bound/2026.09.5/check-columns", json={"columns": 3}
    )
    assert bad.status_code == 400


def test_evaluate_marks_missing_net_amount_undetermined(client: TestClient) -> None:
    body = {
        "profile": YEAR_BOUND,
        "record_key": "belegnummer",
        "records": [
            _beleg(nettobetrag=None, zahlungsempfaenger="Alpha GmbH"),
            _beleg(belegnummer="B2"),
        ],
    }
    answer = client.post("/risk/evaluate", json=body)
    assert answer.status_code == 200, answer.text
    data = answer.json()
    first, second = data["records"]
    assert first["key"] == "B1"
    assert first["flags"]["RF02"] is None and first["flags"]["RF08"] is None
    assert first["undetermined"] == {"RF02": NETTO_FEHLT, "RF08": NETTO_FEHLT}
    assert first["inputs"]["RF08"]["nettobetrag"] is None
    assert first["inputs"]["RF08"]["vergabenummer"] == "0=ni"
    assert "RF09" in first["codes"]
    hit = next(h for h in first["hits"] if h["code"] == "RF09")
    assert hit["inputs"]["Name"] == "Alpha GmbH"
    assert second["flags"]["RF08"] is True
    assert second["undetermined"] == {}
    summary = {s["code"]: s for s in data["summary"]}
    assert summary["RF02"]["unbestimmt"] == 1
    assert [r["code"] for r in data["rules"]][0] == "RF01"
    assert "rechnungsdatum_dt" in data["columns"]


def test_evaluate_reports_missing_columns_and_skipped_rules(client: TestClient) -> None:
    body = {
        "profile": {"id": "audit_designer.flowstat_belegliste", "version": "1254591156d3"},
        "records": [{"projektbetrag": 30_000.0, "vergabe": ""}],
    }
    data = client.post("/risk/evaluate", json=body).json()
    assert "BL_RF03_MISSING_PAYMENT_DATE" in data["skipped"]
    assert data["skipped"]["BL_RF03_MISSING_PAYMENT_DATE"].startswith("Spalten fehlen")
    assert data["missing_columns"]["BL_RF03_MISSING_PAYMENT_DATE"] == ["zahlungsdatum"]
    assert data["records"][0]["key"] is None


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ([], 400, "invalid_request"),
        ({"profile": YEAR_BOUND, "records": [1]}, 400, "invalid_request"),
        ({"profile": YEAR_BOUND, "records": [], "extra": 1}, 400, "invalid_request"),
        ({"profile": YEAR_BOUND, "records": [], "reference_date": "31.01.2026"}, 400, None),
        ({"profile": YEAR_BOUND, "records": [], "record_key": 5}, 400, None),
        ({"profile": {"id": "x", "version": "1"}, "records": []}, 404, "profile_not_found"),
        ({"profile": YEAR_BOUND, "records": [_beleg(bruttobetrag="viel")]}, 400, "input_error"),
        ({"profile": YEAR_BOUND, "records": [], "points": {"RF01": 1}}, 422, "profile_error"),
        ({"records": []}, 400, "invalid_request"),
        ({"profile": YEAR_BOUND, "records": [], "points": {"RF01": True}}, 400, None),
        ({"profile": YEAR_BOUND, "records": [], "points": {"RF01": "1"}}, 400, None),
        ({"profile": YEAR_BOUND, "records": [], "points": [1]}, 400, None),
        ({"profile": YEAR_BOUND, "records": [], "columns": [1]}, 400, None),
        ({"profile": {"id": 1, "version": "1"}, "records": []}, 400, None),
    ],
)
def test_evaluate_rejects_invalid_requests(
    client: TestClient, body: Any, status: int, code: str | None
) -> None:
    answer = client.post("/risk/evaluate", json=body)
    assert answer.status_code == status, answer.text
    if code is not None:
        assert answer.json()["error"]["code"] == code


def test_invalid_json_and_limits() -> None:
    small = TestClient(create_app("", max_records=1, max_body_bytes=2_000))
    answer = small.post("/evaluate", content=b"{nope", headers={"content-type": "application/json"})
    assert answer.status_code == 400
    assert answer.json()["error"]["code"] == "invalid_json"
    many = {"profile": YEAR_BOUND, "records": [_beleg(), _beleg()]}
    assert small.post("/evaluate", json=many).json()["error"]["code"] == "too_many_records"
    huge = {"profile": YEAR_BOUND, "records": [_beleg(Name="x" * 3_000)]}
    assert small.post("/evaluate", json=huge).status_code == 413


def test_flatten_and_reference_date() -> None:
    result = handle_evaluate(
        {
            "profile": YEAR_BOUND,
            "flatten": True,
            "reference_date": "2026-01-31",
            "records": [{**_beleg(), "meta": {"quelle": "MDB"}}],
        }
    )
    assert "meta.quelle" in result["columns"]


def test_json_safe_has_no_nan() -> None:
    value = {"a": math.nan, "b": [math.inf, -math.inf], "c": date(2026, 1, 2), "d": Decimal("1.5")}
    safe = json_safe(value)
    assert safe == {"a": "NaN", "b": ["Infinity", "-Infinity"], "c": "2026-01-02", "d": 1.5}
    json.dumps(safe, allow_nan=False)
    assert json_safe({"x": object()})["x"].startswith("<object")


def test_library_errors_map_to_http_status() -> None:
    assert library_error(DependencyError("x")).status == 503
    assert library_error(InputError("x")).status == 400
    assert library_error(ProfileError("x")).status == 422
    assert ApiError(418, "c", "m").to_dict() == {"error": {"code": "c", "message": "m"}}


def test_rule_parameters_skip_fields_and_substitutes() -> None:
    params = {
        "field": "betrag",
        "missing_value": 0.0,
        "column_missing_value": 1.0,
        "multiple": 1000,
        "flag": True,
        "nested": {"amount_field": "x", "limits": [1.0, 2.0], "name": "t"},
    }
    assert rule_parameters(params) == {"multiple": 1000, "nested.limits": [1.0, 2.0]}


def test_every_packaged_profile_has_catalog_fields() -> None:
    from auditcore_risk import available_profiles

    for pid, version in available_profiles():
        assert profile_fields(load_profile(pid, version)), (pid, version)


def test_fastapi_router_matches_starlette(client: TestClient) -> None:
    pytest.importorskip("fastapi")
    from fastapi import FastAPI

    from auditcore_risk.web import build_fastapi_router

    app = FastAPI()
    app.include_router(build_fastapi_router("/api/risk"))
    fast = TestClient(app)
    path = "/profiles/riskanalysis.year_bound/2026.09.5"
    assert fast.get(f"/api/risk{path}").json() == client.get(f"/risk{path}").json()
    body = {"profile": YEAR_BOUND, "records": [_beleg(nettobetrag=None)]}
    assert fast.post("/api/risk/evaluate", json=body).json() == (
        client.post("/risk/evaluate", json=body).json()
    )
