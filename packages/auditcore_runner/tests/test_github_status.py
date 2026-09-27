from __future__ import annotations

import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import pytest

from auditcore_runner import github, profile_io, status
from auditcore_runner.hardware import HostFacts
from auditcore_runner.profile import Auth, Profile

RUNNERS = {
    "runners": [
        {
            "id": 1,
            "name": "workstation-host1-cpu-gross-1-1",
            "status": "online",
            "busy": True,
            "labels": [{"name": n} for n in ("self-hosted", "linux", "x64", "auditcore", "cpu-gross")],
        },
        {
            "id": 2,
            "name": "server-host2-cpu-3-17904",
            "status": "online",
            "busy": False,
            "labels": [{"name": n} for n in ("self-hosted", "linux", "x64", "auditcore", "cpu")],
        },
        {"id": 3, "name": "fremder-runner", "status": "online", "busy": False, "labels": [{"name": "self-hosted"}]},
    ]
}
RUNS = {"workflow_runs": [{"id": 77}]}
JOBS = {
    "jobs": [
        {"status": "queued", "labels": ["self-hosted", "auditcore", "cpu-gross"]},
        {"status": "in_progress", "labels": ["self-hosted", "auditcore"]},
        {"status": "queued", "labels": ["ubuntu-latest"]},
    ]
}


class FakeGitHub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def __call__(
        self, method: str, url: str, headers: dict[str, str], body: bytes | None
    ) -> tuple[int, dict[str, str], bytes]:
        etag = headers.get("If-None-Match")
        self.calls.append((url, etag))
        if etag == '"v1"':
            return 304, {}, b""
        for key, body in (("runners", RUNNERS), ("jobs", JOBS), ("runs?status", RUNS)):
            if key in url:
                return 200, {"ETag": '"v1"', "X-RateLimit-Remaining": "4999"}, json.dumps(body).encode()
        return 404, {}, b"{}"


@pytest.fixture
def workstation() -> Profile:
    text = files("auditcore_runner").joinpath("data", "beispiele", "workstation-2gpu.json").read_text(encoding="utf-8")
    return profile_io.from_json(json.loads(text))


def test_etag_cache_and_rate_limit(workstation: Profile) -> None:
    fake = FakeGitHub()
    client = github.Client("t", fake)
    first = github.list_runners(client, workstation.target)
    second = github.list_runners(client, workstation.target)
    assert first == second and fake.calls[1][1] == '"v1"' and client.remaining == 4999


def test_queue_and_busy_by_class(workstation: Profile) -> None:
    client = github.Client("t", FakeGitHub())
    assert github.queued_by_class(client, workstation) == {"cpu-gross": 1}
    runners = github.list_runners(client, workstation.target)
    assert github.busy_by_class(runners, workstation, workstation.runner_prefix()) == {"cpu-gross": 1}


def test_http_error_raises_without_token(workstation: Profile) -> None:
    client = github.Client("geheim", lambda method, url, headers, body: (401, {}, b""))
    with pytest.raises(github.GitHubError) as error:
        github.list_runners(client, workstation.target)
    assert "geheim" not in str(error.value)


def test_pat_token_from_file(tmp_path: Path) -> None:
    token = tmp_path / "token"
    token.write_text("abc\n", encoding="utf-8")
    assert github.resolve_token(Auth("pat", token_file=str(token))) == "abc"


def test_status_and_prometheus(
    workstation: Profile, workstation_facts: HostFacts, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(status.install, "image_present", lambda image: True)
    monkeypatch.setattr(status.install, "network_present", lambda name: False)
    monkeypatch.setattr(status, "active_instances", lambda name: 2)
    current = status.collect(workstation, workstation_facts, github.Client("t", FakeGitHub()))
    assert current["unbekannte_runner"] == ["fremder-runner", "server-host2-cpu-3-17904"]
    known = replace(workstation, target=replace(workstation.target, known_runner_prefixes=("server-",)))
    assert status.unknown_runners(known, github.list_runners(github.Client("t", FakeGitHub()), known.target)) == [
        "fremder-runner"
    ]
    classes = current["klassen"]
    assert (
        isinstance(classes, dict) and classes["cpu-gross"]["registriert"] == 1 and classes["cpu-gross"]["belegt"] == 1
    )
    text = status.prometheus(current)
    assert 'auditcore_runner_instances{rechner="workstation",klasse="cpu-gross",zustand="max"} 3' in text
    assert 'auditcore_runner_unknown_registered{rechner="workstation"} 2' in text
    assert current["profil_version"] == 0 and current["sync"] == "aus" and len(str(current["profil_hash"])) == 16
    path = status.write(current)
    assert json.loads(path.read_text(encoding="utf-8"))["schema"] == "auditcore-runner/status/1"


def test_status_without_github(
    workstation: Profile, workstation_facts: HostFacts, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(status.install, "image_present", lambda image: False)
    monkeypatch.setattr(status.install, "network_present", lambda name: False)
    monkeypatch.setattr(status, "active_instances", lambda name: 0)
    current = status.collect(workstation, workstation_facts, None)
    assert current["unbekannte_runner"] is None and current["klassen"]["cpu-gross"]["registriert"] is None  # type: ignore[index]
