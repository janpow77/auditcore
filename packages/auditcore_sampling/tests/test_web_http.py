"""Starlette routes and the optional FastAPI router of auditcore_sampling.web."""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.applications import Starlette  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_sampling.web import create_app, create_router, routes  # noqa: E402

PREFIX = "/api/sampling"
SIZE = {
    "method": "portal.mus_poisson",
    "population_value": 475_478.94,
    "materiality": 50_000.0,
    "expected_error_rate": 0.005,
    "confidence_level": 0.95,
}
SELECTION = {
    "method": "srs",
    "items": [{"id": f"B{i}", "value": float(i)} for i in range(1, 21)],
    "sample_size": 4,
    "seed": 11,
}


def _fastapi_client() -> TestClient:
    fastapi = pytest.importorskip("fastapi")
    app = fastapi.FastAPI()
    app.include_router(create_router(PREFIX))
    return TestClient(app)


@pytest.fixture(params=["starlette", "fastapi"])
def client(request: pytest.FixtureRequest) -> TestClient:
    if request.param == "fastapi":
        return _fastapi_client()
    return TestClient(create_app(PREFIX))


def test_profiles_and_size(client: TestClient) -> None:
    profiles = client.get(f"{PREFIX}/profiles")
    assert profiles.status_code == 200 and profiles.json()["recommended"]["mus"]
    size = client.post(f"{PREFIX}/size", json=SIZE)
    assert size.status_code == 200 and size.json()["sample_size"] == 30


def test_selection_allocation_and_export(client: TestClient) -> None:
    drawn = client.post(f"{PREFIX}/selection", json=SELECTION).json()
    assert drawn["seed"] == 11 and drawn["selected"] == 4
    allocation = client.post(
        f"{PREFIX}/allocation",
        json={"total_sample_size": 4, "method": "equal", "strata": {"A": 3, "B": 3}},
    )
    assert allocation.json()["allocated"] == 4
    exported = client.post(f"{PREFIX}/selection/export", json={**SELECTION, "format": "csv"})
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert 'filename="stichprobe-srs-seed-11.csv"' in exported.headers["content-disposition"]
    assert exported.content.decode("utf-8").count("\r\n") == 5


def test_errors_are_json_with_status(client: TestClient) -> None:
    invalid = client.post(f"{PREFIX}/size", content=b"{nope")
    assert invalid.status_code == 400 and invalid.json()["error"]["code"] == "invalid_json"
    rejected = client.post(f"{PREFIX}/size", json={**SIZE, "confidence_level": 0.93})
    assert rejected.status_code == 422 and "0.93" in rejected.json()["error"]["message"]


def test_body_limit_and_mountable_routes() -> None:
    small = TestClient(create_app(PREFIX, max_body_bytes=64))
    assert small.post(f"{PREFIX}/selection", json=SELECTION).status_code == 413
    app = Starlette(routes=routes("/x"))
    assert TestClient(app).get("/x/profiles").status_code == 200
