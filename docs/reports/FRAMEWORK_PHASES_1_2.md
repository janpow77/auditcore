# AUDITCORE PLATFORM BUILD REPORT — Framework, Phasen 1–2

Stand: 22. September 2026. Repository: `janpow77/auditcore`.
Architektur: [ADR-001](../architecture/ADR-001-multi-package-monorepo.md).
Dieser Bericht ergänzt den historischen [Plattformbericht](PLATFORM_BUILD_REPORT.md).
Frühere Inventar- und Integrationsnachweise werden dadurch nicht nachträglich
auf einen neueren Quellstand umgedeutet.

## Implementierter Umfang

| Komponente | Nachweisbarer Stand |
|---|---|
| auditcore | Installierbare Plattformdistribution; Fachpakete erhalten eigene Distributionen im selben Repository. Keine obligatorische Plattformabhängigkeit der Fachpakete. |
| quality | Syntax, Architektur, Typen, Dokumentation, Secrets, Privacy/OSS, Dependencies, Komplexität, API, Regression, Supply Chain und Policy werden getrennt bewertet. |
| Framework Policy Integration | Gepinnte Quellen aus `verwaltung-app-framework`, Anwendbarkeit vor Security-Gates, getrennte MUSS/BEDINGT/SOLL-Behandlung. |
| Applicability Evaluation | UNKNOWN bleibt unbekannt. F-15 unterscheidet insbesondere Regelwerke, Prompts und Agenten. Nachweise binden Artefaktidentität, Quellhash, Kontext und Frameworkcommit. |
| consolidator | Mehrpaket-Katalog, API-/Dependency-Inventur, Quellhashes und persistente Snapshots. Technische Boilerplate-Duplikate werden aus fachlichen Kandidaten ausgeschlossen. Potenzielle Consumer sind keine bestätigten Consumer. |
| apprefactor | Charakterisierte Funktionen und Klassen, tatsächliche Import-/Requirements-Umstellung, nachgelagerte Policy-Prüfung und transaktionaler Rollback. |
| deployer | Wheel/sdist, SBOM, Manifest, Debian-Bibliotheken, explizite Debian-Abhängigkeitszuordnung, lokale Python-Paketquelle und signierte APT-Indizes. Anwendungspaketierung bleibt getrennt und benötigt den Deployment-Handoff. |

Die öffentliche Bereitstellung auf PyPI oder einem erreichbaren APT-Server ist
`NOT_EXECUTED`. Ein gebautes Paket oder ein lokaler Index ist keine Veröffentlichung.

## Tatsächlich ausgeführte Prüfungen

- Editable Installation mit `python -m pip install -e '.[dev]'`: PASS.
- pytest: **226 bestanden**, einschließlich Paketverwaltung, Nachweisbindung,
  Migration/Rollback, Wheel-/Debian-Validierung und Requirements-Installation.
- `ruff check .`: PASS; `mypy src`: PASS, 46 Quelldateien.
- `bandit -q -ll -r src`: PASS; `pip-audit`: keine bekannten Schwachstellen gefunden.
- Alle fünf CLI-Hilfen und Wheel-/sdist-Build: PASS.
- Die fünf geforderten Selfcheck-Befehle wurden ausgeführt, jeweils Exitcode 0.
  **Die fachlichen JSON-Gesamtstatus lauten jeweils `REVIEW_REQUIRED`.**
  Erfolgreiche Befehlsausführung wird nicht mit einer vollständigen Policy-Freigabe
  gleichgesetzt. Rohdaten: `.auditcore/verification/results.json` und
  `.auditcore/{core,quality,consolidator,apprefactor,deployer}-selfcheck.json`.

