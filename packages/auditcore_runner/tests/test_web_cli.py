from __future__ import annotations

import http.client
import io
import json
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path

import pytest

from auditcore_runner import cli, install, profile_io, status, web
from auditcore_runner.hardware import HostFacts


@pytest.fixture
def profile_file(tmp_path: Path) -> Path:
    text = files("auditcore_runner").joinpath("data", "beispiele", "workstation-2gpu.json").read_text(encoding="utf-8")
    path = tmp_path / "profil.json"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def server(
    profile_file: Path, workstation_facts: HostFacts, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[str, int]]:
    monkeypatch.setattr(
        status,
        "collect",
        lambda profile, facts, client: {"schema": status.STATUS_SCHEMA, "rechner": profile.host, "klassen": {}},
    )
    monkeypatch.setattr(install, "image_present", lambda image: True)
    monkeypatch.setattr(install, "network_present", lambda name: True)
    app = web.App(profile_file, facts=lambda: workstation_facts, apply_enabled=False)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(app, read_only=False))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield "127.0.0.1", httpd.server_address[1]
    httpd.shutdown()


def request(
    address: tuple[str, int], method: str, path: str, body: object = None, headers: dict[str, str] | None = None
) -> tuple[int, object]:
    connection = http.client.HTTPConnection(*address, timeout=10)
    data = json.dumps(body).encode() if body is not None else None
    connection.request(method, path, body=data, headers=headers or {})
    response = connection.getresponse()
    raw = response.read()
    content = json.loads(raw) if response.getheader("Content-Type", "").startswith("application/json") else raw.decode()
    return response.status, content


def test_read_endpoints_and_security_headers(server: tuple[str, int]) -> None:
    code, data = request(server, "GET", "/api/status")
    assert code == 200 and isinstance(data, dict) and data["rechner"] == "workstation" and data["nur_lesen"] is False
    code, data = request(server, "GET", "/api/profil")
    assert code == 200 and isinstance(data, dict) and data["probleme"] == [] and len(data["profil_hash"]) == 16
    code, page = request(server, "GET", "/")
    assert code == 200 and "flowaudit-runner-console" in str(page)
    code, metrics = request(server, "GET", "/metrics")
    assert code == 200 and "auditcore_runner" in str(metrics)
    code, _ = request(server, "GET", "/runner-elements.js")
    assert code == 404


def test_changes_require_header(server: tuple[str, int], profile_file: Path) -> None:
    body = {"profil": json.loads(profile_file.read_text(encoding="utf-8"))}
    code, data = request(server, "POST", "/api/profil/pruefen", body)
    assert code == 403 and "X-Auditcore-Runner" in str(data)
    headers = {"X-Auditcore-Runner": "1", "Content-Type": "application/json"}
    code, data = request(server, "POST", "/api/profil/pruefen", body, headers)
    assert code == 200 and isinstance(data, dict) and data["gueltig"] is True
    code, data = request(server, "POST", "/api/profil/anwenden", {**body, "erwartete_version": 5}, headers)
    assert code == 409 and "Version 0" in str(data)
    code, data = request(server, "POST", "/api/profil/anwenden", {**body, "erwartete_version": 0}, headers)
    assert code == 200 and isinstance(data, dict) and data["version"] == 1
    code, data = request(server, "POST", "/api/profil/anwenden", {"profil": {"schema": "falsch"}}, headers)
    assert code == 422


def test_read_only_listener_refuses_changes(profile_file: Path, workstation_facts: HostFacts) -> None:
    app = web.App(profile_file, facts=lambda: workstation_facts, apply_enabled=False)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(app, read_only=True))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        headers = {"X-Auditcore-Runner": "1"}
        code, data = request(("127.0.0.1", httpd.server_address[1]), "POST", "/api/werkzeuge", {}, headers)
        assert code == 403 and "nur lokal" in str(data).lower()
    finally:
        httpd.shutdown()


def test_cli_profile_commands(
    profile_file: Path,
    workstation_facts: HostFacts,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "detect", lambda: workstation_facts)
    monkeypatch.setattr(install, "image_present", lambda image: True)
    monkeypatch.setattr(install, "network_present", lambda name: True)
    assert cli.main(["profil", "schema"]) == 0
    assert json.loads(capsys.readouterr().out)["title"].startswith("Runner-Profil")
    monkeypatch.setattr("sys.stdin", io.StringIO(profile_file.read_text(encoding="utf-8")))
    assert cli.main(["--profil", str(profile_file), "profil", "pruefen", "--datei", "-", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["gueltig"] is True
    args = [
        "--profil",
        str(profile_file),
        "profil",
        "anwenden",
        "--datei",
        str(profile_file),
        "--json",
        "--trockenlauf",
    ]
    assert cli.main([*args, "--erwartete-version", "9"]) == 3
    capsys.readouterr()
    assert cli.main([*args, "--quelle", "flow-agent", "--wer", "zentrale"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["version"] == 1 and profile_io.load(profile_file).change.source == "flow-agent"
    assert cli.main(["profil", "erkennen", "--vorlage", "server-cpu", "--ziel", "owner/repo"]) == 0


def test_cli_findings_and_workflows(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = tmp_path / "ergebnis.json"
    result.write_text(
        json.dumps(
            {
                "befunde": [
                    {
                        "werkzeug": "ruff",
                        "regel": "F401",
                        "datei": "a.py",
                        "zeile": 1,
                        "meldung": "unused",
                        "schwere": "fehler",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    baseline = tmp_path / "baseline.json"
    assert cli.main(["befunde", "--ergebnis", str(result), "--baseline-setzen", str(baseline)]) == 0
    assert cli.main(["befunde", "--ergebnis", str(result), "--baseline", str(baseline)]) == 0
    assert "0 zu bearbeiten" in capsys.readouterr().out
    flows = tmp_path / "wf"
    flows.mkdir()
    (flows / "ci.yml").write_text(
        "on: [pull_request]\njobs:\n  t:\n    runs-on: [self-hosted]\n    steps: []\n", encoding="utf-8"
    )
    assert cli.main(["workflows", "pruefen", str(flows), "--ohne-extern", "--json"]) == 1
    assert {f["regel"] for f in json.loads(capsys.readouterr().out)} == {"fork", "dependabot"}
    assert cli.main(["hook", "--pfad", str(tmp_path)]) == 0
    assert "auditcore-runner lokal schnell" in capsys.readouterr().out
