"""Client for GitHub's runner scale set API (backend ``scaleset``).

A Python re-implementation of the protocol spoken by the MIT-licensed
reference client ``github.com/actions/scaleset`` (commit ``e6daac7``, see
``LICENSES/actions-scaleset-MIT.txt``); no code is copied. The API version is
pinned (:data:`API_VERSION`).

Flow: a registration token (GitHub REST) buys an admin connection to the
Actions service (``/actions/runner-registration``); with it the client finds
or creates one scale set per runner class, opens a message session and
long-polls the session's queue. Every message carries statistics, of which
``totalAssignedJobs`` drives the demand; each message is deleted after it was
handled. Runners get a JIT configuration from the scale set.

Tokens only travel to ``api.github.com`` and to hosts below
``actions.githubusercontent.com`` over TLS; they are never logged.
"""

from __future__ import annotations

import base64
import http.client
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast
from urllib.parse import quote, urlencode, urlsplit

from . import github
from .profile import Target

API_VERSION = "6.0-preview"
REFERENCE = "actions/scaleset@e6daac702355cdb5b880b4fbdcf6d85dcd9e48e5"
SCALE_SETS = "_apis/runtime/runnerscalesets"
RUNNERS = "_apis/distributedtask/pools/0/agents"
MAX_CAPACITY_HEADER = "X-ScaleSetMaxCapacity"
TRUSTED_SUFFIX = ".actions.githubusercontent.com"
LONG_POLL_SECONDS = 70

# (method, url, headers, body) → (status, body)
Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, bytes]]


class ScaleSetError(github.GitHubError):
    """A scale set call failed; the message never contains a token."""


class SessionExpiredError(ScaleSetError):
    """The message queue token expired (HTTP 401); refresh the session."""


