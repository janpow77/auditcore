"""REST contract ``auditcore_sampling.guidance/1``: framework-free functions and routes."""

from __future__ import annotations

import pytest

from auditcore_sampling.web import ContractError, guidance_catalogue, guidance_draw, guidance_size

PREFIX = "/api/sampling"
CONSERVATIVE = {
    "method": "guidance.mus_conservative",
    "factor_profile": "kom_2017_tables",
    "confidence_level": 0.9,
    "book_value": 4_199_882_024,
    "anticipated_error_rate": 0.002,
}
STRATIFIED = {
    "method": "guidance.srs_stratified",
    "factor_profile": "kom_2017_tables",
    "confidence_level": 0.8,
    "book_value": 1_396_535_319,
    "anticipated_error_rate": 0.018,
    "strata": [
        {"name": "Programm 1", "population_size": 3582, "sd": 444},
        {"name": "Programm 2", "population_size": 1225, "sd": 9818},
        {"name": "Hochwert", "population_size": 5, "exhaustive": True},
    ],
}


def test_catalogue_lists_every_planner_with_source() -> None:
    catalogue = guidance_catalogue()
    assert catalogue["contract"] == "auditcore_sampling.guidance/1"
    assert catalogue["status_label"] == "nach Leitfaden"
    methods = {m["id"]: m for m in catalogue["methods"]}  # type: ignore[union-attr]
    assert set(methods) == {
        "guidance.srs",
        "guidance.srs_stratified",
        "guidance.difference",
        "guidance.difference_stratified",
        "guidance.mus_standard",
        "guidance.mus_stratified",
        "guidance.mus_conservative",
        "guidance.nonstatistical",
    }
    assert methods["guidance.mus_conservative"]["source"].endswith("6.3.5.2")
    assert catalogue["procedures"][0]["id"] == "zs.value_share_escalation"  # type: ignore[index]


def test_size_matches_the_library_and_carries_the_derivation() -> None:
    plan = guidance_size(CONSERVATIVE)
    assert plan["sample_size"] == 136 and plan["status"] == "GUIDANCE_EGESIF_16_0014_01"
    assert plan["inputs"]["materiality_rate"] == 0.02  # type: ignore[index]
    assert [s["label"] for s in plan["derivation"]][0] == "Zuverlässigkeitsfaktor"  # type: ignore[index]
    stratified = guidance_size(STRATIFIED)
    assert stratified["sample_size"] == 126
    assert [r["sample_size"] for r in stratified["strata"]] == [90, 31, 5]  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"method": "guidance.unbekannt"}, "Unbekannte Methode"),
        ({"factor_profile": None}, "factor_profile"),
        ({"confidence_level": 0.97}, "Tabelle 4"),
        ({"anticipated_error_rate": "0,2"}, "endliche Zahl"),
    ],
)
def test_size_rejects_invalid_requests(change: dict[str, object], message: str) -> None:
    with pytest.raises(ContractError, match=message):
        guidance_size({**CONSERVATIVE, **change})


def test_nonstatistical_and_mus_with_book_values() -> None:
    minimum = guidance_size(
        {"method": "guidance.nonstatistical", "rule": "cpr_2021_art79_2", "population_size": 187}
    )
    assert minimum["sample_size"] == 19
    values = [50.0] + [10.0] * 95
    plan = guidance_size(
        {
            "method": "guidance.mus_standard",
            "factor_profile": "exact",
            "confidence_level": 0.9,
            "book_value": sum(values),
            "anticipated_error_rate": 0.0,
            "error_rate_sd": 0.02,
            "book_values": values,
        }
    )
    assert plan["strata"][0]["exhaustive"] is True  # type: ignore[index]


def test_draw_is_reproducible_with_a_visible_seed() -> None:
    body = {
        "procedure": "zs.value_share_escalation",
        "amounts": [100.0] * 40,
        "errors": [50.0] * 40,
        "seed": 7,
    }
    first, second = guidance_draw(body), guidance_draw(body)
    assert first == second and first["seed"] == 7 and first["final_stage"] == 5
    generated = guidance_draw({**body, "seed": None, "parameters": {"escalate": False}})
    assert generated["seed_generated"] is True and generated["final_stage"] == 1
    with pytest.raises(ContractError, match="Unbekannte Parameter"):
        guidance_draw({**body, "parameters": {"anteil": 0.3}})


@pytest.mark.parametrize("framework", ["starlette", "fastapi"])
def test_routes(framework: str) -> None:
    pytest.importorskip("httpx")
    from starlette.testclient import TestClient

    if framework == "fastapi":
        fastapi = pytest.importorskip("fastapi")
        from auditcore_sampling.web import create_router

        app = fastapi.FastAPI()
        app.include_router(create_router(PREFIX))
    else:
        from auditcore_sampling.web import create_app

        app = create_app(PREFIX)
    client = TestClient(app)
    assert client.get(f"{PREFIX}/guidance/profiles").json()["contract"].endswith("/1")
    assert client.post(f"{PREFIX}/guidance/size", json=CONSERVATIVE).json()["sample_size"] == 136
    bad = client.post(f"{PREFIX}/guidance/size", json={**CONSERVATIVE, "book_value": -1})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_input"
    drawn = client.post(
        f"{PREFIX}/guidance/draw",
        json={"procedure": "zs.value_share_escalation", "amounts": [1.0, 2.0], "seed": 1},
    )
    assert drawn.status_code == 200
