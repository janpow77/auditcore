"""REST-Vertrag dummybundle_ui/1: Katalog, Erzeugung, Rezepte, Grenzen und Fehlerform."""

from __future__ import annotations

import json
from dataclasses import replace
from importlib import import_module
from typing import Any

import pytest

from auditcore_dummybundle import web
from auditcore_dummybundle.errors import BudgetExceededError
from auditcore_dummybundle.model import Budget

PARAMS = {"seed": 42, "base_date": "2026-01-01", "operations": 3}


def request(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"mode": "templates", "templates": ["N1"], "params": dict(PARAMS)}
    body.update(changes)
    return body


def test_catalogue_lists_public_templates_types_and_limits() -> None:
    data = web.catalogue()
    assert data["contract"] == "dummybundle_ui/1"
    assert data["library"] == "auditcore_dummybundle 0.2.0"
    assert data["marking"] == "SYNTHETISCH"
    ids = [t["id"] for t in data["templates"]]
    assert ids == ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "N1"]
    for entry in data["templates"]:
        assert entry["purpose"] and entry["legal_basis"] and entry["column_count"] > 0
        assert entry["status"] == "Freigegeben" and len(entry["content_hash"]) == 64
        assert entry["release"]["human_release_approval"] == "GRANTED"
        assert entry["release"]["approved_on"] == "2026-10-13"
    sources = {t["id"]: {table["source"] for table in t["tables"]} for t in data["templates"]}
    assert sources["V4"] == {"claims", "receipts"} and sources["V5"] == {"payment_applications"}
    assert {b["id"] for b in data["bundles"]} == {"kette", "vorhabenpruefung", "abschluss"}
    assert all(set(b["templates"]) <= set(ids) for b in data["bundles"])
    assert len(data["field_types"]) == 21 and len(data["rules"]) == 2
    assert len(data["anomalies"]) == 13 and len(data["checks"]) == 8
    assert data["limits"]["max_operations"] == 50 and "include_private" not in data["limits"]
    json.dumps(data, ensure_ascii=False)


def test_non_public_templates_only_for_hosts_that_ask(monkeypatch: pytest.MonkeyPatch) -> None:
    templates_module = import_module("auditcore_dummybundle.templates")
    hidden = {k: replace(v, public=k != "V1") for k, v in templates_module.templates().items()}
    monkeypatch.setattr(templates_module, "templates", lambda: hidden)
    monkeypatch.setattr(web, "templates", lambda: hidden)
    assert "V1" not in [t["id"] for t in web.catalogue()["templates"]]
    shown = web.catalogue(web.Limits(include_private=True))
    assert "V1" in {t["id"] for t in shown["templates"]}
    with pytest.raises(web.ContractError) as error:
        web.generate(request(templates=["V1"]))
    assert error.value.code == "unknown_template" and error.value.status == 422
    assert web.generate(request(templates=["V1"]), web.Limits(include_private=True))["tables"]


def test_generate_returns_document_with_metadata() -> None:
    data = web.generate(request(templates=["V0", "N1"]))
    meta = data["_meta"]
    assert meta["marking"] == "SYNTHETISCH" and meta["seed"] == 42
    assert meta["version"] == "0.2.0" and meta["max_workers"] == 1
    assert [t["name"] for t in data["tables"]] == ["Vorhaben", "Belegliste"]
    assert "solution" not in data
    assert data == web.generate(request(templates=["V0", "N1"]))
    json.dumps(data, ensure_ascii=False)


def test_preview_shortens_rows_but_reports_the_count() -> None:
    full = web.generate(request())
    short = web.generate(request(options={"preview": True}))
    table, preview = full["tables"][0], short["tables"][0]
    assert len(preview["rows"]) == 20 < preview["row_count"] == len(table["rows"])
    assert preview["rows"] == table["rows"][:20]


def test_solution_only_on_request() -> None:
    params = {**PARAMS, "anomalies": ["paid_before_invoice"], "anomaly_rate": "0.1"}
    plain = web.generate(request(params=params))
    solved = web.generate(request(params=params, options={"solution": True}))
    assert "solution" not in plain and solved["solution"]
    assert all(key.startswith("gt_") for key in solved["solution"][0])
    assert plain["tables"] == solved["tables"]


