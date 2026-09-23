# Funktionsübersicht und Bibliothekszuordnung

Stand: 22. September 2026. Dieser Bericht ergänzt den Paketplan um tatsächlich
untersuchte Anwendungsfunktionen. Die neuen Bibliotheken sind damit nicht schon
implementiert. Nächster konkreter Consumer ist auf Nutzerwunsch **regulierung**:
Bibliotheken herstellen, Anwendung refactorieren, verifizieren und als natives
Debian-/APT-Paket bereitstellen. Das Anwendungsrepository bleibt eigenständig.

## Ergebnis und Umfang

Die erneute authentifizierte GitHub-Abfrage lieferte **71 eigene Repositories**.
Für 70 nicht leere Repositories wurden die untersuchten Git-SHAs mit dem aktuellen
Default-Branch auf GitHub abgeglichen; alle 70 stimmten bei der Abfrage überein.
`auditinvoice` ist leer und besitzt keinen untersuchbaren Commit.
Die vollständigen getrackten Dateibäume wurden gelesen, auch Dateien, die im
Sparse-Checkout nicht sichtbar sind. **7.424 Python-Dateien wurden erfolgreich
per AST gelesen**, zwei weitere weisen vorhandene Syntaxfehler auf.
62.084 Funktions-/Methodendefinitionen und 10.766 Klassen wurden gezählt.
Diese Zahlen enthalten Tests, Migrationen und Kopien; sie sind weder die Zahl
fachlicher Fähigkeiten noch die Zahl unabhängig wiederverwendbarer Bausteine.

Die maschinenlesbare [Repository- und Modulliste](../reports/function-landscape.json)
enthält pro Repository SHA, Dateitypen, Services, UI-Seiten, Testdateien,
Python-Zählungen und Parsefehler. Alle 71 sind unten mit ihrer funktionalen
Einordnung verlinkt. Eine Datei-/AST-Inventur ersetzt keine vollständige
fachliche Prüfung jeder Funktion. Frontend-, VBA-, Rust- und andere Sprachen
sind nicht durch den Python-Parser semantisch geprüft.

Vertieft wurden die zuletzt ausdrücklich genannten Anwendungen untersucht:

