# AGENTS.md – Arbeitsregeln für KI-Agenten in auditcore

Kurzfassung für Claude, Codex und andere Agenten. Ziel: **erst Maschinenberichte,
dann gezielt Quelltext.** Architektur-Dokumente nur für die konkrete Frage lesen.

## 1. Zuerst lesen (statt Code und lange Doku)

| Frage | Befehl bzw. Quelle |
|---|---|
| Was ist im PR rot? | Step-Summary „Befundbericht“ bzw. Artefakt `report.md`/`report.json` (Workflows `code-quality-gate`, `domain-packages`) |
| Befund lokal erzeugen | `pytest -n auto --junitxml=j.xml --cov=auditcore --cov-report=json:c.json` und `auditcore-codegate report --junit j.xml --coverage c.json --api-compare-ref origin/main` |
| Qualitäts-Ratchet | `auditcore-codegate check [--package auditcore_x] [--skip-mypy]` |
| Welche Pakete betrifft meine Änderung? | `python scripts/ci_affected_packages.py --base origin/main` |
| Öffentliche API gebrochen? | `auditcore-codegate report --api-compare-ref origin/main` (Abschnitt „Öffentliche API“) |
| Doppelte Funktionen, Inventur | `auditcore-consolidate packages …`, `docs/quality/duplikate.md` |
| Hilfsfunktionen/Verträge der Apps | `auditcore-helpers check` |
| Bibliotheksqualität eines Pakets | `auditcore-bibquality <pfad> --context contexts/<name>.json` |
| Refactoring einer App | `auditcore-refactor inspect/plan/verify` |

Architektur nur gezielt: `docs/architecture/ADR-001-multi-package-monorepo.md`
(Paketgrenzen), `docs/quality/code-quality.md` (Maßstäbe),
`AUDITCORE_LASTENHEFT.md` nur bei fachlichen Regeln.

## 2. Aufbau in einem Satz

Plattform `src/auditcore` (Werkzeuge: quality, consolidator, apprefactor,
deployer, helpers, policy) plus eigenständige Fachpakete `packages/auditcore_*`
(Python) und `packages-js/*`; Fachkerne importieren keine Plattform-Werkzeuge,
Web-Frameworks oder App-Infrastruktur (`tests/test_architecture.py` je Paket).

## 3. Prüfen vor dem Commit

```bash
pytest -n auto                         # Root; in packages/<x>: pytest -n auto
ruff check . && ruff format --check .
mypy src                               # strict; je Paket: cd packages/<x> && mypy src
auditcore-codegate check --skip-mypy   # schneller Ratchet
python scripts/ci_lock.py --check      # Abhängigkeiten geändert? dann ohne --check neu erzeugen
```

Marker: `slow`, `gpu` (torch/Donut; `-m gpu`), `network`. Zeitlimit je Test 120 s
(`pytest-timeout`), die 25 langsamsten Tests stehen am Ende jeder Ausgabe.

## 4. Regeln

- **Ratchet:** Keine Metrik in `quality/baseline.json` darf steigen; Verbesserungen
  mit `auditcore-codegate check --update-baseline` festschreiben. Neue Module
  erfüllen alle Maßstäbe (≤ 400 Zeilen, Funktionen ≤ 60 Zeilen, Komplexität ≤ 10,
  kein `Any`, englische Bezeichner, `mypy --strict`).
- **Gemeinsame Hilfen** gehören nach `auditcore_common`; paketübergreifende Kopien
  zählen als `duplicate_functions`.
- **Interne Pins** sind exakt (`auditcore_common==0.2.0`); veröffentlichte
  Versionen sind unveränderlich, Änderungen brauchen neue Versionen.
- **Keine erfundenen** Geschäftsregeln, Schwellenwerte oder Testergebnisse; Tests
  nutzen synthetische Daten.
- **Workflows:** Eigene Runner (NUC, janpow-ai) sehen nie Fork-Code, Secrets oder
  Dependabot-Läufe; `tests/test_workflow_runner_guard.py` erzwingt das.
- **Deutsch** in Doku, Meldungen und Commits; Bezeichner im Code englisch.

## 5. Weniger Tokens

- Rote Tests: nur die im Befundbericht genannte Datei und Zeile öffnen, nicht das Paket.
- Große Dateien nie ganz lesen; `grep -n`, Symbolnamen aus dem API-Abschnitt nutzen.
- Routine-Texte (Testnamen, Docstrings, Commit-Texte) dürfen lokal erzeugt werden;
  Fachentscheidungen nicht.
