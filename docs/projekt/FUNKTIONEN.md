# AuditCore – Funktionen

| Funktion | Umsetzung / Einstieg | Ergebnis |
| --- | --- | --- |
| Fachbibliotheken wiederverwenden | `packages/auditcore_*`, Paketverzeichnis in `README.md` | Versionierte, unabhängig prüfbare Fachfunktionen |
| Gemeinsame App-Hilfen verwenden | `auditcore_common`, `packages-js/`, `auditcore-helpers` | Gemeinsame Verträge statt abweichender Kopien |
| Codequalität und API prüfen | `auditcore-quality`, `auditcore-bibquality`, `auditcore-codegate` | Befunde, API-Vergleich, Qualitäts-Ratchet |
| Inventur und Duplikate ermitteln | `auditcore-consolidate` | Nachvollziehbare Inventur und Konsolidierungsgrundlage |
| Refactoring vorbereiten und prüfen | `auditcore-refactor inspect/plan/verify` | Plan und Regressionsnachweise |
| Paketauslieferung unterstützen | `auditcore-deploy`, Release-/APT-Skripte | Reproduzierbare Paketartefakte nach den Release-Regeln |
| Repo-Prüfungen ausführen | `auditcore-runner lokal pr --host --pfad .` | Gemeinsamer Maschinenbericht der konfigurierten Werkzeuge |

Vor neuen Aufgaben werden vorhandene Komponenten, Regeln und Vorlagen gesucht. Neue Fachregeln werden nicht aus allgemeinen Modellannahmen erfunden. Maschinenberichte werden vor einer breiten Quelltextsuche gelesen.

Der Runner bündelt Prüfungen; er ersetzt weder die fachliche Abnahme noch die Paket- und Release-Gates. Graphify liefert eine Struktur- und Zusammenhangsanalyse; daraus folgt kein Nachweis, dass das Programm fachlich korrekt ist.

Quellen: `README.md`, `pyproject.toml`, `src/auditcore/tools/`, `packages/auditcore_runner/docs/werkzeuge.md`.