def check_url(url: str) -> None:
    """Only TLS to GitHub's API or the Actions service may receive a token."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme != "https" or not (host == github.API_HOST or host.endswith(TRUSTED_SUFFIX)):
        raise ScaleSetError(f"unerwartete Adresse für die Scale-Set-API: {parts.scheme}://{host}")


def https(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, bytes]:
    check_url(url)
    parts = urlsplit(url)
    connection = http.client.HTTPSConnection(parts.hostname or "", parts.port, timeout=LONG_POLL_SECONDS)
    target = parts.path + (f"?{parts.query}" if parts.query else "")
    try:
        connection.request(method, target, body=body, headers={"User-Agent": "auditcore-runner", **headers})
        response = connection.getresponse()
        return response.status, response.read()
    except OSError as error:
        raise ScaleSetError(f"Scale-Set-API nicht erreichbar: {type(error).__name__}") from error
    finally:
        connection.close()


@dataclass(frozen=True)
class Statistics:
    available: int = 0
    acquired: int = 0
    assigned: int = 0
    running: int = 0
    registered: int = 0
    busy: int = 0
    idle: int = 0

    @classmethod
    def parse(cls, data: object) -> Statistics:
        values = data if isinstance(data, dict) else {}

        def number(key: str) -> int:
            value = values.get(key, 0)
            return value if isinstance(value, int) and value >= 0 else 0

        return cls(
            number("totalAvailableJobs"),
            number("totalAcquiredJobs"),
            number("totalAssignedJobs"),
            number("totalRunningJobs"),
            number("totalRegisteredRunners"),
            number("totalBusyRunners"),
            number("totalIdleRunners"),
        )

    @property
    def waiting(self) -> int:
        """Jobs assigned to the scale set that no runner has started yet."""
        return max(self.assigned - self.running, 0)

    def as_dict(self) -> dict[str, int]:
        return {
            "verfuegbar": self.available,
            "angenommen": self.acquired,
            "zugewiesen": self.assigned,
            "laufend": self.running,
            "runner_registriert": self.registered,
            "runner_belegt": self.busy,
            "runner_frei": self.idle,
        }


@dataclass(frozen=True)
class Message:
    message_id: int
    statistics: Statistics
    job_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class Session:
    session_id: str
    queue_url: str
    queue_token: str
    statistics: Statistics


@dataclass(frozen=True)
class AdminConnection:
    url: str
    token: str
    expires_at: float


def parse_message(body: bytes) -> Message:
    data = json.loads(body)
    if not isinstance(data, dict) or data.get("messageType") != "RunnerScaleSetJobMessages":
        raise ScaleSetError("unbekannter Nachrichtentyp der Scale-Set-Warteschlange")
    batch = json.loads(data["body"]) if data.get("body") else []
    types = tuple(str(item.get("messageType", "")) for item in batch if isinstance(item, dict))
    return Message(int(data.get("messageId", 0)), Statistics.parse(data.get("statistics")), types)


def parse_session(body: bytes) -> Session:
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ScaleSetError("ungültige Sitzungsantwort")
    queue_url = str(data.get("messageQueueUrl", ""))
    check_url(queue_url)
    return Session(
        str(data.get("sessionId", "")),
        queue_url,
        str(data.get("messageQueueAccessToken", "")),
        Statistics.parse(data.get("statistics")),
    )


def token_expiry(token: str) -> float:
    """``exp`` of an (unverified) JWT; 0 when it cannot be read."""
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return float(claims.get("exp", 0))
    except (IndexError, ValueError, AttributeError):
        return 0.0


def _id(data: object) -> int:
    value = data.get("id") if isinstance(data, dict) else None
    if not isinstance(value, int):
        raise ScaleSetError("Antwort ohne id")
    return value


def config_url(target: Target) -> str:
    return f"https://github.com/{target.name}"


@dataclass
class ScaleSetClient:
    """One target (repository or organisation); tokens stay in memory."""

    target: Target
    github_token: Callable[[], str]
    transport: Transport = https
    clock: Callable[[], float] = time.time
    admin: AdminConnection | None = field(default=None, repr=False)

    def _admin(self) -> AdminConnection:
        if self.admin and self.admin.expires_at - 60 > self.clock():
            return self.admin
        headers = {"Authorization": f"Bearer {self.github_token()}", "Accept": "application/vnd.github+json"}
        path = f"https://{github.API_HOST}/{self.target.api_base}/actions/runners/registration-token"
        status, body = self.transport("POST", path, headers, None)
        if status != 201:
            raise ScaleSetError(f"Registrierungstoken: HTTP {status}")
        registration = str(json.loads(body)["token"])
        payload = json.dumps({"url": config_url(self.target), "runner_event": "register"}).encode()
        headers = {"Authorization": f"RemoteAuth {registration}", "Content-Type": "application/json"}
        status, body = self.transport(
            "POST", f"https://{github.API_HOST}/actions/runner-registration", headers, payload
        )
        data = json.loads(body) if 200 <= status < 300 else {}
        if not data.get("url") or not data.get("token"):
            raise ScaleSetError(f"Actions-Dienst: HTTP {status}")
        check_url(str(data["url"]))
        token = str(data["token"])
        self.admin = AdminConnection(str(data["url"]), token, token_expiry(token) or self.clock() + 600)
        return self.admin

    def _call(self, method: str, path: str, query: dict[str, str] | None = None, payload: object = None) -> object:
        admin = self._admin()
        url = f"{admin.url.rstrip('/')}/{path.lstrip('/')}?{urlencode({**(query or {}), 'api-version': API_VERSION})}"
        headers = {"Authorization": f"Bearer {admin.token}", "Content-Type": "application/json"}
        body = None if payload is None else json.dumps(payload).encode()
        status, response = self.transport(method, url, headers, body)
        if status not in (200, 201, 204):
            raise ScaleSetError(f"{method} {path.split('?')[0]}: HTTP {status}")
        return json.loads(response) if response.strip() else None

    def runner_group_id(self, name: str) -> int:
        data = self._call("GET", "_apis/runtime/runnergroups/", {"groupName": name})
        groups = cast(dict[str, object], data).get("value") if isinstance(data, dict) else None
        if not isinstance(groups, list) or len(groups) != 1:
            raise ScaleSetError(f"Runner-Gruppe {name!r} nicht eindeutig gefunden")
        return _id(groups[0])

    def find_scale_set(self, name: str, group_id: int) -> int | None:
        data = self._call("GET", SCALE_SETS, {"runnerGroupId": str(group_id), "name": name})
        found = cast(dict[str, object], data).get("value") if isinstance(data, dict) else None
        if not isinstance(found, list) or not found:
            return None
        if len(found) > 1:
            raise ScaleSetError(f"mehrere Scale-Sets namens {name!r}")
        return _id(found[0])

    def ensure_scale_set(self, name: str, group_id: int, labels: tuple[str, ...]) -> int:
        """Id of the scale set ``name``; created (ephemeral runners, no self-update) if missing."""
        existing = self.find_scale_set(name, group_id)
        if existing is not None:
            return existing
        payload = {
            "name": name,
            "runnerGroupId": group_id,
            "labels": [{"name": label, "type": "System"} for label in (labels or (name,))],
            "RunnerSetting": {"disableUpdate": True},
        }
        created = self._call("POST", SCALE_SETS, payload=payload)
        return _id(created)

    def delete_scale_set(self, scale_set_id: int) -> None:
        self._call("DELETE", f"{SCALE_SETS}/{scale_set_id}")

    def create_session(self, scale_set_id: int, owner: str) -> Session:
        admin = self._admin()
        url = f"{admin.url.rstrip('/')}/{SCALE_SETS}/{scale_set_id}/sessions?api-version={API_VERSION}"
        headers = {"Authorization": f"Bearer {admin.token}", "Content-Type": "application/json"}
        status, body = self.transport("POST", url, headers, json.dumps({"ownerName": owner}).encode())
        if status == 409:
            raise ScaleSetError("für dieses Scale-Set lauscht bereits eine andere Sitzung")
        if status != 200:
            raise ScaleSetError(f"Sitzung anlegen: HTTP {status}")
        return parse_session(body)

    def refresh_session(self, scale_set_id: int, session: Session) -> Session:
        admin = self._admin()
        path = f"{SCALE_SETS}/{scale_set_id}/sessions/{quote(session.session_id)}"
        url = f"{admin.url.rstrip('/')}/{path}?api-version={API_VERSION}"
        status, body = self.transport("PATCH", url, {"Authorization": f"Bearer {admin.token}"}, None)
        if status != 200:
            raise ScaleSetError(f"Sitzung erneuern: HTTP {status}")
        return parse_session(body)

    def delete_session(self, scale_set_id: int, session: Session) -> None:
        self._call("DELETE", f"{SCALE_SETS}/{scale_set_id}/sessions/{quote(session.session_id)}")

    def get_message(self, session: Session, last_message_id: int, max_capacity: int) -> Message | None:
        """Long-poll; ``None`` when the server timed out without a message (HTTP 202)."""
        separator = "&" if "?" in session.queue_url else "?"
        query = f"{separator}{urlencode({'lastMessageId': last_message_id})}" if last_message_id > 0 else ""
        headers = {
            "Accept": f"application/json; api-version={API_VERSION}",
            "Authorization": f"Bearer {session.queue_token}",
            MAX_CAPACITY_HEADER: str(max(max_capacity, 0)),
        }
        status, body = self.transport("GET", session.queue_url + query, headers, None)
        if status == 202:
            return None
        if status == 401:
            raise SessionExpiredError("Warteschlangen-Token abgelaufen")
        if status != 200:
            raise ScaleSetError(f"Nachricht holen: HTTP {status}")
        return parse_message(body)

    def delete_message(self, session: Session, message_id: int) -> None:
        base, _, query = session.queue_url.partition("?")
        url = f"{base.rstrip('/')}/{message_id}" + (f"?{query}" if query else "")
        headers = {"Authorization": f"Bearer {session.queue_token}", "Content-Type": "application/json"}
        status, _ = self.transport("DELETE", url, headers, None)
        if status == 401:
            raise SessionExpiredError("Warteschlangen-Token abgelaufen")
        if status != 204:
            raise ScaleSetError(f"Nachricht löschen: HTTP {status}")

    def generate_jit(self, scale_set_id: int, runner_name: str) -> tuple[int, str]:
        """(runner id, encoded JIT configuration) for one ephemeral runner."""
        payload = {"name": runner_name, "workFolder": "_work"}
        data = self._call("POST", f"{SCALE_SETS}/{scale_set_id}/generatejitconfig", payload=payload)
        encoded = data.get("encodedJITConfig") if isinstance(data, dict) else None
        if not isinstance(encoded, str) or not isinstance(data, dict):
            raise ScaleSetError("JIT-Antwort ohne Konfiguration")
        return _id(data.get("runner")), encoded

    def remove_runner(self, runner_id: int) -> None:
        self._call("DELETE", f"{RUNNERS}/{runner_id}")
