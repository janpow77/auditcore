"""CLI-Rahmen: Status, Konfigurationsprüfung, Schemas und geplante Gruppen."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest

from auditcore_officebank import __version__
from auditcore_officebank.cli import EXIT_CONFIG, EXIT_NOT_IMPLEMENTED, build_parser, main
from auditcore_officebank.stages import planned_groups


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--version"])
    assert caught.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_status_lists_all_stages(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Etappe 0 Gerüst: konfig, status – verfügbar" in out
    assert "Etappe 2 VM: vm – geplant" in out


def test_check_host_and_project(
    host_file: Path, project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(["konfig", "pruefen", "--rechner", str(host_file), "--projekt", str(project_dir)]) == 0
    )
    out = capsys.readouterr().out
    assert "VM „testgast“ (utm), MCP-Endpunkte: oeffentlich, Upload-Ziele: 1" in out
    assert "P-DEMO (access), 2 Module, Lint-Profil access" in out


def test_check_without_target(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["konfig", "pruefen"]) == EXIT_CONFIG
    assert "Nichts geprüft" in capsys.readouterr().err


def test_check_reports_config_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    file = tmp_path / "profil.toml"
    file.write_text('schema = "x"\npassword = "geheim"\n', encoding="utf-8")
    assert main(["konfig", "pruefen", "--rechner", str(file)]) == EXIT_CONFIG
    err = capsys.readouterr().err
    assert "Konfigurationsfehler" in err
    assert "geheim" not in err


def test_default_host_profile_path() -> None:
    args = build_parser().parse_args(["konfig", "pruefen", "--rechner"])
    assert str(args.rechner).endswith("auditcore-officebank/profil.toml")


@pytest.mark.parametrize("kind", ["rechner", "projekt"])
def test_schema_output(kind: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["konfig", "schema", kind]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema["$id"] == f"auditcore-officebank/{kind}/1"


@pytest.mark.parametrize("group", planned_groups())
def test_planned_groups_exit_3(group: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([group, "irgendwas", "--option"]) == EXIT_NOT_IMPLEMENTED
    assert "noch nicht umgesetzt" in capsys.readouterr().err


def test_module_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["auditcore-officebank", "status"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("auditcore_officebank", run_name="__main__")
    assert caught.value.code == 0
