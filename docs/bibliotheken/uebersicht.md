# Bibliotheken im Überblick

auditcore verwaltet eigenständig installierbare Bibliotheken: Python-Pakete
unter `packages/` (pip und APT) und npm-Pakete unter `packages-js/`
(npm-Workspace). Anwendungen bleiben in ihren eigenen Repositories und
beziehen die Pakete über den Paketindex bzw. die APT-Quelle
([Installation](../deployment/package-feed.md)). Jede Paket-README folgt der
[README-Vorlage](readme-vorlage.md).

## Einordnung

**Querschnitt** – fachneutrale Bausteine, die andere Pakete nutzen:
`auditcore_common` (gemeinsame, verhaltensgleich nachgewiesene Hilfsfunktionen)
und `auditcore_harvest` (Abrufkern für Quellenadapter: Vertrag, Paging,
Wiederholung, Checkpoints). Vorgesehen, aber noch nicht in `main`:
`auditcore_auth`, `auditcore_identifiers` und `auditcore_llm_client`; sie
erscheinen im Katalog, sobald ihre Pull Requests gemergt sind.

**Fachbibliotheken** – Prüf- und Verwaltungslogik ohne Webframework oder
Datenbank: Stichprobe, Statistik, Risiko-Merkmale, Vergabe, Datenschutz,
Dokumentenvergleich, Preis- und Marktberechnungen, Geodaten, Kanban,
Berichtsformate sowie die synthetischen Generatoren für Testdaten und
Rechnungen.

**Quellen-Adapter** (`*_sources`) – Anbindung externer Veröffentlichungen und
Register auf dem Vertrag von `auditcore_harvest`: Rechtsquellen, Förder- und
Beihilfetransparenz, Register- und Sanktionslisten, Preis- und Immobilienquellen.
Die Adapter liefern Datensätze mit Herkunft; Speicherung, Zeitplanung und
Zugangsdaten bleiben bei der Anwendung.

**Oberfläche und Frontend-Logik (npm)** – `@flowaudit/ui` (Vue-3-Komponenten,
Web Components, Theming, i18n), `@flowaudit/ui-react` (React-Hüllen für die
Web Components), `@flowaudit/kanban-core` (framework-freie Kanban-Regeln mit
Parität zu `auditcore_kanban`) und `@flowaudit/bpmn-editor`
(BPMN-2.0-Editor).

**Status** im Katalog: *charakterisiert* – Verhalten der Quellanwendungen vor
der Übernahme aufgezeichnet und im Paket als Test nachgewiesen (legacy-exakt,
Abweichungen nur dokumentiert); *neu, gegen charakterisierte Verträge* –
Neuimplementierung, deren Schnittstellen und Regeln aus charakterisierten
Anwendungen stammen; *konsolidiert* – zusammengeführte Hilfsfunktionen mit
Gleichheitsnachweis; *neu* – ohne Vorläufer.

## Katalog

<!-- paketkatalog:start (generiert: python scripts/docs/catalog.py --write) -->
### Querschnitt

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_common`](../../packages/auditcore_common) | 0.1.0 | Shared, behaviour-proven helpers of the auditcore domain packages (JSON, hashing, profiles, safe XML, HTML, numerics) | keine; Extras: `xml` | konsolidiert (Gleichheitsnachweis) |
| [`auditcore_harvest`](../../packages/auditcore_harvest) | 0.1.1 | Shared harvest core: source contracts, paging/retry engine, checkpoints and adapter contract tests | keine | neu, gegen charakterisierte Verträge |

### Fachbibliotheken

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_dataprotection`](../../packages/auditcore_dataprotection) | 0.4.1 | Framework-independent records of processing activities and DPIA calculation | keine; Extras: `excel`, `pdf` | charakterisiert |
| [`auditcore_documents`](../../packages/auditcore_documents) | 0.3.0 | Characterized document comparison, German article-law synopsis and document pipeline core without web or database dependencies | keine; Extras: `docx`, `pdf-text`, `fuzzy`, `docx-render`, `pdf-render`, `mime`, `ocr-raster`, `donut`, `web`, `fastapi` | charakterisiert |
| [`auditcore_dummygenerator`](../../packages/auditcore_dummygenerator) | 0.1.1 | Framework-independent synthetic field and row generation | keine; Extras: `parallel` | charakterisiert |
| [`auditcore_entity_matching`](../../packages/auditcore_entity_matching) | 0.2.1 | Characterized entity name normalisation, LEI checks and transparent fuzzy matching | keine; Extras: `fuzzy` | charakterisiert |
| [`auditcore_geo`](../../packages/auditcore_geo) | 0.2.0 | Charakterisierter Geokern ohne Fremdabhängigkeiten: Großkreisentfernung mit ausdrücklichem Erdmodell, Umkreissuche, Punkt in Fläche mit erkanntem Rand, UTM, GeoPackage-Polygone und Douglas-Peucker. | keine; Extras: `geocoder` | charakterisiert |
| [`auditcore_invoicegenerator`](../../packages/auditcore_invoicegenerator) | 0.2.1 | Characterized synthetic invoice profiles and explicit test scenarios | `auditcore_dummygenerator==0.1.1`; Extras: `pdf` | charakterisiert |
| [`auditcore_invoicesynth`](../../packages/auditcore_invoicesynth) | 0.1.0 | Synthetische Trainings- und Testdaten für eine Donut-basierte Erkennung deutscher und österreichischer Rechnungen: Rechnungsbilder, Ziel-JSON, Manifest mit Datensatz-Hash und Bewertung. | `auditcore_invoicegenerator==0.2.1`; Extras: `render`, `train` | neu |
| [`auditcore_kanban`](../../packages/auditcore_kanban) | 0.1.0 | Framework-free Kanban domain: boards, rank keys, transitions, WIP limits, rights, events and a REST contract | keine; Extras: `ui`, `fastapi` | neu, gegen charakterisierte Verträge |
| [`auditcore_market_indicators`](../../packages/auditcore_market_indicators) | 0.1.0 | Technische Marktindikatoren (Renditen, SMA/EMA, RSI, ATR, ADX, MACD, Volatilität, Z-Score, Breakout) auf einfachen Zahlenfolgen, mit ausdrücklich gewählten, quellengebundenen Profilen. | keine; Extras: `polars` | neu, gegen charakterisierte Verträge |
| [`auditcore_price_analysis`](../../packages/auditcore_price_analysis) | 0.1.1 | Exact tariff calculation (district heating, water, tiers), tariff selection and comparison rules with versioned profiles | keine | charakterisiert |
| [`auditcore_procurement`](../../packages/auditcore_procurement) | 0.2.2 | Procurement notice records (TED, HAD), import normalisation and versioned prechecks | `auditcore_common==0.1.0`; Extras: `html`, `sources` | charakterisiert |
| [`auditcore_reporting`](../../packages/auditcore_reporting) | 0.2.0 | Charakterisierte Flowlib-Zahlenformate für Berichte (Spaltenname → Excel-Zahlenformat) mit benannten Formatprofilen und optionalem, abgesichertem XLSX-Export. | keine; Extras: `excel` | charakterisiert |
| [`auditcore_risk`](../../packages/auditcore_risk) | 0.3.1 | Risk flags from explicit, versioned, source-bound rule profiles (legacy-exact riskanalysis and Flowstat red flags) | `auditcore_entity_matching==0.2.1`; Extras: `fuzzy`, `pandas`, `procurement` | charakterisiert |
| [`auditcore_sampling`](../../packages/auditcore_sampling) | 0.2.0 | Audit sampling sizes, selection and allocation with named method profiles | keine; Extras: `web` | charakterisiert |
| [`auditcore_statistics`](../../packages/auditcore_statistics) | 0.3.1 | Descriptive audit statistics (Benford) with named method profiles | keine; Extras: `web` | charakterisiert |

