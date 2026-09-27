"""In-memory stand-in for GitHub's registration endpoints and the Actions scale set service."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit

SERVICE = "https://pipelines.example.actions.githubusercontent.com/tenant"
QUEUE = "https://broker.actions.githubusercontent.com/message?sessionId=s-1"


def jwt(expires: int) -> str:
    claims = base64.urlsafe_b64encode(json.dumps({"exp": expires}).encode()).decode().rstrip("=")
    return f"e30.{claims}.sig"


@dataclass
class FakeActions:
    """Records every request; answers like the real services for the calls the client makes."""

    admin_expires: int = 2_000_000_000
    scale_sets: dict[str, int] = field(default_factory=dict)
    messages: list[dict[str, object]] = field(default_factory=list)
    queue_token: str = "queue-1"
    expire_queue_once: bool = False
    session_conflict: bool = False
    calls: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)
    deleted_messages: list[int] = field(default_factory=list)
    removed_runners: list[int] = field(default_factory=list)
    deleted_sessions: int = 0

    def __call__(self, method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, bytes]:
        self.calls.append((method, url, headers))
        parts = urlsplit(url)
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        if parts.hostname == "api.github.com":
            return self._github(parts.path, headers)
        if parts.hostname == "broker.actions.githubusercontent.com":
            return self._queue(method, parts.path, headers)
        assert query.get("api-version") == "6.0-preview", url
        assert headers["Authorization"] == f"Bearer {jwt(self.admin_expires)}"
        return self._service(method, parts.path.removeprefix("/tenant/"), query, body)

    def _github(self, path: str, headers: dict[str, str]) -> tuple[int, bytes]:
        if path.endswith("/actions/runners/registration-token"):
            assert headers["Authorization"] == "Bearer gh-token"
            return 201, json.dumps({"token": "reg-1"}).encode()
        assert path == "/actions/runner-registration" and headers["Authorization"] == "RemoteAuth reg-1"
        return 201, json.dumps({"url": SERVICE, "token": jwt(self.admin_expires)}).encode()

    def _service(self, method: str, path: str, query: dict[str, str], body: bytes | None) -> tuple[int, bytes]:
        payload = json.loads(body) if body else None
        if path == "_apis/runtime/runnergroups/":
            return 200, json.dumps({"count": 1, "value": [{"id": 7, "name": query["groupName"]}]}).encode()
        if path == "_apis/runtime/runnerscalesets" and method == "GET":
            found = [{"id": i, "name": n} for n, i in self.scale_sets.items() if n == query["name"]]
            return 200, json.dumps({"count": len(found), "value": found}).encode()
        if path == "_apis/runtime/runnerscalesets" and method == "POST":
            assert isinstance(payload, dict) and payload["RunnerSetting"] == {"disableUpdate": True}
            self.scale_sets[payload["name"]] = 100 + len(self.scale_sets)
            return 200, json.dumps({"id": self.scale_sets[payload["name"]], "name": payload["name"]}).encode()
        return self._scale_set_item(method, path, payload)

    def _scale_set_item(self, method: str, path: str, payload: object) -> tuple[int, bytes]:
        tail = path
        if tail.endswith("/sessions") and method == "POST":
            return (409, b"{}") if self.session_conflict else (200, self._session())
        if "/sessions/" in tail and method == "PATCH":
            self.queue_token = "queue-2"
            return 200, self._session()
        if "/sessions/" in tail and method == "DELETE":
            self.deleted_sessions += 1
            return 204, b""
        if tail.endswith("/generatejitconfig"):
            assert isinstance(payload, dict) and payload["workFolder"] == "_work"
            return 200, json.dumps(
                {"runner": {"id": 555, "name": payload["name"]}, "encodedJITConfig": "ZW5j"}
            ).encode()
        if path.startswith("_apis/distributedtask/pools/0/agents/") and method == "DELETE":
            self.removed_runners.append(int(path.rsplit("/", 1)[1]))
            return 204, b""
        if method == "DELETE" and path.startswith("_apis/runtime/runnerscalesets/"):
            return 204, b""
        return 404, b"{}"

    def _session(self) -> bytes:
        return json.dumps(
            {
                "sessionId": "s-1",
                "messageQueueUrl": QUEUE,
                "messageQueueAccessToken": self.queue_token,
                "statistics": {"totalAssignedJobs": 1, "totalRunningJobs": 0},
            }
        ).encode()

    def _queue(self, method: str, path: str, headers: dict[str, str]) -> tuple[int, bytes]:
        if self.expire_queue_once:
            self.expire_queue_once = False
            return 401, b""
        assert headers["Authorization"] == f"Bearer {self.queue_token}"
        if method == "DELETE":
            self.deleted_messages.append(int(path.rsplit("/", 1)[1]))
            return 204, b""
        assert "X-ScaleSetMaxCapacity" in headers
        if not self.messages:
            return 202, b""
        return 200, json.dumps(self.messages.pop(0)).encode()


def message(message_id: int, assigned: int, running: int = 0, jobs: tuple[str, ...] = ()) -> dict[str, object]:
    return {
        "messageId": message_id,
        "messageType": "RunnerScaleSetJobMessages",
        "statistics": {"totalAssignedJobs": assigned, "totalRunningJobs": running},
        "body": json.dumps([{"messageType": kind, "runnerRequestId": 1} for kind in jobs]),
    }
