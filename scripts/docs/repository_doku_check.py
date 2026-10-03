#!/usr/bin/env python3
"""Prüfung des Dokumentations-Reifegrads und der Qualitätskriterien.

Geprüft werden README, ARCHITEKTUR sowie CLAUDE/AGENTS.

Bewertet ein Repository nach dem 5-Stufen-Reifegradmodell:
  Level 1 (Initial / Ad-hoc)           : < 40 %
  Level 2 (Verwaltet / Grundlegend)    : 40 - 69 %
  Level 3 (Definiert & Standardkonform): 70 - 84 %
  Level 4 (Gemanagt & Agenten-optimiert): 85 - 94 %
  Level 5 (Optimiert & Vollständig)    : 95 - 100 %

Aufruf:
    python scripts/docs/repository_doku_check.py [PFAD]
    python scripts/docs/repository_doku_check.py [PFAD] --json
    python scripts/docs/repository_doku_check.py [PFAD] --min-level 4
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Regex-Muster für CLAUDE.md / AGENTS.md
_CMD_PAT = re.compile(
    r"\b(npm (run|ci|install)|pnpm|yarn|pytest|uv (run|pip|tool|sync)|pip install|"
    r"docker compose|docker build|make\s+\w|cargo (build|run|test|clippy)|uvicorn|"
    r"python\s+-m|python\s+\S+\.py|vite|go (build|test|run)|alembic|ruff|eslint|vitest|"
    r"auditcore-runner)\b",
    re.I,
)
_CMD_HEAD = re.compile(
    r"^#+.*(command|setup|befehl|install|build|run|test|usage|entwickl)", re.I | re.M
)
_ARCH_HEAD = re.compile(
    r"^#+.*(struktur|architekt|architecture|module|aufbau|komponenten|verzeichnis)", re.I | re.M
)
_STACK_HEAD = re.compile(
    r"^#+.*(stack|tech|technolog|voraussetzung|umgebung|anforderung|runtime|sprache|framework)",
    re.I | re.M,
)
_POINTER = re.compile(
    r"(ARCHITEKTUR\.md|ARCHITECTURE\.md|@[\w./~-]+\.(md|json|toml)|\]\([^)]+\.md\)|docs/)", re.I
)


def eval_claude(p: Path) -> dict:
    target = None
    for name in ("CLAUDE.md", "AGENTS.md"):
        cand = p / name
        if cand.is_file():
            target = cand
            break
    if not target:
        return {
            "exists": False,
            "file": None,
            "score": 0,
            "lines": 0,
            "flags": ["Datei fehlt (CLAUDE.md oder AGENTS.md)"],
        }

    raw_text = target.read_text(encoding="utf-8", errors="replace")
    text = raw_text
    # @include auflösen
    for line in raw_text.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("@") and not line_clean.startswith(("@param", "@return")):
            inc_file = p / line_clean[1:].strip()
            if inc_file.is_file():
                text += "\n" + inc_file.read_text(encoding="utf-8", errors="replace")

    lines = raw_text.count("\n") + 1
    score = 0
    flags = []

    # 1. Entwicklerbefehle (30 P.)
    if _CMD_PAT.search(text) or _CMD_HEAD.search(text):
        score += 30
    else:
        flags.append("Keine ausführbaren Entwickler-Befehle gefunden (-30)")

    # 2. Kompaktheit (20 P.)
    if lines <= 200:
        score += 20
    elif lines <= 400:
        score += 10
        flags.append(f"{lines} Zeilen (empfohlen <= 200 Zeilen, -10)")
    else:
        flags.append(f"{lines} Zeilen (> 400 Zeilen Bloat, -20)")

    # 3. Architektur-Sektion (20 P.)
    if _ARCH_HEAD.search(text):
        score += 20
    else:
        flags.append("Keine Architektur-Sektion gefunden (-20)")

    # 4. Tech-Stack (15 P.)
    if _STACK_HEAD.search(text) or re.search(
        r"\b(Python|Rust|TypeScript|FastAPI|Vue|React|Node|Go|C\+\+)\b", text
    ):
        score += 15
    else:
        flags.append("Kein Tech-Stack / keine Runtimes genannt (-15)")

    # 5. Doku-Pointer (15 P.)
    if _POINTER.search(text):
        score += 15
    else:
        flags.append("Keine Verweise auf ARCHITEKTUR.md oder Unterdokumente (-15)")

    return {
        "exists": True,
        "file": target.name,
        "score": min(score, 100),
        "lines": lines,
        "flags": flags,
    }


def eval_arch(p: Path) -> dict:
    target = None
    for name in ("ARCHITEKTUR.md", "ARCHITECTURE.md"):
        cand = p / name
        if cand.is_file():
            target = cand
            break
    if not target:
        return {
            "exists": False,
            "file": None,
            "score": 0,
            "words": 0,
            "flags": ["Datei fehlt (ARCHITEKTUR.md oder ARCHITECTURE.md)"],
        }

    text = target.read_text(encoding="utf-8", errors="replace")
    words = len(text.split())
    score = 0
    flags = []

    # 1. Systemübersicht / Diagramm / Topologie (25 P.)
    if re.search(
        r"(```|┌|\|.*---|Topologie|Übersicht|Overview|Diagram|flowchart|graph\s+(TD|LR))",
        text,
        re.I,
    ):
        score += 25
    else:
        flags.append("Keine Systemübersicht oder Topologie/Diagramm (-25)")

    # 2. Modulkarte / Verzeichnisse (25 P.)
    if re.search(
        r"(Modul|Verzeichnis|Paket|Component|Knoten|Community|Module|Package|Directory|Pipeline)",
        text,
        re.I,
    ):
        score += 25
    else:
        flags.append("Keine Modulkarte / Verzeichnisübersicht (-25)")

    # 3. Zentrale Bausteine / Hotspots (25 P.)
    if re.search(
        r"(Zentral|Hotspot|God\s*_?Node|Schnittstelle|Betweenness|Interface|Store|Router|Kernkomponente|Baustein|Entry\s*point)",
        text,
        re.I,
    ):
        score += 25
    else:
        flags.append("Keine zentralen Bausteine oder Hotspots beschrieben (-25)")

    # 4. Datenfluss & Leitplanken (25 P.)
    if re.search(
        r"(Datenfluss|Fluss|Regel|Leitfaden|Änderung|Zyklen|Clean|Prinzip|Workflow|Data\s*flow|Pipeline|Calling|Constraint)",
        text,
        re.I,
    ):
        score += 25
    else:
        flags.append("Kein Datenfluss oder Architektur-Leitplanken (-25)")

    return {
        "exists": True,
        "file": target.name,
        "score": score,
        "words": words,
        "flags": flags,
    }


def eval_readme(p: Path) -> dict:
    target = p / "README.md"
    if not target.is_file():
        return {
            "exists": False,
            "file": None,
            "score": 0,
            "words": 0,
            "flags": ["Datei fehlt (README.md)"],
        }

    text = target.read_text(encoding="utf-8", errors="replace")
    words = len(text.split())
    score = 0
    flags = []

    # 1. Zweck & Kontext (20 P.)
    if words >= 30 and re.search(r"^#\s+.+", text, re.M):
        score += 20
    else:
        flags.append("Zweck unvollständig oder zu kurz (< 30 Wörter, -20)")

    # 2. Schnellstart / Installation (20 P.)
    if re.search(
        r"(Installation|Schnellstart|Quickstart|Setup|Get Started|Installieren)", text, re.I
    ) or _CMD_PAT.search(text):
        score += 20
    else:
        flags.append("Kein Schnellstart oder Setup-Befehl (-20)")

    # 3. Features / Architektur (20 P.)
    if re.search(r"(Funktion|Feature|Architektur|Umfang|Modul|Vorteil|Konzept)", text, re.I):
        score += 20
    else:
        flags.append("Keine Funktions- oder Architekturübersicht (-20)")

    # 4. Tech-Stack / Voraussetzungen (20 P.)
    if re.search(
        r"(Tech-Stack|Stack|Technologie|Voraussetzung|Anforderung|Prerequisite|Runtime|Python|Rust|Node)",
        text,
        re.I,
    ):
        score += 20
    else:
        flags.append("Kein Tech-Stack oder Voraussetzungen (-20)")

    # 5. Doku-Links (20 P.)
    if re.search(
        r"(ARCHITEKTUR\.md|ARCHITECTURE\.md|CLAUDE\.md|AGENTS\.md|docs/|\[.+\]\(.+\.md\))",
        text,
        re.I,
    ):
        score += 20
    else:
        flags.append("Keine Verlinkung auf ARCHITEKTUR.md oder Detaildoku (-20)")

    return {
        "exists": True,
        "file": target.name,
        "score": score,
        "words": words,
        "flags": flags,
    }


def check_repository(repo_path: Path) -> dict:
    c = eval_claude(repo_path)
    a = eval_arch(repo_path)
    r = eval_readme(repo_path)

    total_score = round((c["score"] + a["score"] + r["score"]) / 3.0, 1)
    if total_score >= 95:
        level, label = 5, "Level 5 (Optimiert & Vollständig)"
    elif total_score >= 85:
        level, label = 4, "Level 4 (Gemanagt & Agenten-optimiert)"
    elif total_score >= 70:
        level, label = 3, "Level 3 (Definiert & Standardkonform)"
    elif total_score >= 40:
        level, label = 2, "Level 2 (Verwaltet & Grundlegend)"
    else:
        level, label = 1, "Level 1 (Initial & Unvollständig)"

    return {
        "repository": repo_path.name,
        "path": str(repo_path.resolve()),
        "total_score": total_score,
        "maturity_level": level,
        "maturity_label": label,
        "claude": c,
        "arch": a,
        "readme": r,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prüfung des Dokumentations-Reifegrads eines Repositories."
    )
    parser.add_argument("path", nargs="?", default=".", help="Pfad zum Repository (Standard: .)")
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")
    parser.add_argument(
        "--min-level", type=int, default=4, help="Mindest-Reifegrad (1-5, Standard: 4)"
    )
    args = parser.parse_args(argv)

    repo_path = Path(args.path).resolve()
    if not repo_path.is_dir():
        print(f"Fehler: Pfad {repo_path} ist kein Verzeichnis.", file=sys.stderr)
        return 2

    res = check_repository(repo_path)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"=== Dokumentations-Reifegrad: {res['repository']} ===")
        print(f"Gesamt-Score: {res['total_score']}%  ->  {res['maturity_label']}\n")
        part = res["readme"]
        name = part["file"] or "README.md"
        print(f"  • {name:<18}: {part['score']}/100 P. ({part['words']} Wörter)")
        for flag in res["readme"]["flags"]:
            print(f"      - {flag}")
        part = res["arch"]
        name = part["file"] or "ARCHITEKTUR.md"
        print(f"  • {name:<18}: {part['score']}/100 P. ({part['words']} Wörter)")
        for flag in res["arch"]["flags"]:
            print(f"      - {flag}")
        part = res["claude"]
        name = part["file"] or "CLAUDE.md"
        print(f"  • {name:<18}: {part['score']}/100 P. ({part['lines']} Zeilen)")
        for flag in res["claude"]["flags"]:
            print(f"      - {flag}")

    if res["maturity_level"] < args.min_level:
        if not args.json:
            print(
                f"\nFEHLER: Reifegrad {res['maturity_level']} liegt unter dem "
                f"geforderten Mindestlevel {args.min_level}.",
                file=sys.stderr,
            )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