### Quellen-Adapter

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_funding_sources`](../../packages/auditcore_funding_sources) | 0.1.2 | Beneficiary, state aid and de-minimis source parsers, identities and cumulation | `auditcore_harvest==0.1.1`; Extras: `xlsx` | charakterisiert |
| [`auditcore_legal_sources`](../../packages/auditcore_legal_sources) | 0.1.1 | Framework-independent legal and audit publication source adapters (DIP, EUR-Lex) | `auditcore_harvest==0.1.1`; Extras: `feeds` | charakterisiert |
| [`auditcore_price_sources`](../../packages/auditcore_price_sources) | 0.1.0 | Price and market data adapters (Bundesbank, Destatis GENESIS, EIA, Tankerkoenig, Overpass, EU Oil Bulletin) on auditcore_harvest | `auditcore_harvest==0.1.1` | neu, gegen charakterisierte Verträge |
| [`auditcore_property_sources`](../../packages/auditcore_property_sources) | 0.1.0 | Property source profiles (Berlin/French rental portals, ZVG forced-auction notices) with harvest adapters, lifecycle and access catalog | keine; Extras: `sources` | charakterisiert |
| [`auditcore_registry_sources`](../../packages/auditcore_registry_sources) | 0.2.0 | Register, sanctions and PEP source adapters, list parsers, screening profiles and a screening review API | `auditcore_harvest==0.1.1`, `auditcore_entity_matching==0.2.1`; Extras: `fuzzy`, `xml`, `html`, `web`, `fastapi` | charakterisiert |

### Oberfläche und Frontend-Logik (npm)

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`@flowaudit/bpmn-editor`](../../packages-js/bpmn-editor) | 0.1.0 | Eigener BPMN-2.0-Zeicheneditor auf Basis von diagram-js und bpmn-moddle (Clean-Room, MIT) | `bpmn-moddle@^10.3.1`, `diagram-js@^15.27.1`, `didi@^11.0.0`, `min-dash@^5.1.0`, `min-dom@^5.3.0`, `tiny-svg@^4.1.4` | neu |
| [`@flowaudit/kanban-core`](../../packages-js/kanban-core) | 0.1.0 | Framework-freie Kanban-Logik (Rang, Übergänge, WIP, Filter, Rechte) – gleiche Regeln wie auditcore_kanban | keine | neu |
| [`@flowaudit/ui`](../../packages-js/ui) | 0.1.0 | Gemeinsame FlowAudit-Oberflächenkomponenten: Vue 3, Web Components, Theming und i18n | `@flowaudit/kanban-core@0.1.0`, `vue@^3.5.0` (peer) | neu |
| [`@flowaudit/ui-react`](../../packages-js/ui-react) | 0.1.0 | React-18-Hüllen für die Web Components von @flowaudit/ui | `@flowaudit/kanban-core@^0.1.0` (peer), `@flowaudit/ui@^0.1.0` (peer), `react@^18.3.0` (peer), `react-dom@^18.3.0` (peer), `vue@^3.5.0` (peer) | neu |
<!-- paketkatalog:end -->
