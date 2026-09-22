# auditcore

**Plattformbibliothek zur Herstellung und Pflege eigenständiger Fachbibliotheken.**
Das Repository verwaltet mehrere separat installierbare Python-Pakete. Anwendungen
bleiben in ihren eigenen Repositories und beziehen benötigte Pakete über pip oder APT.
Grundlage: [Lastenheft](AUDITCORE_LASTENHEFT.md) mit der später ausdrücklich vereinbarten
[Mehrpaket-Architektur](docs/architecture/ADR-001-multi-package-monorepo.md).
Der [Umsetzungsplan](docs/architecture/IMPLEMENTATION_PLAN.md) verlangt zuerst das
fertige Framework und seinen technischen Nachweis, danach die Fachbibliotheken.

| Bereich | Aufgabe |
|---|---|
| `auditcore` | Fachmodelle, versionierte Regeln, Provenienz, Reporting |
| `auditcore.tools.quality` | Deterministische technische Quality Gates |
| `auditcore.tools.consolidator` | Inventur, Vergleich, Kandidaten, Pläne |
| `auditcore.tools.apprefactor` | Characterization, Migration, Wrapper, Verifikation |
| `auditcore.tools.deployer` | Build, Debian, Pakettests, signierte APT-Metadaten |

Der Fachkern importiert keine Tools, Webframeworks, HTTP-Clients oder Datenbanken.
Neue Fachbibliotheken erhalten eigene Distributionen unter `packages/` und
keine automatische Laufzeitabhängigkeit von der Plattform oder anderen Fachpaketen.
Die vorhandene Funktion `auditcore.reporting.get_number_format` wurde mit
34 Characterization-Fällen aus Flowlib übernommen; Herkunft und MIT-Lizenz
stehen unter `docs/provenance` und `LICENSES`.

## Eigenständige Fachpakete

| Distribution / Import | Funktion | Pflichtabhängigkeiten |
|---|---|---|
| [`auditcore_dummygenerator`](packages/auditcore_dummygenerator) | Synthetische Felder und Zeilen, feste Seeds/Bezugsdaten, explizite Fehlerszenarien | Keine |
| [`auditcore_invoicegenerator`](packages/auditcore_invoicegenerator) | Vollständige synthetische Rechnungen, Positions-/Betragsdaten, historische Profile und JSON-Ausgabe | `auditcore_dummygenerator==0.1.0` |
| [`auditcore_reporting`](packages/auditcore_reporting) | Charakterisierte Flowlib-Zahlenformate für Berichte | Keine |

Die Installation des Rechnungsgenerators benötigt weder Reporting noch die
Plattformbibliothek. Alle Pakete werden aus eigenen `pyproject.toml` gebaut und
haben eigene Tests, Anwendbarkeitskontexte und Herkunftsnachweise. Anwendungen
bleiben getrennte Repositories. Synthetische Testrechnungen sind keine Zusage
eines Systems zur verbindlichen Rechnungsstellung. PDF-Renderer gehören derzeit
nicht zum Rechnungspaket.

[Paketgrenzen und weitere Kandidaten](docs/architecture/DOMAIN_PACKAGE_PLAN.md).
Der technische Frameworknachweis ist im
[Phasenbericht](docs/reports/FRAMEWORK_PHASES_1_2.md) dokumentiert.

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
auditcore-quality src/auditcore --strict --context contexts/core.json --format json --output core.json
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

`auditcore-context.json` beschreibt die gesamte Plattformdistribution. `contexts/*.json` trennt Core
und ausführbare Werkzeuge; `--context contexts/consolidator.json` wählt den
Artefaktkontext. Unbestimmter Schutzbedarf und KI-Einsatz bleiben UNKNOWN.
MUSS verlangt Klärung; BEDINGT prüft den konkreten Auslöser; SOLL bleibt eine
Empfehlung. Profile sind nur abgeleitete Gruppierungen. Eine genehmigte Abweichung
benötigt einen vollständigen zuständigen menschlichen Entscheidungsnachweis.
Der Provider selbst stellt diesen niemals aus. Cache: `.auditcore/framework-cache.json`;
offline oder bei unterschiedlichem Remote-Commit immer POLICY_SOURCE_STALE.

