"""REST interface ``auditcore_dataprotection.web`` (contract ``dataprotection_ui/1``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.requests import Request  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_dataprotection import Actor, Permission, load_profile  # noqa: E402
from auditcore_dataprotection.memory import FixedClock, RoleAuthorizer, SequentialIds  # noqa: E402
from auditcore_dataprotection.web import (  # noqa: E402
    CONTRACT,
    DataProtectionApi,
    InMemoryStorage,
    Principal,
    create_app,
    create_backend,
    csv_cell,
    csv_document,
)

PROFILE = load_profile("auditcore.dsgvo", "2026.10.3")
PEOPLE = {"anna", "bert"}
JSON = {"Content-Type": "application/json"}


def _identify(request: Request) -> Principal | None:
    person = request.headers.get("X-Person")
    if person not in PEOPLE:
        return None
    tenant = request.headers.get("X-Tenant", "behoerde")
    return Principal(tenant, Actor(person, frozenset({tenant}), frozenset({"alle"})))


def _api() -> DataProtectionApi:
    backend = create_backend(
        PROFILE,
        InMemoryStorage(),
        RoleAuthorizer({"alle": frozenset(Permission)}),
        clock=FixedClock(),
        ids=SequentialIds(),
    )
    return DataProtectionApi(backend)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(_api(), identify=_identify))


def _as(person: str, **extra: str) -> dict[str, str]:
    return {**JSON, "X-Person": person, **extra}


def _activity(**changes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "Fördermittelverwaltung",
        "referat": "Referat I",
        "zweck": "Bewilligung von Zuwendungen",
        "ermaechtigungsgrundlage": "§ 44 LHO",
        "kategorien_betroffene": "Antragstellende",
        "kategorien_daten": "Stammdaten, Bankverbindung",
        "kategorien_empfaenger": "Landeshauptkasse",
        "speicherdauer": "10 Jahre",
        "tom": "Rollenkonzept, Verschlüsselung",
        "drittlandtransfer": False,
        "besondere_kategorien": False,
        "daten_art10": False,
        "anzahl_betroffene": 500,
    }
    return base | changes


def _content(*activities: dict[str, object]) -> dict[str, object]:
    return {
        "deckblatt": {"verantwortlicher": {"name": "Behörde"}, "dsb": {"name": "DSB"}},
        "referate": ["Referat I"],
        "taetigkeiten": list(activities),
    }


def _released_register(client: TestClient, *activities: dict[str, object]) -> dict[str, Any]:
    draft = client.post(
        "/register/draft", json={"content": _content(*activities)}, headers=_as("anna")
    )
    assert draft.status_code == 200, draft.text
    released = client.post(
        "/register/release",
        json={"expected_revision": draft.json()["revision"]},
        headers=_as("bert"),
    )
    assert released.status_code == 200, released.text
    return dict(released.json())


def test_profile_describes_forms_from_the_rule_profile(client: TestClient) -> None:
    data = client.get("/profile", headers=_as("anna")).json()
    assert data["contract"] == CONTRACT
    assert data["profile"]["id"] == "auditcore.dsgvo"
    columns = {c["key"]: c for c in data["register"]["columns"]}
    assert columns["zweck"]["required"] and columns["zweck"]["kind"] == "text"
    assert columns["drittlandtransfer"]["kind"] == "flag"
    assert columns["anzahl_betroffene"]["kind"] == "count"
    assert columns["zweck"]["reference"].startswith("Art. 30 Abs. 1 lit. b")
    blocks = [b["key"] for b in data["screening"]["blocks"]]
    assert blocks == [key for key, _ in PROFILE.blocks]
    muss = data["screening"]["blocks"][1]["questions"]
    assert len(muss) == 17 and {q["effect"] for q in muss} == {"hart"}
    assert data["risk"]["bands"] == ["offen", "gering", "mittel", "hoch"]
    assert "verworfen" in [d["key"] for d in data["decisions"]]


def test_identity_is_required(client: TestClient) -> None:
    answer = client.get("/register")
    assert answer.status_code == 401
    assert answer.json() == {
        "error": {"code": "unauthenticated", "message": "Anmeldung erforderlich."}
    }


def test_register_draft_check_and_four_eyes_release(client: TestClient) -> None:
    empty = client.get("/register", headers=_as("anna")).json()
    assert empty["draft"] is None and empty["released"] is None and empty["versions"] == []

    incomplete = _content(_activity(zweck="", drittlandtransfer=None))
    issues = client.post(
        "/register/check", json={"content": incomplete}, headers=_as("anna")
    ).json()["issues"]
    codes = {(i["code"], i["subject"].split(":")[1]) for i in issues}
    assert ("missing_field", "zweck") in codes and ("undecided_flag", "drittlandtransfer") in codes

    draft = client.post("/register/draft", json={"content": incomplete}, headers=_as("anna"))
    assert draft.status_code == 200
    body = draft.json()
    assert body["status"] == "entwurf" and body["revision"] == 1 and body["version"] == 1
    assert body["content"]["taetigkeiten"][0]["id"] == "id-activity-1"
    assert any(i["blocking"] for i in body["issues"])

    own = client.post("/register/release", json={"expected_revision": 1}, headers=_as("anna"))
    assert own.status_code == 403 and own.json()["error"]["code"] == "vier_augen_verletzt"
    blocked = client.post("/register/release", json={"expected_revision": 1}, headers=_as("bert"))
    assert blocked.status_code == 409 and "unvollständig" in blocked.json()["error"]["message"]

    fixed = body["content"]
    fixed["taetigkeiten"][0].update(zweck="Bewilligung", drittlandtransfer=False)
    stale = client.post(
        "/register/draft", json={"content": fixed, "expected_revision": 9}, headers=_as("anna")
    )
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "stale_revision"
    saved = client.post(
        "/register/draft", json={"content": fixed, "expected_revision": 1}, headers=_as("anna")
    ).json()
    released = client.post(
        "/register/release", json={"expected_revision": saved["revision"]}, headers=_as("bert")
    )
    assert released.status_code == 200
    assert released.json()["status"] == "freigegeben" and released.json()["released_by"] == "bert"
    state = client.get("/register", headers=_as("anna")).json()
    assert state["draft"] is None and state["released"]["version"] == 1
    assert [v["status"] for v in state["versions"]] == ["freigegeben"]


def test_new_draft_after_release_supersedes_on_next_release(client: TestClient) -> None:
    first = _released_register(client, _activity())
    content = first["content"]
    content["taetigkeiten"][0]["tom"] = "Rollenkonzept, Mehrfaktor-Anmeldung"
    draft = client.post("/register/draft", json={"content": content}, headers=_as("anna")).json()
    assert draft["version"] == 2 and draft["predecessor_version"] == 1
    client.post(
        "/register/release", json={"expected_revision": draft["revision"]}, headers=_as("bert")
    )
    versions = client.get("/register", headers=_as("anna")).json()["versions"]
    assert [(v["version"], v["status"]) for v in versions] == [(2, "freigegeben"), (1, "abgeloest")]


def test_register_exports_with_formula_protection(client: TestClient) -> None:
    _released_register(client, _activity(anmerkungen='=HYPERLINK("http://x")'))
    csv = client.post("/register/export", json={"format": "csv"}, headers=_as("anna"))
    assert csv.status_code == 200
    assert csv.headers["content-type"].startswith("text/csv")
    assert "verarbeitungsverzeichnis_fassung_1.csv" in csv.headers["content-disposition"]
    text = csv.content.decode("utf-8")
    assert text.startswith("﻿Referat;Datenverarbeitungsvorgang;")
    assert '"\'=HYPERLINK(""http://x"")"' in text
    markdown = client.post(
        "/register/export", json={"format": "markdown"}, headers=_as("anna")
    ).text
    assert "## Fördermittelverwaltung" in markdown and "Keine offenen Angaben." in markdown
    html = client.post("/register/export", json={"format": "html"}, headers=_as("anna")).text
    assert html.startswith("<!DOCTYPE html>") and "Fördermittelverwaltung" in html
    missing = client.post(
        "/register/export", json={"format": "html", "source": "draft"}, headers=_as("anna")
    )
    assert missing.status_code == 404
    wrong = client.post("/register/export", json={"format": "xlsx"}, headers=_as("anna"))
    assert wrong.status_code == 400 and wrong.json()["error"]["code"] == "invalid_request"


def test_calculate_uses_the_library_proposal(client: TestClient) -> None:
    answers = {k: "nein" for k in PROFILE.question_keys} | {"art35_3_a": "ja"}
    scenario = {
        "dimension": "vertraulichkeit",
        "description": "Unbefugter Zugriff",
        "severity": 3,
        "likelihood": 4,
        "measures": ["zugriffskontrolle"],
    }
    body = {"answers": answers, "scenarios": [scenario]}
    proposal = client.post("/calculate", json=body, headers=_as("anna")).json()
    assert proposal["screening"]["outcome"] == "pflicht"
    assert proposal["screening"]["hard_triggers"] == ["art35_3_a"]
    assert proposal["risk"]["scenarios"][0]["net_band"] in {"gering", "mittel", "hoch"}
    open_answers = client.post("/calculate", json={"answers": {}}, headers=_as("anna")).json()
    assert open_answers["recommendation"] == "unvollstaendig"
    bad = client.post("/calculate", json={"answers": {"x": "ja"}}, headers=_as("anna"))
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"


def _survey() -> dict[str, object]:
    return {
        "answers": {k: {"value": "nein"} for k in PROFILE.question_keys}
        | {"art35_3_a": {"value": "ja", "justification": "Scoring"}},
        "scenarios": [
            {
                "dimension": "vertraulichkeit",
                "description": "Unbefugter Zugriff",
                "severity": 3,
                "likelihood": 4,
                "measures": ["zugriffskontrolle"],
            }
        ],
        "necessity": "Erforderlich für die Bewilligung.",
        "proportionality": "Nur Pflichtangaben.",
        "dossier": {"team": "Referat I, IT", "umfang": "Bewilligungsverfahren"},
    }


def test_assessment_lifecycle(client: TestClient) -> None:
    register = _released_register(client, _activity())
    activity_id = register["content"]["taetigkeiten"][0]["id"]
    overview = client.get("/assessments", headers=_as("anna")).json()["items"]
    assert overview[0]["id"] == activity_id and overview[0]["dsfa"] is None

    started = client.post("/assessments", json={"activity_id": activity_id}, headers=_as("anna"))
    assert started.status_code == 201
    view = started.json()
    assert view["status"] == "entwurf" and view["proposal"]["recommendation"] == "unvollstaendig"
    base = f"/assessments/{view['id']}"

    view = client.post(
        base, json={"expected_revision": view["revision"], **_survey()}, headers=_as("anna")
    ).json()
    assert view["proposal"]["recommendation"] == "freigabe_mit_auflagen"
    assert view["answers"]["art35_3_a"] == {"value": "ja", "justification": "Scoring"}
    assert view["open_points"] and view["release_blockers"] == []

    view = client.post(
        f"{base}/decide",
        json={
            "expected_revision": view["revision"],
            "decision": "freigabe_mit_auflagen",
            "conditions": ["Mehrfaktor-Anmeldung vor Start"],
        },
        headers=_as("anna"),
    ).json()
    assert view["decision"] == "freigabe_mit_auflagen" and view["decided_by"] == "anna"
    view = client.post(
        f"{base}/dpo-request",
        json={
            "expected_revision": view["revision"],
            "requested_from": "DSB",
            "requested_on": "2026-09-24",
        },
        headers=_as("anna"),
    ).json()
    assert view["dpo_requested_on"] == "2026-09-24"

    own = client.post(
        f"{base}/release", json={"expected_revision": view["revision"]}, headers=_as("anna")
    )
    assert own.status_code == 403
    released = client.post(
        f"{base}/release", json={"expected_revision": view["revision"]}, headers=_as("bert")
    ).json()
    assert released["status"] == "freigegeben" and released["locked"]
    locked = client.post(
        base, json={"expected_revision": released["revision"]}, headers=_as("anna")
    )
    assert locked.status_code == 409

    report = client.post(f"{base}/export", json={"format": "markdown"}, headers=_as("anna"))
    assert "# Datenschutz-Folgenabschätzung" in report.text
    assert "Freigabe mit Auflagen" in report.text
    html = client.post(f"{base}/export", json={"format": "html"}, headers=_as("anna"))
    assert html.headers["content-type"].startswith("text/html")

    again = client.post(f"{base}/reassess", headers=_as("anna"))
    assert again.status_code == 201 and again.json()["version"] == 2
    assert [v["status"] for v in again.json()["versions"]] == ["entwurf", "freigegeben"]
    row = client.get("/assessments", headers=_as("anna")).json()["items"][0]
    assert row["dsfa"]["version"] == 2


@pytest.mark.parametrize(
    ("headers", "content", "status", "code"),
    [
        ({"Content-Type": "text/plain"}, b"{}", 415, "unsupported_media_type"),
        (JSON, b"{nope", 400, "invalid_json"),
        (JSON, b'{"content": {}, "extra": 1}', 400, "invalid_request"),
        (JSON, b"[]", 400, "invalid_request"),
        (JSON, b'{"content": {"taetigkeiten": [{"drittlandtransfer": "ja"}]}}', 422, None),
    ],
)
def test_request_envelope_errors(
    client: TestClient, headers: dict[str, str], content: bytes, status: int, code: str | None
) -> None:
    answer = client.post(
        "/register/draft", content=content, headers={**headers, "X-Person": "anna"}
    )
    assert answer.status_code == status
    assert answer.json()["error"]["code"] == (code or "validation_error")


def test_tenants_are_isolated(client: TestClient) -> None:
    register = _released_register(client, _activity())
    activity_id = register["content"]["taetigkeiten"][0]["id"]
    started = client.post("/assessments", json={"activity_id": activity_id}, headers=_as("anna"))
    other = _as("anna", **{"X-Tenant": "andere"})
    assert client.get("/register", headers=other).json()["released"] is None
    foreign = client.get(f"/assessments/{started.json()['id']}", headers=other)
    assert foreign.status_code == 404


def test_body_limit() -> None:
    small = TestClient(create_app(_api(), identify=_identify, max_body_bytes=10))
    answer = small.post("/calculate", content=b'{"answers": {}}', headers=_as("anna"))
    assert answer.status_code == 413


def test_fastapi_router_matches_starlette() -> None:
    fastapi = pytest.importorskip("fastapi")
    from auditcore_dataprotection.web import create_router

    app = fastapi.FastAPI()
    app.include_router(create_router(_api(), identify=_identify, prefix="/api/dp"))
    client = TestClient(app)
    assert client.get("/api/dp/profile", headers=_as("anna")).json()["contract"] == CONTRACT
    assert client.get("/api/dp/register").status_code == 401


def _contract(name: str) -> dict[str, Any] | None:
    for parent in Path(__file__).resolve().parents:
        path = parent / "contracts" / "common-cases" / f"{name}.json"
        if path.is_file():
            return dict(json.loads(path.read_text(encoding="utf-8")))
    return None


def test_csv_helpers_follow_the_shared_contracts() -> None:
    cells, documents = _contract("csv-cell"), _contract("csv-document")
    if cells is None or documents is None:
        pytest.skip("contracts/common-cases liegt nur im Monorepo")
    for case in cells["cases"]:
        assert csv_cell(case["input"]["value"]) == case["expect"]["value"], case["id"]
    for case in documents["cases"]:
        assert csv_document(case["input"]["rows"]) == case["expect"]["value"], case["id"]
    assert csv_cell(True) == "ja" and csv_cell("\r=1") == '"\'\r=1"'
