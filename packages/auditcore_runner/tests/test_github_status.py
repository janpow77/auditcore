from __future__ import annotations

import json
import os
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


def test_waiting_job_on_second_page_of_running_workflow(workstation: Profile) -> None:
    def fetch(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
        if "status=queued" in url:
            data = {"workflow_runs": [{"id": 11}]}
        elif "status=in_progress" in url:
            data = {"workflow_runs": [{"id": 11}, {"id": 22}]}
        elif "/11/jobs" in url or "page=2" in url:
            data = {"jobs": [{"status": "queued", "labels": ["cpu-gross"]}]}
        else:
            data = {"jobs": [{"status": "completed"}] * 100}
        return 200, {}, json.dumps(data).encode()

    totals = github.queued_by_repo(github.Client("t", fetch), workstation)
    assert totals and all(values == {"cpu-gross": 2} for values in totals.values())


def test_repo_pool_routes_toward_the_larger_matching_queue(workstation: Profile) -> None:
    target = replace(
        workstation.target,
        name="owner/auditcore",
        watched_repos=("owner/flow-agent",),
    )
    profile = replace(workstation, target=target)

    def fetch(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
        if "/actions/runs?" in url:
            run_id = 11 if "owner/auditcore" in url else 22
            payload = {"workflow_runs": [{"id": run_id}]}
        elif "/runs/11/jobs?" in url:
            payload = {"jobs": [{"status": "queued", "labels": ["self-hosted", "auditcore", "cpu-gross"]}]}
        elif "/runs/22/jobs?" in url:
            payload = {
                "jobs": [
                    {"status": "queued", "labels": ["self-hosted", "auditcore", "cpu-gross"]},
                    {"status": "queued", "labels": ["self-hosted", "auditcore", "cpu-gross"]},
                ]
            }
        else:
            payload = {}
        return 200, {}, json.dumps(payload).encode()

    client = github.Client("t", fetch)
    assert github.queued_by_repo(client, profile) == {
        "owner/auditcore": {"cpu-gross": 1},
        "owner/flow-agent": {"cpu-gross": 2},
    }
    assert github.registration_base(client, profile, "cpu-gross", "cpu-gross-1") == "repos/owner/flow-agent"


def test_empty_repo_pool_spreads_slots_deterministically(workstation: Profile) -> None:
    target = replace(
        workstation.target,
        name="owner/auditcore",
        watched_repos=("owner/flow-agent",),
    )
    profile = replace(workstation, target=target)
    client = github.Client("t", lambda method, url, headers, body: (200, {}, b'{"workflow_runs":[]}'))
    first = github.registration_base(client, profile, "cpu-gross", "cpu-gross-1")
    second = github.registration_base(client, profile, "cpu-gross", "cpu-gross-2")
    assert first == github.registration_base(client, profile, "cpu-gross", "cpu-gross-1")
    assert {first, second} == {"repos/owner/auditcore", "repos/owner/flow-agent"}


def test_cached_repo_routing_reuses_a_fresh_queue_snapshot(
    workstation: Profile, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = replace(workstation.target, name="owner/auditcore", watched_repos=("owner/flow-agent",))
    profile = replace(workstation, target=target)
    monkeypatch.setattr(github, "state_dir", lambda: tmp_path)
    calls: list[str] = []

    def fetch(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
        calls.append(url)
        if "/actions/runs?" in url:
            run_id = 11 if "owner/auditcore" in url else 22
            payload = {"workflow_runs": [{"id": run_id}]}
        elif "/runs/11/jobs?" in url or "/runs/22/jobs?" in url:
            payload = {"jobs": [{"status": "queued", "labels": ["self-hosted", "cpu-gross"]}]}
        else:
            payload = {}
        return 200, {}, json.dumps(payload).encode()

    client = github.Client("t", fetch)
    first = github.cached_registration_base(client, profile, "cpu-gross", "slot-1")
    call_count = len(calls)
    second = github.cached_registration_base(client, profile, "cpu-gross", "slot-1")

    assert first == second == "repos/owner/auditcore"
    github.cached_registration_base(client, profile, "gpu-16gb", "slot-2")
    assert any("status=in_progress" in url for url in calls)
    assert call_count > 0 and len(calls) == call_count
    cache = next((tmp_path / "routing").glob("*.json"))
    assert cache.stat().st_mode & 0o777 == 0o600


def test_cached_repo_routing_refreshes_stale_queue_snapshot(
    workstation: Profile, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from auditcore_runner.profile_io import content_hash

    target = replace(workstation.target, name="owner/auditcore", watched_repos=("owner/flow-agent",))
    profile = replace(workstation, target=target)
    monkeypatch.setattr(github, "state_dir", lambda: tmp_path)
    cache_dir = tmp_path / "routing"
    cache_dir.mkdir()
    cache = cache_dir / f"{content_hash(profile)}.json"
    cache.write_text('{"owner/auditcore":{"cpu-gross":99},"owner/flow-agent":{"cpu-gross":0}}', encoding="utf-8")
    os.utime(cache, (0, 0))

    def fetch(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
        if "/actions/runs?" in url:
            payload = {"workflow_runs": [{"id": 11 if "owner/auditcore" in url else 22}]}
        elif "/runs/11/jobs?" in url:
            payload = {"jobs": [{"status": "queued", "labels": ["self-hosted", "cpu-gross"]}]}
        elif "/runs/22/jobs?" in url:
            payload = {}
        else:
            payload = {}
        return 200, {}, json.dumps(payload).encode()

    selected = github.cached_registration_base(github.Client("t", fetch), profile, "cpu-gross", "slot-1")

    assert selected == "repos/owner/auditcore"
    refreshed = json.loads(cache.read_text(encoding="utf-8"))
    assert refreshed["owner/auditcore"]["cpu-gross"] == 1


def test_org_routing_uses_one_registration_scope(workstation: Profile) -> None:
    target = replace(workstation.target, scope="org", name="flowaudit-ai", watched_repos=("owner/auditcore",))
    profile = replace(workstation, target=target)
    client = github.Client("t", lambda *args: (_ for _ in ()).throw(AssertionError("no queue fetch for org")))

    assert github.registration_base(client, profile, "cpu-gross", "slot-1") == "orgs/flowaudit-ai"
    assert github.cached_registration_base(client, profile, "cpu-gross", "slot-1") == "orgs/flowaudit-ai"


def test_repo_routing_falls_back_when_cache_storage_is_unavailable(
    workstation: Profile, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = replace(workstation.target, name="owner/auditcore", watched_repos=("owner/flow-agent",))
    profile = replace(workstation, target=target)
    monkeypatch.setattr(github, "state_dir", lambda: Path("/dev/null"))

    def fetch(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
        payload = {"workflow_runs": []} if "/actions/runs?" in url else {}
        return 200, {}, json.dumps(payload).encode()

    selected = github.cached_registration_base(github.Client("t", fetch), profile, "cpu-gross", "slot-1")

    assert selected == "repos/owner/auditcore"


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
