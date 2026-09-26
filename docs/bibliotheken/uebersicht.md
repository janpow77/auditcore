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
| [`auditcore_auth`](../../packages/auditcore_auth) | 0.1.0 | Passwort-Hashing mit benannten Profilen (bcrypt, argon2id) und JWT-Ausstellung/-Prüfung über PyJWT, mit Kompatibilitätsprofilen, unter denen bisherige Hashes und Token der Anwendungen gültig bleiben. | keine; Extras: `bcrypt`, `argon2`, `jwt`, `fastapi` | neu, gegen charakterisierte Verträge |
| [`auditcore_common`](../../packages/auditcore_common) | 0.1.1 | Gemeinsame Hilfsfunktionen der auditcore-Fachpakete und Anwendungen (JSON, Hashing, Profile, sicheres XML, HTML-Links, Numerik, Zahleneingabe, Dateinamen, Event-Loop), zusammengeführt nur mit Gleichheitsbeweis gegen jede Paketkopie. | keine; Extras: `xml` | konsolidiert (Gleichheitsnachweis) |
| [`auditcore_harvest`](../../packages/auditcore_harvest) | 0.1.2 | Gemeinsamer, frameworkunabhängiger Kern für Datenharvester: Quellenvertrag, Abruf mit Pagination, Zeitgrenzen, Rate-Limits und begrenzten Wiederholungen, Dubletten, idempotente Übergabe an eine Senke und Checkpoints. | `auditcore_common==0.1.1`; Extras: `xml` | neu, gegen charakterisierte Verträge |
| [`auditcore_identifiers`](../../packages/auditcore_identifiers) | 0.1.0 | Prüfen und Normalisieren von Kennungen – IBAN, BIC, USt-IdNr. (alle EU-Staaten), Steuer-ID, Steuernummer, LEI und Handelsregisternummer – mit einheitlichem Ergebnisobjekt und benannten Profilen. | keine; Extras: `web`, `fastapi` | neu, gegen charakterisierte Verträge |
| [`auditcore_llm_client`](../../packages/auditcore_llm_client) | 0.1.1 | Client für den ai-router und das Flow-Agent-Inferenz-Gateway: Chat, Streaming, Embeddings, Rerank, OCR und Health, mit Schwärzung, Wiederholungen und Circuit-Breaker. | keine; Extras: `http` | neu, gegen charakterisierte Verträge |