Nachweise werden je Projekt aus `.auditcore/policy-evidence.json` und
`.auditcore/policy-decisions.json` geladen, jeweils nach Requirement-ID. Technische
Nachweise brauchen `status: VERIFIED`, prüfbare `references` und den aktuellen
Framework-`source_commit` sowie übereinstimmende `artifact`,
`artifact_source_digest` und `context_digest`. `evidence_binding()` berechnet nur
die Bindung und erteilt keine Freigabe. Geänderte Quellen/Kontexte und Belege
anderer Pakete werden abgelehnt. `versioned_artifact_types` unterscheidet etwa
Regelwerke, Prompts und Agenten für die konkrete Testanwendbarkeit.
Abweichungen benötigen zusätzlich die menschlichen
Entscheidungsfelder aus dem Policy-Modell. Unbelegte Selbsterklärungen sind keine
Freigabe. Für den Handoff muss `auditcore-deployment-evidence.json` alle
Betriebsprüfungen mit `status`, `reference`, `reason` und den aktuellen
`source_digest` enthalten. Handoff und Paketplan kontrollieren diesen erneut.

## Inventur und Konsolidierung

```bash
auditcore-consolidate inventory --global
auditcore-consolidate inventory --update
auditcore-consolidate libraries
auditcore-consolidate analyse /path/to/application --with-auditcore
auditcore-consolidate migrate owner/repository:symbol --dry-run
auditcore-consolidate status
auditcore-consolidate packages inventory .
auditcore-consolidate packages status .
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

Die [Mehrpaket-Verwaltung](docs/workspace.md) liest `auditcore-workspace.toml`
und die einzelnen `pyproject.toml`-Dateien, ohne deren Code oder Build-Backends
auszuführen. Sourcehash, API, Abhängigkeiten, Herkunft, bekannte Consumer und
Anwendbarkeitskontext werden pro Distribution persistent erfasst. CURRENT heißt
aktueller Inventarstand, nicht Policy- oder Releasefreigabe.

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
auditcore-refactor plan /path/to/application --library auditcore_fixture==1.0.0 --output plan.json
auditcore-refactor apply plan.json --dry-run
auditcore-refactor apply plan.json
auditcore-refactor verify /path/to/application
auditcore-refactor handoff /path/to/application
auditcore-refactor optimize /path/to/application --safe
```

Ein Plan enthält konkrete Dateien, Imports, Wrapper, Quellhashes, Goldencases,
Policy-Abhängigkeiten und Prüfkommandos. `characterize()` zeichnet tatsächliche
Legacy-Ergebnisse vor Änderungen auf; `compare()` prüft Werte und Exceptiontypen.
Klassenmethoden einschließlich Konstruktorargumenten und reine Importmigrationen
werden durch explizite `characterization_checks` unterstützt. Frische Belege nach
einer Änderung müssen aus tatsächlich erneut ausgeführten Prüfungen stammen.
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

Für Bibliotheken ohne Anwendungsdienst stehen eigenständige installierte Befehle bereit:

```bash
auditcore-deploy build-python /path/to/package --output dist --source-date-epoch 1700000000
auditcore-deploy build-library dist/auditcore_fixture-1.0.0-py3-none-any.whl \
  --output dist/debian --source-date-epoch 1700000000 \
  --maintainer 'Packaging Test <packaging@example.invalid>'
auditcore-deploy pip-index dist/auditcore_fixture-1.0.0-py3-none-any.whl --output dist/simple
```

`auditcore_fixture` ist ein technischer Beispielname, keine veröffentlichte Fachbibliothek.
Bibliotheksbuilds benötigen keinen erfundenen Anwendungs-Handoff. Sie bekommen
eigene Build-/Install-/Lizenzstatus; ein lokaler Testbau ist keine Veröffentlichung.
Details: [pip-/APT-Paketierung](docs/deployment/library-installation.md).
Die folgenden Befehle betreffen dagegen vollständige Anwendungen:

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

Ein Anwendungsbuild benötigt einen aktuellen READY_FOR_DEPLOYMENT-Handoff und die
Deployment-Policy-Nachweise. DEB_BUILT bedeutet noch keine Paketfreigabe.
Installations-, Upgrade-, Remove-, systemd- und Health-Ergebnisse sind getrennt.
Eine normale Docker-Umgebung kann systemd durch schreibgeschützte cgroups
blockieren; diese Grenze darf nicht als bestandener Diensttest ausgegeben werden.
Die [isolierte QEMU-Prüfung](docs/deployment/systemd-validation.md) hat den
tatsächlichen systemd-Lifecycle für technische Testpakete nachgewiesen.
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
