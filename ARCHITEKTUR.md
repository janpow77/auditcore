# Architektur — auditcore

Monorepo-Architektur für die standardisierte Prüfung, Verifikation und Digitalisierung von Förder- und Finanzprozessen (EFRE/ESF+ Prüfbank, Rechnungsverarbeitung und Vorhabenprüfung).

---

## 1. Systemübersicht & Monorepo-Topologie

Das Repository ist als striktes Clean-Domain-Monorepo aufgebaut: Es trennt Plattform-Werkzeuge, wiederverwendbare Fachbibliotheken (Domain Cores) und modulare UI-Komponenten sauber voneinander.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            auditcore Monorepo                               │
├──────────────────────────────┬──────────────────────────────┬───────────────┤
│  Plattform-Tools & CLI       │  Python-Fachpakete (Domain)  │  Frontend UI  │
│  - src/auditcore/quality     │  - packages/auditcore_common │  - packages-js│
│  - src/auditcore/codegate    │  - packages/auditcore_risk   │  - BPMN, Vue  │
│  - src/auditcore/runner      │  - packages/auditcore_pdf    │  - React, Web │
├──────────────────────────────┴──────────────────────────────┴───────────────┤
│  Verträge, Schnittstellen & Qualitätssicherung                              │
│  - contracts/ (JSON-Schemas, Typverträge, Testfälle)                        │
│  - quality/ (Qualitäts-Ratchet baseline.json, Institutslisten)              │
│  - scripts/ (Build-, Paketierungs-, Release- und Validierungsskripte)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Top-Level Verzeichnisstruktur & Datei-Inventar

| Verzeichnis / Datei | Typ | Zweck & Inhalt |
| :--- | :--- | :--- |
| [`packages/`](packages/) | Domänenpakete | 32 eigenständige Python-Bibliotheken (reine Fachdomänen ohne Web- oder ORM-Abhängigkeiten). |
| [`packages-js/`](packages-js/) | UI-Pakete | 10 modulare TypeScript-, Vue- und React-Pakete (z. B. `@auditcore/bpmn-vue`, `@auditcore/ui-core`). |
| [`src/auditcore/`](src/auditcore/) | Plattform-Kern | Plattform-Engine, CLI-Werkzeuge (`codegate`, `consolidator`, `apprefactor`, `policy`, `deployer`). |
| [`contracts/`](contracts/) | Schnittstellen | Formale JSON-Schemas, API-Verträge und gemeinsame Validierungsfälle (`common-cases/`). |
| [`docs/`](docs/) | Dokumentation | Umfassende Handbücher, Fachberichte, Migrationsleitfäden und Prüfdokumentation (siehe [`docs/README.md`](docs/README.md)). |
| [`examples/`](examples/) | Integrationen | Minimale Referenzintegrationen für Consumer-Anwendungen (React, Vue, Web Components). |
| [`quality/`](quality/) | Code-Gates | Qualitäts-Ratchet [`quality/baseline.json`](quality/baseline.json) sowie Institutsnamens-Deny-/Allowlisten. |
| [`requirements/`](requirements/) | Abhängigkeiten | Gependelte Lockfiles ([`requirements/ci.lock`](requirements/ci.lock)) und Werkzeug-Spezifikationen. |
| [`scripts/`](scripts/) | Automatisierung | CI-Checks, Landing-Page-Builder, Paketindex-Erstellung, APT-Paketierung und Release-Helfer. |
| [`tests/`](tests/) | Integrationstests | Monorepo-weite Verifikationstests, Code-Gate-Suites und Prüfbank-Integrationstests. |
| [`ci/`](ci/) | CI-Konfiguration | Spezifikationen und Hilfsskripte für Runner-Umgebungen und GitHub Actions. |
| [`contexts/`](contexts/) | Ausführungskontexte | Strukturierte JSON-Kontexte für Plattformwerkzeuge (`core.json`, `quality.json`, etc.). |
| [`packaging/`](packaging/) | Paketierung | Metadaten und Extras-Konfigurationen für Python- und OS-Pakete. |

### Zentrale Steuerungs- und Konfigurationsdateien