### Fachbibliotheken

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_bpmn`](../../packages/auditcore_bpmn) | 0.1.1 | BPMN 2.0 mit der FlowAudit-Erweiterung (Schema 1.1) sicher lesen, prüfen, vergleichen, neutralisieren und berichten – für Prozessdiagramme von Verwaltungs- und Kontrollsystemen aller Fonds mit geteilter Mittelverwaltung. | keine; Extras: `xml`, `excel`, `pdf`, `legal` | charakterisiert |
| [`auditcore_dataprotection`](../../packages/auditcore_dataprotection) | 0.5.0 | Frameworkunabhängige Bibliothek, mit der Anwendungen eigene Verzeichnisse von Verarbeitungstätigkeiten (VVT) und Datenschutz-Folgenabschätzungen (DSFA) anlegen, berechnen, versionieren, freigeben und ausgeben. | `auditcore_common==0.1.1`; Extras: `excel`, `pdf`, `web`, `fastapi` | charakterisiert |
| [`auditcore_documents`](../../packages/auditcore_documents) | 0.3.3 | Dokumentvergleich (Checklisten und Fließtext aus DOCX/PDF), Gesetzessynopse für Artikelgesetze und ein frameworkunabhängiger Kern der Dokumentpipeline mit OCR-Ports. | `auditcore_common==0.1.1`, `auditcore_identifiers==0.1.0`; Extras: `docx`, `pdf-text`, `fuzzy`, `docx-render`, `pdf-render`, `mime`, `ocr-raster`, `donut`, `web`, `fastapi` | charakterisiert |
| [`auditcore_dummygenerator`](../../packages/auditcore_dummygenerator) | 0.1.2 | Frameworkunabhängiger Generator für synthetische Testdaten: einzelne Felder (Namen, Adressen, Kennungen, Beträge, Datumswerte) und ganze Zeilen mit festem Seed und Bezugsdatum. | keine; Extras: `parallel` | charakterisiert |
| [`auditcore_entity_matching`](../../packages/auditcore_entity_matching) | 0.2.3 | Nachvollziehbare Normalisierung von Firmen- und Personennamen nach benannten, versionierten Profilen, LEI-Prüfung nach ISO 17442 und transparente unscharfe Abgleiche. | `auditcore_common==0.1.1`; Extras: `fuzzy` | charakterisiert |
| [`auditcore_geo`](../../packages/auditcore_geo) | 0.3.0 | Charakterisierter Geokern ohne Fremdabhängigkeiten: Großkreisentfernung mit ausdrücklichem Erdmodell, Umkreissuche, Punkt in Fläche mit erkanntem Rand, UTM, GeoPackage-Polygone und Douglas-Peucker. | `auditcore_common==0.1.1`; Extras: `geocoder`, `web`, `fastapi` | charakterisiert |
| [`auditcore_invoicegenerator`](../../packages/auditcore_invoicegenerator) | 0.2.2 | Synthetische Testrechnungen mit vollständigen Parteien, Positionen, Beträgen und Datumsfeldern, expliziten Fehlerfällen und einem charakterisierten historischen Flowinvoice-Profil; JSON-Ausgabe, PDF optional. | `auditcore_dummygenerator==0.1.2`; Extras: `pdf` | charakterisiert |
| [`auditcore_invoicesynth`](../../packages/auditcore_invoicesynth) | 0.1.2 | Synthetische Trainings- und Testdaten für eine Donut-basierte Erkennung deutscher und österreichischer Rechnungen: Rechnungsbilder, Ziel-JSON, Manifest mit Datensatz-Hash und Bewertung. | `auditcore_common==0.1.1`, `auditcore_invoicegenerator==0.2.2`; Extras: `render`, `train` | neu |
| [`auditcore_kanban`](../../packages/auditcore_kanban) | 0.1.1 | Framework-freies Kanban-Domänenmodell mit Rang-Schlüsseln, Übergangsregeln, WIP-Limits, Rechten, Ereignisprotokoll und einem REST-Vertrag für die Anwendungen der FlowAudit-Familie. | keine; Extras: `ui`, `fastapi` | neu, gegen charakterisierte Verträge |
| [`auditcore_market_indicators`](../../packages/auditcore_market_indicators) | 0.1.2 | Technische Marktindikatoren (Renditen, SMA/EMA, RSI, ATR, ADX, MACD, Volatilität, Z-Score, Breakout) auf einfachen Zahlenfolgen, mit ausdrücklich gewählten, quellengebundenen Profilen. | `auditcore_common==0.1.1`; Extras: `polars` | neu, gegen charakterisierte Verträge |
| [`auditcore_price_analysis`](../../packages/auditcore_price_analysis) | 0.1.2 | Exakte Jahreskostenberechnung für regulierte Tarife (Nahwärme, Wasser mit Staffeln), deterministische Tarifauswahl und Vergleichsregeln (Abweichung, Ampel, Gruppenstatistik) auf versionierten, quellengebundenen Profilen. | `auditcore_common==0.1.1` | charakterisiert |
| [`auditcore_procurement`](../../packages/auditcore_procurement) | 0.2.3 | Vergabebekanntmachungen (TED, HAD) als kanonischer Datensatz mit verhaltensgleicher TED-Normalisierung und Dateiimport sowie deterministische, versionierte Vergabe-Vorprüfungen mit EU-Schwellenwerten je Geltungszeitraum. | `auditcore_common==0.1.1`; Extras: `html`, `sources` | charakterisiert |
| [`auditcore_reporting`](../../packages/auditcore_reporting) | 0.2.2 | Charakterisierte Flowlib-Zahlenformate für Berichte (Spaltenname → Excel-Zahlenformat) mit benannten Formatprofilen und optionalem, abgesichertem XLSX-Export. | keine; Extras: `excel` | charakterisiert |
| [`auditcore_risk`](../../packages/auditcore_risk) | 0.3.3 | Risiko-Merkmale (Red Flags) aus ausdrücklich gewählten, versionierten und quellengebundenen Regelprofilen, jedes Merkmal mit Code, Begründung, Belegwerten und Quellfundstelle. | `auditcore_common==0.1.1`, `auditcore_entity_matching==0.2.3`; Extras: `fuzzy`, `pandas`, `procurement`, `web`, `fastapi` | charakterisiert |
| [`auditcore_sampling`](../../packages/auditcore_sampling) | 0.2.2 | Stichprobenumfänge (MUS, einfache Zufallsstichprobe), systematische MUS-Auswahl, Zufallsauswahl und Schichtung mit ausdrücklich benannten, quellengebundenen Methoden. | `auditcore_common==0.1.1`; Extras: `web` | charakterisiert |
| [`auditcore_statistics`](../../packages/auditcore_statistics) | 0.3.3 | Beschreibende Prüfstatistik (Benford-Test erster und erster zwei Ziffern, Konformitätsmaße nach MAD und z-Test) mit benannten, quellengebundenen Methodenprofilen. | `auditcore_common==0.1.1`; Extras: `web` | charakterisiert |

### Quellen-Adapter

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`auditcore_funding_sources`](../../packages/auditcore_funding_sources) | 0.1.4 | Quellenprofile für Fördertransparenz, Beihilfen und das zentrale De-minimis-Register: Parser, stabile Identitäten, Bestandssemantik der Harvest-Modi, Registerabgleich und eine versionierte De-minimis-Kumulierung. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.2`; Extras: `xlsx` | charakterisiert |
| [`auditcore_legal_sources`](../../packages/auditcore_legal_sources) | 0.1.4 | Quellenadapter für Rechts-, Parlaments- und Prüfquellen – Bundestag DIP, EUR-Lex/Cellar, BaFin, CURIA und Europäischer Rechnungshof – mit strikter Antwortprüfung und Normalisierung zu `LegalDocument`. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.2`; Extras: `feeds` | charakterisiert |
| [`auditcore_price_sources`](../../packages/auditcore_price_sources) | 0.1.2 | Preis- und Marktdatenquellen (Bundesbank, Destatis GENESIS, EIA, Tankerkönig, Overpass, EU Oil Bulletin) als Adapter auf `auditcore_harvest`, mit Einheit, Zeitbezug und Wertstatus je Datensatz. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.2` | neu, gegen charakterisierte Verträge |
| [`auditcore_property_sources`](../../packages/auditcore_property_sources) | 0.1.2 | Getrennte Quellprofile für Immobiliendaten – Berliner und französische Mietportale sowie Zwangsversteigerungen des ZVG-Portals – mit Harvest-Adaptern, reinem ZVG-Lebenszyklus und Zugangskatalog. | `auditcore_common==0.1.1`; Extras: `sources` | charakterisiert |
| [`auditcore_registry_sources`](../../packages/auditcore_registry_sources) | 0.2.2 | Register-, Sanktions- und PEP-Quellen mit quellengebundenen Profilen: Listenformate lesen, Listen über `auditcore_harvest` abrufen, Namen abgleichen, Firmendaten prüfen und Screening-Treffer nachvollziehbar entscheiden. | `auditcore_common==0.1.1`, `auditcore_harvest==0.1.2`, `auditcore_entity_matching==0.2.3`; Extras: `fuzzy`, `xml`, `html`, `web`, `fastapi` | charakterisiert |

