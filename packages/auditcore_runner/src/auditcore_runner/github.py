"""Minimal GitHub REST client: credentials, runners and queued jobs per label.

Credentials are read from files named in the profile (fine-grained PAT or
GitHub App private key) or from ``gh auth token``; they are never stored in
the profile. GET requests use ETag/If-None-Match, so unchanged answers do not
count against the rate limit.
"""

from __future__ import annotations

import http.client
import json
import os
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from .profile import Auth, Profile, Target, expand, state_dir

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


def list_runners(client: Client, target: Target, max_pages: int = 20) -> list[RunnerInfo]:
    """Every registered runner of the target (all pages)."""
    runners: list[RunnerInfo] = []
    for base in target.registration_bases:
        for page in range(1, max_pages + 1):
            items = _objects(client.get(f"{base}/actions/runners?per_page=100&page={page}"), "runners")
            runners += [
                RunnerInfo(
                    runner_id=int(str(item.get("id", 0))),
                    name=str(item.get("name", "")),
                    online=item.get("status") == "online",
                    busy=bool(item.get("busy")),
                    labels=_label_names(item),
                )
                for item in items
            ]
            if len(items) < 100:
                break
    return runners


def class_of(labels: tuple[str, ...], profile: Profile) -> str | None:
    """The profile class whose labels a job requests (all job labels must match)."""
    wanted = set(labels)
    for name, settings in sorted(profile.classes.items()):
        if wanted and wanted <= set(settings.labels):
            return name
    return None


def _pages(client: Client, path: str, key: str) -> Iterator[dict[str, object]]:
    page = 1
    while True:
        items = _objects(client.get(f"{path}&per_page=100&page={page}"), key)
        yield from items
        if len(items) < 100:
            return
        page += 1


def queued_by_repo(client: Client, profile: Profile) -> dict[str, dict[str, int]]:
    """Waiting jobs by repository and runner class for repo-level pool routing."""
    counts: dict[str, dict[str, int]] = {repo: {} for repo in profile.target.queue_repos}
    for repo in profile.target.queue_repos:
        run_ids = set()
        for state in ("queued", "in_progress"):
            runs = _pages(client, f"repos/{repo}/actions/runs?status={state}", "workflow_runs")
            run_ids.update(run["id"] for run in runs if isinstance(run.get("id"), int))
        for run_id in run_ids:
            jobs = _pages(client, f"repos/{repo}/actions/runs/{run_id}/jobs?filter=latest", "jobs")
            for job in jobs:
                name = class_of(_label_names(job), profile) if job.get("status") == "queued" else None
                if name:
                    counts[repo][name] = counts[repo].get(name, 0) + 1
    return counts


def queued_by_class(client: Client, profile: Profile) -> dict[str, int]:
    """Waiting jobs that one of this machine's classes could take."""
    totals: dict[str, int] = {}
    for classes in queued_by_repo(client, profile).values():
        for name, count in classes.items():
            totals[name] = totals.get(name, 0) + count
    return totals


def registration_base(client: Client, profile: Profile, runner_class: str, slot: str) -> str:
    """Choose the repo with the most queued work; spread idle slots deterministically."""
    target = profile.target
    if target.scope == "org":
        return target.api_base
    repos = target.registration_repos
    if len(repos) < 2:
        return target.api_base
    return _registration_base(target, queued_by_repo(client, profile), runner_class, slot)


def cached_registration_base(client: Client, profile: Profile, runner_class: str, slot: str) -> str:
    """Share a short-lived queue snapshot across slots to keep GitHub API use bounded."""
    target = profile.target
    if target.scope == "org" or len(target.registration_repos) < 2:
        return target.api_base
    return _registration_base(target, cached_queued_by_repo(client, profile), runner_class, slot)


def cached_queued_by_repo(client: Client, profile: Profile) -> dict[str, dict[str, int]]:
    """One queue snapshot for registration and capacity reporting."""
    from .profile_io import content_hash

    target = profile.target

    directory = state_dir() / "routing"
    cache_path = directory / f"{content_hash(profile)}.json"
    lock_path = cache_path.with_suffix(".lock")
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with lock_path.open("a", encoding="utf-8") as lock_file:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            counts = _read_queue_cache(cache_path, max(15, 10 * len(target.queue_repos)))
            if counts is not None and (
                set(counts) != set(target.queue_repos)
                or any(
                    not isinstance(count, int) or count < 0 for values in counts.values() for count in values.values()
                )
            ):
                counts = None
            if counts is None:
                counts = queued_by_repo(client, profile)
                temporary = cache_path.with_suffix(f".{os.getpid()}.tmp")
                temporary.write_text(json.dumps(counts, sort_keys=True), encoding="utf-8")
                temporary.chmod(0o600)
                temporary.replace(cache_path)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except (ImportError, OSError):
        counts = queued_by_repo(client, profile)
    return counts


def _read_queue_cache(path: Path, ttl_seconds: int) -> dict[str, dict[str, int]] | None:
    try:
        if time.time() - path.stat().st_mtime > ttl_seconds:
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(raw, dict) or any(not isinstance(value, dict) for value in raw.values()):
        return None
    return cast(dict[str, dict[str, int]], raw)


def _registration_base(target: Target, counts: dict[str, dict[str, int]], runner_class: str, slot: str) -> str:
    repos = target.registration_repos
    busiest = max((classes.get(runner_class, 0) for classes in counts.values()), default=0)
    if busiest:
        candidates = [repo for repo in repos if counts[repo].get(runner_class, 0) == busiest]
        offset = sum(map(ord, slot)) % len(candidates)
        return f"repos/{candidates[offset]}"
    offset = sum(map(ord, slot)) % len(repos)
    return f"repos/{repos[offset]}"


def busy_by_class(runners: list[RunnerInfo], profile: Profile, prefix: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for runner in runners:
        if not runner.busy or not runner.name.startswith(prefix):
            continue
        name = class_of(runner.labels, profile)
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts
