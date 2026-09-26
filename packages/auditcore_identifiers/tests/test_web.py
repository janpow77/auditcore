"""REST contract ``identifiers_ui/1`` and its Starlette/FastAPI adapters (synthetic values)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from auditcore_identifiers.web import (
    CONTRACT,
    ContractError,
    Limits,
    catalogue,
    check_batch,
    check_one,
)
from auditcore_identifiers.web._http import handle

VALID_IBAN = "DE89 3704 0044 0532 0130 00"
WRONG_IBAN = "DE89370400440532013001"


def test_catalogue_lists_kinds_profiles_reasons_and_limits() -> None:
    data: dict[str, Any] = catalogue()
    assert data["contract"] == CONTRACT == "identifiers_ui/1"
    assert data["recommended_profile"] == "strict"
    assert [k["id"] for k in data["kinds"]] == [
        "iban", "bic", "vat_id", "tax_id", "tax_number", "lei", "register_number"]
    assert [k["id"] for k in data["kinds"] if k["country"]] == ["vat_id"]
    strict = data["profiles"][0]
    assert strict["id"] == "strict" and not strict["legacy"] and len(strict["kinds"]) == 7
    legacy = {p["id"]: p["kinds"] for p in data["profiles"]}
    assert legacy["flowworkshop.legacy"] == ["lei"]
    assert {r["id"] for r in data["reasons"]} >= {"invalid_checksum", "missing"}
    assert data["detail_labels"]["checksum"] == "Prüfziffer"
    assert data["limits"]["max_items"] == Limits().max_items


def test_single_check_returns_reason_message_and_labels() -> None:
    result: dict[str, Any] = check_one({"kind": "iban", "value": WRONG_IBAN, "profile": "strict"})
    assert result["contract"] == CONTRACT
    answer = result["result"]
    assert (answer["status"], answer["reason"]) == ("INVALID", "invalid_checksum")
    assert answer["reason_label"] == "Prüfziffer falsch"
    assert answer["message"] == "IBAN-Prüfziffer ist falsch" and answer["kind_label"] == "IBAN"


def test_valid_value_is_normalised_with_details() -> None:
    body = {"kind": "vat_id", "value": "136695976", "country": "DE", "profile": "strict"}
    answer: Any = check_one(body)["result"]
    assert answer["status"] == "VALID" and answer["normalized"] == "DE136695976"
    assert answer["details"]["checksum"] == "verified" and answer["reason_label"] is None


def test_legacy_profile_is_applied_as_named() -> None:
    body = {"kind": "iban", "value": WRONG_IBAN, "profile": "flowinvoice.legacy"}
    assert check_one(body)["result"]["status"] == "VALID"  # type: ignore[index]


def test_missing_value_is_a_result_not_an_error() -> None:
    answer = check_one({"kind": "tax_id", "value": None, "profile": "strict"})["result"]
    assert answer["status"] == "MISSING"  # type: ignore[index]


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"kind": "iban", "value": "x"}, "unknown_profile"),
        ({"kind": "iban", "value": "x", "profile": "lax"}, "unknown_profile"),
        ({"kind": "isin", "value": "x", "profile": "strict"}, "unknown_kind"),
        ({"kind": "iban", "value": 5, "profile": "strict"}, "invalid_input"),
        ({"kind": "iban", "value": "D" * 201, "profile": "strict"}, "invalid_input"),
        ({"kind": "vat_id", "value": "x", "country": "DEU1", "profile": "strict"},
         "invalid_input"),
        ({"kind": "lei", "value": "x", "profile": "flowinvoice.legacy"}, "unsupported_kind"),
        ([], "invalid_input"),
    ],
)
def test_single_check_rejects_contract_violations(body: object, code: str) -> None:
    with pytest.raises(ContractError) as caught:
        check_one(body)
    assert caught.value.code == code and caught.value.status == 422


def test_batch_reports_each_row_and_a_summary() -> None:
    answer: dict[str, Any] = check_batch({"profile": "flowworkshop.legacy", "items": [
        {"ref": "Zeile 2", "kind": "lei", "value": "7LTWFZYICNSX8D621K86"},
        {"kind": "iban", "value": VALID_IBAN},
        {"ref": 7, "kind": "unbekannt", "value": "x"},
        {"kind": "lei", "value": ""},
    ]})
    rows = answer["results"]
    assert [r["ref"] for r in rows] == ["Zeile 2", "2", "7", "4"]
    assert rows[0]["status"] == "VALID" and rows[0]["error"] is None
    assert rows[1]["error"]["code"] == "unsupported_kind" and "status" not in rows[1]
    assert rows[2]["error"]["code"] == "unknown_kind"
    assert answer["summary"] == {
        "total": 4, "valid": 1, "invalid": 0, "missing": 1, "not_checked": 2}


def test_batch_limits_and_structure() -> None:
    with pytest.raises(ContractError, match="nicht leere Liste"):
        check_batch({"profile": "strict", "items": []})
    with pytest.raises(ContractError) as caught:
        check_batch({"profile": "strict", "items": [{"kind": "iban"}] * 3}, Limits(max_items=2))
    assert caught.value.status == 413
    with pytest.raises(ContractError, match=r"items\[0\]\.value"):
        check_batch({"profile": "strict", "items": [{"kind": "iban", "value": 1}]})
    with pytest.raises(ContractError, match=r"items\[0\]\.ref"):
        check_batch({"profile": "strict", "items": [{"kind": "iban", "ref": True}]})


def test_dispatch_maps_errors_to_http() -> None:
    limits = Limits(max_body_bytes=64)
    assert handle("check", b"{", limits).status == 400
    assert handle("check", b" " * 65, limits).status == 413
    reply = handle("check", b'{"kind": "iban", "value": "x"}', limits)
    assert reply.status == 422
    assert json.loads(reply.body)["error"]["code"] == "unknown_profile"


def test_starlette_and_fastapi_give_identical_answers() -> None:
    testclient = pytest.importorskip("starlette.testclient")
    pytest.importorskip("fastapi")
    from fastapi import FastAPI

    from auditcore_identifiers.web import create_app, create_router

    app = FastAPI()
    app.include_router(create_router("/api/kennungen"))
    clients = [testclient.TestClient(create_app("/api/kennungen")), testclient.TestClient(app)]
    item = {"kind": "iban", "value": WRONG_IBAN}
    body = {"profile": "strict", "items": [item]}
    answers = [
        (c.get("/api/kennungen/catalogue").content,
         c.post("/api/kennungen/check", json={**item, "profile": "strict"}).content,
         c.post("/api/kennungen/check/batch", json=body).content)
        for c in clients
    ]
    assert answers[0] == answers[1]
    assert json.loads(answers[0][2])["summary"]["invalid"] == 1
    assert clients[0].post("/api/kennungen/check", content=b"[").status_code == 400
