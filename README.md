# auditcore

Frameworkunabhängige Fachbibliothek und vier Werkzeuge in **einem Python-Projekt
mit einem Releasezyklus**. Verbindliche Spezifikation:
[AUDITCORE_LASTENHEFT.md](AUDITCORE_LASTENHEFT.md).

| Bereich | Aufgabe |
|---|---|
| `auditcore` | Fachmodelle, versionierte Regeln, Provenienz, Reporting |
| `auditcore.tools.quality` | Deterministische technische Quality Gates |
| `auditcore.tools.consolidator` | Inventur, Vergleich, Kandidaten, Pläne |
| `auditcore.tools.apprefactor` | Characterization, Migration, Wrapper, Verifikation |
| `auditcore.tools.deployer` | Build, Debian, Pakettests, signierte APT-Metadaten |

Der Fachkern importiert keine Tools, Webframeworks, HTTP-Clients oder Datenbanken.
Neue Fachlogik gehört standardmäßig in ein Domain-Modul innerhalb `auditcore`.
Die vorhandene Funktion `auditcore.reporting.get_number_format` wurde mit
34 Characterization-Fällen aus Flowlib übernommen; Herkunft und MIT-Lizenz
stehen unter `docs/provenance` und `LICENSES`.

## Installation

Python 3.11 oder neuer, für Entwicklung:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

Der Core benötigt nur die Standardbibliothek. Extras: `quality`, `analysis`,
`deploy`, `all`. GitHub-Zugriff nutzt eine bereits angemeldete `gh`-CLI.
Debian-Builds benötigen `dpkg-deb`; isolierte Pakettests benötigen Docker auf
**dem Buildsystem**, nicht auf dem Zielserver.

## Quality Gates

```bash
auditcore-quality src/auditcore --strict --format json --output core.json
auditcore-bibquality src/auditcore/tools/quality
auditcore-bibquality src/auditcore/tools/consolidator
auditcore-bibquality src/auditcore/tools/apprefactor
auditcore-bibquality src/auditcore/tools/deployer
auditcore-quality src/auditcore --api-snapshot api.json
auditcore-quality src/auditcore --compare-api api.json
```

`auditcore-bibquality` ist ein Alias. `--no-external-tools` markiert Ruff,
Mypy, Bandit und pip-audit als NOT_EXECUTED. Konfiguration steht unter
`[tool.auditcore-bibquality]` in `pyproject.toml`; Ignore-Kommentare werden
sichtbar protokolliert. Core und Tool-Komponenten haben getrennte Prüfumfänge.
[Status- und Exitcode-Semantik](docs/quality-semantics.md).

## Framework und Anwendbarkeit

`GitFrameworkPolicyProvider` liest
`janpow77/verwaltung-app-framework` am dokumentierten Git-Commit. Matrix,
Prüfkatalog, Standardsregister und Security-Dokumente bleiben externe Quelle.
Die lokale Adapterdatei enthält technische Auslöser und Quellhashes, keinen
unabhängigen Anforderungskatalog. Bei Drift bleibt die Bewertung REVIEW_REQUIRED.

`auditcore-context.json` hält Projektfakten fest. Fehlende Werte sind UNKNOWN.
MUSS verlangt Klärung; BEDINGT prüft den konkreten Auslöser; SOLL bleibt eine
Empfehlung. Profile sind nur abgeleitete Gruppierungen. Eine genehmigte Abweichung
benötigt einen vollständigen zuständigen menschlichen Entscheidungsnachweis.
Der Provider selbst stellt diesen niemals aus. Cache: `.auditcore/framework-cache.json`;
offline oder bei unterschiedlichem Remote-Commit immer POLICY_SOURCE_STALE.

## Inventur und Konsolidierung

```bash
auditcore-consolidate inventory --global
auditcore-consolidate inventory --update
auditcore-consolidate libraries
auditcore-consolidate analyse /path/to/application --with-auditcore
auditcore-consolidate migrate owner/repository:symbol --dry-run
auditcore-consolidate status
```

GLOBAL inventarisiert den authentifizierten Account einschließlich privater,
archivierter, Fork- und Organisations-Repositories. Die strukturelle Analyse
liest Python per AST und Dependency-Manifeste als Daten. Sie importiert keinen
fremden Code. Unveränderte Commitstände werden wiederverwendet. Das lokale
Inventar liegt atomar und mit Dateimodus 0600 unter `.auditcore/inventory`.
Leere/ausgeschlossene Repositories und Parsefehler erhalten explizite Gründe.

REPO ist für lokale UI/API-Arbeiten, REPO_AUDITCORE für Fachlogik und GLOBAL
für die Gesamtlandschaft gedacht. Die konservative automatische Moduswahl nutzt
bei Unklarheit REPO_AUDITCORE. Der Consolidator erzeugt Pläne und verändert keine
Anwendungsimplementierungen. AST-Gleichheit ersetzt keine fachliche Freigabe.
Abweichende Regeln oder Sicherheitsgrenzen erzeugen Entscheidungsbedarf.

## KIRA und Graphify

```bash
export KIRA_MEMORY_URL='https://your-approved-endpoint/api/memory'
# MEMORY_API_KEY über Secret Store/Umgebung bereitstellen, nicht hier eintragen.
auditcore-consolidate kira sync
auditcore-consolidate kira search "Dokumentenparser"
auditcore-consolidate graphify /path/to/repository
```

