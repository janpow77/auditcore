"""Werkzeug doku_reifegrad: Bewertung von README, ARCHITEKTUR und CLAUDE/AGENTS."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from auditcore_runner.werkzeuge import doku_reifegrad as doku

README_VOLL = """# Beispielprojekt

Dieses Projekt prüft Belege und erzeugt Berichte für die Prüfbehörde. Es bündelt
Erfassung, Bewertung und Ausgabe in einer Anwendung und ist für den Einsatz in der
Verwaltung gedacht.

## Installation

Schnellstart mit `pip install beispiel`.

## Funktionen

Module für Erfassung und Bericht.

## Voraussetzungen

Python 3.11.

Weitere Details in [ARCHITEKTUR.md](ARCHITEKTUR.md).
"""

ARCH_VOLL = """# Architektur

## Übersicht

```
eingang -> kern -> ausgabe
```

## Module

Das Paket `kern` ist der zentrale Baustein; der Datenfluss läuft von links nach rechts.
"""

CLAUDE_VOLL = """# Hinweise für Agenten

## Befehle

pytest -q

## Architektur

Siehe ARCHITEKTUR.md.

## Tech-Stack

Python und FastAPI.
"""


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_vollstaendiges_repository_erreicht_level_5(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"README.md": README_VOLL, "ARCHITEKTUR.md": ARCH_VOLL, "CLAUDE.md": CLAUDE_VOLL},
    )
    report = doku.check_repository(repo)
    assert report["total_score"] == 100.0
    assert report["maturity_level"] == 5
    assert report["readme"]["flags"] == []
    assert report["arch"]["flags"] == []
    assert report["claude"] == {
        "exists": True,
        "file": "CLAUDE.md",
        "score": 100,
        "lines": CLAUDE_VOLL.count("\n") + 1,
        "flags": [],
    }


def test_leeres_repository_meldet_fehlende_dateien(tmp_path: Path) -> None:
    report = doku.check_repository(tmp_path)
    assert report["total_score"] == 0.0
    assert report["maturity_level"] == 1
    assert report["claude"]["flags"] == ["Datei fehlt (CLAUDE.md oder AGENTS.md)"]
    assert report["arch"]["flags"] == ["Datei fehlt (ARCHITEKTUR.md oder ARCHITECTURE.md)"]
    assert report["readme"]["flags"] == ["Datei fehlt (README.md)"]


def test_duerftige_dateien_sammeln_alle_abzuege(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": "kurz\n",
            "ARCHITECTURE.md": "nichts\n",
            "AGENTS.md": "x\n" * 450,
        },
    )
    report = doku.check_repository(repo)
    assert report["readme"]["score"] == 0 and len(report["readme"]["flags"]) == 5
    assert report["arch"]["file"] == "ARCHITECTURE.md"
    assert report["arch"]["score"] == 0 and len(report["arch"]["flags"]) == 4
    claude = report["claude"]
    assert claude["file"] == "AGENTS.md" and claude["score"] == 0
    assert any("> 400 Zeilen" in flag for flag in claude["flags"])
    assert len(claude["flags"]) == 5


def test_mittellange_agentendatei_kostet_zehn_punkte() -> None:
    score, flags = doku._score_agent_text("pytest\n", 300)
    assert score == 40
    assert flags[0] == "300 Zeilen (empfohlen <= 200 Zeilen, -10)"


def test_eingebundene_dateien_zaehlen_mit(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "stack.md").write_text("## Tech-Stack\n\nRust\n", encoding="utf-8")
    raw = "@docs/stack.md\n@param ignorieren\n@fehlt.md\n"
    text = doku._agent_text(tmp_path, raw)
    assert "Rust" in text
    assert text.count("\n") > raw.count("\n")


@pytest.mark.parametrize(
    ("score", "level"),
    [(100, 5), (90, 4), (75, 3), (50, 2), (10, 1)],
)
def test_stufengrenzen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, score: int, level: int) -> None:
    def teil(_path: Path) -> dict[str, object]:
        return {"exists": True, "file": "x", "score": score, "flags": [], "words": 0, "lines": 0}

    for name in ("eval_claude", "eval_arch", "eval_readme"):
        monkeypatch.setattr(doku, name, teil)
    assert doku.check_repository(tmp_path)["maturity_level"] == level


def test_main_textausgabe_und_mindestlevel(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path, {"README.md": "kurz\n", "CLAUDE.md": "x\n"})
    assert doku.main([str(repo), "--min-level", "1"]) == 0
    out = capsys.readouterr().out
    assert "Gesamt-Score" in out and "README.md" in out and "ARCHITEKTUR.md" in out
    assert "Zweck unvollständig" in out

    assert doku.main([str(repo)]) == 1
    assert "FEHLER: Reifegrad 1 liegt unter dem geforderten Mindestlevel 4." in capsys.readouterr().err


def test_main_json_ohne_fehlertext(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert doku.main([str(tmp_path), "--json"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out)["maturity_level"] == 1
    assert captured.err == ""


def test_main_lehnt_fehlendes_verzeichnis_ab(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert doku.main([str(tmp_path / "fehlt")]) == 2
    assert "ist kein Verzeichnis" in capsys.readouterr().err