@pytest.mark.parametrize(
    ("body", "code", "status"),
    [
        (request(params={**PARAMS, "operations": 51}), "invalid_input", 422),
        (request(params={"base_date": "2026-01-01"}), "missing", 422),
        (request(params={**PARAMS, "sql": 1}), "unknown_key", 422),
        (request(params={**PARAMS, "anomalies": ["x"]}), "unknown_value", 422),
        (request(params={**PARAMS, "eu_rate": "0.9"}), "invalid_input", 422),
        (request(templates=[]), "too_large", 413),
        (request(templates=["V99"]), "unknown_template", 422),
        (request(mode="sql"), "unknown_value", 422),
        (request(extra=1), "unknown_key", 422),
        (request(options={"solution": "ja"}), "invalid_input", 422),
        ("kein Objekt", "invalid_input", 422),
    ],
    ids=[
        "zu_viele_vorhaben",
        "ohne_startwert",
        "fremder_parameter",
        "fremde_auffaelligkeit",
        "eu_ueber_oeffentlich",
        "keine_vorlage",
        "unbekannte_vorlage",
        "fremde_betriebsart",
        "fremder_schluessel",
        "option_kein_wahrheitswert",
        "kein_objekt",
    ],
)
def test_contract_errors(body: object, code: str, status: int) -> None:
    with pytest.raises(web.ContractError) as error:
        web.generate(body)
    assert (error.value.code, error.value.status) == (code, status)
    payload = error.value.to_dict()["error"]
    assert isinstance(payload, dict) and set(payload) == {"code", "message", "path"}


def test_too_many_tables_is_too_large() -> None:
    with pytest.raises(web.ContractError) as error:
        web.generate(request(templates=["V2"], params={**PARAMS, "operations": 40}))
    assert (error.value.code, error.value.status) == ("too_large", 413)


def test_recipe_round_trip_through_the_contract() -> None:
    run = {"seed": 5, "base_date": "2026-01-01", "rows": 30, "country": "AT"}
    start = web.recipe_from_template({"template": "V2", "run": run})
    checked = web.check_recipe(start)
    assert checked["recipe"] == start["recipe"] and checked["notices"] == []
    assert len(checked["preview"]["tables"][0]["rows"]) == 20
    data = web.generate({"mode": "recipe", "recipe": checked["recipe"]})
    assert data["tables"][0]["row_count"] == 30
    assert data["_meta"]["recipe"] == start["recipe"] and data["_meta"]["derived_from"] == "V2"
    assert data == web.generate({"mode": "recipe", "recipe": start["recipe"]})


def test_recipe_from_other_version_gives_a_notice() -> None:
    recipe = web.recipe_from_template(
        {"template": "N1", "run": {"seed": 1, "base_date": "2026-01-01"}}
    )["recipe"]
    recipe["generator"] = {"package": "auditcore_dummybundle", "version": "9.9.9"}
    notices = web.check_recipe({"recipe": recipe})["notices"]
    assert len(notices) == 1 and "9.9.9" in notices[0]


def test_recipe_limits_and_errors() -> None:
    with pytest.raises(web.ContractError) as error:
        web.recipe_from_template({"template": "V5", "run": {"seed": 1, "base_date": "2026-01-01"}})
    assert error.value.code == "no_free_start"
    recipe = web.recipe_from_template(
        {"template": "N1", "run": {"seed": 1, "base_date": "2026-01-01", "rows": 10}}
    )["recipe"]
    recipe["run"]["rows"] = 5001
    with pytest.raises(web.ContractError):
        web.check_recipe({"recipe": recipe})
    recipe["run"]["rows"] = 10
    recipe["fields"][0]["type"] = "exec"
    with pytest.raises(web.ContractError) as error:
        web.generate({"mode": "recipe", "recipe": recipe})
    assert error.value.path == "fields[0].type"


def test_time_budget_stops_cooperatively() -> None:
    budget = Budget(seconds=-1.0)
    with pytest.raises(BudgetExceededError):
        for _ in range(100):
            budget.tick()
    with pytest.raises(web.ContractError) as error:
        web.generate(request(params={**PARAMS, "operations": 50}), web.Limits(max_seconds=-1.0))
    assert (error.value.code, error.value.status) == ("timeout", 503)