- [`.auditcore-runner.toml`](.auditcore-runner.toml): Konfiguration der lokalen und CI-Prüfprofile für den `auditcore-runner` (`checklists`, `pdf`, `privacy`, `runner`, `schnell`, `voll`).
- [`pyproject.toml`](pyproject.toml): Monorepo-Workspace-Konfiguration (Ruff, Mypy, Pytest, Pyrefly, Setuptools).
- [`package.json`](package.json) / [`package-lock.json`](package-lock.json): Root-Konfiguration der JavaScript/TypeScript-Toolchain und Workspaces.
- [`eslint.config.mjs`](eslint.config.mjs): Zentrales Flat-Config-Regelwerk für JavaScript, TypeScript und Vue.
- [`playwright.config.ts`](playwright.config.ts): Konfiguration für automatisierte E2E- und Rendering-Prüfungen der UI-Komponenten.
- [`renovate.json5`](renovate.json5) & [`.github/dependabot.yml`](.github/dependabot.yml): Wöchentliche, gruppierte Aktualisierungsregeln für Dev-Tools und Actions.
- [`AUDITCORE_LASTENHEFT.md`](AUDITCORE_LASTENHEFT.md): Verbindliches Anforderungs- und Pflichtenheft mit 5 Phasen, Migrationsregeln und CI-Kriterien.
- [`CHANGELOG.md`](CHANGELOG.md): Historie sämtlicher veröffentlichter Versionen nach Keep-a-Changelog-Standard.
- [`README.md`](README.md): Zentrale Übersicht, Anwendungsphasen, Framework-Spezifikationen und Paketkatalog.

---

## 3. Modulkarte der Fachbibliotheken (`packages/`)

Die 32 Python-Pakete decken fünf Kernbereiche des Prüfwesens ab:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Phasen des Prüfprozesses                          │
├─────────────────────┬───────────────────────┬───────────────────────────────┤
│ Phase 1: Stammdaten │ Phase 2: Risiko & Vergabe │ Phase 3: Buchung & Stichprobe │
│ - auditcore_account │ - auditcore_procurement   │ - auditcore_sampling          │
│ - auditcore_auth    │ - auditcore_risk          │ - auditcore_extrapolation     │
│ - auditcore_geo     │ - auditcore_market_indic. │ - auditcore_statistics        │
├─────────────────────┴───────────────────────┴───────────────────────────────┤
│ Phase 4: Beleg- & Rechnungsprüfung         │ Phase 5: Checklisten & Bericht  │
│ - auditcore_invoicesynth / invoicegenerator │ - auditcore_checklists        │
│ - auditcore_documents / pdf / privacy       │ - auditcore_reporting / bpmn  │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Fundament & Querschnitt:**
   - [`auditcore_common`](packages/auditcore_common/): Universelle Basistypen, Hash-Prüfsummen, Validierungslogik und Fehlerklassen.
   - [`auditcore_identifiers`](packages/auditcore_identifiers/): Validierung von Steuernummern, USt-IdNr., IBAN, Aktenzeichen und Kennungen.
   - [`auditcore_auth`](packages/auditcore_auth/) & [`auditcore_account`](packages/auditcore_account/): Rollen, Rechte, Mandanten und Benutzerverwaltung.
   - [`auditcore_runner`](packages/auditcore_runner/): Einheitliche Prüfbank (`auditcore-runner`) für standardisierte Code-, Sicherheits- und Fachprüfungen.

2. **Vergabe & Beschaffung:**
   - [`auditcore_procurement`](packages/auditcore_procurement/): EU-Schwellenwerte, Vergabeverfahren und Fristenprüfung nach VgV/UVgO.
   - [`auditcore_market_indicators`](packages/auditcore_market_indicators/): Marktpreisindikatoren und statistische Preisvergleiche.
   - [`auditcore_price_analysis`](packages/auditcore_price_analysis/) & [`auditcore_price_sources`](packages/auditcore_price_sources/): Preisdatenquellen und Wirtschaftlichkeitsanalysen.

3. **Risikoanalyse & Datenabgleich:**
   - [`auditcore_risk`](packages/auditcore_risk/): Risikobewertung, VerwK-Scores und Anomalieerkennung.
   - [`auditcore_entity_matching`](packages/auditcore_entity_matching/): Unscharfer Dublettenabgleich und Namensharmonisierung.
   - [`auditcore_registry_sources`](packages/auditcore_registry_sources/) & [`auditcore_property_sources`](packages/auditcore_property_sources/): Schnittstellen zu Handelsregistern und Geodaten.