| Anwendung | Detailübersicht | Abdeckung |
|---|---|---|
| Flowworkshop | [Funktionen und Router](FUNCTIONS_WORKSHOP.md) | 27 Funktionsgruppen, 33 Routermodule, 44 Servicemodule; UI und Aufrufstellen |
| OSINT / map.flowaudit.de | [Dienste und Kartenfunktionen](FUNCTIONS_OSINT_MAP.md) | Vier Python-Dienste, zehn Werkzeuge, 40 JavaScript-Module, Deploymentzuordnung |
| Audit-Designer einschließlich eingebettetem FlowStat | [Module, Services und MCP](FUNCTIONS_DESIGNER_FLOWSTAT_MCP.md) | Elf Modulbereiche, vollständiger statischer API-/Serviceindex, repräsentative Aufrufketten |
| Eigenständiges FlowStat | [Analysen und Variantenvergleich](FUNCTIONS_DESIGNER_FLOWSTAT_MCP.md) | Rechenfamilien, Router und Vergleich mit der eingebetteten Variante |
| FlowAudit-MCP | [Registrierte Werkzeuge](FUNCTIONS_DESIGNER_FLOWSTAT_MCP.md#flowaudit-mcp-registrierte-schnittstellen) | HTTP-/Stdio-Verträge und Implementierungszuordnung, keine behauptete Ausführung aller Fachtools |
| Regulierung | [Funktionen, Refactoring und Debian-Pfad](FUNCTIONS_REGULIERUNG_MIGRATION.md) | Dienste/Router, Bibliotheksbedarf, bestehender Betrieb und konkrete Migrationsgates |

**Nicht ausgeführt:** Anwendungstests, Browser-End-to-End-Tests, produktive
Harvester, aktive Securityscans, Office-Kompilierung, Installation oder Migration
dieser Anwendungen. Vorhandene Testdateien sind als Testinventar ausgewiesen.
Eine erfolgreiche Syntaxanalyse ist kein bestandener Funktionstest.

## Zusammenführung nach fachlichem Vertrag

| Fähigkeiten / Quellen | Ziel | Wichtige Grenze |
|---|---|---|
| VVT anlegen/bearbeiten/versionieren, DSFA erstellen und berechnen; Designer-Arbeitsdokumente | `auditcore_dataprotection` | Exportvorlage ist keine Risikoberechnung; menschliche Freigabe, Rechte und Audit-Trail erhalten |
| Wasser-/Nahwärmepreise, Staffel-/Rundungsmechanik, Vergleichskennzahlen | `auditcore_price_analysis` | Fachprofile und Gültigkeit explizit; Kraftstoff-Vollzugsentscheidung nicht als allgemeine Preisformel behandeln |
| Externe Indizes und Preis-/Energiequellen | `auditcore_price_sources` + `auditcore_harvest` | Quellenrevisionen, Einheiten, Datenlücken und Freigabe erhalten |
| TED, HAD und weitere Vergabebekanntmachungen; Vergabedaten und Prüfprofile | `auditcore_procurement` | Quellenadapter optional; Abruf ist keine bestandene Vergabeprüfung |
| EU-Begünstigte, State Aid, De-minimis-Register | `auditcore_funding_sources` | Getrennte Quellenprofile; Kumulierung als nachvollziehbarer Fachvertrag mit geprüften Regelversionen |
| Sanktionen, Register und Unternehmensinformationen | `auditcore_registry_sources` | Quelle, Stand und Treffergüte dokumentieren; keine automatische Personen-/Unternehmensentscheidung |
| LEI, Namen, Adressen, Entitätsabgleich | `auditcore_entity_matching` | Unsicherheit und manuelle Bestätigung beibehalten; abweichende Gewichte nicht harmonisieren |
| DIP, EUR-Lex, CURIA, Prüfberichte und weitere Rechts-/Prüfquellen | `auditcore_legal_sources` | TED/HAD gehören ausdrücklich zu Procurement |
| Pagination, Limits, Retry, Cursor, Provenienz, idempotente Übergabe | `auditcore_harvest` | Keine allgemeine Bewertung, kein fester ORM; dokumentierte Adapter- und Testverträge |
| Statistik, Datenprüfungen, Benford, Ausreißer und Verteilungen | `auditcore_statistics` | Standalone- und Designer-FlowStat differenziell charakterisieren |
| MUS/SRS, Schichtung, Stichprobenumfang, Hochrechnung | `auditcore_sampling` | Prüfmethodik und Parameter erhalten; keine automatische Auswahl einer fachlichen Variante |
| Dokumentparser, Vergleich, Tabellen-/Textnormalisierung | `auditcore_documents` | OCR/Office/KI als optionale Provider, schwere Laufzeitkomponenten getrennt |
| Excel/PDF/DOCX-Berichte und Vermerke | `auditcore_reporting` erweitern | Bestehende Bibliothek verwenden; Anwendungsabfragen und Fachentscheidung bleiben getrennt |
| Koordinaten, Gebietsschnitt, Radius, Raster-/Höhenprofile | `auditcore_geo` | GIS-/Rasterabhängigkeiten optional; Kartenoberfläche bleibt Anwendung |
| Synthesedaten und synthetische Rechnungen | vorhandene Generatorbibliotheken | Vorhandene Consumer tatsächlich auf installierte Pakete umstellen |

Der bisherige Plan mit 20 benannten Paketen bleibt eine **vorläufige Auswahl**.
Diese Inventur belegt zusätzliche Funktionsfamilien; sie beschließt nicht
automatisch für jede davon eine weitere Distribution:

- **Checklisten:** Workshop verarbeitet bereits eigene und Designer-Paketformate.
  Gemeinsamen Baum-/Fragen-/Antwort-/Paketvertrag als weiteren Bibliothekskandidaten
  untersuchen; UI, Bearbeitungsrechte, Freigaben und Projektpersistenz bleiben App.
- **Nachrichten/Feeds:** OSINT besitzt Feedparser, Lesetextbereinigung, Themen- und
  Quellenstatus. Wiederverwendung innerhalb einer Quellenfamilie auf dem Harvestkern
  prüfen; ein zusätzliches Nachrichtenpaket erst mit begründetem Vertrag beschließen.
- **BPMN/Personal/ESI und weitere Berechnungen:** Im FlowStat-Bestand vorhanden;
  nicht allein wegen numerischer Ausgabe als allgemeine Statistik einordnen.
- **Dokumentvergleich:** Bereits abgegrenzter Designer-Kern und mehrere Consumer;
  zuerst als Modul von `auditcore_documents` verwenden.
- **Securityscanner:** Workshop enthält aktive HTTP-/TLS-/Portprüfungen. Als
  Werkzeug/Provider mit bestehenden Ziel-/Berechtigungsgrenzen behandeln.
- **MCP, RAG und Notebookbetrieb:** Fachprüfer können Bibliotheken konsumieren;
  Protokollserver, OAuth, Isolation, Vektorspeicher und Modellbetrieb bleiben Dienste.
- **Signierte Austausch-/Updatepakete:** Verträge aus Designer und Regulierung
  vergleichen, bestehende Signatur-/Revisions-/Restoregates erhalten; kein
  unkontrolliertes Zusammenwerfen unterschiedlicher Paketformate.

## KIRA/RAG: tatsächlich gelesen

KIRA wurde über den vorhandenen `KiraKnowledgeStore.search` und dessen konfigurierte
Memory-API abgefragt. Die Credentials wurden aus der vorhandenen lokalen
Graphify-KIRA-Konfiguration geladen und nicht in Berichte übernommen. Vier
semantische Abfragen lieferten:

| Abfrage | Treffer | Ergebnis und Grenze |
|---|---:|---|
| Workshop / State Aid / Checklisten | 19 | Graphbefunde zu Validator, Bericht/PDF und Frontend-API; teilweise Projektalias `workshop` statt `flowworkshop` |
| OSINT / Ortsdienst / Kartendienst | 20 | Unter anderem SHA-belegte OSINT-Symbolkataloge; Trefferlimit erreicht, keine vollständige Indexabdeckung behauptet |
| Designer / FlowStat / MCP | 8 | Auch gebaute Plotly-Dateien und fremde Treffer; Zentralität von Bundles ist keine Fachbibliothekspriorität |
| Regulierung / DSFA / Calculator / Deployment | 13 | Auch Framework-DSFA und Auditcore-Releaseinformationen; Quellenvertrag und Repository erst verifizieren |

Ein zusätzlicher FlowAudit-`memory_search` wurde für die Projekthistorie gelesen.
Er liefert unter anderem frühere Flowlib-Architektur und Modultrennung im Designer.
Historische Test-/Betriebsaussagen wurden **nicht** als heutige Prüfergebnisse übernommen.
Die fachliche RAG-Suche wurde nach `knowledge_capabilities` gezielt mit
`dokumenttyp=code_referenz` aufgerufen. Sie lieferte zwei Ausschnitte desselben
QChess-VBA-Importdokuments, keinen vollständigen Anwendungskatalog.
Der Dienst meldete `reranker_degraded=true`; Ranking damit eingeschränkt.
Kein Suchtreffer ist ein Ersatz für den fixierten GitHub-Code.

Private Laufnachweise: `.auditcore/function-overview-kira.json` und
`.auditcore/function-overview-mcp-evidence.json`. Keine neuen KIRA-Einträge
geschrieben, kein globaler Sync oder vollständiger RAG-Export behauptet.
Die [maschinenlesbare Nachweiszusammenfassung](../reports/function-source-evidence.json)
enthält Abfrageumfang, Status, Grenzen und Prüfsummen der lokalen Laufnachweise.

## Graphify: tatsächlich abgefragt und abgeglichen

Der erreichbare Graphify-MCP-Standardgraph meldete **415.247 Knoten und 1.011.698
Kanten**, 2.575 Communities; 79 % EXTRACTED und 21 % INFERRED. Diese Zahlen sind
Serverangaben, keine Bestätigung aktueller und fehlerfreier Aufrufketten für alle
71 Repositories. Abfragen zu Workshop und Regulierung sowie gezielte Node- und
Nachbarschaftsabfragen wurden ausgeführt.

- Workshop-Bericht: Graph führte zum realen `state_aid_audit_report.py` und seinen
  Sections. Der Name `build_audit_report()` ist mehrdeutig zwischen Workshop und
  Designer; die Nachbarschaftsabfrage über die ausgegebene ID fand keinen Knoten.
  Die relevante Consumerkette wurde deshalb am Quellcode geprüft.
- OSINT: `ortsdienst/dienst.py` ist als `osint::ortsdienst_dienst` identifiziert;
  Nachbarschaft liefert unter anderem `Bestand`, `haversine_km`, `normalisieren`.
  Das sind überwiegend `contains`-Kanten, keine Aufrufbeweise.
- Regulierung: `calculate_wasser()` liefert extrahierte Verbindungen zu Staffel-
  und Rundungsfunktionen. Abweichende Zeilennummern und als INFERRED bezeichnete
  Testkanten werden nicht ungeprüft als aktuelle gerichtete Aufrufe übernommen.
- FlowStat: `run_benford()` existiert in mehreren Graphkontexten. Ein
  `pdf_editor`-Alias für eingebettete Designerpfade macht die Zuordnung prüfpflichtig.
  Dasselbe Aliasproblem betrifft `mcp_http_server.py`.
- OSINTs eingecheckter Graph wurde zusätzlich gelesen: 1.283 Knoten / 2.286 Kanten,
  aber ein älterer Build-Commit; begleitende Berichte nennen noch 813 / 1.234.
  Deshalb **STALE / inkonsistente Artefaktstände**, keine aktuelle Vollabdeckung.

Graphify wurde damit verwendet; es wurde kein neuer Gesamtgraph gebaut und keine
vollständige strukturelle Analyse aller Sprachen behauptet. Die lokale AST-Inventur
ergänzt die Befunde, löst aber keine dynamischen Python-/JavaScript-Aufrufe vollständig.

## Regulierung als erster Consumer

Die [konkrete Migrationsvorbereitung](FUNCTIONS_REGULIERUNG_MIGRATION.md) hat
Vorrang vor weiteren spekulativen Paketaufteilungen. Sie bindet jede Extraktion
an Legacy-Charakterisierung, installierte Bibliotheksversion, echte Consumer-
Imports, Regression/Integration und erneute Framework-Policy-Evaluation.

Bestehender Zustand: Offline-Docker-Tar-Paket und signierter, systemd-gestützter
**Updater**, noch kein nachgewiesenes natives `.deb` der Anwendung. Der
`/api/health`-Endpunkt ist keine Datenbank-/Migrationsbereitschaftsprüfung.
PostgreSQL-Erweiterungen, Redis, OCR und PDF-Laufzeit dürfen bei der Umstellung
nicht übersehen werden. Ziel ist vorgebautes Frontend plus reproduzierbare
Python-/Systemabhängigkeiten ohne Compiler, npm oder PyPI-Zugriff am Zielserver.

Freigabe erst nach echten Anwendungs-, Policy-, Installations-, Upgrade-,
Entfernungs- und Wiederherstellungsnachweisen. Eine bloße Bibliotheksinstallation
oder ein erfolgreicher Debian-Build begründet kein `READY_FOR_DEPLOYMENT`.

## Verbleibende Grenzen

Die drei vorhandenen Generator-/Reportingpakete decken Regulierung noch nicht
vollständig ab. Neue Pakete brauchen Rechteprüfung; die bestehende MIT-Freigabe
zweier Generatorquellen gilt nicht für alle hier gelesenen Repositories.
Fachliche Regelkonflikte bleiben `HUMAN_DECISION_REQUIRED`, fehlende Security-/
Policyentscheidungen `REVIEW_REQUIRED`. Die vorhandenen Syntaxfehler in
`flowstat/backend/tests/fix_tests.py:69` und
`llm-rag-audit-presentation/update_app.py` bleiben im Inventar sichtbar.

Die folgende Gesamtmatrix ist eine **funktionale Einordnung aller Repositories**
mit vollständiger Dateibaum-/Python-AST-Inventur. Nur die oben verlinkten
Anwendungen haben in diesem Durchgang eine vertiefte Funktionsübersicht erhalten.
Für andere Repositories darf die Matrix nicht als vollständiger Funktionsaudit
oder bereits fertiger Extraktionsplan ausgegeben werden.

## Gesamtmatrix aller Repositories

| Repository / untersuchter Commit | Python lesbar / Fehler | Funktionale Einordnung und nächste Grenze |
|---|---:|---|
| [3dprint / 0e05fe1c6192](https://github.com/janpow77/3dprint/tree/0e05fe1c61927f9c05c719da7eb9b9634561ec49) | 0 / 0 | 3D-Webanwendung behalten; kein Python-Fachkern belegt |
| [Ausgabenliste / 9b9eda8f6367](https://github.com/janpow77/Ausgabenliste/tree/9b9eda8f6367e55c9380e56f0eb86afb79366075) | 0 / 0 | Extensionloser VBA-Bestand; fachliche Aggregation charakterisieren, Office-Adapter behalten |
| [Beleglisten / f21211a86b87](https://github.com/janpow77/Beleglisten/tree/f21211a86b87b339faba88bd2826ab08c493da50) | 0 / 0 | Office-Datei-/Druckautomatisierung behalten; Dokumentadapter nur bei echtem Vertrag |
| [Blendertool / 34c79f69ef49](https://github.com/janpow77/Blendertool/tree/34c79f69ef49812f753efe2be9a1be29158fa9c1) | 17 / 0 | Blender-Plugin behalten; isolierbare Geometrie erst bei Consumerbeleg |
| [Checkboxes / 28a393379b76](https://github.com/janpow77/Checkboxes/tree/28a393379b761390c9a2b5b40b6789a1778b6394) | 0 / 0 | Kleines Office-Makro; kein neues Python-Paket |
| [Drucknachweise / 58e6426e1640](https://github.com/janpow77/Drucknachweise/tree/58e6426e16400c8913347d85ba1f183bd49d3355) | 0 / 0 | Kein implementierter Paketkern im aktuellen Tree |
| [EGPU_EVO-X2_Manager / 722788ded5f7](https://github.com/janpow77/EGPU_EVO-X2_Manager/tree/722788ded5f70178d52ea8193da207f7d7b29a56) | 4 / 0 | Rust-Dienst und Pythonclient getrennt betreiben; keine Pflichtabhängigkeit |
| [Formular_Callcenter / 9380b10478ce](https://github.com/janpow77/Formular_Callcenter/tree/9380b10478ce0de57bed5a2f4b834a8a486a89ec) | 0 / 0 | Office-Anwendung behalten; Import-/Dokumentverträge erst charakterisieren |
| [QCHESS / d794ad4dcfe9](https://github.com/janpow77/QCHESS/tree/d794ad4dcfe9b402da6ef4132012b1eb77e7f836) | 0 / 0 | Legacy Office/C#; Qualityadapter statt neues Allzweckpaket |
| [QCHESS_Bericht / 59e029384cdf](https://github.com/janpow77/QCHESS_Bericht/tree/59e029384cdf93e98cac9370f2ffd85ef72e06b6) | 0 / 0 | Office-Berichtsworkflow behalten; Vorlagen/Exportcharakterisierung nötig |
| [QCHESS_PRINT / 51f7883dff4b](https://github.com/janpow77/QCHESS_PRINT/tree/51f7883dff4b7816e010dad80764081c3262edc2) | 4 / 0 | Mit vorhandenem docformatter abgleichen; keine blinde Doppelbibliothek |
| [Report_new / e78cf50f6ede](https://github.com/janpow77/Report_new/tree/e78cf50f6ede1ac36a39f6168b4ec9635cde8910) | 0 / 0 | 21 Office-Exportdateien inventarisieren; kein leerer Bestand |
| [SAP_Auswertung / 48ea66ada4cf](https://github.com/janpow77/SAP_Auswertung/tree/48ea66ada4cf460a4a53f2775bf0c41d43a48bd1) | 0 / 0 | Kein implementierter SAP-Analysekern im aktuellen Tree |
| [Statistik / 15aeef34ffbf](https://github.com/janpow77/Statistik/tree/15aeef34ffbf6b1f05b237af4f75a0b5176d5525) | 10 / 0 | Benannte Statistik-/Versionsanalyseprofile und Reportingadapter |
| [Statistik_Vorhabenpruefung / 13d104c22bd2](https://github.com/janpow77/Statistik_Vorhabenpruefung/tree/13d104c22bd238b053ec741a2ba5b3cf0c7b4f4d) | 0 / 0 | VBA-Fachberechnung zuerst vollständiges Projekt charakterisieren |
| [VBA_Excel_tools / a11cede1097d](https://github.com/janpow77/VBA_Excel_tools/tree/a11cede1097d34a5895b5684abece8502757314f) | 0 / 0 | Kein implementierter Werkzeugkern im aktuellen Tree |
| [VideoArchivAssistent / 8dcc0ee94f17](https://github.com/janpow77/VideoArchivAssistent/tree/8dcc0ee94f174fb174c24e0f285b13a197a1a820) | 264 / 0 | Medien-/Jobdienst behalten; isolierte Metadatenparser nur bei belegtem Nutzen |
| [ai-router / 426cd78e86df](https://github.com/janpow77/ai-router/tree/426cd78e86df9f822452af035b8d58a19f7aa820) | 97 / 0 | Routerdienst/Clients behalten; Providerabgleich mit llm-router und eGPU |
| [audit-portal / d8eefa426826](https://github.com/janpow77/audit-portal/tree/d8eefa426826bdecb67036774f3128ae05e7d0d0) | 992 / 0 | Statistik/Sampling, Dokumente, Screening; Varianten statt Kopien harmonisieren |
| [audit_designer / 030a71e083ef](https://github.com/janpow77/audit_designer/tree/030a71e083ef0feddc14545b095a4945bc0bbd7a) | 2123 / 0 | **[Detailanalyse](FUNCTIONS_DESIGNER_FLOWSTAT_MCP.md)**. H1–H3 und Analysekerne priorisieren; Workflows/KI/DB bleiben Anwendung |
| [auditcore / 793e8cb2452a](https://github.com/janpow77/auditcore/tree/793e8cb2452a92cb84d533720e1deffab32fb0b2) | 104 / 0 | Plattform und drei vorhandene Fachdistributionen weiterpflegen |
| [auditdatabase / bba911e918e1](https://github.com/janpow77/auditdatabase/tree/bba911e918e102426d4ca2f88fd377fe8ca585e4) | 154 / 0 | H1 plus vorhandene Dokumentpakete wiederverwenden |
| [auditinvoice / kein Commit](https://github.com/janpow77/auditinvoice) | 0 / 0 | Leeres Repository, keine implementierten Funktionen inventarisierbar |
| [auswertungjkb / 3e250425bac5](https://github.com/janpow77/auswertungjkb/tree/3e250425bac59a64da9f6d1c9dde966665d7a65e) | 42 / 0 | Analyse-/Reportingprofile abgrenzen; abweichende Formatregeln erhalten |
| [cockpit / 2dd001fc041a](https://github.com/janpow77/cockpit/tree/2dd001fc041a69c25f515833f215c23a099a4be5) | 71 / 0 | Betriebs-/Inventuranbindung als Provider, Host-/Secretrechte bewahren |
| [e-invoice-preparer / b3d64459c4bf](https://github.com/janpow77/e-invoice-preparer/tree/b3d64459c4bfa3a7e45799205bbf948ed2219133) | 0 / 0 | Frontend behalten; Rechnungs-Datenvertrag prüfen, kein belegter Pythonkern |
| [evo-x2-setup / acfc8b28965a](https://github.com/janpow77/evo-x2-setup/tree/acfc8b28965ad9241015fd749aa7d80a3a5298ca) | 0 / 0 | Setup-/Betriebsskripte als Deployer-Referenz, nicht Fachbibliothek |
| [flow-agent / 864b2a7d5822](https://github.com/janpow77/flow-agent/tree/864b2a7d582269f3e6f45e1d3f6eca22c50674c1) | 183 / 0 | Vorhandene Client-/Vertragspakete nutzen; Agent/Betriebsrechte getrennt |
| [flowaudit / d8107f6b4287](https://github.com/janpow77/flowaudit/tree/d8107f6b4287228974bc3b0f405bdd95182a66d5) | 190 / 0 | Quality/Consolidator/AppRefactor-Adapter und benannte Analyseprofile |
| [flowaudit-landingpage / d7e5f2768b4d](https://github.com/janpow77/flowaudit-landingpage/tree/d7e5f2768b4d1494352d95605e8bffd7e4903741) | 0 / 0 | Webauftritt behalten; kein Domainpaket belegt |
| [flowaudit_testdatengenerator_docker / 5987ab7731ea](https://github.com/janpow77/flowaudit_testdatengenerator_docker/tree/5987ab7731eabfc998b639bcedebeee4ac5c6349) | 0 / 0 | Betriebsdokumentation; keine zweite Generatorimplementierung |
| [flowaudit_testdatengenerator_frontend / 05bc5ac560df](https://github.com/janpow77/flowaudit_testdatengenerator_frontend/tree/05bc5ac560dfff3bc7181323240745215492d09a) | 2 / 0 | Bestehendes auditcore_dummygenerator konsumieren; echte Appmigration noch offen |
| [flowinvoice / fb2d18568d2e](https://github.com/janpow77/flowinvoice/tree/fb2d18568d2eaf64574d131ceae51a936b9aac02) | 466 / 0 | Vorhandenes Invoicepaket nutzen; Dokument-/Rechercheadapter separat prüfen |
| [flowlib / aca2dc6aad25](https://github.com/janpow77/flowlib/tree/aca2dc6aad25aea0720312dbcc6da00b0bcba330) | 14 / 0 | Bestehende Bibliothek nutzen; Reporting extrahiert, HTTP/Auth-Clients getrennt |
| [flownavigator / 9dff858d3772](https://github.com/janpow77/flownavigator/tree/9dff858d3772e59533886dfbae70c672d574a1d4) | 91 / 0 | Anwendungs-/Modulverträge prüfen; kein pauschaler Workflow-Kern ohne Consumer |
| [flowpiano / 07ed41736f36](https://github.com/janpow77/flowpiano/tree/07ed41736f36d4e7a8aaaaa54cef6ff60a278365) | 0 / 0 | Swift/Web-Musikanwendung behalten; außerhalb Auditdomain |
| [flowsearch / 10cb2a3ead38](https://github.com/janpow77/flowsearch/tree/10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4) | 71 / 0 | H2/H3 priorisieren; Rechercheorchestrierung und DB bleiben App |
| [flowstat / d665ac221f50](https://github.com/janpow77/flowstat/tree/d665ac221f50ba1f465b7337bdd4aa218d78ec8a) | 133 / 1 | **[Detailanalyse](FUNCTIONS_DESIGNER_FLOWSTAT_MCP.md)**. Statistik/Sampling extrahieren; vorhandener Test-Parsefehler bleibt PARTIAL |
| [flowvoice / 28f5623ab30f](https://github.com/janpow77/flowvoice/tree/28f5623ab30ff392531fd870013961e1e1529013) | 55 / 0 | Sprachdienst/Audioadapter behalten; separat charakterisierbare Audiohilfen prüfen |
| [flowworkshop / a05bb2143bd9](https://github.com/janpow77/flowworkshop/tree/a05bb2143bd96d5e981f9462f05b965e1658be36) | 198 / 0 | **[Detailanalyse](FUNCTIONS_WORKSHOP.md)**. H2/H3 und Entity-Matching priorisieren; Unterrichts-/Reviewworkflow bleibt App |
| [graphify-kira / 1714914ba37c](https://github.com/janpow77/graphify-kira/tree/1714914ba37cdd7c47f2febc3c548166563b5d41) | 20 / 0 | Bestehender Consolidator-Provider; keine neue Fachdistribution nötig |
| [ki-pilotprogramm / dac4b137bfb4](https://github.com/janpow77/ki-pilotprogramm/tree/dac4b137bfb443d36bdf3f4c8350f9f3dabb85bc) | 0 / 0 | Frontend/Pilotanwendung behalten; kein Python-Fachkern belegt |
| [kino / 3e73a7194313](https://github.com/janpow77/kino/tree/3e73a71943131ac75171605facf795fc0476f893) | 36 / 0 | Kino-/Abstimmungsanwendung behalten; derzeit kein Audit-Domainzuschnitt |
| [kiraclaw / 43cd98e90f03](https://github.com/janpow77/kiraclaw/tree/43cd98e90f03f124701ee53541b5f358c5e7eeae) | 28 / 0 | KI-Orchestrierungsdienst und Clients als technische Adapter behandeln |
| [krypto / 34d601726227](https://github.com/janpow77/krypto/tree/34d601726227f913548a118e144de5519eee0f3f) | 536 / 0 | H5-Marktdaten und benannter Indikatorkern; Portfolioentscheidungen getrennt |
| [llm-rag-audit-presentation / c59fe09e05f6](https://github.com/janpow77/llm-rag-audit-presentation/tree/c59fe09e05f6d44bdc7ef1a92280f8deebe5ca75) | 4 / 1 | Präsentationsprojekt; kein Paketzwang, Parsefehler update_app.py offen |
| [llm-router / 2dade44643df](https://github.com/janpow77/llm-router/tree/2dade44643df50523c5ec23b41c9cfd803013b2f) | 44 / 0 | Technischer Routerdienst; Beziehung zu ai-router zuerst revisionsgebunden klären |
| [nuc-admin / 751df0edaf5d](https://github.com/janpow77/nuc-admin/tree/751df0edaf5d8a78e22d2d187056a2b9c3a5b651) | 92 / 0 | Betriebs-/Inventur-/Deploymentprovider; Auth und Audit beibehalten |
| [openclaw / 55ada5d38a60](https://github.com/janpow77/openclaw/tree/55ada5d38a60a82f566f8fd25ef2a70a96976d44) | 0 / 0 | Deployment-/Agentintegration; keine eigenständige Fachlogik belegt |
| [osint / d361ddb9a502](https://github.com/janpow77/osint/tree/d361ddb9a502bb899065e799d50104f306cfdc89) | 32 / 0 | **[Detailanalyse](FUNCTIONS_OSINT_MAP.md)**. H4-Geo und Quellenadapter; Portal/Auth/Scheduler getrennt |
| [pdf-editor / ce3441312975](https://github.com/janpow77/pdf-editor/tree/ce34413129751dfd72fac6cefa55b02718bff27b) | 57 / 0 | Dokumentbearbeitung als App; reine PDFoperationen gezielt prüfen |
| [python_diagramm / 9b68539303f7](https://github.com/janpow77/python_diagramm/tree/9b68539303f71488f4b4b7a3be79f22e0a0e0aad) | 0 / 0 | Kein implementierter Diagrammkern im aktuellen Tree |
| [qaaudit / c78be5c86454](https://github.com/janpow77/qaaudit/tree/c78be5c86454d457e5c66d0c65b5117a8528d462) | 69 / 0 | Bewertungs-/Maßnahmenmodelle nur mit fachlichem Vertrag extrahieren |
| [qchess-src / 902ed69dde67](https://github.com/janpow77/qchess-src/tree/902ed69dde6720e557af5fe372054577d7fe6167) | 11 / 0 | Vorhandenes Analysepaket als Qualityplugin weiterverwenden |
| [rechnungslegung-seminar / 31fc51d52ac9](https://github.com/janpow77/rechnungslegung-seminar/tree/31fc51d52ac978c5d960e5c8df61d0739b8f4e11) | 184 / 0 | Beleg-/Aufgabenrenderer als Profile/Adapter; Lehraufgaben bleiben App |
| [regulierung / a5d48ea4b90a](https://github.com/janpow77/regulierung/tree/a5d48ea4b90a410210ec25e707781ef9e21ad743) | 505 / 0 | **[Detailanalyse](FUNCTIONS_REGULIERUNG_MIGRATION.md)**. Datenschutzregister/DSFA-Erstellung priorisieren; H4 und Preisanalysen getrennt |
| [reranker-service / 5ca0e67a1c41](https://github.com/janpow77/reranker-service/tree/5ca0e67a1c41df2fdfeb30d890ded6f825aa0f18) | 5 / 0 | Modellservice behalten; expliziter Retrievalprovider |
| [riskanalysis / b5c523bf7eaa](https://github.com/janpow77/riskanalysis/tree/b5c523bf7eaa326153778d9751f176f03d4d56ed) | 86 / 0 | Risiko-/Privacy-/Screeningprofile; MDBimport und fachliche Gewichte getrennt |
| [router / bd2c2c2ba47f](https://github.com/janpow77/router/tree/bd2c2c2ba47f420fe66f317d5c39a4501d9d8d3b) | 0 / 0 | Rust-/Netzwerkbetrieb behalten; Deployeradapter unter Rechteprüfung |
| [router-tray / ace87d030a6a](https://github.com/janpow77/router-tray/tree/ace87d030a6ab61b43e3c4c277a545f479a73333) | 22 / 0 | Desktop-Bedienung bleibt eigener Client |
| [spoke-agent / a133aeeb0637](https://github.com/janpow77/spoke-agent/tree/a133aeeb0637f46dae0b9b27630e46d440aa3ed9) | 13 / 0 | Hostagent/Deploymentintegration; keine Domain-Runtime |
| [spoke-stack / a98008feea48](https://github.com/janpow77/spoke-stack/tree/a98008feea482526460d89bddccd060dadb28dfe) | 0 / 0 | Betriebsmanifestfamilie als Deployerreferenz |
| [spoke-widget / a179562c67fd](https://github.com/janpow77/spoke-widget/tree/a179562c67fdbcd285eba8b428de7e592f759693) | 1 / 0 | Rust/Desktopclient behalten; Protokollvertrag mit Spoke prüfen |
| [system-migrate / 2f9afa4572f6](https://github.com/janpow77/system-migrate/tree/2f9afa4572f66b2ea984c901e652eee6b8b5a633) | 52 / 0 | Inventur-/Migrationsadapter; Systemzustand/Privilegien getrennt |
| [versteigerung / e4ad7af0eaee](https://github.com/janpow77/versteigerung/tree/e4ad7af0eaee0b151cc5e3358f95b961d7f3a448) | 62 / 0 | H5-Immobilienadapter; Bewertung/DB/OCR-Orchestrierung bleibt App |
| [verwaltung-app-framework / 15f5338f783f](https://github.com/janpow77/verwaltung-app-framework/tree/15f5338f783f2c7d5760a9bb299be06d27326be0) | 13 / 0 | Verbindliche Policyquelle, zusätzlich VVT-Vertrag prüfen; kein Ersatz der Quelle |
| [vision-service / 4c249036c5eb](https://github.com/janpow77/vision-service/tree/4c249036c5eb91b87f650c4e73239d6e195b39c7) | 12 / 0 | OCR-Modellbetrieb separat, Dokumentpaket nutzt Providervertrag |
| [wesenszug / a27c963b2062](https://github.com/janpow77/wesenszug/tree/a27c963b20623e45ce8228dfe3fa0fb9c2a081bb) | 77 / 0 | Eigenständige Anwendung; Schutz-/Einwilligungslogik nicht ungeprüft verallgemeinern |
| [whisper-service / a7c9612933d7](https://github.com/janpow77/whisper-service/tree/a7c9612933d71aad474225c5018f84b3595d1fef) | 5 / 0 | Transkriptionsservice als Provider; keine Modellgewichte in Fachruntime |
| [wohnungsmonitor / 76571bfaa343](https://github.com/janpow77/wohnungsmonitor/tree/76571bfaa3435bfc6858b3cbaae8c4ea3969ef91) | 16 / 0 | H5-Portalparser und H4-Geo; Quellenprofile getrennt |
| [x_chat / 2ef4138ba140](https://github.com/janpow77/x_chat/tree/2ef4138ba14002ab4bd1401970336a53b8a2b29b) | 157 / 0 | Chat-/KI-Anwendung behalten; Clients nur nach tatsächlichem Mehrfachbedarf |
