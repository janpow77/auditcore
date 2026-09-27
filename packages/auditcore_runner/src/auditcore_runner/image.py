"""Runner image: version check against GitHub's runner releases and rebuild.

GitHub only accepts registrations from runner v2.329.0 on, and a runner must
follow a new release within 30 days. ``check`` reports the image's version,
the latest release and the deadline; ``build_command`` rebuilds the image on
the digest-pinned base of a given release.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib.resources import files

from . import github

MINIMUM_VERSION = (2, 329, 0)
GRACE = timedelta(days=30)
BASE_IMAGE = "ghcr.io/actions/actions-runner"
LISTENER = re.compile(r'"Runner\.Listener/(\d+)\.(\d+)\.(\d+)"')
VERSION_FILE = "/home/runner/bin/Runner.Listener.deps.json"


def parse_version(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def text_version(version: tuple[int, int, int] | None) -> str:
    return ".".join(map(str, version)) if version else "unbekannt"


def image_version(image: str) -> tuple[int, int, int] | None:
    """Runner version inside a local image (reads the listener's deps file)."""
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--entrypoint", "cat", image, VERSION_FILE],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = LISTENER.search(result.stdout)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


@dataclass(frozen=True)
class Release:
    version: tuple[int, int, int]
    published: datetime


def latest_release(client: github.Client) -> Release:
    data = client.get("repos/actions/runner/releases/latest")
    if not isinstance(data, dict):
        raise github.GitHubError("unerwartete Antwort zu actions/runner")
    version = parse_version(str(data.get("tag_name", "")))
    published = str(data.get("published_at", ""))
    if version is None or not published:
        raise github.GitHubError("Runner-Release ohne Version")
    return Release(version, datetime.fromisoformat(published.replace("Z", "+00:00")))


@dataclass(frozen=True)
class VersionStatus:
    current: tuple[int, int, int] | None
    latest: Release | None
    now: datetime

    @property
    def state(self) -> str:
        """``aktuell``, ``frist`` (update due before deadline), ``abgelaufen`` or ``unbekannt``."""
        if self.current is None:
            return "unbekannt"
        if self.current < MINIMUM_VERSION:
            return "abgelaufen"
        if self.latest is None or self.current >= self.latest.version:
            return "aktuell"
        return "abgelaufen" if self.now >= self.latest.published + GRACE else "frist"

    def as_dict(self) -> dict[str, object]:
        return {
            "image_version": text_version(self.current),
            "neueste_version": text_version(self.latest.version) if self.latest else None,
            "frist_bis": (self.latest.published + GRACE).date().isoformat() if self.latest else None,
            "mindestversion": text_version(MINIMUM_VERSION),
            "zustand": self.state,
        }


def base_digest(version: tuple[int, int, int]) -> str:
    """Pull the release tag and return its pinned ``repo@sha256:…`` reference."""
    tag = f"{BASE_IMAGE}:{text_version(version)}"
    subprocess.run(["docker", "pull", "-q", tag], capture_output=True, timeout=1800, check=True)
    result = subprocess.run(
        ["docker", "image", "inspect", tag, "--format", "{{json .RepoDigests}}"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    digests = json.loads(result.stdout)
    pinned = next((d for d in digests if d.startswith(BASE_IMAGE)), "")
    if not pinned:
        raise RuntimeError(f"kein Digest für {tag}")
    return str(pinned)


def build_command(image: str, base: str) -> list[str]:
    context = str(files("auditcore_runner").joinpath("data"))
    return ["docker", "build", "--pull", "--build-arg", f"BASE={base}", "-t", image, context]
