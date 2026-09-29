# AuditCore – Architektur

## Zweck und Grenzen

AuditCore stellt wiederverwendbare Prüf- und Fachbibliotheken sowie Werkzeuge zur Codequalität bereit. Die Plattform liegt in `src/auditcore`, eigenständige Python-Fachpakete in `packages/auditcore_*`, JavaScript-/TypeScript-Pakete in `packages-js/`. Die Pakete haben eigene Versionen, Tests und Abhängigkeiten.

## Bausteine und Datenfluss

- **Fachkerne:** verarbeiten explizite Eingaben zu fachlichen Ergebnissen. Gemeinsame Hilfen liegen in `auditcore_common`. Fachkerne importieren keine Plattform-Werkzeuge, Web-Frameworks oder App-Infrastruktur.
- **Plattform:** `src/auditcore/tools/quality`, `consolidator`, `apprefactor`, `deployer`, `helpers` und `policy` prüfen, inventarisieren oder unterstützen Änderungen und Auslieferung.
- **Runner:** `packages/auditcore_runner` liest Repo-Prüfprofile, startet Werkzeuge und vereinheitlicht deren Befunde. Ein vorhandenes Profil allein belegt noch keine bestandene Prüfung.
- **Integrationen:** Anwendungen verwenden veröffentlichte Fachpakete oder die gemeinsamen JS-Bibliotheken; GitHub-Workflows führen die jeweiligen Qualitäts- und Paketprüfungen aus.

Prüfpfad: Quelltext und Repo-Konfiguration → Prüfwerkzeuge → Maschinenbericht mit Regel und Fundstelle → gezielte Korrektur → erneute Prüfung. Maßgeblich sind tatsächliche Werkzeugergebnisse und die geltenden Baselines.

## Verträge

Interne Paketabhängigkeiten sind exakt gepinnt. Veröffentlichte Versionen bleiben unverändert. Öffentliche APIs und Paketgrenzen werden geprüft. Bestehende Qualitätsmetriken dürfen gegenüber `quality/baseline.json` nicht schlechter werden; neue Module erfüllen die Regeln aus `AGENTS.md`.

## Dokumentationsumfang

Diese Datei, `FUNKTIONEN.md` und `ABNAHME.md` bilden die Kerndokumentation für Graphify. `.graphifyignore` schließt weitere Prosa, Office-Dateien, PDFs und Medien aus. Programmcode einschließlich `.bas` bleibt im bisherigen Codeumfang. Bestehende Detaildokumente bleiben als Quellen erhalten. Ein geänderter Korpus benötigt einen neuen Analyseplan; pausierte Laufmanifeste werden nicht nachträglich verändert.

Quellen: `README.md`, `AGENTS.md`, `docs/architecture/ADR-001-multi-package-monorepo.md`, `docs/quality/code-quality.md`, `packages/auditcore_runner/pyproject.toml`.