KIRA nutzt den bestehenden Memory-API-Vertrag `/entries` und `/search`, prüft
vor Indexierung auf Secrets/Datenschutzhinweise und speichert Source-SHAs.
Ein leerer Suchindex bedeutet NOT_FOUND_IN_CURRENT_INDEX. Kein KIRA ersetzt
GitHub als Codequelle. Fehlende URL/Key: NOT_CONFIGURED. HTTP ist ausschließlich
für Loopback-Endpunkte zulässig; Credentials werden nicht über Redirects versendet.

Graphify läuft code-only ohne externes LLM. Fehlt es oder schlägt es fehl,
werden NOT_EXECUTED und die lokalen AST-Abhängigkeiten getrennt ausgegeben.
Die Infrastrukturprovider sind über Protocols austauschbar und werden mit Fakes
ohne externe Systeme getestet.

## AppRefactor, Regression und Optimierung

```bash
auditcore-refactor inspect /path/to/application
auditcore-refactor plan /path/to/application --output plan.json
auditcore-refactor apply plan.json --dry-run
auditcore-refactor apply plan.json
auditcore-refactor verify /path/to/application
auditcore-refactor optimize /path/to/application --safe
```

Ein Plan enthält konkrete Dateien, Imports, Wrapper, Quellhashes, Goldencases,
Policy-Abhängigkeiten und Prüfkommandos. `characterize()` zeichnet tatsächliche
Legacy-Ergebnisse vor Änderungen auf; `compare()` prüft Werte und Exceptiontypen.
`apply()` kontrolliert Quellstand, Sicherheitsgrenzen und Policy vor/nach der
Migration. Fehlgeschlagene Prüfungen stellen Originaldateien wieder her.
Compatibility Wrapper erhalten Signaturen; die Legacy-Bereinigung bleibt ein
separater, nachweisabhängiger Schritt. Sichere Importoptimierung läuft erst nach
Baseline-Verifikation und führt danach die gleiche Prüfsuite aus.

Die Konfiguration `auditcore-verification.json` ordnet folgenden Kategorien
Argumentlisten zu: `shared_library`, `application_unit`, `regression`, `integration`,
`framework`, `ruff`, `typing`, `security`, `dependencies`, `quality`. Fehlende
Kommandos sind NOT_EXECUTED. Befehle werden ohne Shell ausgeführt. Das Projekt
ist für die fachliche Vollständigkeit seiner konkreten Tests verantwortlich.

## Debian, APT und Release

```bash
auditcore-deploy inspect /path/to/application
auditcore-deploy plan /path/to/application
auditcore-deploy build /path/to/application --dry-run
auditcore-deploy build /path/to/application --output dist
auditcore-deploy test-package dist/application.deb
auditcore-deploy test-upgrade dist/old.deb dist/new.deb
auditcore-deploy apt-repo build dist --signing-key YOUR_KEY_ID
```

`auditcore-deploy.json` wird durch `ApplicationDeploymentProfile` beschrieben.
Es benennt Version, Quellcommit/-digest, Entry Point, Runtime-Strategie,
Frontend-Build, Debian-Abhängigkeiten, Servicekonto, Konfiguration, Health-URL
und reproduzierbaren Buildzeitpunkt. Ausgeliefert werden vorgebaute Assets und
entweder Debian-Laufzeitabhängigkeiten oder gehashte Offline-Wheels. `postinst`
führt keine PyPI/npm-Downloads aus. Konfiguration: `/etc/<app>`; persistente
Daten: `/var/lib/<app>`; Programm: `/opt/<app>`; Betrieb über systemd/journald.
`apt remove` und auch `purge` löschen fachliche Daten nicht automatisch.

Ein Build benötigt einen aktuellen READY_FOR_DEPLOYMENT-Handoff und die
Deployment-Policy-Nachweise. DEB_BUILT bedeutet noch keine Paketfreigabe.
Installations-, Upgrade-, Remove-, systemd- und Health-Ergebnisse sind getrennt.
Eine normale Docker-Umgebung kann systemd durch schreibgeschützte cgroups
blockieren; diese Grenze darf nicht als bestandener Diensttest ausgegeben werden.
APT-Publikation benötigt geprüfte Signaturen und einen expliziten Zielpfad.

Wheel/sdist: `python -m build`. SBOMs stammen aus tatsächlichen Wheel-/Paketdateien,
werden gegen CycloneDX 1.6 validiert und über Digests gebunden. Debian-Systempakete
sind deklarierte Dependencies; deren vollständige Betriebssystemauflösung ist
zusätzlich im Installationsumfeld zu erfassen. Keine Zertifizierungsbehauptung.

## Prompts, Policies und Beiträge

Versionierte Prompts unter `consolidator/prompts` werden mittels
`importlib.resources` geladen und mit Hash/Version referenziert. Sie steuern
Analyse, nicht Freigaben. JSON-Policies unter `consolidator/policies` bestimmen
Konsolidierung, Architekturgrenzen, Human Decisions und verpflichtende Tests.
[CONTRIBUTING.md](CONTRIBUTING.md) beschreibt Änderungen und Prüfungen.

Tatsächlicher Umsetzungs- und Prüfstand:
[Platform Build Report](docs/reports/PLATFORM_BUILD_REPORT.md).
