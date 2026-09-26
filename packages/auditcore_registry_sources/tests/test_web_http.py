"""Starlette routes and FastAPI router speak the same REST contract."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from web_support import make_service, pep_body, sanctions_body

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.requests import Request  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_registry_sources.web import Actor  # noqa: E402
from auditcore_registry_sources.web.http import MAX_BODY, create_app  # noqa: E402

BASE = "/api/screening"


def header_identity(request: Request) -> Actor | None:
    """Test resolver: actor from a header (a real consumer uses its session)."""
    value = request.headers.get("x-test-actor")
    return Actor(value, value.upper()) if value else None


async def async_identity(request: Request) -> Actor | None:
    return header_identity(request)


def starlette_client(**options: Any) -> TestClient:
    return TestClient(create_app(make_service(**options), header_identity))


def fastapi_client(**options: Any) -> TestClient:
    fastapi = pytest.importorskip("fastapi")
    from auditcore_registry_sources.web.fastapi_router import create_router

    app = fastapi.FastAPI()
    app.include_router(create_router(make_service(**options), async_identity))
    return TestClient(app)


CLIENTS: list[Callable[..., TestClient]] = [starlette_client, fastapi_client]
A = {"x-test-actor": "pruefer-a"}
B = {"x-test-actor": "pruefer-b"}


@pytest.mark.parametrize("factory", CLIENTS)
def test_full_review_flow(factory: Callable[..., TestClient]) -> None:
    client = factory(four_eyes_outcomes=["confirmed"])
    settings = client.get(f"{BASE}/settings", headers=A)
    assert settings.status_code == 200 and settings.json()["four_eyes_outcomes"] == ["confirmed"]
    assert settings.headers["cache-control"] == "no-store"
    assert len(client.get(f"{BASE}/sources", headers=A).json()["sources"]) == 4
    created = client.post(f"{BASE}/runs", json=sanctions_body(), headers=A)
    assert created.status_code == 201, created.text
    run = created.json()
    hit = run["subjects"][0]["hits"][0]
    url = f"{BASE}/runs/{run['run_id']}/hits/{hit['hit_id']}"
    decided = client.post(
        f"{url}/decision",
        json={"outcome": "confirmed", "reason": "Identisch.", "expected_sequence": 0},
        headers=A,
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["review"]["status"] == "pending_second_review"
    same = client.post(f"{url}/second-review", json={"approve": True, "reason": "x"}, headers=A)
    assert same.status_code == 409 and same.json()["error"]["code"] == "same_person"
    ok = client.post(f"{url}/second-review", json={"approve": True, "reason": "Ja."}, headers=B)
    assert ok.json()["review"]["status"] == "confirmed"
    log = client.get(f"{BASE}/runs/{run['run_id']}/log", headers=B).json()
    assert [e["type"] for e in log["events"]] == [
        "run_created",
        "decision_recorded",
        "second_review_recorded",
    ]
    filtered = client.get(f"{BASE}/runs/{run['run_id']}?status=confirmed", headers=A).json()
    assert [h["hit_id"] for h in filtered["subjects"][0]["hits"]] == [hit["hit_id"]]
    assert client.get(f"{BASE}/runs", headers=A).json()["runs"][0]["run_id"] == run["run_id"]
    assert client.post(f"{BASE}/runs", json=pep_body(), headers=A).status_code == 201


@pytest.mark.parametrize("factory", CLIENTS)
def test_errors_are_json_with_codes(factory: Callable[..., TestClient]) -> None:
    client = factory()
    assert client.get(f"{BASE}/settings").status_code == 401
    unauth = client.post(f"{BASE}/runs", content=b"kein json")
    assert unauth.status_code == 401 and unauth.json()["error"]["code"] == "unauthenticated"
    form = client.post(f"{BASE}/runs", data={"kind": "sanctions"}, headers=A)
    assert form.status_code == 415
    broken = client.post(
        f"{BASE}/runs", content=b"{", headers={**A, "content-type": "application/json"}
    )
    assert broken.status_code == 400 and broken.json()["error"]["code"] == "invalid_json"
    big = client.post(
        f"{BASE}/runs",
        content=b" " * (MAX_BODY + 1),
        headers={**A, "content-type": "application/json"},
    )
    assert big.status_code == 413
    invalid = client.post(f"{BASE}/runs", json={"kind": "sanctions"}, headers=A)
    assert invalid.status_code == 422
    assert invalid.json()["error"]["message"].startswith("Das Profil ist ausdrücklich")
    assert client.get(f"{BASE}/runs/fehlt", headers=A).status_code == 404


def test_fastapi_router_is_documented_in_openapi() -> None:
    client = fastapi_client()
    paths = client.get("/openapi.json").json()["paths"]
    assert f"{BASE}/runs/{{run_id}}/hits/{{hit_id}}/decision" in paths
    assert f"{BASE}/sources" in paths
