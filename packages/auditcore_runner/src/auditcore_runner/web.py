"""Local web UI: status, settings of this machine and tool switches (stdlib HTTP server).

Security: binds to 127.0.0.1 by default. Changes (POST) are accepted only from
loopback, with the header ``X-Auditcore-Runner: 1`` and a loopback ``Host`` (no
DNS rebinding). An optional second listener (e.g. a Tailscale address) is
strictly read-only.
"""

from __future__ import annotations

import ipaddress
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path

from . import anwenden, install, profile_io, status
from .hardware import HostFacts, detect
from .profile import Profile
from .validation import validate
from .werkzeuge import einstellungen
from .werkzeuge.ausfuehren import Runner, last_result_path
from .werkzeuge.katalog import Registry
from .werkzeuge.modell import DEFAULT_PROFILES, ToolSetting

STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/tokens.css": ("tokens.css", "text/css; charset=utf-8"),
    # Web-Component-Bundle der Gruppe `runner` aus @auditcore/ui (beim Paketbau abgelegt).
    "/runner-elements.js": ("runner-elements.js", "text/javascript; charset=utf-8"),
}
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}
MAX_BODY = 256 * 1024


class RequestError(ValueError):
    def __init__(self, status_code: HTTPStatus, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class App:
    """State shared by all requests."""

    profile_path: Path
    facts: Callable[[], HostFacts] = detect
    apply_enabled: bool = True
    status_cache: tuple[float, dict[str, object]] | None = None
    image_tools: tuple[float, dict[str, str]] | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def profile(self) -> Profile:
        return profile_io.load(self.profile_path)

    def status(self) -> dict[str, object]:
        with self.lock:
            if self.status_cache and time.monotonic() - self.status_cache[0] < 15:
                return self.status_cache[1]
            current = status.collect(self.profile(), self.facts(), None)
            self.status_cache = (time.monotonic(), current)
            return current

    def profile_view(self) -> dict[str, object]:
        current = self.profile()
        problems = validate(current, self.facts())
        return {
            "profil": profile_io.to_json(current),
            "profil_hash": profile_io.content_hash(current),
            "hardware": self.facts().as_dict(),
            "probleme": [p.as_dict() for p in problems],
            "netzsperre_befehl": install.firewall_command() if current.network.enabled else None,
        }

    def _unwrap(self, raw: object) -> tuple[object, int | None]:
        """Body: ``{"profil": {...}, "erwartete_version": n}`` or the bare profile."""
        if isinstance(raw, dict) and "profil" in raw:
            expected = raw.get("erwartete_version")
            return raw["profil"], expected if isinstance(expected, int) and not isinstance(expected, bool) else None
        return raw, None

    def check(self, raw: object) -> dict[str, object]:
        body, _ = self._unwrap(raw)
        try:
            return anwenden.evaluate(body, self.profile_path, self.facts())[1]
        except profile_io.ProfileFormatError as error:
            raise RequestError(HTTPStatus.UNPROCESSABLE_ENTITY, str(error)) from error

    def apply(self, raw: object) -> dict[str, object]:
        body, expected = self._unwrap(raw)
        try:
            result = anwenden.apply(
                body,
                self.profile_path,
                self.facts(),
                source="lokal",
                who="ui",
                expected_version=expected,
                run=self.apply_enabled,
            )
        except profile_io.ProfileFormatError as error:
            raise RequestError(HTTPStatus.UNPROCESSABLE_ENTITY, str(error)) from error
        self.status_cache = None
        if result.get("konflikt"):
            raise RequestError(HTTPStatus.CONFLICT, str(result.get("meldung")))
        return result

    def tools(self) -> dict[str, object]:
        registry = Registry()
        with self.lock:
            if not self.image_tools or time.monotonic() - self.image_tools[0] > 300:
                runner = Runner(Path.cwd(), self.profile().image)
                versions = {name: runner.version(tool) for name, tool in registry.tools.items()}
                self.image_tools = (time.monotonic(), versions)
            versions = self.image_tools[1]
        machine = einstellungen.load()
        return {
            "werkzeuge": [
                {
                    "name": t.name,
                    "bereich": t.area,
                    "installation": t.install,
                    "autofix": t.can_fix,
                    "kosten_minuten": t.cost.minutes,
                    "im_image": versions.get(t.name, ""),
                }
                for t in registry.tools.values()
            ],
            "profile": {
                name: {tool: _setting_json(machine.get(name, {}).get(tool) or p.setting(tool)) for tool in p.tools}
                for name, p in DEFAULT_PROFILES.items()
            },
        }

    def save_tools(self, raw: object) -> dict[str, object]:
        try:
            parsed = einstellungen.parse(raw)
        except einstellungen.ToolSettingsError as error:
            raise RequestError(HTTPStatus.UNPROCESSABLE_ENTITY, str(error)) from error
        einstellungen.save(parsed)
        return {"gespeichert": True}


def last_result() -> dict[str, object]:
    """Last ``lokal`` run including ``gesamt`` (gruen/rot) and ``probleme``; empty before the first run."""
    path = last_result_path()
    if not path.exists():
        return {"gesamt": "unbekannt", "probleme": [], "werkzeuge": [], "befunde": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {"gesamt": "unbekannt"}


def _setting_json(setting: ToolSetting) -> dict[str, object]:
    return {"aktiv": setting.enabled, "zeitlimit_s": setting.timeout_seconds, "prioritaet": setting.priority}


def is_loopback(address: str) -> bool:
    try:
        return ipaddress.ip_address(address).is_loopback
    except ValueError:
        return False


def _host_is_loopback(host_header: str) -> bool:
    host = host_header.rsplit(":", 1)[0].strip("[]")
    return host in {"localhost", "127.0.0.1", "::1"}


class Handler(BaseHTTPRequestHandler):
    """JSON API and static page; ``app`` and ``read_only`` are bound by :func:`make_handler`."""

    server_version = "auditcore-runner"
    app: App
    read_only: bool = True

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - stdlib signature
        return

    def _send(self, code: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in SECURITY_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: HTTPStatus, data: object) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _static(self, name: str, content_type: str) -> None:
        resource = files("auditcore_runner").joinpath("data", "web", name)
        if resource.is_file():
            self._send(HTTPStatus.OK, resource.read_bytes(), content_type)
        else:
            self._json(HTTPStatus.NOT_FOUND, {"fehler": f"{name} nicht im Paket"})

    def _read_routes(self) -> dict[str, Callable[[], None]]:
        app, read_only = self.app, self.read_only
        return {
            "/api/status": lambda: self._json(HTTPStatus.OK, {**app.status(), "nur_lesen": read_only}),
            "/api/profil": lambda: self._json(HTTPStatus.OK, {**app.profile_view(), "nur_lesen": read_only}),
            "/api/werkzeuge": lambda: self._json(HTTPStatus.OK, app.tools()),
            "/api/ergebnis": lambda: self._json(HTTPStatus.OK, last_result()),
            "/metrics": lambda: self._send(
                HTTPStatus.OK, status.prometheus(app.status()).encode(), "text/plain; version=0.0.4"
            ),
        }

    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        path = self.path.split("?", 1)[0]
        try:
            if path in STATIC:
                self._static(*STATIC[path])
            elif path in self._read_routes():
                self._read_routes()[path]()
            else:
                self._json(HTTPStatus.NOT_FOUND, {"fehler": "nicht gefunden"})
        except (OSError, ValueError) as error:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"fehler": str(error)})

    def _allowed_to_change(self) -> bool:
        local = is_loopback(self.client_address[0]) and _host_is_loopback(self.headers.get("Host", ""))
        return local and not self.read_only

    def _body(self) -> object:
        if not self._allowed_to_change():
            raise RequestError(HTTPStatus.FORBIDDEN, "Änderungen nur lokal am Rechner")
        if self.headers.get("X-Auditcore-Runner") != "1":
            raise RequestError(HTTPStatus.FORBIDDEN, "Kopfzeile X-Auditcore-Runner fehlt")
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise RequestError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Anfrage zu groß")
        try:
            return json.loads(self.rfile.read(length) or b"null")
        except ValueError as error:
            raise RequestError(HTTPStatus.BAD_REQUEST, "kein gültiges JSON") from error

    def do_POST(self) -> None:  # noqa: N802 - stdlib naming
        routes: dict[str, Callable[[object], object]] = {
            "/api/profil/pruefen": self.app.check,
            "/api/profil/anwenden": self.app.apply,
            "/api/werkzeuge": self.app.save_tools,
        }
        route = routes.get(self.path)
        try:
            if route is None:
                raise RequestError(HTTPStatus.NOT_FOUND, "nicht gefunden")
            self._json(HTTPStatus.OK, route(self._body()))
        except RequestError as error:
            self._json(error.status_code, {"fehler": str(error)})


def make_handler(app: App, read_only: bool) -> type[BaseHTTPRequestHandler]:
    """Handler class bound to one app; ``read_only`` refuses every change."""
    return type("BoundHandler", (Handler,), {"app": app, "read_only": read_only})


def serve(app: App, host: str, port: int, read_only_address: str = "") -> None:  # pragma: no cover - blocking
    servers = [ThreadingHTTPServer((host, port), make_handler(app, read_only=not is_loopback(host)))]
    if read_only_address:
        servers.append(ThreadingHTTPServer((read_only_address, port), make_handler(app, read_only=True)))
    for extra in servers[1:]:
        threading.Thread(target=extra.serve_forever, daemon=True).start()
    servers[0].serve_forever()
