"""Minimal GitHub REST client: credentials, runners and queued jobs per label.

Credentials are read from files named in the profile (fine-grained PAT or
GitHub App private key) or from ``gh auth token``; they are never stored in
the profile. GET requests use ETag/If-None-Match, so unchanged answers do not
count against the rate limit.
"""

from __future__ import annotations

import http.client
import json
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from .profile import Auth, Profile, Target, expand

API_HOST = "api.github.com"
# (method, path, headers, body) → (status, response headers, body)
Fetch = Callable[[str, str, dict[str, str], bytes | None], tuple[int, dict[str, str], bytes]]


class GitHubError(RuntimeError):
    """A GitHub call failed; the message is safe to show (no token)."""


def _https(method: str, path: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
    """One request to the fixed GitHub API host over TLS."""
    connection = http.client.HTTPSConnection(API_HOST, timeout=20)
    try:
        connection.request(method, path, body=body, headers={"User-Agent": "auditcore-runner", **headers})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    except OSError as error:
        raise GitHubError(f"GitHub nicht erreichbar: {type(error).__name__}") from error
    finally:
        connection.close()


def _app_token(auth: Auth, fetch: Fetch) -> str:
    """Installation token of a GitHub App (needs the optional ``PyJWT[crypto]``)."""
    try:
        import jwt
    except ImportError as error:  # pragma: no cover - depends on optional extra
        raise GitHubError("GitHub App braucht das Extra auditcore_runner[github-app]") from error
    key = expand(auth.app_key_file).read_text(encoding="utf-8")
    now = int(time.time())
    assertion = jwt.encode({"iat": now - 60, "exp": now + 540, "iss": str(auth.app_id)}, key, algorithm="RS256")
    status, _, body = fetch(
        "POST",
        f"/app/installations/{auth.installation_id}/access_tokens",
        {"Authorization": f"Bearer {assertion}", "Accept": "application/vnd.github+json"},
        None,
    )
    if status != 201:
        raise GitHubError(f"App-Token: HTTP {status}")
    return str(json.loads(body)["token"])


def resolve_token(auth: Auth, fetch: Fetch = _https) -> str:
    """Token for API calls according to the profile's auth kind."""
    if auth.kind == "pat":
        return expand(auth.token_file).read_text(encoding="utf-8").strip()
    if auth.kind == "app":
        return _app_token(auth, fetch)
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitHubError("gh ist nicht verfügbar") from error
    if result.returncode != 0 or not result.stdout.strip():
        raise GitHubError("gh ist nicht angemeldet (gh auth login)")
    return result.stdout.strip()


@dataclass
class Client:
    token: str
    fetch: Fetch = _https
    etags: dict[str, tuple[str, object]] = field(default_factory=dict)
    remaining: int | None = None

    def get(self, path: str) -> object:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        cached = self.etags.get(path)
        if cached:
            headers["If-None-Match"] = cached[0]
        status, response_headers, body = self.fetch("GET", f"/{path}", headers, None)
        lowered = {k.lower(): v for k, v in response_headers.items()}
        if lowered.get("x-ratelimit-remaining", "").isdigit():
            self.remaining = int(lowered["x-ratelimit-remaining"])
        if status == 304 and cached:
            return cached[1]
        if status != 200:
            raise GitHubError(f"GET {path}: HTTP {status}")
        data: object = json.loads(body)
        if "etag" in lowered:
            self.etags[path] = (lowered["etag"], data)
        return data


@dataclass(frozen=True)
class RunnerInfo:
    runner_id: int
    name: str
    online: bool
    busy: bool
    labels: tuple[str, ...]


def _objects(data: object, key: str) -> list[dict[str, object]]:
    items = data.get(key, []) if isinstance(data, dict) else []
    return (
        [cast(dict[str, object], item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []
    )


def _label_names(item: dict[str, object]) -> tuple[str, ...]:
    labels = item.get("labels", [])
    if not isinstance(labels, list):
        return ()
    names = [x.get("name") if isinstance(x, dict) else x for x in labels]
    return tuple(str(name) for name in names if name)


def list_runners(client: Client, target: Target) -> list[RunnerInfo]:
    data = client.get(f"{target.api_base}/actions/runners?per_page=100")
    return [
        RunnerInfo(
            runner_id=int(str(item.get("id", 0))),
            name=str(item.get("name", "")),
            online=item.get("status") == "online",
            busy=bool(item.get("busy")),
            labels=_label_names(item),
        )
        for item in _objects(data, "runners")
    ]


def class_of(labels: tuple[str, ...], profile: Profile) -> str | None:
    """The profile class whose labels a job requests (all job labels must match)."""
    wanted = set(labels)
    for name, settings in sorted(profile.classes.items()):
        if wanted and wanted <= set(settings.labels):
            return name
    return None


def queued_by_class(client: Client, profile: Profile) -> dict[str, int]:
    """Waiting jobs that one of this machine's classes could take."""
    counts: dict[str, int] = {}
    for repo in profile.target.queue_repos:
        runs = client.get(f"repos/{repo}/actions/runs?status=queued&per_page=50")
        for run in _objects(runs, "workflow_runs"):
            jobs = client.get(f"repos/{repo}/actions/runs/{run.get('id')}/jobs?filter=latest&per_page=100")
            for job in _objects(jobs, "jobs"):
                name = class_of(_label_names(job), profile) if job.get("status") == "queued" else None
                if name:
                    counts[name] = counts.get(name, 0) + 1
    return counts


def busy_by_class(runners: list[RunnerInfo], profile: Profile, prefix: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for runner in runners:
        if not runner.busy or not runner.name.startswith(prefix):
            continue
        name = class_of(runner.labels, profile)
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts
