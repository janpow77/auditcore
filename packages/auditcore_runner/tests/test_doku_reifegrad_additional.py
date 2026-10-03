"""Repository documentation gates behave consistently in installed runner wheels."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from auditcore_runner.werkzeuge import doku_reifegrad as docs

AGENT = "# Entwicklung\npytest\n# Architektur\nPython\nARCHITEKTUR.md\n"
ARCH = "# Übersicht\nModule, zentrale Schnittstellen und Datenfluss.\n"
README = (
    "# Beispiel\nDieses Repository enthält eine kleine Bibliothek zur Verarbeitung von Tabellen. "
    "Die Anwendung kann die vorhandenen Funktionen für ihre Auswertungen verwenden. "
    "Die Ergebnisse werden als strukturierte Daten zurückgegeben.\n"
    "## Installation\npytest\n## Funktionen\n## Voraussetzungen\nPython\nARCHITEKTUR.md\n"
)


def complete(path: Path) -> None:
    (path / "AGENTS.md").write_text(AGENT)
    (path / "ARCHITEKTUR.md").write_text(ARCH)
    (path / "README.md").write_text(README)


def test_empty_repository_reports_all_missing_files(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    report = docs.check_repository(tmp_path)
    assert report["total_score"] == 0 and report["maturity_level"] == 1
    for part in ["claude", "arch", "readme"]:
        assert not report[part]["exists"] and report[part]["flags"]
    assert docs.main([str(tmp_path)]) == 1
    assert "Mindestlevel" in capsys.readouterr().err


def test_complete_repository_and_json_cli(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    complete(tmp_path)
    assert docs.main([str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["maturity_level"] == 5 and report["total_score"] == 100
    assert report["claude"]["file"] == "AGENTS.md"
    assert docs.main([str(tmp_path)]) == 0
    assert "Level 5" in capsys.readouterr().out


def test_short_unhelpful_files_fail_with_concrete_flags(tmp_path: Path) -> None:
    for filename in ["CLAUDE.md", "ARCHITECTURE.md", "README.md"]:
        (tmp_path / filename).write_text("x")
    report = docs.check_repository(tmp_path)
    assert len(report["readme"]["flags"]) == 5
    assert len(report["arch"]["flags"]) == 4
    assert len(report["claude"]["flags"]) == 4
    assert report["arch"]["file"] == "ARCHITECTURE.md"


def test_agent_includes_and_file_precedence(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("x")
    (tmp_path / "rules.md").write_text(AGENT)
    (tmp_path / "CLAUDE.md").write_text("@rules.md\n@missing.md\n@param ignored\n@return ignored\n")
    result = docs.eval_claude(tmp_path)
    assert result["file"] == "CLAUDE.md" and result["score"] == 100
    assert result["lines"] == 5


@pytest.mark.parametrize("lines,score", [(250, 90), (450, 80)])
def test_oversized_agent_instructions_are_penalized(tmp_path: Path, lines: int, score: int) -> None:
    (tmp_path / "AGENTS.md").write_text(AGENT + "\n" * lines)
    result = docs.eval_claude(tmp_path)
    assert result["score"] == score and result["flags"]


@pytest.mark.parametrize("missing,level", [("docs", 4), ("arch", 3), ("readme", 2)])
def test_intermediate_maturity_levels(tmp_path: Path, missing: str, level: int) -> None:
    complete(tmp_path)
    if missing == "docs":
        (tmp_path / "README.md").write_text(README.replace("ARCHITEKTUR.md", ""))
    elif missing == "arch":
        (tmp_path / "README.md").write_text("# Beispiel\nInstallation Python\n")
    else:
        (tmp_path / "README.md").unlink()
    assert docs.check_repository(tmp_path)["maturity_level"] == level


def test_invalid_path_is_cli_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert docs.main([str(tmp_path / "missing")]) == 2
    assert "kein Verzeichnis" in capsys.readouterr().err
