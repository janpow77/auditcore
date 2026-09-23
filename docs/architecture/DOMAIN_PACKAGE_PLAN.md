# Fachpaketplan nach dem technischen Framework-Nachweis

Stand: 22. September 2026. **Fortgeschriebener Paketplan.** Dummy, Invoice und
Reporting sind seit Preview v0.1.0 veröffentlicht; PDF-/Excel-Erweiterungen
werden separat geprüft. Neue Kandidaten sind noch keine veröffentlichten Pakete
und keine abgeschlossenen Anwendungsmigrationen. Grundlage bleibt Phase A/B des
[Umsetzungsplans](IMPLEMENTATION_PLAN.md), gemäß [ADR-001](ADR-001-multi-package-monorepo.md).
Dieser Plan dokumentiert den Zuschnitt. Den aktuellen Veröffentlichungsstand
belegen die Releaseberichte; Anwendungen bleiben eigene Repositories.

## Ergebnis und Reihenfolge

Die erste Welle besteht aus `auditcore_dummygenerator`, darauf aufbauend
`auditcore_invoicegenerator`, sowie dem kleineren, bereits charakterisierten
Zuschnitt `auditcore_reporting`. Danach folgen Statistik und Stichproben.
Privacy, Dokumentinterpretation, Risiko und Vergabe werden erst mit ihren
jeweiligen fachlichen bzw. Sicherheitsnachweisen übernommen.

**Die untenstehende ursprüngliche Reihenfolge wird durch den erweiterten Auftrag
ergänzt:** Register-/DSFA-Funktionalität einschließlich Berechnung hat jetzt
Priorität; Harvester und weitere Analyse-/Werkzeugfamilien werden ebenfalls
berücksichtigt. Die [Abdeckung aller 71 Repositories](REPOSITORY_PACKAGE_COVERAGE.md)
enthält Quellen, konkrete Consumer und die aktualisierte Reihenfolge.

Die vertiefte [Funktionsübersicht](FUNCTION_OVERVIEW.md) ergänzt jetzt Workshop,
OSINT/map.flowaudit, Audit-Designer einschließlich MCP und eingebettetem FlowStat,
Standalone-FlowStat sowie Regulierung. 20 bisher benannte Pakete sind kein
abschließend vollständiger Funktionskatalog. Zusätzliche Kandidaten wie
Checklisten und Nachrichtenquellen sind dort mit konkreten Belegen abgegrenzt.
**Erster gezielt zu migrierender Consumer ist Regulierung**; dafür gilt der
[Refactoring-/Debianplan](FUNCTIONS_REGULIERUNG_MIGRATION.md).

| Priorität | Eigenständige Distribution | Gemeinsam darin halten | Bewusst außerhalb halten |
|---|---|---|---|
| 1 | `auditcore_dummygenerator` | Synthetische Namen, Adressen, Zahlen, Datumswerte, Felder, Zeilen und explizite Fehlerfälle | FastAPI-Endpunkte, Uploads, CSV-Downloadantworten, Serverkonfiguration und Workerbetrieb |
| 2 | `auditcore_invoicegenerator` | Rechnungsmodelle, Positionen, Summen, Datums-/Fehlerprofile und nachvollziehbare synthetische Szenarien | Celery-Jobs, DB-Persistenz, Benutzerrechte und verbindliche Rechnungsstellung |
| 3 | `auditcore_reporting` | Formatprofile und fachliche Berichtsdaten; Excel-Anbindung bei Bedarf als Extra | HTTP-Exports, Anwendungsabfragen, Authentifizierungs-/KI-Clients aus Flowlib |
| 4 | `auditcore_statistics` | Benford, numerische Ausreißer- und Verteilungskennzahlen mit expliziten Parametern | Risikourteile, Prüfentscheidungen und automatisch gewählte Schwellen |
| 5 | `auditcore_sampling` | MUS/SRS, Schichtung, Hochrechnung und methodische Varianten | Stille Vereinheitlichung unterschiedlicher Stichprobenformeln |
| 6 | `auditcore_privacy` | Deterministische Pseudonymmechanik, Kollisionsbehandlung und passende Datenverträge | Schlüsselverwaltung, Mandantenwahl, Mapping-Speicherung und Berechtigungen |
| 7 | `auditcore_documents` | Dokumentdaten, reine Normalisierung und später isolierte Parser | Das gesamte vorhandene OCR-/PDF-/KI-Servicepaket |
| 8 | `auditcore_risk`, `auditcore_procurement` | Mechanik plus explizite, versionierte Regelprofile; Procurement umfasst auch TED, HAD und weitere Vergabebekanntmachungen | Pauschale gemeinsame Rechtsauslegung oder ungeprüfte Schwellen-/Gewichtsänderungen |