Der installierte Framework-Selfcheck prüft eine frische Wheelinstallation,
tatsächliche Imports aus `site-packages`, fünf installierte CLIs, Paketinventur,
Migration und signierte APT-Installation. Technische Fixtures sind ausdrücklich
keine migrierten Fachanwendungen. Der abschließende lokale Lauf um 16:28 UTC
bestand vollständig: `.auditcore/installed-framework/run-dt88bylk/result.json`.
Wheel-SHA256: `742c82fcd01275bbdfb69c43bd210f5d48800553beb36938becfa5320eb91fb3`.
Alle Schritte verwenden dieselbe unveränderliche Wheelkopie. Der Migrationscheck
erzeugt die Python-Paketquelle über die installierte CLI und prüft die tatsächliche
Requirements-Neuinstallation mit Hash und Downloadpfad im pip-Installationsbericht.
APT-Signatur, Installation, Upgrade, Remove, Manipulationsabwehr und Plattformimport
bestanden ebenfalls. Geprüfter Implementierungsstand: `9962e11`.
CI: [Lauf 35754279581](https://github.com/janpow77/auditcore/actions/runs/35754279581)
scheiterte trotz bestandener Unit-Tests: der frische Runner hatte keinen Zugriff
auf die damals private Framework-Quelle; zwei Python-Versionen trafen zusätzlich
den 15-Sekunden-PyPI-ReadTimeout. Auf ausdrückliche Nutzeranweisung wurde ausschließlich
`verwaltung-app-framework` öffentlich gestellt. Anonymer Git-Zugriff wurde am
unveränderten Commit `15f5338f783f2c7d5760a9bb299be06d27326be0` nachgewiesen.
Keine Deploy-Keys oder Secrets wurden angelegt. Dependency-Audits erhalten nun
60 Sekunden pro Netzabfrage; Fehler werden weiterhin nicht unterdrückt.
Der erneute [CI-Lauf 35754894466](https://github.com/janpow77/auditcore/actions/runs/35754894466)
bestand auf **Python 3.11, 3.12 und 3.13** für Commit
`b6a396f115ef333be9927f79105797ac7171cb2b`. Python 3.12 führte die vollständige
installierte Migration und den signierten APT-Zyklus aus; 3.11/3.13 die installierte
CLI-/Inventurprüfung. Ein weiterer lokaler vollständiger Lauf ohne vorbereiteten
Frameworkcheckout bestand ebenfalls: `.auditcore/installed-framework/run-8xc8whf8/`;
Wheel-SHA256 `d5226f464749e8c79eef7ed635c83f4a3bedf69f1da3748ebbb09d8e617c242b`.
Damit ist der **technische Frameworknachweis abgeschlossen**. Die separat
ausgewiesenen fachlichen Policy-/Releaseentscheidungen bleiben unverändert offen.

### Regression und Integration

Der Migrationsnachweis führt zehn konfigurierte Prüfkategorien tatsächlich aus.
Der positive Fall ändert Klassenimport und Requirements und prüft den installierten
Bibliotheksaufruf. Fehlende oder veraltete Nachweise blockieren vor Änderungen;
ein absichtlich fehlgeschlagener Integrationstest führt zum vollständigen Rollback.
Der Fixture-Quality-Bericht bleibt getrennt sichtbar und kann `REVIEW_REQUIRED`
enthalten. Die Fixture-Belege sind nicht auf reale Anwendungen übertragbar.

### Debian Package Support und Package Installation Tests

Die Plattform baut reine Python-Bibliotheken ohne Downloads in Maintainerskripten.
Laufzeitabhängigkeiten benötigen eine explizite Debian-Zuordnung. Ein eigener
Testsignaturschlüssel und `signed-by` sichern den lokalen APT-Test; manipulierte
Indizes müssen abgewiesen werden. Der Container hat bei der Installation kein Netz.

Die Anwendungsfixtures wurden zusätzlich unter echtem systemd als PID 1 in einer
isolierten QEMU-VM geprüft: **12 Prüfungen PASS**, einschließlich MainPID,
Servicekonto, Healthcheck, Upgrade, Entfernung und Datenerhalt.
[Umfang, Artefaktdigests und Grenzen](../deployment/systemd-validation.md).
Keine reale Anwendung erhielt dadurch `READY_FOR_DEPLOYMENT`.

## Externe Inventur und offene Entscheidungen

| Feld | Status |
|---|---|
| GitHub Inventory / Repositories found | Historische Erstinventur: 71 Repositories, 84.752 Symbole; PARTIAL wegen zwei Parsefehlern. Kein erneuter vollständiger Scan in dieser Framework-Prüfung. |
| KIRA | Konfiguriert; historischer Sync PARTIAL. Unsichere Schreibvorgänge werden journalisiert und per exaktem Rücklesen abgeglichen, ohne blindes erneutes Senden. |
| Graphify | Frühere Codeanalyse von fünf Repositories ausgeführt; kein neuer Graphify-Lauf für die Framework-Erweiterung behauptet. Lokale AST-Analyse verfügbar. |
| Library Candidates | Konservative neue Filter implementiert und getestet; historische 2.438 Rohkandidaten sind keine freigegebenen Pakete. |
| Libraries / Modules created | In Phasen 1–2 keine neuen Fachpakete; bestehendes `auditcore.reporting` bleibt kompatibel. |
| Applications migrated / optimized | In dieser Phase keine realen Anwendungen; technische Fixture-Migration separat nachgewiesen. |
| Applicable Framework Tests | Anwendbarkeit ausgewertet; vorhandene technische Tests ausgeführt. Ausstehende Governance-/Releasebelege bleiben REVIEW_REQUIRED. |
| Policy Review Required | Quellengebundene F-09-/F-15-Belege und weitere je Werkzeug anwendbare Anforderungen; keine pauschale Freigabe aus Unit-Tests. |
| Human Decisions Required | Lizenz-/Veröffentlichungsrechte ungeklärter Quellrepos sowie fachlich abweichende Regeln vor realer Harmonisierung. |
| Open Blockers | Unvollständiger KIRA-Sync und reale Consumer-/Releasebelege. Diese verhindern keine lokale technische Paketentwicklung, bleiben aber Freigabegrenzen. |

Weitere Pakete entstehen erst nach dem technischen Frameworknachweis, anhand
konkreter Quellen und Characterization. Leere Domain-Pakete werden nicht angelegt.
