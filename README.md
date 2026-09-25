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

## Pakete

Alle Bibliotheken des Repositorys – Python-Pakete unter `packages/` und
npm-Pakete unter `packages-js/`. Die Tabelle wird aus `pyproject.toml`,
`package.json`, dem Abschnitt „Zweck“ der Paket-README und `provenance.json`
erzeugt; jede Paket-README folgt der
[README-Vorlage](docs/bibliotheken/readme-vorlage.md).

<!-- paketkatalog:start (generiert: python scripts/docs/catalog.py --write) -->
33 Pakete, gruppiert nach Einordnung ([Übersicht](docs/bibliotheken/uebersicht.md)):

**Querschnitt**

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_auth`](packages/auditcore_auth) | 0.1.0 | Passwort-Hashing mit benannten Profilen (bcrypt, argon2id) und JWT-Ausstellung/-Prüfung über PyJWT, mit Kompatibilitätsprofilen, unter denen bisherige Hashes und Token der Anwendungen gültig bleiben. | keine; Extras: `bcrypt`, `argon2`, `jwt`, `fastapi` | neu, gegen charakterisierte Verträge |
| [`auditcore_common`](packages/auditcore_common) | 0.1.1 | Gemeinsame Hilfsfunktionen der auditcore-Fachpakete und Anwendungen (JSON, Hashing, Profile, sicheres XML, HTML-Links, Numerik, Zahleneingabe, Dateinamen, Event-Loop), zusammengeführt nur mit Gleichheitsbeweis gegen jede Paketkopie. | keine; Extras: `xml` | konsolidiert (Gleichheitsnachweis) |
| [`auditcore_harvest`](packages/auditcore_harvest) | 0.1.1 | Shared harvest core: source contracts, paging/retry engine, checkpoints and adapter contract tests | keine | neu, gegen charakterisierte Verträge |
| [`auditcore_identifiers`](packages/auditcore_identifiers) | 0.1.0 | Prüfen und Normalisieren von Kennungen – IBAN, BIC, USt-IdNr. (alle EU-Staaten), Steuer-ID, Steuernummer, LEI und Handelsregisternummer – mit einheitlichem Ergebnisobjekt und benannten Profilen. | keine | neu, gegen charakterisierte Verträge |
| [`auditcore_llm_client`](packages/auditcore_llm_client) | 0.1.1 | Client für den ai-router und das Flow-Agent-Inferenz-Gateway: Chat, Streaming, Embeddings, Rerank, OCR und Health, mit Schwärzung, Wiederholungen und Circuit-Breaker. | keine; Extras: `http` | neu, gegen charakterisierte Verträge |

**Fachbibliotheken**

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_bpmn`](packages/auditcore_bpmn) | 0.1.0 | BPMN 2.0 mit der FlowAudit-Erweiterung (Schema 1.1) sicher lesen, prüfen, vergleichen, neutralisieren und berichten – für Prozessdiagramme von Verwaltungs- und Kontrollsystemen aller Fonds mit geteilter Mittelverwaltung. | keine; Extras: `xml`, `excel`, `pdf`, `legal` | charakterisiert |
| [`auditcore_dataprotection`](packages/auditcore_dataprotection) | 0.4.3 | Framework-independent records of processing activities and DPIA calculation | `auditcore_common==0.1.1`; Extras: `excel`, `pdf` | charakterisiert |
| [`auditcore_documents`](packages/auditcore_documents) | 0.3.2 | Characterized document comparison, German article-law synopsis and document pipeline core without web or database dependencies | `auditcore_common==0.1.1`; Extras: `docx`, `pdf-text`, `fuzzy`, `docx-render`, `pdf-render`, `mime`, `ocr-raster`, `donut`, `web`, `fastapi` | charakterisiert |
| [`auditcore_dummygenerator`](packages/auditcore_dummygenerator) | 0.1.1 | Framework-independent synthetic field and row generation | keine; Extras: `parallel` | charakterisiert |
| [`auditcore_entity_matching`](packages/auditcore_entity_matching) | 0.2.2 | Characterized entity name normalisation, LEI checks and transparent fuzzy matching | `auditcore_common==0.1.1`; Extras: `fuzzy` | charakterisiert |
| [`auditcore_geo`](packages/auditcore_geo) | 0.3.0 | Charakterisierter Geokern ohne Fremdabhängigkeiten: Großkreisentfernung mit ausdrücklichem Erdmodell, Umkreissuche, Punkt in Fläche mit erkanntem Rand, UTM, GeoPackage-Polygone und Douglas-Peucker. | keine; Extras: `geocoder`, `web`, `fastapi` | charakterisiert |
| [`auditcore_invoicegenerator`](packages/auditcore_invoicegenerator) | 0.2.1 | Characterized synthetic invoice profiles and explicit test scenarios | `auditcore_dummygenerator==0.1.1`; Extras: `pdf` | charakterisiert |
| [`auditcore_invoicesynth`](packages/auditcore_invoicesynth) | 0.1.1 | Synthetische Trainings- und Testdaten für eine Donut-basierte Erkennung deutscher und österreichischer Rechnungen: Rechnungsbilder, Ziel-JSON, Manifest mit Datensatz-Hash und Bewertung. | `auditcore_invoicegenerator==0.2.1`; Extras: `render`, `train` | neu |
| [`auditcore_kanban`](packages/auditcore_kanban) | 0.1.0 | Framework-free Kanban domain: boards, rank keys, transitions, WIP limits, rights, events and a REST contract | keine; Extras: `ui`, `fastapi` | neu, gegen charakterisierte Verträge |
| [`auditcore_market_indicators`](packages/auditcore_market_indicators) | 0.1.1 | Technische Marktindikatoren (Renditen, SMA/EMA, RSI, ATR, ADX, MACD, Volatilität, Z-Score, Breakout) auf einfachen Zahlenfolgen, mit ausdrücklich gewählten, quellengebundenen Profilen. | keine; Extras: `polars` | neu, gegen charakterisierte Verträge |
| [`auditcore_price_analysis`](packages/auditcore_price_analysis) | 0.1.1 | Exact tariff calculation (district heating, water, tiers), tariff selection and comparison rules with versioned profiles | keine | charakterisiert |
| [`auditcore_procurement`](packages/auditcore_procurement) | 0.2.2 | Procurement notice records (TED, HAD), import normalisation and versioned prechecks | `auditcore_common==0.1.1`; Extras: `html`, `sources` | charakterisiert |
| [`auditcore_reporting`](packages/auditcore_reporting) | 0.2.1 | Charakterisierte Flowlib-Zahlenformate für Berichte (Spaltenname → Excel-Zahlenformat) mit benannten Formatprofilen und optionalem, abgesichertem XLSX-Export. | keine; Extras: `excel` | charakterisiert |
| [`auditcore_risk`](packages/auditcore_risk) | 0.3.2 | Risk flags from explicit, versioned, source-bound rule profiles (legacy-exact riskanalysis and Flowstat red flags) | `auditcore_common==0.1.1`, `auditcore_entity_matching==0.2.2`; Extras: `fuzzy`, `pandas`, `procurement`, `web`, `fastapi` | charakterisiert |
| [`auditcore_sampling`](packages/auditcore_sampling) | 0.2.1 | Audit sampling sizes, selection and allocation with named method profiles | keine; Extras: `web` | charakterisiert |
| [`auditcore_statistics`](packages/auditcore_statistics) | 0.3.2 | Descriptive audit statistics (Benford) with named method profiles | `auditcore_common==0.1.1`; Extras: `web` | charakterisiert |