Statistik bleibt nur dann eine eigene Distribution, wenn ihr eigener Vertrag
und ihre tatsächlichen Consumer belegt sind. Ausschließlich von Sampling
benötigte numerische Hilfen bleiben intern in `auditcore_sampling`.
Ein `auditcore_utils`, ein allgemeines `auditcore_validation` oder separate
Pakete für jede einzelne Generatorfeldart sind derzeit nicht begründet.

Alle Anwendungen behalten eigene Repositories, Oberfläche, Datenbank,
Berechtigungen und Releaseentscheidungen. Fachpakete ziehen die Plattform
`auditcore` nicht automatisch als Laufzeitabhängigkeit nach.

## Erweiterter Auftrag: Register, DSFA, Harvester, Analysen und Tools

Die vorherige Liste ist **keine vollständige Liste aller Bibliotheken**. Sie war
auf ausgewählte Fachkerne begrenzt. Der Nutzer hat nun ausdrücklich die
Erweiterung vorhandener Bibliotheken sowie die Berücksichtigung der Harvester,
Analysen, Werkzeuge und der Datenschutzfunktionen aus `regulierung` verlangt.
Die aktuelle repositoryübergreifende Abdeckung wird separat dokumentiert.

### Gemeinsamer Harvesterkern

`auditcore_harvest` ist als gemeinsame technische Bibliothek für die angebundenen
Datenquellen vorgesehen: Abrufablauf, Pagination, Rate-Limits/Retry, Teilfehler,
Provenienz, inkrementelle Checkpoints und Übergabe an injizierbare Senken.
Die Quellenfamilien (`legal_sources`, `funding_sources`, `registry_sources`
usw.) liefern ihre Adapter und Parser und hängen vom Kern ab. Der Kern zieht
nicht alle Quellenpakete nach. Mindestens zwei Quellenfamilien müssen den
wiederverwendbaren Vertrag praktisch belegen; neue Quellen benötigen passende
Adapter. [Ausführlicher Zuschnitt H0](REPOSITORY_PACKAGE_COVERAGE.md#h0--gemeinsamer-datenharvest-auditcore_harvest).
Status: geplant, noch keine installierbare Distribution.

### `auditcore_dataprotection`: VVT und DSFA einschließlich Berechnung

**Ein eigenständig installierbares Fachpaket soll Anwendungen ermöglichen,
eigene Verarbeitungsverzeichnisse und Datenschutz-Folgenabschätzungen anzulegen,
zu bearbeiten, zu berechnen, zu versionieren und auszugeben.** Die Funktionalität
ist der Gegenstand der Wiederverwendung; vorhandene Registerinhalte werden nicht
als allgemeiner Datensatz übernommen.

Das Verzeichnis und die zu einer Tätigkeit gehörende DSFA teilen stabile
Tätigkeitskennungen, Versionsbezüge, Maßnahmen und Änderungsnachweise. Deshalb
gehören sie in ein gemeinsames Paket mit klaren Teilmodulen:

| Teilmodul | Wiederverwendbare Fähigkeit |
|---|---|
| `register` | Verzeichnis und Verarbeitungstätigkeiten anlegen/ändern, Felder prüfen, stabile Kennungen, Fassungen und nachvollziehbare Änderungen verwalten. |
| `assessment` | Eine DSFA aus einer konkreten Tätigkeitsfassung erstellen; Fragen, Begründungen, Risiken und Maßnahmen erfassen; Bearbeitungsstände prüfen. |
| `calculation` | Schwellwertanalyse, Bruttorisiko aus Schwere und Wahrscheinlichkeit, Maßnahmenwirkung, Nettorisiko und begründeten Vorschlag berechnen. |
| `rules` | Explizite versionierte Frage-/Maßnahmenkataloge, Rechtsregime, Schwellen und Bewertungsprofile mit Herkunft und Anwendbarkeit. |
| `workflow` | Fachliche Übergangsbedingungen, notwendige Begründungen, DSB-Beteiligung und erneuten Prüfbedarf bei geänderter Tätigkeit abbilden. |
| `export` | Register- und DSFA-Berichtsdaten sowie optionale Excel-/PDF-Ausgabe. Allgemeine Ausgabetechnik nur bei passendem Vertrag über `auditcore_reporting`. |

**Berechnung ist ein verpflichtender Kernumfang**, kein späterer optionaler
Formularzusatz. Ergebnis und Begründung müssen die tatsächlich angewendete
Regelversion nennen. Fachliche Entscheidung und technische Berechnung bleiben
unterscheidbar; unbekannte/fehlende Angaben benötigen einen sichtbaren Zustand.

Konkrete Quellbasis, lokal und gegen GitHub-HEAD geprüft am 22.09.2026:
`janpow77/regulierung@a5d48ea4b90a410210ec25e707781ef9e21ad743`.

- `backend/app/services/dsfa/bewertung.py`: `Antwort`, `Szenario`,
  `Schwellwertergebnis`, `Risikoergebnis`, `Vorschlag`,
  `vorbelegung_aus_taetigkeit`, `werte_schwellwert_aus`, `werte_risiko_aus`,
  `erstelle_vorschlag`, `vorschlag_als_json`. Der Berechnungsteil ist bereits
  weitgehend rein und importiert seinen Katalog sowie die Standardbibliothek.
- `backend/app/services/dsfa/katalog.py`: Fragen, Maßnahmen, Fundstellen und
  vorhandene Rechtsregime; diese sind versionierte Quellprofile, keine hiermit
  bestätigte allgemeingültige Rechtsauslegung.
- `backend/app/services/mandant_dsgvo_service.py`: Tätigkeitskennungen,
  Registerfassungen, Bearbeitung/Freigabe und Workbook-Ausgabe.
- `backend/app/services/dsfa/verwaltung.py`: Erstellung aus Tätigkeiten,
  Vorschlagsberechnung, Bearbeitung, Freigabe, Änderungsvergleich und Neubewertung.
- `backend/app/services/dsfa/export.py`: HTML-/PDF-Bericht und Workbook.
- `backend/tests/test_dsfa_bewertung.py`, `test_dsfa_verwaltung.py`,
  `test_mandant_dsgvo.py`: vorhandene Berechnungs- und Ablaufprüfungen als
  Ausgangspunkt für tatsächlich auszuführende Characterization.

Die Anwendung behält Datenbankadapter, Mandantenzugriff, serverseitige Rechte,
Benutzeroberfläche und unveränderliche Speicherung freigegebener Fassungen.
Die Bibliothek darf Vier-Augen-Prinzip, Versionsschutz oder DSB-Beteiligung
nicht umgehen. Diese Anforderungen sind bei der Consumerintegration erneut
zu prüfen. Allgemeine Pseudonymisierungsmechanik bleibt der getrennte Kandidat
`auditcore_privacy`; sie ist keine Pflichtabhängigkeit der Register-/DSFA-Funktion.

Bereits lokal ausgeführt: 19 unveränderte Originaltests bestanden, 129 weitere
Ausgaben beobachtet, anschließend 148 Original-/Replaytests exakt bestanden.
Nachweise: `.auditcore/dataprotection-characterization/{REPORT.md,result.json}`.
Das ist eine Charakterisierung des reinen Berechnungskerns, keine vollständige
VVT-/DSFA-Workflowabnahme oder rechtliche Bestätigung. Insbesondere doppelte
Kriterien, unvollständige Antworten und explizite Netto-Nullwerte brauchen einen
klaren Bibliotheksvertrag. Bestehende Schutzprüfungen des Verwaltungsadapters
müssen beim Herauslösen erhalten bleiben.

Vor Extraktion weiterhin abzusichern sind insbesondere leere
oder unvollständige Antworten, doppelte Kriterien, unbekannte Schlüssel,
Regimewechsel, Schwellenränder, Maßnahmenwirkung und explizite Restwerte.
Der aktuelle Legacycode überspringt unbekannte/negative Antworten; seine
Behandlung unvollständiger Erhebungen muss charakterisiert und fachlich geprüft
werden, bevor daraus ein allgemeiner Freigabevertrag abgeleitet wird.

Status: **konkreter Paketauftrag/Kandidat, noch keine veröffentlichte Distribution**.
Die bisherige MIT-Freigabe für zwei Generatorkerne umfasst diese Quellen nicht.
Zusätzlich nennt ein Quellkommentar BfDI-Mustermaterial unter CC-BY-SA 4.0;
Vorlagenrechte und Codeherkunft werden getrennt geprüft. Es wird keine
pauschale MIT-Umlizenzierung der bestehenden Register-/DSFA-Unterlagen behauptet.

## Evidenzbasis und Aussagegrenzen

Ausgewertet wurden das persistierte GitHub-Inventar und die dazu vorhandenen
lokalen Checkouts. Für die folgenden sieben Checkouts wurden die angegebenen
HEADs und unveränderte getrackte Arbeitsdateien erneut lokal überprüft.
Dies ist **keine erneute Abfrage der heutigen GitHub-Remote-HEADs**.
Vor einer Extraktion wird der gewählte Quellstand ausdrücklich fixiert oder
die Inventur für eine neuere Revision aktualisiert.

| Referenz | Repository | Beobachteter Commit | Lizenz im Inventar |
|---|---|---|---|
| DUMMY | `janpow77/flowaudit_testdatengenerator_frontend` | `05bc5ac560dfff3bc7181323240745215492d09a` | `UNKNOWN` |
| INVOICE | `janpow77/flowinvoice` | `fb2d18568d2eaf64574d131ceae51a936b9aac02` | `UNKNOWN` |
| FLOWLIB | `janpow77/flowlib` | `aca2dc6aad25aea0720312dbcc6da00b0bcba330` | MIT |
| JKB | `janpow77/auswertungjkb` | `3e250425bac59a64da9f6d1c9dde966665d7a65e` | `UNKNOWN` |
| STAT | `janpow77/flowstat` | `d665ac221f50ba1f465b7337bdd4aa218d78ec8a` | `UNKNOWN` |
| RISK | `janpow77/riskanalysis` | `b5c523bf7eaa326153778d9751f176f03d4d56ed` | `UNKNOWN` |
| PORTAL | `janpow77/audit-portal` | `d8eefa426826bdecb67036774f3128ae05e7d0d0` | `NOASSERTION` |

`UNKNOWN`/`NOASSERTION` bedeutet Lizenzprüfung erforderlich, nicht automatisch
fehlende Nutzungsrechte oder Ablehnung. Der Nutzer hat lokale Extraktion und
Pflege seiner Repositories autorisiert. Unklare Lizenzmetadaten verhindern daher
keine lokale technische Extraktion oder isolierte Tests im beauftragten Umfang.
Für Weitergabe und Veröffentlichung müssen Rechte und Bedingungen hingegen
belegt sein; Originalnotices bleiben bei lokaler Übernahme erhalten.
Für PORTAL wurde zusätzlich die tatsächliche
[LICENSE am fixierten Commit](https://github.com/janpow77/audit-portal/blob/d8eefa426826bdecb67036774f3128ae05e7d0d0/LICENSE)
gelesen: proprietäre Software ohne allgemeine Nutzungs-/Open-Source-Lizenz.
Der Inventarwert `NOASSERTION` wird deshalb nicht als fehlende Lizenzdatei
interpretiert. Daraus folgt keine automatische MIT-Umlizenzierung oder öffentliche
Veröffentlichungsfreigabe; die MIT-Lizenz der Plattform gilt nicht automatisch
für übernommene Quellen. Für ausdrücklich lokale Testbauten kann
`build --allow-unreviewed-license` verwendet werden. Der entsprechende
Reviewstatus und die Originalnotices bleiben sichtbar; die Option ist keine
Freigabe zur Veröffentlichung.

Consumerangaben unten unterscheiden beobachtete lokale Aufrufstellen und
geplante Bibliotheksconsumer. Kein bisheriger lokaler Aufruf ist ein Nachweis,
dass die zukünftige Distribution bereits installiert oder integriert ist.
AST-Callerlisten sind heuristisch: gleichnamige Methoden wie `generate` können
fremde Aufrufer zugeordnet bekommen. Für die ersten Consumer wurden deshalb
die konkreten Import-/Aufrufstellen zusätzlich im Quelltext geprüft.

## 1. `auditcore_dummygenerator`

**Zuschnitt:** ein Paket mit zusammenhängendem Feld-/Zeilenvertrag, optional
intern gegliedert in `fields`, `rows`, `scenarios`. Keine Verteilung auf
Adress-, Zahlen-, Datumspakete. Länder-/Feldtabellen gehören zum selben Vertrag.

- Quelle DUMMY: `backend/generator.py`, Klasse `TestDataGenerator`, insbesondere
  `generate_first_name`, `generate_city`, `generate_iban`, `generate_date_range`,
  `generate_amount`, `generate_field`, `apply_deviation`, `generate_rows` und
  `_generate_rows_sequential`.
- Beobachteter erster Consumer: DUMMY `backend/main.py` importiert die Klasse
  und ruft `TestDataGenerator(seed=request.seed)` sowie `generate_rows(request_dict)`
  auf. Der Endpunkt bleibt in der Anwendung; später ersetzt ein Compatibility
  Wrapper den bisherigen Klassenimport.
- Beobachtete Abhängigkeiten: Standardbibliothek einschließlich Zufall und
  Datum; für die bestehende Parallelvariante optional `joblib`. Der reine
  Generator verwendet weder FastAPI noch eine Datenbank. Der erste Paketkern
  benötigt keinen Worker-/Webserver. Parallelisierung bleibt eine gesondert
  geprüfte optionale Ausführungsvariante.
- Der bisherige Konstruktor verwendet bereits `random.Random(seed)`. Die
  Datumsvorgabe in `generate_field` kann jedoch `datetime.now()` verwenden.
  Ein Seed allein garantiert deshalb noch keine reproduzierbaren Ergebnisse.
- `generate_iban` erzeugt die Prüfziffer zufällig. Die bestehende Ausgabe darf
  nicht als garantiert gültige IBAN dokumentiert werden. Bestehendes Verhalten
  zunächst charakterisieren; ein neuer Gültigkeitsmodus erhält einen
  ausdrücklichen, getesteten Vertrag.
- `_generate_batch` kopiert den Request flach, ändert verschachtelte Feldparameter
  und ruft erneut `generate_rows` auf. Workerrekursion, Mutation des Eingabeobjekts,
  Batchgrenzen und Fehlerweitergabe sind vor einer Parallelübernahme zu prüfen.

**Characterization-Paket:** Feldarten/Ländervarianten, leere und ungültige
Parameter, feste Seeds plus festgehaltene Zeit, referenzierte Felder,
Auto-Increment, Betragsrundung, Fehlerquoten 0/100 %, Zeilenanzahl 0/1/Schwellwert,
Unverändertheit der Eingaben. Parallelmodus zusätzlich mit bewusst fehlgeschlagenem
Worker, stabiler Reihenfolge und vollständiger Zeilenzahl prüfen.

**Erster umsetzbarer Umfang:** sequenzieller Feld-/Zeilenkern plus realer
Consumerpfad in DUMMY. Joblib und weitere Workeroptimierungen erweitern diesen
Umfang erst nach dessen Nachweis. Rechts-/Lizenzstatus bleibt separat sichtbar.

## 2. `auditcore_invoicegenerator`

**Zuschnitt:** synthetische Rechnungen und ihre Beziehungen, nicht ein allgemeines
Fachverfahrenspaket. Grunddaten werden über den Vertrag von
`auditcore_dummygenerator` bezogen. Fachliche Szenarien und Datensätze sind
versionierte Profile innerhalb des Pakets; nicht alle Flowinvoice-Regeln werden
dadurch verbindliche Standardregeln.

Der technisch bevorzugte Ausgangspunkt ist der bereits getrennte Daten-/Renderer-
Zuschnitt in PORTAL. Seine lokale technische Bearbeitung ist im beauftragten
Umfang autorisiert; eine öffentliche Weitergabe ist damit nicht nachgewiesen. INVOICE liefert
die verwandte Legacy-Variante und tatsächliche Consumerpfade. Beide Stände
werden vor einer gemeinsamen API getrennt charakterisiert.

Konkrete Quellen:

| Quelle/Symbol | Nutzen | Notwendige Abtrennung |
|---|---|---|
| PORTAL `backend/app/services/generator/invoice_data.py:_generate_invoice_data` | Bereits DB-frei ausgelagerte Datenerzeugung; zusätzliche explizite Parameter für Referenzdatum, Steuerschema und Belegvariante | Private Legacy-API, verzögerte Anwendungsimporte und bestehende Zustandskopplung vor öffentlichem Paketvertrag auflösen |
| PORTAL `backend/app/services/generator/pdf_render.py:BelegRenderer` | Öffentliche Klasse `BelegRenderer(seed=0)`; `render(beleg, *, realism=None, template_seed=None)` liefert PDF-Bytes, Text und Metadaten | Renderer und benötigte Ressourcen als optionalen Ausgabeadapter abgrenzen; ReportLab-Abhängigkeit prüfen |
| INVOICE `backend/app/worker/tasks.py:_generate_invoice_data` | Bereits verwendeter Rechnungserzeugungspfad mit Templates, Fehlerraten und Projektkontext | Rund 2.700 Zeilen in einer Workerdatei; kein geeigneter unveränderter Paketkern. Schrittweise mit charakterisierten Hilfsfunktionen und Datenverträgen zerlegen |
| INVOICE `backend/app/worker/tasks.py:_format_invoice_pdf` | Bestehende PDF-Ausgabe synthetischer Rechnungen | Dateipfad-/Rendereradapter; ReportLab nicht zur Pflichtabhängigkeit des reinen Datenkerns machen |
| INVOICE `backend/app/services/generator/category_positions.py:CatalogPosition`, `MixConfig`, `CategoryMixingEngine` | Positionskatalog und nachvollziehbare Mischungen | Fachliche Kataloge/Labels als explizite Profile erhalten |
| INVOICE `backend/app/services/generator/ground_truth_synthesizer.py:GroundTruthSynthesizer.synthesize` | Erwartete Trainingsbefunde aus bekannten Positionslabels | Ground Truth als erwarteten Szenariobefund behandeln, nicht als universell richtige Prüfentscheidung |
| INVOICE `backend/app/services/generator/scenario_generator.py:ScenarioConfig`, `ScenarioGenerator.generate` | Zusammenhängende Szenarien mit Firmen, Förderkontext und Folgebeziehungen | EFRE-/Beihilfe-/Bescheidinhalte zunächst abgrenzen; sie sind nicht notwendiger Bestandteil jeder synthetischen Rechnung |

Beobachtete Consumerpfade: `backend/app/api/generator.py` verwendet
`_generate_invoice_data` und `_format_invoice_pdf` für die Vorschau;
`backend/app/worker/tasks.py:_generate_invoices_async` verwendet beide für den
Generatorjob. API, Celery-Orchestrierung, Persistenz und Berechtigungen bleiben
in INVOICE. Erst diese Pfade werden später auf das installierte Paket umgestellt.
In PORTAL importiert/reexportiert `backend/app/worker/tasks.py` die getrennten
Generator-/Rendererfunktionen. Die Vorschau liegt ebenfalls in
`backend/app/api/generator.py`; `backend/app/modules/test_data/generator.py`
verwendet bereits Referenzdatum, Seed und explizites Zurücksetzen der Historie.
Diese Aufrufpfade sind besonders geeignet, um deterministische Paketaufrufe
und das Beibehalten von Anwendungszuständigkeiten nachzuweisen.

Abhängigkeiten: der vorhandene Worker enthält umfassende Anwendungsimporte;
diese dürfen nicht als Paketpflicht übernommen werden. Der Szenariogenerator
verwendet Standardbibliothek, `Faker` und lokale Katalogmodule. PDF-Ausgabe
benötigt ReportLab; eine optionale Ausgabeanbindung ist deshalb sinnvoll.
`DemoDataGenerator` erzeugt insbesondere Sanktions-/TED-Beispieldaten und ist
nicht gleichbedeutend mit dem Rechnungskern. Die Generatorklassen werden nicht
allein aufgrund ihrer Namen zusammenkopiert.

**Characterization-Paket:** pro Rechnungstemplate bekannte Eingaben und Ausgaben;
festgehaltene Uhrzeit, Zufallsquelle und UUID-Erzeugung; Positions-/Netto-/Steuer-/
Bruttobeträge; vorhandene Rundung inklusive absichtlich falscher Beträge;
Datumsformate, Währungen, Fehlerschwere und Fehlerraten; Ground-Truth-Zuordnung.
`_generate_invoice_data` verwendet aktuell globale Zufallsfunktionen und
`datetime.now()`, während Szenarioteile eigene Zufallsquellen/Faker nutzen.
Diese Verträge müssen vor einer vereinheitlichten Seed-API getrennt beobachtet
werden. Ein Wechsel von Float-Rundung zu Decimal ist eine Verhaltensänderung
und darf nicht nebenbei bei der Extraktion erfolgen.
PORTAL besitzt dazu bereits `backend/tests/test_generator_pdf_render.py` mit
Fällen für Templates, Summen/Text, Seeds/PDF-Hashes, Steuerschemata, Varianten
und Wiederherstellung des Zufallszustands. Diese Tests sind eine nutzbare
Ausgangsbasis, wurden für diese Planerstellung aber nicht ausgeführt.
Die beiden Hauptfunktionen `_generate_invoice_data` und `_format_invoice_pdf`
sind zwischen INVOICE und PORTAL nicht AST-identisch; die identische Teilfunktion
`_inject_errors` rechtfertigt deshalb keine Gleichsetzung der gesamten Generatoren.

**Erster umsetzbarer Umfang:** ein tatsächlich verwendetes Rechnungstemplate,
der zugehörige Daten-/Fehlervertrag und ein Vorschau-/Testdaten-Consumer; danach weitere
Templates und der Workerpfad. PDF und Trainingsprofile folgen mit jeweils
eigenen Golden-/Integrationstests. Keine KI-Anbindung im Datenkern erforderlich.

## 3. `auditcore_reporting`

- FLOWLIB `python/flowlib/excel/formats.py:get_number_format` und die bereits
  übernommene Plattformfunktion `auditcore.reporting.get_number_format` bilden
  den kleinsten abgegrenzten Ausgangspunkt. Vorhandene 34 Characterization-Fälle
  aus der bisherigen Übernahme werden erhalten; in dieser Planung wurden
  keine neuen fachlichen Testläufe durchgeführt.
- Beobachteter Consumer: FLOWLIB `python/flowlib/excel/report.py:write_dataframe`
  importiert die Formatfunktion und verwendet ihr Ergebnis für Excel-Zellen.
- JKB `audit_excel_utils.py:get_number_format` wird von `format_worksheet` und
  `_format_existing_sheet` verwendet. Die Implementierung ist nicht AST-identisch:
  FLOWLIB berücksichtigt primär Spaltennamensmuster, JKB zusätzlich Werte.
  Beide werden zunächst als benannte Formatprofile charakterisiert.
- Der Formatkern benötigt Standardbibliothek; `openpyxl` wird erst für echte
  Excel-Adapter erforderlich. Der vorhandene Flowlib-Quelldateiimport von
  openpyxl begründet keine Pflichtabhängigkeit der isolierten Formatfunktion.

**Characterization:** überschneidende Spaltenmuster/Priorität, unbekannte Namen,
Groß-/Kleinschreibung, Datum/Prozent/Betrag, Werttypen und JKB-Grenzfälle.
Die bestehende `auditcore.reporting`-API erhält einen kontrollierten
Kompatibilitätsweg; neue Fachpakete dürfen keine zyklische Plattformabhängigkeit
erzeugen. Die Flowlib-Baselineprobleme (fehlende referenzierte README und
bisherige Ruff-Befunde) werden als eigenständige Consumerarbeit behandelt.

## 4. Statistik und Stichproben: zwei Verträge, keine Formelangleichung

STAT `backend/app/services/analysis_core_service.py` enthält `run_benford`,
`run_outlier`, `run_duplicates` und weitere Verfahren. Modulimporte umfassen
NumPy, pandas, SciPy und fuzzywuzzy; der benötigte Ausschnitt wird je Funktion
bestimmt. Ein kompletter Serviceimport würde unnötige Abhängigkeiten mitziehen.
`run_benford` ist ein konkreter erster Statistik-Kandidat: ein-/zweistellige
Analyse, Null-/Negativwerte, fehlende Spalten und leere Daten charakterisieren.
Kennzahlen liefern keine automatisch festgestellten Risikofälle.

STAT `backend/app/services/sampling_service.py` enthält `_calculate_mus_sample_size`,
`_calculate_srs_sample_size`, `run_mus_standard`, `run_srs_standard`, geschichtete
und Zwei-Perioden-Varianten. Reine Größenberechnung kann zunächst mit
Standardbibliothek auskommen; Auswahl-/Tabellenverfahren benötigen weitere
numerische Abhängigkeiten. Diese werden nicht pauschal vorgezogen.

**Konkreter fachlicher Konflikt:** PORTAL enthält
`backend/app/modules/flowstat/services/sampling_service.py:_calculate_mus_sample_size`.
Am fixierten Stand verwendet STAT eine Z-Wert-/Wesentlichkeitsformel; PORTAL
verwendet `POISSON_RELIABILITY_FACTORS`, erwarteten Fehlerbetrag und eine
begrenzte verbleibende Präzision. Validierung und Grenzfallverhalten unterscheiden
sich ebenfalls. Der Kommentar im PORTAL-Code beansprucht eine bestimmte
methodische Grundlage; deren fachliche Richtigkeit wird durch diese statische
Planung **nicht** bestätigt. Status: `HUMAN_DECISION_REQUIRED`.

Zunächst getrennte Varianten und ihre Legacy-Ausgaben erhalten. Nicht einfach
die ältere Datei als gemeinsamen Kern auswählen. Das eingebettete Flowstat-Modul
belegt vorhandene Codeabstammung, aber keinen unabhängigen methodischen Consumer.
Seed, Reihenfolge, Schichtung, Fehlerquote, Konfidenz und Null-/Negativwerte
gehören in die Golden Tests jeder Variante.

## 5. Privacy, Documents, Risk und Procurement

| Paket | Konkrete Quellen | Voraussetzung und Grenze |
|---|---|---|
| `auditcore_privacy` | INVOICE `backend/app/verwk/services/pseudonymization.py:StablePseudonyms.code`; RISK `backend/app/services/pseudonymization.py:StablePseudonyms.code` | Die Methoden sind am inventarisierten Stand AST-identisch. Trotzdem ganzen Klassenvertrag samt `_unique`, Schlüsseln und Mappinglebensdauer prüfen. Modulimporte umfassen auch pandas/Faker/Anwendungsfunktionen; nur die benötigte Mechanik isolieren |
| `auditcore_documents` | INVOICE `backend/app/services/parser.py:PDFParser` | Das Modul umfasst u. a. pdfplumber, pdf2image, pytesseract, torch/transformers, HTTP/Redis und Anwendungsdienste. Es ist **kein** direkt übernehmbarer reiner Parser. Zuerst einzelne Datenverträge/Normalisierer aus realen Consumerfällen herauslösen |
| `auditcore_risk` | RISK `backend/app/pipeline/red_flags.py:compute_red_flags`, `_near_threshold`, `red_flag_summary` | pandas/NumPy/rapidfuzz und Anwendungsregeln beobachtet. Gewichte, Schwellen, Matching und Auslegung als versionierte Regeln mit Herkunft behandeln; kein gemeinsamer Score ohne fachliche Entscheidung |
| `auditcore_procurement` | INVOICE und PORTAL jeweils `backend/app/services/procurement_analyzer.py:ProcurementPreChecker.run_prechecks` | Die Methode ist AST-identisch, ruft aber mehrere fachliche Teilprüfungen auf. Schwellen-, Dokumenten-, Angebots- und Wertabweichungsregeln einzeln vergleichen. Gesamten Analyzer samt KI-/Anwendungsimporten nicht übernehmen |

Privacy benötigt zusätzlich Kollisions-, Wiederholbarkeits-, Mandanten-/
Schlüsseltrennungs- und Offenlegungstests; Pseudonymisierung wird nicht als
Anonymisierung bezeichnet. Dokumentparser benötigen Format-/Fehlerfixtures und
Ressourcengrenzen; Uploadberechtigungen verbleiben in den Anwendungen.
Risk/Procurement bleiben bei abweichenden Regeln
`HUMAN_DECISION_REQUIRED` bzw. `SECURITY_OR_POLICY_REVIEW_REQUIRED`.

## Abhängigkeiten, Liefergegenstände und Abnahme pro Paket

Geplanter Graph: `invoicegenerator → dummygenerator`; `sampling → statistics`
nur bei tatsächlich gemeinsamem numerischem Vertrag. Reporting, Documents und
Privacy bleiben unabhängig installierbar. Kein Rückimport zur Plattform und
keine automatische Vollinstallation aller Fachpakete. Jedes Paket erhält
`packages/auditcore_<domain>/pyproject.toml`, eigenen Importnamensraum und eine
explizite deklarierte Abhängigkeitsliste; optionale Renderer erhalten Extras.

Jeder Übergang wird mit konkreten Nachweisen abgeschlossen:

1. GitHub-Revision, Quellsymbole, Nutzungsrechte, Consumerpfad und
   `ApplicabilityContext` festhalten; unbekannte Fakten sichtbar lassen.
2. Legacy-Implementierung mit bekannten Eingaben tatsächlich ausführen und
   Ergebnisse/Fehler vor einer Änderung als Characterization sichern.
3. Abgegrenzten Vertrag extrahieren; Varianten und Sicherheitsgrenzen erhalten.
4. Eigenes Wheel/sdist bauen, Paket isoliert installieren und echte Aufrufe aus
   Requirements nachweisen. Bei APT-Bedarf .deb aus demselben Code prüfen.
5. Einen realen Consumer in dessen eigenem Repository migrieren: Imports,
   Versionsbindung, Wrapper, Regression/Integration und tatsächliche Aufrufherkunft.
6. Anwendbare Framework-Tests und Quality Gates erneut ausführen; erst danach
   Legacy-Code kontrolliert entfernen, API-Snapshot/Provenienz/Inventar und KIRA
   aktualisieren. Paketbau allein ist keine abgeschlossene Konsolidierung.

Dieser Plan bestätigt weder Framework-Abnahme noch Fachfreigaben oder
Paketveröffentlichungen. Er legt die nächste ausführbare Reihenfolge und die
konkreten Quell-/Verhaltensnachweise fest; fachlicher Code bleibt unverändert.
