"""Benford REST contract and its Starlette/FastAPI adapters."""

from __future__ import annotations

import json

import pytest

from auditcore_statistics.web import ContractError, analyse, catalogue
from auditcore_statistics.web._http import decode
from auditcore_statistics.web.analysis import MAX_VALUES

VALUES = [123, 187, 2450, 31, 4.2, 1.9, 0, None, -12.5, 999, 15, 18, 1100, 27, 36]
VALUES_BODY = {"test": "first_two", "profile": "nigrini.2012", "values": VALUES}


def test_catalogue_offers_tests_short_values_and_profiles() -> None:
    data = catalogue()
    assert [t["id"] for t in data["tests"]] == ["first", "first_two", "second"]
    assert [s["id"] for s in data["short_values"]] == ["pad", "exclude"]
    assert data["defaults"]["short_values"] == "pad"
    assert data["defaults"]["lower_bound"] == {"first": None, "first_two": None, "second": None}
    assert data["profiles"][0]["id"] == "nigrini.2012"


def test_analyse_reports_distribution_exclusions_and_conformity() -> None:
    result = analyse({"test": "first", "profile": "nigrini.2012", "values": VALUES})
    distribution, conformity = result["distribution"], result["conformity"]
    assert distribution["excluded"] == {
        "missing": 1,
        "zero": 1,
        "short": 0,
        "below_lower_bound": 0,
    }
    assert distribution["lower_bound"] is None
    assert distribution["negative_absolute"] == 1 and distribution["analysed"] == 13
    assert conformity["test"] == "first" and len(conformity["rows"]) == 9
    assert conformity["mad_label"] in {p for p in catalogue()["profiles"][0]["level_labels"]}


def test_json_numbers_are_analysed_exactly_as_sent() -> None:
    payload = decode(
        b'{"test": "first_two", "profile": "nigrini.2012", '
        b'"short_values": "exclude", "lower_bound": null, "values": [0.1, 1e-7, 0.000123, 5]}'
    )
    result = analyse(payload)
    assert result["distribution"]["excluded"]["short"] == 3
    rows = {r["digit"]: r["observed_count"] for r in result["distribution"]["rows"]}
    assert rows[12] == 1


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"test": "last"}, "'test'"),
        ({"profile": None}, "'profile'"),
        ({"values": []}, "nicht leere Liste"),
        ({"values": ["12"]}, "Zahl oder null"),
        ({"values": [True]}, "Zahl oder null"),
        ({"values": [0, None]}, "Keine auswertbaren Werte"),
        ({"short_values": "pad"}, "nur für zweistellige"),
    ],
)
def test_analyse_rejects_invalid_requests(change: dict[str, object], message: str) -> None:
    body = {"test": "first", "profile": "nigrini.2012", "values": VALUES, **change}
    with pytest.raises(ContractError, match=message):
        analyse(body)


def test_two_digit_tests_default_to_pad_without_lower_bound() -> None:
    """Ohne Angaben: ``pad`` und keine Untergrenze, kein Wert fällt still weg.

    Mit ``lower_bound`` 10 fallen 4,2 und 1,9 unter die Grenze und werden gezählt.
    """
    result = analyse({"test": "second", "profile": "nigrini.2012", "values": VALUES})
    distribution = result["distribution"]
    assert distribution["short_values"] == "pad" and distribution["lower_bound"] is None
    assert distribution["excluded"]["below_lower_bound"] == 0
    assert result["conformity"]["analysed"] == 13
    bounded = analyse(
        {"test": "second", "profile": "nigrini.2012", "values": VALUES, "lower_bound": 10}
    )
    assert bounded["distribution"]["excluded"]["below_lower_bound"] == 2
    assert bounded["conformity"]["analysed"] == 11
    with pytest.raises(ContractError, match="short_values"):
        analyse({**VALUES_BODY, "short_values": "drop"})
    with pytest.raises(ContractError, match="lower_bound"):
        analyse({**VALUES_BODY, "lower_bound": -1})


def test_value_limit() -> None:
    with pytest.raises(ContractError) as info:
        analyse({"test": "first", "profile": "nigrini.2012", "values": [1] * (MAX_VALUES + 1)})
    assert info.value.status == 413


def _clients() -> list[object]:
    pytest.importorskip("starlette")
    pytest.importorskip("httpx")
    from starlette.testclient import TestClient

    from auditcore_statistics.web import create_app, create_router

    clients: list[object] = [TestClient(create_app("/api/benford"))]
    fastapi = pytest.importorskip("fastapi")
    app = fastapi.FastAPI()
    app.include_router(create_router("/api/benford"))
    clients.append(TestClient(app))
    return clients


def test_http_adapters_share_the_contract() -> None:
    body = {"test": "first", "profile": "nigrini.2012", "values": VALUES}
    for client in _clients():
        assert client.get("/api/benford/profiles").status_code == 200  # type: ignore[attr-defined]
        ok = client.post("/api/benford/analyze", content=json.dumps(body))  # type: ignore[attr-defined]
        assert ok.status_code == 200 and ok.json()["conformity"]["profile"] == "nigrini.2012"
        bad = client.post("/api/benford/analyze", content=b"[")  # type: ignore[attr-defined]
        assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_json"
        rejected = client.post("/api/benford/analyze", json={**body, "test": "x"})  # type: ignore[attr-defined]
        assert rejected.status_code == 422


def test_body_limit() -> None:
    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

    from auditcore_statistics.web import create_app

    client = TestClient(create_app(max_body_bytes=16))
    body = {"test": "first", "profile": "nigrini.2012", "values": VALUES}
    assert client.post("/analyze", json=body).status_code == 413