**Quellen-Adapter**

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_funding_sources`](packages/auditcore_funding_sources) | 0.1.3 | Quellenprofile für Fördertransparenz, Beihilfen und das zentrale De-minimis-Register: Parser, stabile Identitäten, Bestandssemantik der Harvest-Modi, Registerabgleich und eine versionierte De-minimis-Kumulierung. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.1`; Extras: `xlsx` | charakterisiert |
| [`auditcore_legal_sources`](packages/auditcore_legal_sources) | 0.1.3 | Quellenadapter für Rechts-, Parlaments- und Prüfquellen – Bundestag DIP, EUR-Lex/Cellar, BaFin, CURIA und Europäischer Rechnungshof – mit strikter Antwortprüfung und Normalisierung zu `LegalDocument`. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.1`; Extras: `feeds` | charakterisiert |
| [`auditcore_price_sources`](packages/auditcore_price_sources) | 0.1.1 | Preis- und Marktdatenquellen (Bundesbank, Destatis GENESIS, EIA, Tankerkönig, Overpass, EU Oil Bulletin) als Adapter auf `auditcore_harvest`, mit Einheit, Zeitbezug und Wertstatus je Datensatz. | `auditcore_harvest==0.1.1` | neu, gegen charakterisierte Verträge |
| [`auditcore_property_sources`](packages/auditcore_property_sources) | 0.1.2 | Getrennte Quellprofile für Immobiliendaten – Berliner und französische Mietportale sowie Zwangsversteigerungen des ZVG-Portals – mit Harvest-Adaptern, reinem ZVG-Lebenszyklus und Zugangskatalog. | `auditcore_common==0.1.1`; Extras: `sources` | charakterisiert |
| [`auditcore_registry_sources`](packages/auditcore_registry_sources) | 0.2.1 | Register-, Sanktions- und PEP-Quellen mit quellengebundenen Profilen: Listenformate lesen, Listen über `auditcore_harvest` abrufen, Namen abgleichen, Firmendaten prüfen und Screening-Treffer nachvollziehbar entscheiden. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.1`, `auditcore_entity_matching==0.2.2`; Extras: `fuzzy`, `xml`, `html`, `web`, `fastapi` | charakterisiert |

