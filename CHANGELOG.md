# Changelog

## Unreleased

- npm `@auditcore/bpmn-flowaudit`, `@auditcore/bpmn-vue` und
  `@auditcore/bpmn-react` 0.4.0: Reiter „Prüfungsmerkmale“ – Name/Wert-Merkmale
  nach dem Profil (`profile.properties`), gespeichert als `camunda:property` und
  damit im Camunda Modeler lesbar. Keine feste Merkmalsliste in der Bibliothek;
  Laden und Speichern ohne Bearbeitung bleiben unverändert. Anlass: Pflege der
  Prüfungsmerkmale der Systemprüfungen im BPMN-Editor des audit_designer
  (07.10.2026).
- npm `@auditcore/bpmn-flowaudit`, `@auditcore/bpmn-vue` und
  `@auditcore/bpmn-react` 0.3.1: Ordner der Diagrammsammlung umbenennen – auf
  der Ordnerkarte direkt, im Baum per Doppelklick oder F2. Leere Namen werden
  nicht übernommen. Anlass: Rückmeldung zum BPMN-Editor des audit_designer
  (07.10.2026).
- npm `@auditcore/bpmn-flowaudit`, `@auditcore/bpmn-vue` und
  `@auditcore/bpmn-react` 0.3.0: Übersicht der obersten Ebene als Ordnerkarten
  mit inline bearbeitbaren Beschreibungen und eingeklapptem Bereich
  „Prüfhinweise“, Palette „Elemente“/„Pool mit Rolle“ als Symbole, Kacheln oder
  Liste, Umbruch der Rollenkacheln, dezente Linienauswahl (diagram-js-Grundstile
  jetzt in `style.css` enthalten) sowie Aktionen des Hosts (`hostActions`,
  `folderActions`). Anlass: Auftrag des audit_designer zum BPMN-Editor
  (06.10.2026).
- Neues Paket `auditcore_officebank` 0.1.0 (unveröffentlicht), Etappe 0 laut
  [Plan](docs/projekt/20261005_Plan_auditcore_officebank_0.1.md): Rechnerprofil
  und Projektdatei mit Schemaversion, Ausgabe-Maskierung, Gast-Schnittstelle mit
  Fake, CLI `auditcore-officebank` (`status`, `konfig`; geplante Gruppen enden
  mit Exit 3), Kern nur Standardbibliothek, Extras `[docx]` und `[xlsx]`. Dazu
  das Plugin-Gerüst `plugins/auditcore-office/` (Manifest, 8 Skills und
  6 Agenten als Platzhalter) und das Prüfprofil `officebank`.
- Pre-release v0.8.1 (05.10.2026): `auditcore_tyfindings` 0.2.0 mit dem
  Standardprofil 2026.10.2 (deutsche Kategoriebezeichnungen); alle übrigen
  Bibliotheken und npm-Pakete unverändert. Öffentlicher Nachweis in
  `docs/reports/domain-public-installation-v0.8.1.json`.
- `auditcore_tyfindings` 0.2.0: Profil `efre.tof_2021_2027` 2026.10.2 mit
  deutschen Kategoriebezeichnungen (`kategorie_de`, Fassung der AKB-Auswertung,
  fachlich freigegeben am 05.10.2026) ist neues `STANDARDPROFIL`; neu
  `ToFEintrag.kategorie_de` und `ToFProfil.kategorie_de(kategorie)`. Regeln und
  Zuordnungsergebnisse unverändert, 2026.10.1 bleibt ladbar.
- Pre-release v0.8.0 (04.10.2026): neues Paket `auditcore_tyfindings` 0.1.0
  (Types of Findings 2021–2027); alle übrigen Bibliotheken unverändert.
  Öffentlicher Nachweis in `docs/reports/domain-public-installation-v0.8.0.json`.
- Neues Paket `auditcore_tyfindings` 0.1.0: Types of Findings 2021–2027 für
  Feststellungen der EFRE-Verwaltungsprüfungen, portiert aus dem VBA-Modul
  `modAKB_ToF.bas` – Katalog (86 Unterkategorien), Zuordnung der
  Fehlerkennziffern mit Schlüsselwortregeln und Gold-plating-Kennzeichen,
  Formalregeln für nichtfinanzielle Mängel, versioniertes Profil
  `efre.tof_2021_2027` 2026.10.1 mit Fingerabdruck. Dazu die bewusst
  unvollständige Tabelle `efre.kuerzungsgrund_zs` (nur „0“ sicher, übrige
  Schlüssel vom Fachbereich zu befüllen). Lokaler Paritätstest gegen eine
  VBA-Ergebnismappe: 574 Belege und 46 Mängel ohne Abweichung.

