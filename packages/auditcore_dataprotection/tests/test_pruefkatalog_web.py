"""REST-Schnittstelle des Wizards, der Checkliste und der Betriebsentscheidung (LIB-23, T-17)."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from pruefkatalog_support import ROLES, cover, full_activity, hdsig  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_dataprotection import Actor  # noqa: E402
from auditcore_dataprotection.memory import FixedClock, RoleAuthorizer, SequentialIds  # noqa: E402
from auditcore_dataprotection.memory_records import (  # noqa: E402
    FakeCentralRegister,
    InMemoryOperationRepository,
    InMemoryTransferRepository,
)
from auditcore_dataprotection.web import (  # noqa: E402
    DataProtectionApi,
    InMemoryStorage,
    Principal,
    create_app,
    create_backend,
)

JSON = {"Content-Type": "application/json"}


def _identify(request: Request) -> Principal | None:
    person = request.headers.get("X-Person", "")
    role = request.headers.get("X-Role", "")
    if not person or role not in ROLES:
        return None
    return Principal("behoerde", Actor(person, frozenset({"behoerde"}), frozenset({role})))


@pytest.fixture
def client() -> TestClient:
    backend = create_backend(
        hdsig(),
        InMemoryStorage(),
        RoleAuthorizer(ROLES),
        clock=FixedClock(),
        ids=SequentialIds(),
        transfers=InMemoryTransferRepository(),
        decisions=InMemoryOperationRepository(),
        central_port=FakeCentralRegister(),
    )
    return TestClient(create_app(DataProtectionApi(backend), identify=_identify))


def _as(person: str, role: str) -> dict[str, str]:
    return {**JSON, "X-Person": person, "X-Role": role}


def _start(client: TestClient) -> tuple[str, int]:
    saved = client.post(
        "/register/draft",
        json={"content": {**cover(), "taetigkeiten": [full_activity()]}},
        headers=_as("fach", "fach"),
    )
    assert saved.status_code == 200, saved.text
    body: dict[str, Any] = saved.json()
    activity_id = str(body["content"]["taetigkeiten"][0]["id"])
    return activity_id, int(body["revision"])


def test_assistent_und_checkliste_ueber_rest(client: TestClient) -> None:
    activity_id, revision_ = _start(client)
    overview = client.get(f"/activities/{activity_id}/workspace", headers=_as("fach", "fach"))
    assert overview.status_code == 200
    data = overview.json()
    assert data["assistent"]["mode"] == "gefuehrt"
    assert set(data["status"]) == {
        "dokumentation",
        "dsfa_erforderlichkeit",
        "dsfa_bearbeitung",
        "konsultation",
        "zentrale_uebernahme",
        "betriebsentscheidung",
    }
    assert "compliant" not in str(data)
    answered = client.post(
        f"/activities/{activity_id}/answers",
        json={"question_id": "5.6", "value": "unklar", "expected_revision": revision_},
        headers=_as("fach", "fach"),
    )
    assert answered.status_code == 200, answered.text
    tasks = answered.json()["assistent"]["tasks"]
    assert {"step": "W05", "question": "5.6", "kind": "unklar", "number": "5.6"} in tasks
    stale = client.post(
        f"/activities/{activity_id}/answers",
        json={"question_id": "5.6", "value": "ja", "expected_revision": revision_},
        headers=_as("fach", "fach"),
    )
    assert stale.status_code == 409
    item = client.post(
        f"/activities/{activity_id}/checklist/CHK-16",
        json={"status": "nachgewiesen", "expected_revision": revision_ + 1},
        headers=_as("fach", "fach"),
    )
    assert item.status_code == 422
    assert "konkreten Nachweis" in item.json()["error"]["message"]


def test_betriebsentscheidung_serverseitig_gesperrt(client: TestClient) -> None:
    activity_id, revision_ = _start(client)
    client.post(
        "/register/release", json={"expected_revision": revision_}, headers=_as("l", "leitung")
    )
    body = {
        "outcome": "fuer_definierten_umfang_erteilt",
        "environment": "produktion",
        "scope": "Pilot",
        "justification": "Begründung der Entscheidung mit ausreichender Länge für den Test.",
    }
    path = f"/activities/{activity_id}/operation"
    assert client.post(path, json=body, headers=_as("dev", "entwicklung")).status_code == 403
    assert client.post(path, json=body, headers=_as("root", "admin")).status_code == 403
    gated = client.post(path, json=body, headers=_as("chef", "entscheidung"))
    assert gated.status_code == 409
    assert "GATE-03" in gated.json()["error"]["message"]


def test_uebertragung_idempotent_ueber_rest(client: TestClient) -> None:
    _, revision_ = _start(client)
    client.post(
        "/register/release", json={"expected_revision": revision_}, headers=_as("l", "leitung")
    )
    first = client.post("/register/transfer", json={}, headers=_as("l", "leitung"))
    second = client.post("/register/transfer", json={}, headers=_as("l", "leitung"))
    assert first.status_code == 200, first.text
    assert first.json() == second.json()
    assert first.json()["status"] == "uebernommen"
    pattern = client.post("/register/public-pattern", json={}, headers=_as("l", "leitung"))
    assert pattern.status_code == 403
    allowed = client.post("/register/public-pattern", json={}, headers=_as("root", "admin"))
    assert allowed.status_code == 200
    assert "Beispielbehörde" not in allowed.text


def test_alle_arbeitsbereichs_endpunkte(client: TestClient) -> None:
    fach = _as("fach", "fach")
    created = client.post("/activities", json={"name": "Neue Tätigkeit"}, headers=fach)
    assert created.status_code == 201, created.text
    activity_id, revision_ = _start_existing(created.json())
    base = f"/activities/{activity_id}"
    suggestion = client.post(
        f"{base}/answers",
        json={
            "question_id": "1.3",
            "value": "Vorschlag",
            "origin": "vorlage",
            "expected_revision": revision_,
        },
        headers=fach,
    )
    assert suggestion.status_code == 200, suggestion.text
    revision_ += 1
    confirmed = client.post(
        f"{base}/answers/confirm",
        json={"question_id": "1.3", "expected_revision": revision_},
        headers=fach,
    )
    assert confirmed.status_code == 200
    revision_ += 1
    moved = client.post(
        f"{base}/navigate",
        json={"mode": "frei", "step": "W05", "expected_revision": revision_},
        headers=fach,
    )
    assert moved.json()["assistent"]["current_step"] == "W05"
    revision_ += 1
    records = client.post(
        f"{base}/records",
        json={
            "evidence": [{"id": "E1", "kind": "test", "reference": "Test", "version": "1"}],
            "expected_revision": revision_,
        },
        headers=fach,
    )
    assert records.status_code == 200, records.text
    revision_ += 1
    bad_records = client.post(f"{base}/records", json={"evidence": "x"}, headers=fach)
    assert bad_records.status_code == 400
    item = client.post(
        f"{base}/checklist/CHK-19",
        json={
            "status": "nicht_anwendbar",
            "justification": "x" * 60,
            "owner": "fach",
            "due": "2026-12-31",
            "objection": "",
            "expected_revision": revision_,
        },
        headers=fach,
    )
    assert item.status_code == 200, item.text
    revision_ += 1
    second = client.post(
        f"{base}/checklist/CHK-19/confirm",
        json={"expected_revision": revision_},
        headers=_as("zweite", "fach"),
    )
    assert second.status_code == 200, second.text
    bad_status = client.post(f"{base}/checklist/CHK-19", json={"status": "fertig"}, headers=fach)
    assert bad_status.status_code == 400
    package = client.get(f"{base}/review-package", headers=fach)
    assert package.status_code == 200 and package.json()["art"] == "pruefpaket"
    confirm = client.post(
        "/register/transfer/confirm",
        json={"key": "x", "central_id": "1", "proof": "p"},
        headers=_as("z", "zentral"),
    )
    assert confirm.status_code == 404
    no_release = client.post("/register/transfer", json={}, headers=_as("l", "leitung"))
    assert no_release.status_code == 409
    no_pattern = client.post("/register/public-pattern", json={}, headers=_as("root", "admin"))
    assert no_pattern.status_code == 422
    urgent = client.post(
        f"{base}/operation",
        json={
            "outcome": "abgelehnt",
            "environment": "p",
            "scope": "s",
            "justification": "j" * 60,
            "urgent": {
                "justification": "x",
                "consultation_initiated_on": "2026-01-01",
                "follow_up": "y",
            },
        },
        headers=_as("chef", "entscheidung"),
    )
    assert urgent.status_code == 409  # keine freigegebene Fassung


def _start_existing(overview: dict[str, Any]) -> tuple[str, int]:
    return str(overview["taetigkeit_id"]), int(overview["register"]["revision"])


def test_ohne_konfiguration_klare_fehler() -> None:
    from dataclasses import replace

    backend = create_backend(hdsig(), InMemoryStorage(), RoleAuthorizer(ROLES))
    api = DataProtectionApi(replace(backend, workspace=None))
    who = Principal("behoerde", Actor("fach", frozenset({"behoerde"}), frozenset({"fach"})))
    from auditcore_dataprotection.errors import ConflictError

    for call in (
        lambda: api.work.overview(who, "x"),
        lambda: api.work.transfer(who, {}),
        lambda: api.work.confirm_transfer(who, {"key": "k", "central_id": "c", "proof": "p"}),
        lambda: api.work.decide(who, "x", {}),
    ):
        with pytest.raises(ConflictError):
            call()