**Oberfläche und Frontend-Logik (npm)**

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`@flowaudit/bpmn-editor`](packages-js/bpmn-editor) | 0.1.0 | Eigener, vollständiger BPMN-2.0-Zeicheneditor in TypeScript auf Basis von diagram-js und bpmn-moddle, framework-frei und unter MIT-Lizenz. | `bpmn-moddle@^10.3.1`, `diagram-js@^15.27.1`, `didi@^11.0.0`, `min-dash@^5.1.0`, `min-dom@^5.3.0`, `tiny-svg@^4.1.4` | neu |
| [`@flowaudit/bpmn-flowaudit`](packages-js/bpmn-flowaudit) | 0.1.0 | Framework-freie FlowAudit-Fachschicht für den BPMN-Editor: Schema flowaudit 1.0/1.1, Rollen, Kennzeichen, Prüfbezüge, Prüfregeln, Anreicherung, Neutralisierung, Vergleiche, Durchlauftest, Berichte und Export. | `bpmn-moddle@^10.3.1`, `@flowaudit/bpmn-editor@^0.1.0` (peer) | neu |
| [`@flowaudit/bpmn-react`](packages-js/bpmn-react) | 0.1.0 | Dünner, typisierter React-Wrapper um die Web Component `<flowaudit-bpmn-editor>` aus `@flowaudit/bpmn-vue` – für React 18.3 und 19. | `@flowaudit/bpmn-flowaudit@0.1.0`, `@flowaudit/bpmn-vue@0.1.0`, `react@^18.3.0 || ^19.0.0` (peer), `react-dom@^18.3.0 || ^19.0.0` (peer) | neu |
| [`@flowaudit/bpmn-vue`](packages-js/bpmn-vue) | 0.1.0 | Vue-3-Oberfläche des FlowAudit-BPMN-Editors mit Eigenschaften-Panel, Sammlung, Prüfansichten und Export – als Vue-Bibliothek, Web Component `<flowaudit-bpmn-editor>` und eigenständige App. | `@flowaudit/bpmn-editor@0.1.0`, `@flowaudit/bpmn-flowaudit@0.1.0`, `vue@^3.5.0` (peer) | neu |
| [`@flowaudit/kanban-core`](packages-js/kanban-core) | 0.1.0 | Framework-freie Kanban-Logik in TypeScript mit denselben Regeln wie das Python-Paket `auditcore_kanban`: Rang-Schlüssel, Übergänge, WIP-Limits, Filter, Fristen, Rechte, Validierung und reine Befehle. | keine | neu |
| [`@flowaudit/ui`](packages-js/ui) | 0.1.0 | Gemeinsame Oberflächenkomponenten der FlowAudit-Anwendungen als Vue-3-Komponenten und Web Components, mit Designtoken, Hell-/Dunkelmodus und Sprachunterstützung. | `@flowaudit/kanban-core@0.1.0`, `leaflet@^1.9.4`, `vue@^3.5.0` (peer) | neu |
| [`@flowaudit/ui-react`](packages-js/ui-react) | 0.1.0 | React-18-Hüllen für die Web Components aus `@flowaudit/ui`: Objekte werden als Eigenschaften gesetzt und Ereignisse als `onXxx`-Handler verdrahtet. | `@flowaudit/kanban-core@^0.1.0` (peer), `@flowaudit/ui@^0.1.0` (peer), `react@^18.3.0` (peer), `react-dom@^18.3.0` (peer), `vue@^3.5.0` (peer) | neu |
<!-- paketkatalog:end -->

Kein Fachpaket benötigt die Plattformbibliothek zur Laufzeit. Alle Pakete
werden aus eigenen `pyproject.toml` bzw. `package.json` gebaut und haben eigene
Tests, Anwendbarkeitskontexte und Herkunftsnachweise. Anwendungen bleiben
getrennte Repositories. Synthetische Testrechnungen sind keine Zusage eines
Systems zur verbindlichen Rechnungsstellung.

Veröffentlichte Previews (zuletzt
[v0.3.2](https://github.com/janpow77/auditcore/releases/tag/v0.3.2)) enthalten
Wheels, Source-Distributionen und signierte Debian-Pakete; der Paketindex
`https://janpow77.github.io/auditcore/simple/` verlinkt alle Versionen mit
SHA-256. [Installation über Paketindex, Requirements oder APT](docs/deployment/package-feed.md)
und [vollständiger Paketbericht](docs/reports/DOMAIN_PACKAGES_REPORT.md).

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

**Pflicht-Gate Code-Qualität:** `auditcore-codegate check` misst je Paket
Komplexität (McCabe ≤ 10), Modul- und Funktionslängen, `Any`, `mypy --strict`
und englische Bezeichner (bei `packages-js/` auch Dateigrößen und
`eslint-disable`) und vergleicht per Ratchet mit `quality/baseline.json`.
Kein Wert darf steigen, Verbesserungen werden im selben PR mit
`--update-baseline` festgeschrieben. CI-Job, pre-commit-Hook und
Release-Blocker: [Code-Qualitätsmaßstäbe](docs/quality/code-quality.md).

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