- `auditcore_dataprotection` 0.5.3 (#234): `render_pdf` übergibt WeasyPrint
  einen `URLFetcher` statt einer Funktion und bricht mit WeasyPrint ≥ 68 bei
  Ressourcenverweisen nicht mehr ab; nur `data:` wird aufgelöst, alles andere
  ohne Abruf ausgelassen. Extra `pdf`: `weasyprint>=60.2,!=68.0`.

- Pre-release v0.7.0 (03.10.2026): neues Paket `auditcore_flow_agent` 0.1.0
  (Auftragswarteschlange, Ressourcenvergabe, Prozesswächter); alle übrigen
  Bibliotheken unverändert. Öffentlicher Nachweis in
  `docs/reports/domain-public-installation-v0.7.0.json`.

- Code-Qualitäts-Gate: Fällt ruff oder mypy aus, nennt die Meldung Exit-Code
  oder beendendes Signal und die Ausgabe des Werkzeugs (bisher bei leerem
  stderr nur „ruff failed:“). Wird das Werkzeug von außen durch ein Signal
  beendet, etwa unter Speicherdruck auf einem geteilten Runner, wiederholt das
  Gate den Aufruf genau einmal; jeder andere Exit-Code schlägt sofort fehl.

- `auditcore_risk` 0.4.0: neue Profilversion `audit_designer.flowstat_belegliste`
  2026.10.1 rechnet BL_RF07 und BL_RF10 in ganzen Cent (RK-C12, fachlich
  freigegeben; Legacy-Profil 1254591156d3 unverändert; 41 BL_RF07-Treffer mit genau 1 Cent Differenz entfallen
  in den 112 Flowstat-Frames, ein Beleg mit unendlichem Betrag wird unbestimmt);
  neuer Spaltenpfad `columns.evaluate_columns` / `frame.evaluate_frame_columns`
  ohne `to_dict("records")` (500.000 Belege 0,9 s statt 21,9 s). Neue
  Abhängigkeiten `auditcore_compute==0.1.0` und `numpy>=1.24`
  (`packaging/library-runtime.json`).
- `auditcore_compute` 0.1.0 (vor Veröffentlichung ergänzt): `to_cents_buffer`
  und `factorize` vektorisiert und bitgleich zum Elementpfad,
  `validation.first_occurrence_codes`.

- Neues Paket `auditcore_compute` 0.1.0: deterministische Rechenkerne mit
  optionaler Numba-Kompilierung (`@accelerate`, `to_buffer`, Rückfall auf
  dieselbe Python-Funktion mit Meldung, `fastmath` verboten), Zinsen auf
  Rückforderungen mit stückweisen Sätzen, Quoten in ganzen Cent,
  Plausibilitätsprüfungen und kompensierte Statistik. Erste Bibliothek mit
  einer Drittpaket-Laufzeitabhängigkeit (NumPy): `verify_domain_packages.py`
  installiert deklarierte Drittpakete aus `packaging/library-runtime.json`
  vor den hashgebundenen Wheels und im APT-Test aus einem abgeleiteten Image.
- `auditcore_extrapolation` und UI: verbleibende Leitfaden-Verfahren – Ausschluss
  nach verhältnismäßiger Kontrolle (7.10), negative Stichprobeneinheiten (4.6),
  Discovery- und Stop-or-go-Stichprobe (7.9.6), Programme über mehrere
  Zeiträume; neue Komponente `AttributeSampling`/`FlowauditAttributeSampling`
  (`npm run ui:neu`), mehrstufige Teilstichproben mit Teilschichten und dritter
  Stufe in der Hochrechnung.
- `auditcore_reporting`: versionierte Berichtsvorlagen als Bibliotheksfunktion
  (`auditcore_reporting.templates`): Datenvertrag als JSON-Schema-Teilmenge,
  bedingte Textbausteine mit Pflichtkennzeichen und Rechtsgrundlage,
  Abschnitte mit Bedingung und Wiederholung, deterministische Ausgabe als DOCX
  (Standardbibliothek), HTML und PDF (neues Extra `pdf`, reportlab, BSD) sowie
  Befüllen von Word-Vorlagen der Anwendung mit Sicherheitsprüfung (Makros,
  ActiveX, OLE, externe Quellen, nachladende Felder, ZIP-Bomben; XML über
  `auditcore_common.safe_xml`, neues Extra `docx`). Neutrale Vorlagen
  `vermerk` und `pruefbericht`, Gestaltung nur als austauschbares Profil
  (`neutral-v1`). REST-Vertrag `reporting_ui/1` um `/templates…` erweitert;
  Oberfläche `ReportTemplates` / `FlowauditReportTemplates`
  (`<flowaudit-report-templates>`) per Generator, Paritätsfälle, Demo und
  Browsertest. Spezifikation um die Invarianten I14–I18 ergänzt.
- auditcore_documents: Bestandsprüfung `documents_batch_checks/1` (C-01 bis
  C-13, A-07, B-12, Ergänzungen ERG-01/ERG-02) mit Oberfläche `BatchChecks` /
  `<flowaudit-batch-checks>` / `FlowauditBatchChecks`; Regelmeldungen der
  Pipeline deutsch (D9). Siehe `docs/ui/batch-checks-rest.md`.
- `auditcore_extrapolation`: fehlende Verfahren des Stichprobenleitfadens
  EGESIF_16-0014-01 ergänzt – mehrere Zeiträume, zwei-/dreistufige Stichprobe
  inkl. ETC, Neuberechnung des Konfidenzniveaus (7.7), Gruppen von Programmen
  (7.8), Merkmalsstichprobe (7.9); REST `evaluation/1` abwärtskompatibel
  erweitert, `POST /attributes`; UI `ExtrapolationPanel`/`FlowauditExtrapolation`
  mit Zeiträumen, Gruppen, Teilstichproben und Neuberechnung. Fehlerbehebung:
  konservativer MUS-Ansatz mit allen Niveaus aus Tabelle 4.
- `auditcore_sampling`: Stichprobenumfang nach dem KOM-Leitfaden
  EGESIF_16-0014-01 als neues Modul `guidance` mit Status „nach Leitfaden“
  (SRS, Differenzenschätzung, MUS Standard/geschichtet/konservativ,
  nicht-statistische Mindestumfänge nach Art. 79 Abs. 2 VO (EU) 2021/1060),
  Belegziehung einer Zwischengeschalteten Stelle (`intermediate_body`,
  Paritätstest gegen flowinvoice), REST-Vertrag `auditcore_sampling.guidance/1`;
  Oberfläche `SampleSizePlanner` / `FlowauditSampleSizePlanner`
  (`<flowaudit-sample-size-planner>`). Konsistenztest Planung → Hochrechnung
  in `auditcore_extrapolation`.
- Preview v0.4.2 veröffentlicht (Prerelease, 185 Assets, main `f2220bf5`) und
  anonym installiert: pip 27/27 (hashgebunden) und 27/27 (Paketindex), APT
  (debian:bookworm) 27/27, npm 9/9 aus den Tarball-URLs sowie die Beispiele
  Vue, React und Web Components. Nachweise
  `docs/reports/domain-public-installation-v0.4.2.json` und
  `docs/reports/npm-tarball-installation-v0.4.2.json`, Hashes in
  `docs/deployment/package-feed.md`. Die README-Installationszeilen der Pakete
  zeigen auf v0.4.2. Das Donut-Job-Image bezieht seine auditcore-Abhängigkeiten
  wieder hashgebunden aus dem Release (`requirements-auditcore.txt` auf v0.4.2).
- `scripts/regulierung_package_test.py`: Der Gast richtet PGDG und das
  Timescale-Repository für den Codename des Gast-Images ein und installiert
  PostgreSQL, TimescaleDB und PostGIS in den Versionen aus den
  Kontrollfeldern des Pakets (`Regulierung-PostgreSQL`, `-TimescaleDB`,
  `-PostGIS`); damit läuft die Lebenszyklusprüfung auch mit
  `--guest-image ubuntu:26.04`. Nachweise der regulierung-Build-Matrix
  Ubuntu 26.04 (Python 3.14) und 24.04 unter
  `docs/validation/regulierung-apt/ubuntu-26.04/`.

- **Institutsneutrale Pakete:** Die Pakete nennen keine konkreten Institute
  mehr, sondern fachlich neutrale Rollen (z. B. „Zwischengeschaltete Stelle“,
  Art. 71 Abs. 3 VO (EU) 2021/1060; Code `intermediate_body`). Neuer Wächter
  `scripts/check_institution_names.py` im Job `code-quality-gate`: Namen aus
  `quality/institutsnamen-denylist.txt` sind in `packages/`, `packages-js/`,
  `docs/ui/` u. a. verboten, Ausnahmen nur mit Begründung in
  `quality/institutsnamen-ausnahmen.txt`. Umbenannte bzw. neu versionierte
  Profile:
  - `auditcore_risk`: `flowinvoice.rbvk_wibank` heißt jetzt
    `flowinvoice.rbvk_intermediate_body` (Versionen `fb2d18568d2e` und
    `2026.09.2`, fachlich unverändert, neue Fingerprints). Die alte Kennung
    lädt übergangsweise mit `DeprecationWarning` das neue Profil
    (`profiles.DEPRECATED_ALIASES`, entfällt mit dem ersten Release nach dem
    31.12.2026). Charakterisierungs-Fixture: Schlüssel `rbvk` statt des
    Institutsnamens.
  - `auditcore_legal_sources`: `auditdatabase.esi` und `audit_designer.vp_ai`
    2026.09.2 ersetzen 2026.09.1 (Relevanz-Schlagwörter „Zwischengeschaltete
    Stelle“ und „Landesförderinstitut“ statt Institutsnamen);
    `auditcore_bpmn` nutzt `auditdatabase.esi` 2026.09.2, der Quellkatalog
    von `auditcore_harvest` ist nachgezogen.
  - `auditcore_funding_sources`: `designer.deminimis.authority_levels`
    2026.09.2 ersetzt 2026.09.1 (Erkennungsmuster mit Institutsnamen
    entfallen; Zuordnung über Landesnamen und Landesbehörden).
  - `auditcore_procurement`: Der User-Agent der HAD-Suche lautet
    `EFRE-AuditTool/2.0` (ohne Behördenzusatz).
  Beobachtete Fixtures sind entsprechend neutralisiert und tragen den Hinweis
  `neutralized`; die Aufzeichnungswerkzeuge neutralisieren künftig selbst.
  Die BPMN-Neutralitätstests lesen die Namen aus der Denylist.
- Paketkatalog: neuer Status **„spezifiziert“** für charakterisierte Pakete
  mit fachlicher Spezifikation (`docs/spezifikation.md` je Paket: Zweck,
  Verträge, Invarianten, Fehlerfälle, Abgrenzung, bewusste Abweichungen vom
  Altverhalten), Invarianten als Hypothesis-Eigenschaftstests und benannten
  Legacy-Varianten. `scripts/docs/specification.py` prüft den
  `specification`-Block in `provenance.json`; `catalog.py` setzt den Status
  nur, wenn er hält (Vorlage `docs/bibliotheken/spezifikation-vorlage.md`).
  Welche Pakete umgestellt sind, steht in den Paket-CHANGELOGs.
- Duplikatgruppe A16 abgeschlossen: Die Prüfung „JSON-Objekt am Pfad“ in
  sampling (`as_object`), geo (`Body.of`) und extrapolation (`Reader`) nutzt
  `auditcore_common.rest.json_object`; geo `web.decode`, `Reply` und `_json`
  laufen über `auditcore_common.rest` (`decode_body` mit neuen Parametern
  `too_large_code`/`invalid_json_code`). Verhalten unverändert
  (Differenztests, Paketlauf alt gegen neu über HTTP).
- flowinvoice-Parität für die gemeinsamen Oberflächen: `auditcore_statistics`
  Chi²-Test mit kritischen Werten und auffällige Ziffern (REST-Feld `metrics`),
  `auditcore_risk` Betrugsprüfsignale im Vertrag der Risiko-Merkmale
  (`POST /fraud-signals/evaluate`, Profil `flowinvoice.fraud_signals` 2026.09.3
  mit Bezeichnungen), Benford-Komponente (Vue/React) mit `metrics`,
  `autoAnalyse`, `hideInputs`. Keine Versionsanhebung.

## 0.4.2 – 2026-09-26

- **Breaking – npm-Scope umbenannt:** Alle JS-Pakete unter `packages-js/`
  heißen jetzt `@auditcore/<paket>` statt `@flowaudit/<paket>` (common,
  ui-core, ui, ui-react, kanban-core, bpmn-editor, bpmn-flowaudit, bpmn-vue,
  bpmn-react), einheitlich mit den Python-Paketen `auditcore_*`. Auf npm war
  unter dem alten Scope nie etwas veröffentlicht. Release-Tarballs heißen
  `auditcore-<paket>-<version>.tgz`, die npm-Organisation ist `auditcore`,
  die Registry-Sperre in `.npmrc` lautet `@auditcore:registry=…`.
  Unverändert bleiben Web-Component-Tags (`<flowaudit-…>`),
  Komponentennamen (`Flowaudit…`), CSS-Präfixe (`--fa-*`) und Klassennamen.
  Umstellung der Anwendungen: `docs/ui/umbenennung-auditcore.md`.

- Vorbereitung Release v0.4.2: Versionen aller seit v0.4.1 geänderten Pakete
  angehoben. Python: `auditcore_common` 0.2.0 (neues Modul `rest` mit
  `json_object`), documents 0.4.0, identifiers 0.2.0, invoicesynth 0.2.0,
  reporting 0.3.0, neues Paket `auditcore_extrapolation` 0.1.0; alle übrigen
  als Patch (README im Wheel geändert, Pins auf `auditcore_common==0.2.0` und
  die neuen Paketstände). npm: `@auditcore/ui-core` 0.2.0,
  `@auditcore/ui-react` 1.1.0, `@auditcore/common` 0.1.1,
  `@auditcore/kanban-core` 0.2.1, `@auditcore/bpmn-editor` 0.1.1,
  `@auditcore/bpmn-flowaudit`/`-vue`/`-react` 0.2.1; `@auditcore/ui` 0.3.0
  erstmals als Release-Datei. Die npm-Pakete liegen ab diesem Release als
  `npm pack`-Tarballs mit `npm-packages.json` bei.
- Code-Gate: `codegate_js` zählt Build-Ausgaben `dist-*` (z. B. `dist-wc`,
  `dist-standalone` von bpmn-vue) nicht mehr als Quelltext.
- Donut-Job-Image (`donut-train-image`): Verlangt das Rad von
  `auditcore_invoicesynth` auditcore-Stände, die noch nicht veröffentlicht
  sind, baut der Workflow genau diese Abhängigkeiten aus demselben
  Repository-Stand (`docker/train/deps_source.py`, Label `auditcore.deps=repo`).
  Sonst bleiben sie hashgebunden aus dem Release.
- Vue ↔ React per Code erzwungen statt nur dokumentiert:
  `npm run ui:gate` (`scripts/js/ui-parity-gate.mjs`, fail closed in
  `js-packages` und im Pflicht-Job `code-quality-gate`) leitet die
  öffentlichen Komponenten aus den Quellen ab (Exporte, `ELEMENTS`,
  `defineCustomElement`; TypeScript-Compiler-API) und prüft je Komponente die
  native React-Fassung und umgekehrt, je Gruppe Kernmodul mit Controller und
  Stil sowie `cases-<gruppe>.ts`, die ein Vue- und ein React-Paritätstest
  importieren, und dass das React-Paket kein Vue lädt. Ausnahmen nur
  befristet in `quality/ui-parity-exceptions.json` (Ratchet: nur Abbau).
  Generator `npm run ui:neu -- <gruppe> <Komponente>` erzeugt Kern,
  Stil, Vue-SFC, Web Component, React-Komponente, Exporte, Paritätsfälle,
  beide Paritätstests und Doku-Stub; das Gerüst besteht Lint, Typprüfung,
  Tests und Gate (`npm run test:scripts`). Bestand: Vue exportiert jetzt auch
  `KanbanToolbar`, `CardAppearance`, `CardChecklistEditor`, `CardReferences`,
  `CardTagsEditor`, `ColumnEditorRow`, `DbKanbanColumn`, `DbKanbanCard` (wie
  React); neue Paritätsfälle für den Datei-Import (`TableImport`) und die
  BPMN-Basis (`FaIcon`, `BaseDialog`); `cases.ts` aufgeteilt in
  `cases-synopsis.ts`/`cases-table.ts`, BPMN-Seitenansichten in
  `cases-views.ts`; Kern `ui-core/src/table/` und `ui-core/src/base/index.ts`.
  Drei befristete Ausnahmen (Controller für Basis und Tabelle,
  Paritätsfälle der BPMN-Web-Component).
- npm-Veröffentlichung der `@auditcore`-Pakete: Workflow `npm-publish`
  veröffentlicht nach einem GitHub-Release (oder von Hand mit Tag, standardmäßig
  als Probelauf) genau die signierten Release-Tarballs auf npmjs.org, nach
  Prüfung von Signatur, SHA-256, Größe und npm-Integrität gegen
  `npm-packages.json` (`scripts/npm_publish.py`), in Abhängigkeitsreihenfolge,
  idempotent (gleiche Version mit gleicher Integrität wird übersprungen, mit
  anderem Inhalt nie überschrieben und als Fehler gemeldet), `--provenance`, dist-tag `next` für
  Vorabversionen. Anmeldung per Trusted Publishing, für die Erstveröffentlichung
  per Secret `NPM_TOKEN`; Automatik erst mit der Variable
  `NPM_PUBLISH_ENABLED`. Alle `package.json` unter `packages-js/` mit
  `repository` (nötig für Provenance), `homepage`, `bugs` und
  `publishConfig.access=public`. Installationsdoku: `npm install
  @auditcore/<paket>` als Standardweg, Tarball-URL für Intranet/offline;
  Einrichtung in `docs/deployment/npm-veroeffentlichung.md`. Keine
  Versionsanhebung (Paketstände kommen mit v0.4.2).

- Neues Paket `auditcore_extrapolation` 0.1.0: Hochrechnung von
  Stichprobenfehlern für Prüfbehörden nach dem KOM-Leitfaden EGESIF_16-0014-01
  (Mittelwert-, Verhältnis- und Differenzenschätzung, MUS Standard/geschichtet/
  konservativ mit Hochwertschicht, nicht-statistische Stichproben),
  Gesamtfehlerquote (TER) mit systemischen und anomalen Fehlern,
  Fehlerobergrenze und Ergebnis, getrennt davon Restfehlerquote (RER) nach
  CPRE_23-0013-01 Annex 3; REST-Vertrag `auditcore_extrapolation.evaluation/1`.
  Oberfläche `ExtrapolationPanel`/`<flowaudit-extrapolation>` (Vue) und
  `FlowauditExtrapolation` (React nativ) auf dem Kern in `@auditcore/ui-core`
  mit Paritätsfällen. `EXPECTED_SOURCES`, `packaging/library-extras.json` und
  Baseline ergänzt.

- `auditcore_common.rest.json_object`: gemeinsame JSON-Objekt-Prüfung der
  REST-Verträge `identifiers_ui/1` und `reporting_ui/1` (vorher wörtlich
  gleiche `_object`-Kopien, `duplicate_functions` wieder 0); beide Pakete
  hängen neu von `auditcore_common==0.1.1` ab, ihre `ContractError` sind
  Unterklassen von `rest.ContractError`. Differenztest gegen beide Kopien,
  Duplikatgruppe A16 in `docs/quality/duplikate.md`. Keine Versionsanhebung.

- Tabellenexport nach Excel: `auditcore_reporting.web` mit versioniertem
  REST-Vertrag `reporting_ui/1` (`GET /profiles`, `POST /preview`,
  `POST /export`; Starlette und FastAPI, neue Extras `web` und `fastapi`,
  `packaging/library-extras.json` ergänzt) und Oberfläche
  `<flowaudit-report-export>` (Vue `ReportExportPanel`, React nativ
  `FlowauditReportExport`, Kern `createReportingController` in
  `@auditcore/ui-core`): Formatprofil wählen, Vorschau mit Excel-Format je
  Spalte, ersten Zeilen und Probelauf, XLSX-Export. Das Paket hat keine
  Berichtsvorlagen; „Vorlage“ ist hier das Formatprofil
  (`docs/ui/reporting-rest.md`). Sechs Paritätsfälle plus Interaktionsfolge,
  Demo-Seite „Tabellenexport (Excel)“ und API-E2E-Test.

- CI (`js-packages`, `nightly`): Vitest-Worker an die CPU-Quote der
  selbst gehosteten Runner angepasst (`scripts/js/vitest-workers.sh` setzt
  `VITEST_MAX_WORKERS`). Node 20 (libuv 1.46) ignoriert die cgroup-Quote von
  2 CPUs und meldet 20, Vitest startete daher 19 Worker; die Paritätstests in
  `ui-react` liefen sporadisch in das 5-s-Zeitlimit. Node 22 beachtete die
  Quote bereits. Das pauschale `testTimeout` von 20 s in
  `ui-react/vitest.config.ts` (aus #159) ist wieder entfernt; nur die
  Paritätsdateien setzen über `test/parity/setup.ts` gezielt 10 s.

- Geo-Karte: UTM-Eingabe des Bezugspunkts (`POST /utm/geographisch` von
  `auditcore_geo.web`) in Vue (`GeoUtmInput`) und React nativ – Zone,
  Halbkugel, Ost- und Nordwert mit Feldprüfung im Kern
  (`parseUtm`, `parseMetres`), Rückrechnung über den neuen optionalen
  Port-Eintrag `fromUtm` (`createGeoRestPort` bietet ihn an), Felder
  folgen dem Bezugspunkt; Ellipsoid-Auswahl auch vor dem ersten
  Bezugspunkt. 5 Paritätsfälle plus 2 Interaktionsfolgen, E2E ergänzt.

- „Kennung prüfen“: REST-Vertrag `identifiers_ui/1` in
  `auditcore_identifiers.web` (Extras `web`, `fastapi`) und Oberfläche
  `IdentifierCheck`/`<flowaudit-identifier-check>` (Vue) sowie native
  `FlowauditIdentifierCheck` (React) auf gemeinsamem Kern in
  `@auditcore/ui-core` (`createIdentifierController`,
  `createIdentifiersRestPort`): Prüfprofil mit sichtbarer Empfehlung,
  Einzelprüfung mit Status, Begründung, Grund, Normalform und Einzelheiten,
  Stapelprüfung aus CSV/TSV über den TableImport-Controller mit
  Spaltenzuordnung, Filter „Nur Auffälligkeiten“ und CSV-Export. 4
  Paritätsfälle plus 2 Interaktionsfolgen, Demo-Seite und API-E2E
  (`docs/ui/identifiers-rest.md`).

- Belegerkennung: REST-Vertrag `documents_extraction/1` in
  `auditcore_documents.web` (Upload → Extraktionsergebnis mit Konfidenz →
  Validierungsbefunde; OCR/Donut nur über Ports der Anwendung, ohne Engine
  abgeschaltet) und Oberfläche `<flowaudit-extraction>` (Vue `FaExtraction`,
  React nativ `FlowauditExtraction`, Kern `createExtractionController` in
  `@auditcore/ui-core`), 8 Paritätsfälle plus Interaktionsfolge, Demo mit
  Attrappen-Ports. Vertrag: `docs/ui/extraction-rest.md`.

- Donut-Nachtraining E3 auf dem GPU-Rechner (`auditcore_invoicesynth.train`):
  Job-Image `ghcr.io/janpow77/auditcore-donut-train:cu128` (Workflow
  `donut-train-image`, Basis per Digest, torch 2.11.0+cu128, gepinnte
  Laufzeit, Lizenzhinweise unter `/licenses`); Hängeschutz mit atomarer
  `progress.json` samt Herzschlag, SIGTERM → Checkpoint (Frist 90 s),
  NaN/Inf-Loss und CUDA-OOM mit Sicherung des letzten guten Stands und
  eigenen Exit-Codes, gezählte unlesbare Beispiele; Kommando je Lauf im
  FlowAgent-Job (zweiter Lauf 1536×1152, Seed + 1, vorher gleiche
  Konfiguration auf beiden Karten); `train.evaluate` bewertet Kandidat und
  Donut-CORD mit einem Befehl. Keine Versionsanhebung.

- `auditcore_common`-Migrationen Teil A: neues Modul `auditcore_common.rest`
  (rahmenwerkfreier Teil der REST-Schicht, Duplikatgruppe B1);
  `auditcore_sampling` und `auditcore_statistics` nutzen es,
  `auditcore_sampling` zusätzlich `numeric.numpy_pairwise_sum`/`numpy_round`,
  `auditcore_market_indicators` `numpy_pairwise_sum`, `require_finite`,
  `canonical_sha256` und die Profil-Lader. sampling und market_indicators
  hängen neu von `auditcore_common==0.1.1` ab. Paritätstests alt ↔ neu
  (Differenz- und Hypothesis-Tests in `auditcore_common`); keine
  Verhaltensänderung.

- Offene `auditcore_common`-Migrationen (Teil B): `auditcore_price_sources`
  (kanonisches JSON, Paketbytes bytegleich), `auditcore_geo` (Endlichkeit),
  `auditcore_property_sources` (HTML-Erkennung, Zeitzonenprüfung) und
  `auditcore_invoicesynth` (SHA-256, Steuersatz, Kennungen) nutzen
  `auditcore_common`; `auditcore_documents` nutzt die Prüfziffern aus
  `auditcore_identifiers` (neue Pflichtabhängigkeit `auditcore_identifiers==0.1.0`).
  Neue Pins `auditcore_common==0.1.1` für geo, invoicesynth und price_sources.
  Paritätstests alt ↔ neu je Paket; Code-Gate `duplicate_functions` 4 → 0
  (documents 2 → 0, identifiers 2 → 0). Keine Versionsanhebung (Release v0.4.2).
- JS-Bauwerkzeuge: Vite 7 → 8 (Rolldown statt Rollup, Oxc statt esbuild,
  CSS-Minifizierung mit Lightning CSS) und vite-plugin-dts 4 → 5
  (unplugin-dts, `@vue/language-core` 3 als eigene Entwicklungsabhängigkeit).
  Konfigurationen auf `build.rolldownOptions`, `oxc`, `codeSplitting: false`
  und `import.meta.dirname` umgestellt. Exporte und Typdeklarationen der Pakete sind
  unverändert (Vue-SFC-Deklarationen im Format von language-core 3).
  `@auditcore/bpmn-flowaudit` kennzeichnet `src/index.ts` als
  seiteneffektbehaftet, damit die Stile der Diagrammschicht (`--fa-hit`,
  Rundgang-/Vergleichsmarkierungen) in Standalone-App und Web Component
  ankommen; die Web Component `<flowaudit-bpmn-editor>` enthielt sie bisher
  nicht. Lizenzprüfung: Einzelfreigabe für `lightningcss` (MPL-2.0, nur
  Entwicklungsabhängigkeit von Vite 8).

## 0.4.1 – 2026-09-26 (einschließlich 0.4.0 und der Vorschauen seit 0.3.0)

- Vorbereitung Release v0.4.1: Versionen aller seit v0.4.0 geänderten Pakete
  angehoben (Pins auf `auditcore_common==0.1.1` und die neuen Paketstände),
  `auditcore_harvest` 0.1.2 parst Feeds nur noch über defusedxml
  (`auditcore_common.safe_xml`, neues Extra `xml`), `canonical_hash` und der
  Profil-Fingerprint von `auditcore_price_analysis` nutzen
  `auditcore_common.hashing` (duplicate_functions 7 → 4). Die signierte
  APT-Release-Datei trägt ein `Date`-Feld (RFC 2822, `SOURCE_DATE_EPOCH`
  beachtet); apt meldet nicht mehr „Invalid 'Date' entry“.
- Festlegungen der gemeinsamen Vertragsfälle entschieden (Nutzer, 25.09.2026):
  Ersatzwert „—“, Dateigröße Basis 1024 mit KB/MB und Dezimalkomma, „1.5“ und
  „1.234“ in Beträgen ungültig bzw. mehrdeutig mit Hinweis, höchstens zwei
  Nachkommastellen bei Beträgen (de), Anzeige-Zeitzone Europe/Berlin
  (`contracts/common-cases/decisions.json`: Status „festgelegt (Nutzer
  2026-09-25)“, `DECISIONS.md`). Verträge `parse-number`, `empty-value`,
  `format-date`, `format-filesize` jetzt `verbindlich`; Rundung von Beträgen
  und Trenner Datum/Zeit bleiben vorläufig.
- Neues Paket `auditcore_bpmn` 0.1.0: BPMN 2.0 mit FlowAudit-Erweiterung
  Schema 1.1 (verbindlich in `docs/bpmn/flowaudit-schema-1.1.md`, XSD im
  Paket), gehärtetes Parsen, Elementmodell, Prüfregeln mit stabilen IDs
  (de/en), Profile je Förderperiode (KA nach Anhang XI VO (EU) 2021/1060 und
  Anhang IV Delegierte VO (EU) Nr. 480/2014 aus den amtlichen Texten),
  Diagrammsammlung mit Speicher-Port, Versions- und Soll/Ist-Vergleich,
  Neutralisieren, Anreichern von Altbeständen, Berichte (Prozesstabelle,
  RCM, Feststellungen, KA-Kategorievorschlag) sowie die legacy-treue
  Übernahme von `bpmn_analyzer.py`, `validate_bpmn_bva` und
  `bpmn_export.py` aus audit_designer (charakterisiert, eine dokumentierte
  Abweichung). `EXPECTED_SOURCES` und `packaging/library-extras.json`
  ergänzt.
- CI-Automatisierung (Rechteinhaber, 25.09.2026): Sammel-Check `ci-ok` als
  Required Check neben `code-quality-gate`, Workflows `autofix` (ruff, ESLint,
  reine Baseline-Absenkungen; Hilfsskript `scripts/ci_baseline_lower_only.py`),
  `update-pr-branches`, `dependabot-automerge` und `nightly` (Vollprüfung mit
  Issue „Nightly rot“), dazu `.github/dependabot.yml` und Auto-Merge im
  Repository. Siehe `docs/deployment/ci-automatisierung.md`.

## 0.3.0

- Helfer-Verträge für App-Repositorys (Nutzerauftrag 25.09.2026, „Frontend-
  inventur im Code einbauen, damit die Fehler immer identifiziert werden“):
  neues Modul `auditcore.tools.helpers`, Befehl `auditcore-helpers`
  (`scan`, `lint`, `contracts`, `check`, `toolchain`, `rules`), gemeinsame
  Vertragsfälle `contracts/common-cases/*.json` (11 Verträge, 165 Fälle,
  JSON-Schema, Festlegungen vorläufig in `DECISIONS.md`), 11 deklarative
  Regeln (u. a. Zahlparser wie `BeleglisteGrid.parseDecimal`, Datum ohne
  Zeitzone, handgebaute €-Formatierung, CSV ohne Formelschutz, 422-Fehlertexte;
  zwei Regeln führen erkannte Helfer isoliert aus), Ratchet gegen
  `.auditcore/helpers-baseline.json`, Action `.github/actions/helper-contracts`,
  Nachtlauf `scripts/helpers_nightly.sh` mit systemd-User-Timer (nicht
  aktiviert). Siehe `docs/quality/helper-contracts.md`.
- Verbindliche Code-Qualitätsmaßstäbe als Ratchet (Rechteinhaber, 25.09.2026):
  neue Module `auditcore.tools.quality.codegate*`, Befehl
  `auditcore-codegate check` bzw. `scripts/verify_code_quality.py`, Baseline
  `quality/baseline.json`, Pflicht-Job `code-quality-gate`, pre-commit-Hook
  und Release-Blocker in `verify_domain_packages.py`/`prepare_library_release.py`.
  Siehe `docs/quality/code-quality.md`.

## 0.2.0

- Pflicht zum fachlichen Rauchtest nach Produktions-Deploys (Rechteinhaber,
  24.09.2026): neues Modul `auditcore.tools.deployer.smoke`, Befehl
  `auditcore-deploy smoke`, Blocker in `auditcore-deploy plan` für jedes
  Ziel außer `internal_test` ohne gültige `functional_smoke`-Fälle, Action
  `.github/actions/functional-smoke`. Health-Endpunkte zählen nicht als
  Rauchtest. Siehe `docs/deployment/functional-smoke.md`.

## 0.1.0

Initial platform: framework-independent core models and reporting function,
policy-aware quality gates, GitHub inventory and consolidation planning,
KIRA/Graphify providers, transactional application migration, Debian builds
and isolated lifecycle validation. Release authorization remains separate from
technical build success; see the platform build report for actual evidence.