### Oberfläche und Frontend-Logik (npm)

| Paket | Version | Zweck | Abhängigkeiten | Status |
|---|---|---|---|---|
| [`@flowaudit/bpmn-editor`](../../packages-js/bpmn-editor) | 0.1.0 | Eigener, vollständiger BPMN-2.0-Zeicheneditor in TypeScript auf Basis von diagram-js und bpmn-moddle, framework-frei und unter MIT-Lizenz. | `bpmn-moddle@^10.3.1`, `diagram-js@^15.27.1`, `didi@^11.0.0`, `min-dash@^5.1.0`, `min-dom@^5.3.0`, `tiny-svg@^4.1.4` | neu |
| [`@flowaudit/bpmn-flowaudit`](../../packages-js/bpmn-flowaudit) | 0.2.0 | Framework-freie FlowAudit-Fachschicht für den BPMN-Editor: Schema flowaudit 1.0/1.1, Rollen, Kennzeichen, Prüfbezüge, Prüfregeln, Anreicherung, Neutralisierung, Vergleiche, Durchlauftest, Berichte und Export. | `bpmn-moddle@^10.3.1`, `@flowaudit/bpmn-editor@^0.1.0` (peer) | neu |
| [`@flowaudit/bpmn-react`](../../packages-js/bpmn-react) | 0.2.0 | Native React-Oberfläche des FlowAudit-BPMN-Editors für React 18.3 und 19 – ohne Vue-Laufzeit und ohne Web Components, auf demselben framework-freien Kern wie `@flowaudit/bpmn-vue`. | `@flowaudit/bpmn-editor@0.1.0`, `@flowaudit/bpmn-flowaudit@0.2.0`, `@flowaudit/ui-core@0.1.0`, `react@^18.3.0 || ^19.0.0` (peer), `react-dom@^18.3.0 || ^19.0.0` (peer) | neu |
| [`@flowaudit/bpmn-vue`](../../packages-js/bpmn-vue) | 0.2.0 | Vue-3-Oberfläche des FlowAudit-BPMN-Editors mit Eigenschaften-Panel, Sammlung, Prüfansichten und Export – als Vue-Bibliothek, Web Component `<flowaudit-bpmn-editor>` und eigenständige App. | `@flowaudit/bpmn-editor@0.1.0`, `@flowaudit/bpmn-flowaudit@0.2.0`, `@flowaudit/ui-core@0.1.0`, `vue@^3.5.0` (peer) | neu |
| [`@flowaudit/common`](../../packages-js/common) | 0.1.0 | Framework-freie Hilfsfunktionen der FlowAudit-Anwendungen in TypeScript: deutsche Formatierung in Berliner Zeit, strikte Zahleneingabe, API-Fehlertexte, REST, Token, CSV, Zeitsteuerung, Sortierung und Prüfziffern. | keine | neu |
| [`@flowaudit/kanban-core`](../../packages-js/kanban-core) | 0.2.0 | Framework-freie Kanban-Logik in TypeScript mit denselben Regeln wie das Python-Paket `auditcore_kanban`: Rang-Schlüssel, Übergänge, WIP-Limits, Filter, Fristen, Rechte, Validierung und reine Befehle. | keine | neu |
| [`@flowaudit/ui`](../../packages-js/ui) | 0.3.0 | Gemeinsame Oberflächenkomponenten der FlowAudit-Anwendungen als Vue-3-Komponenten und Web Components, mit Designtoken, Hell-/Dunkelmodus und Sprachunterstützung. | `@flowaudit/common@0.1.0`, `@flowaudit/kanban-core@0.2.0`, `@flowaudit/ui-core@0.1.0`, `vue@^3.5.0` (peer) | neu |
| [`@flowaudit/ui-core`](../../packages-js/ui-core) | 0.1.0 | Framework-freier Kern der FlowAudit-Oberflächen: Texte, Datentypen der REST-Verträge, View-Modelle, Zustandsautomaten, Ports, Exporte und Stile – gemeinsam für Vue und React. | `@flowaudit/common@0.1.0`, `@flowaudit/kanban-core@0.2.0`, `leaflet@^1.9.4` | neu |
| [`@flowaudit/ui-react`](../../packages-js/ui-react) | 1.0.0 | Native React-Komponenten (React 18/19) der FlowAudit-Oberflächen von Tabelle bis Kanban – ohne Vue, auf den Kernen `@flowaudit/ui-core` und `@flowaudit/kanban-core`. | `@flowaudit/common@0.1.0`, `@flowaudit/ui-core@0.1.0`, `@flowaudit/kanban-core@0.2.0`, `react@^18.3.0 || ^19.0.0` (peer), `react-dom@^18.3.0 || ^19.0.0` (peer) | neu |
<!-- paketkatalog:end -->
