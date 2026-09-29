# AuditCore – Abnahmekriterien und Prüfprofil

## Ausführung

Das Repo-Profil steht in `.auditcore-runner.toml`. Zuerst die Entwicklungsumgebung gemäß `README.md` mit `.[dev]` installieren und aktivieren, dann im Repo:

```bash
auditcore-runner lokal pr --host --pfad . --ohne-cache
```

Der Runner muss Repo-Befehlsüberschreibungen (`befehl`) unterstützen. Auf diesem Arbeitsplatz wurde dafür der vorhandene Runner aus `packages/auditcore_runner` lokal editierbar installiert; andere Rechner benötigen ebenfalls diesen Funktionsstand. Werkzeuge laufen aus der aktivierten Entwicklungsumgebung. Rohberichte liegen unter `.auditcore-runner/`, der zusammengefasste letzte Bericht standardmäßig unter `~/.local/state/auditcore-runner/letztes-ergebnis.json` (bei gesetztem `XDG_STATE_HOME` dort). Den letzten Bericht vor einem weiteren Lauf archivieren, wenn er dauerhaft als Nachweis dienen soll.

## Kriterien

| ID | Kriterium | Nachweis |
| --- | --- | --- |
| AC-01 | Root-Tests bestehen; fehlende Abhängigkeiten oder ausgelassene Prüfungen sind sichtbar. | Profil `pr`: pytest mit JUnit-Bericht; GPU-/Netztests separat |
| AC-02 | Quelltext erfüllt Lint- und Typregeln. | Profil `pr`: Ruff und `mypy src`; zusätzlich `ruff format --check .` |
| AC-03 | Qualitätsmetriken verschlechtern sich nicht. | Profil `pr`: `auditcore-codegate check --skip-mypy`; Baseline nicht zur Verschleierung erhöhen |
| AC-04 | Geänderte Fachpakete bleiben unabhängig und API-kompatibel. | Betroffene Pakete über `scripts/ci_affected_packages.py --base origin/main` ermitteln; deren Tests, Architekturtests und Typprüfung sowie API-Bericht ausführen |
| AC-05 | Abhängigkeiten und Workflow-Sicherheit entsprechen den Repo-Gates. | `python scripts/ci_lock.py --check`; CI `code-quality-gate` und `domain-packages`, einschließlich Workflow-Prüfungen |
| AC-06 | Betroffene JS-Pakete funktionieren und sind auslieferbar. | Root npm-Gates aus `README.md`: lint, typecheck, test, build und Beispielprüfung |
| AC-07 | Graphify verarbeitet genau drei Kerndokumente zusätzlich zum bisherigen Codeumfang. | `graphify.detect.detect` muss als Dokumente nur `docs/projekt/{ARCHITEKTUR,FUNKTIONEN,ABNAHME}.md` liefern; keine PDFs/Medien |

## Aussagegrenze und Pflege

Diese Tabelle definiert Anforderungen und behauptet keinen bestandenen Lauf. Das Profil deckt die lokale Python-Basis ab; Paket-, JS-, GPU-, Netz-, Release- und CI-Gates bleiben abhängig vom Änderungsumfang erforderlich. Ein fehlendes, übersprungenes oder fehlgeschlagenes Werkzeug gilt nicht als bestandene Abnahme. Befunde müssen vor der Freigabe bewertet werden.

Bei Änderungen an Schnittstellen, Funktionen oder Anforderungen werden diese drei Dokumente im selben Änderungsvorgang aktualisiert. Detailquellen werden verlinkt statt vollständig kopiert. Die ausführbaren Befehle werden zentral im Prüfprofil gepflegt.

## Prüfnachweis vom 28.09.2026 – aktualisiert

Der veraltete API-Überblick in `auditcore_invoicesynth` ist korrigiert. Das Root-Profil
`pr` besteht einschließlich aller 606 Root-Tests, Ruff, Mypy und Qualitäts-Ratchet.
Zusätzlich: `ruff format --check .`, CI-Lock-Prüfung sowie npm lint/typecheck/test/build
bestanden. Das Profil `runner` prüft das separat ausgelieferte Runner-Paket.
Bei 91 formatierten Python-Dateien blieb der ausführbare AST unverändert.

Die APT-Kandidaten für Plattform und Runner liegen mit Build- und Testberichten unter
`~/.local/state/flowaudit/deploy/20260928/`. Es wird kein öffentlicher Paketfeed publiziert.
Pakettests unterscheiden Installation/CLI/Deinstallation von fachlichen App-Prüfungen.

Plattform- und Runner-Pakete bestehen Installation, CLI-Aufrufe und Deinstallation
auf beiden Ubuntu-Zielen (24.04 und 26.04). Im VM-Testaufbau werden geerbte
Container-Markierungen vor dem Erzeugen des Gast-Dateisystems entfernt: Andernfalls
ignoriert systemd im QEMU-Gast das übergebene Test-Startziel. Nach dieser Korrektur
besteht das Root-Profil erneut; beide Regulierung-Lifecycle-Tests bestehen ebenfalls.
Die Paketberichte binden das Ergebnis an die SHA-256-Prüfsumme des getesteten Pakets.