4. **Finanzmathematik, Stichproben & Hochrechnung:**
   - [`auditcore_sampling`](packages/auditcore_sampling/): Statistische Stichproben nach KOM-Leitfaden (MUS, Zufallsauswahl, Schichtungsverfahren).
   - [`auditcore_extrapolation`](packages/auditcore_extrapolation/): Fehlerhochrechnung und Konfidenzintervalle nach Leitfaden EGESIF_16-0014-01.
   - [`auditcore_statistics`](packages/auditcore_statistics/): Deskriptive Statistiken, Benford-Analyse und Chi²-Konformitätstests.

5. **Dokumente, Datenschutz & Berichte:**
   - [`auditcore_pdf`](packages/auditcore_pdf/): Revisionssichere PDF-Manipulation, Zertifikatsprüfung und Schwärzungslogging.
   - [`auditcore_privacy`](packages/auditcore_privacy/): DS-GVO-konforme Pseudonymisierung, Maskierung und Hash-Erzeugung.
   - [`auditcore_checklists`](packages/auditcore_checklists/): Prüflisten, hierarchische Fragebäume und Prüfpfade mit Im- und Export.
   - [`auditcore_reporting`](packages/auditcore_reporting/): Textbausteine, Word-/PDF-Export und Berichtsgenerierung.
   - [`auditcore_bpmn`](packages/auditcore_bpmn/): Prüf- und Prozessdiagramme im BPMN 2.0-Standard.

---

## 4. Frontend- und UI-Architektur (`packages-js/`)

Die UI-Bibliotheken bilden ein modulares Designsystem für Vue 3 und React:
- [`@auditcore/ui-core`](packages-js/ui-core/): Framework-agnostischer Zustand und Hilfsfunktionen.
- [`@auditcore/ui`](packages-js/ui/): Wiederverwendbare Vue-3-Komponenten (Runner-Konsole, Tabellen, Filter).
- [`@auditcore/ui-react`](packages-js/ui-react/): Native React-Entsprechungen für Prüftabellen und Synopsen.
- [`@auditcore/bpmn-vue`](packages-js/bpmn-vue/) & [`@auditcore/bpmn-editor`](packages-js/bpmn-editor/): BPMN-Visualisierung und Workflow-Editor.
- [`@auditcore/kanban-core`](packages-js/kanban-core/): Statusboards für Prüfungs- und Feststellungsabläufe.
- [`@auditcore/layout`](packages-js/layout/): Einheitliche Seiten-Layouts, Kopfzeilen und Navigation.

---

## 5. Zentrale Bausteine & Hotspots (Clean Domain)

1. **Clean Domain & Framework-Freiheit:**
   - Fachpakete (`packages/auditcore_*`) importieren **weder Web-Frameworks** (FastAPI, Flask) **noch Datenbank-ORMs** (SQLAlchemy, Tortoise).
   - Fachlogik ist deterministisch, thread-sicher und rein funktional oder über reine Datenklassen modelliert.
   - Schnittstellen nach außen erfolgen über Eingabe- und Ausgabemodelle (Pydantic / Dataclasses).

2. **Hierarchischer Datenfluss & Zyklenfreiheit:**
   - Der Datenfluss verläuft streng gerichtet:
     ```
     Anwendung / Consumer (z. B. audit_designer)
        │
        ▼
     Spezifische Fachbibliothek (z. B. auditcore_sampling, auditcore_pdf)
        │
        ▼
     Basisbibliothek (auditcore_common)
     ```
   - Zirkuläre Abhängigkeiten zwischen Fachpaketen sind durch Architekturtests (`tests/test_architecture.py`) verboten.

3. **Qualitäts-Ratchet & Invarianten:**
   - Code-Metriken (Komplexität, Typabdeckung, Zeilenanzahl) dürfen sich nie verschlechtern; Verbesserungen werden automatisch in [`quality/baseline.json`](quality/baseline.json) ratchetiert.
   - Fachpakete sichern ihre Invarianten über hypothesenbasierte Eigenschaftstests (`tests/test_spezifikation.py`).
