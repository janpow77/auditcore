# Repository-Abdeckung: Fachbibliotheken, Harvester, Analysen und Werkzeuge

Stand: 22. September 2026. **Planung und Quelleninventur; keine zusätzliche
Bibliothek implementiert, kein fremdes Anwendungsrepository geändert.**
Der bisherige [Domain-Paketplan](DOMAIN_PACKAGE_PLAN.md) war eine erste Auswahl,
kein vollständiger Katalog aller möglichen Bibliotheken. Harvester, weitere
Analysen, bestehende Bibliotheken und technische Werkzeuge gehören ausdrücklich
zum Gesamtbestand. Dieses Dokument ergänzt den Plan um alle aktuell sichtbaren
eigenen Repositories und einen fachlich begründeten nächsten Zuschnitt.

Die nachfolgende [vertiefte Funktionsübersicht](FUNCTION_OVERVIEW.md) enthält
die erneute GitHub-/Gitbaum-/AST-Inventur aller 71 Repositories, tatsächliche
KIRA/RAG-/Graphify-Abfragen und Detailberichte für Workshop, OSINT/map.flowaudit,
Designer/MCP, FlowStat und Regulierung. Sie ergänzt diese erste Einordnung;
Regulierung ist der erste konkrete Refactoring-/Debian-Consumer.

## Erhebung und belastbare Grenzen

Der authentifizierte GitHub-Owner ist `janpow77`. Die aktuelle REST-Abfrage
`user/repos?affiliation=owner` sowie GraphQL `viewer.repositories` lieferten
**71 eigene Repositories**, ohne weitere Ergebnisseite. Gegenüber den 71 Namen
des persistenten Inventars gibt es keine Ergänzung oder Entfernung. Default-
Branch und Commit wurden für alle 71 frisch abgefragt. Fremde Organisationen,
Collaborator-Repositories anderer Eigentümer, andere Branches und lokale
unveröffentlichte Projekte sind dadurch nicht vollständig abgedeckt.

Quellen: persistierte `repositories.json`, `symbols.json`, `dependencies.json`
und vorhandene Checkouts unter `.auditcore/repositories/`; aktuelle Metadaten
unter `.auditcore/coverage-current-repositories.jsonl` und
`.auditcore/coverage-current-heads.json`. Zusätzlich wurden GitHub-Bäume mit
bisher unklarer/geringer Dateiabdeckung gelesen
(`.auditcore/coverage-small-trees.json`) und ausgewählte Quellsymbole,
Imports sowie tatsächliche Aufrufstellen geprüft. Commit-/Dirty-Prüfung der
vorhandenen Checkouts: `.auditcore/coverage-checkout-verification.json`.
Die vollständigen SHAs stehen in den unten verlinkten GitHub-Tree-Adressen.

**Wesentliche Korrektur der alten Inventur:** `file_count=0` im Python-/Manifest-
Katalog bedeutet nicht, dass ein Repository leer ist. `Report_new` enthält
21 Office-Exportdateien, `Ausgabenliste` extensionlosen VBA-Code, `evo-x2-setup`
29 überwiegend Shell-/Service-/Setup-Dateien und `router` 77 Dateien unter
anderem für Rust und Betrieb. Fünf frühere UNKNOWN-Revisionen sind jetzt
aufgelöst: Checkboxes, SAP_Auswertung, VBA_Excel_tools, Drucknachweise und
python_diagramm. Von diesen enthält Checkboxes echten extensionlosen VBA-Code;
die anderen vier enthalten nur README-Dokumentation. `auditinvoice` ist laut
aktueller GitHub-Auskunft tatsächlich leer. Die früher ausgewiesenen sechs
leeren Repositories sind deshalb keine korrekte aktuelle Gesamtbeschreibung.

Die vorhandenen Parsefehler in `flowstat/backend/tests/fix_tests.py` und
`llm-rag-audit-presentation/update_app.py` bleiben sichtbar. Nicht-Python-Code
hat hier Dateibaum-/Manifest- und punktuelle Quellenabdeckung, keine behauptete
vollständige Symbol-/Callgraph-Abdeckung. Kein Harvester wurde gegen produktive
Datenquellen gestartet, keine API-Limits verbraucht und kein Consumer migriert.

## Welche Einheiten entstehen sollen

1. **Fachbibliotheken:** deterministische fachliche Datenverträge, Berechnungen,
   Normalisierung und Parser mit eigenem Nutzen und Charakterisierung.
2. **Quellenadapter/Harvester:** HTTP-/Feed-/Portal-Anbindung mit explizitem
   Transport, Herkunft und Quellversion. Diese dürfen I/O-Abhängigkeiten haben,
   bleiben aber getrennt von reinen Berechnungskernen und Anwendungsdatenbanken.
3. **Plattformwerkzeuge/Plugins:** Analyse, Migration, Betrieb und Integration
   in die vorhandenen vier auditcore-Werkzeuge. Kein zusätzliches Fachpaket
   allein deshalb, weil eine Funktion Python verwendet.
4. **Anwendungen und Dienste:** UI, Authentifizierung, Rollen, Datenhaltung,
   Scheduler, KI-Modellbetrieb und Release bleiben in ihrem Repository.

Ein Repository kann mehrere dieser Rollen enthalten. Es wird weder mit auditcore
zusammengelegt noch pauschal in ein Paket umgewandelt. Bereits brauchbare Pakete
wie `docformatter`, `humanizer`, Flowlib, Flow-Agent-Verträge oder
`legacy_office_quality` werden zuerst als bestehende Bausteine geprüft;
automatisches Umbenennen oder doppeltes Paketieren wäre keine Konsolidierung.
Keine neue Distribution erhält ohne technischen Grund eine Runtime-Abhängigkeit
von der Plattform auditcore. Ein `auditcore_utils` oder ein einziges Paket für
sämtliche Harvester, Analysen und Werkzeuge ist nicht vorgesehen.

## Konkrete zusätzliche Paketfamilien

Die folgenden Namen sind Planungsziele, keine bereits veröffentlichten Pakete.
Quell-SHAs sind pro Repository in der Abdeckungstabelle festgehalten. Ein
beobachteter Anwendungsaufruf ist ein **Legacy-Consumer**, noch kein Consumer
der vorgeschlagenen Distribution. Ähnliche eingebettete Kopien beweisen keine
unabhängige Herkunft oder bereits erfolgte Wiederverwendung.

### D — Verarbeitungsverzeichnisse erstellen und DSFA berechnen: `auditcore_dataprotection`

**Priorität aufgrund der ausdrücklichen Nutzerpräzisierung:** Die Bibliothek
soll jeder Consumer-Anwendung ermöglichen, ein eigenes Verarbeitungsverzeichnis
anzulegen, Tätigkeiten zu bearbeiten/versionieren und daraus eine eigene DSFA
mit Fragen, Risiken, Maßnahmen, Stellungnahmen, Review und Export zu führen.
**Die DSFA-Berechnung ist verpflichtender Kernumfang:** Schwellwertanalyse,
Bruttorisiko, Maßnahmenwirkung, Nettorisiko und begründeter Bewertungsvorschlag
werden anhand expliziter versionierter Profile berechnet.
Es geht nicht bloß um das Lesen vorhandener Datenschutzdokumente oder um eine
Liste gesetzlicher Anforderungen. Dies ist eine eigene fachliche Fähigkeit,
getrennt von Pseudonymisierung in `auditcore_privacy`.

Konkrete Quelle ist `regulierung` am unten vollständig verlinkten Commit
`a5d48ea4b90a410210ec25e707781ef9e21ad743`:

- `backend/app/services/mandant_dsgvo_service.py`: `taetigkeit_kennung`,
  `taetigkeiten_mit_kennung`, `speichere_entwurf`, `freigeben`, `vorbelegen`,
  `baue_verarbeitungsverzeichnis_workbook`.
- `backend/app/services/dsfa/bewertung.py`: Dataclasses `Antwort`, `Szenario`,
  `Schwellwertergebnis`, `Risikoergebnis`, `Vorschlag`; Funktionen
  `vorbelegung_aus_taetigkeit`, `werte_schwellwert_aus`, `werte_risiko_aus`,
  `erstelle_vorschlag`, `vorschlag_als_json`.
- `dsfa/katalog.py` enthält versionierbare Fragen-/Maßnahmenprofile;
  `dsfa/verwaltung.py` speichert Fassungen, Entscheidungen, DSB-Stellungnahme
  und Freigabe; `dsfa/export.py` liefert Ausgaben. Die vorhandenen ORM-Modelle
  `MandantDsfa` und `MandantDsgvoDokument` sind Persistenzadapter, keine
  unverändert zu exportierende Bibliotheks-API.
- Tatsächliche Consumer sind `api/admin/mandant_dsgvo.py`, `api/admin/dsfa.py`
  sowie die Ansichten `MandantDsgvoSeite.tsx` und `MandantDsfaAnsicht.tsx`.
  Ihre Oberfläche bleibt erhalten. Ein Pythonpaket allein stellt diese UI
  nicht automatisch in jeder anderen Anwendung bereit; dafür braucht es
  explizite Consumer-API-/UI-Integration.

Paketvertrag: Erstellen und Bearbeiten von Tätigkeiten/Registern/DSFA,
versionierte Entwürfe, explizite Zustandsübergänge, nachvollziehbare Berechnung
und serialisierbare Exportdaten; Dateiformate als optionale Renderer. Storage,
Actor-/Rechteprüfung und Audit-Ausleitung über klar definierte Ports anbinden.
Mandantentrennung, Vier-Augen-Prinzip, Versionsschutz und Audit-Trail werden
bei der Extraktion geprüft und erhalten, nicht zugunsten einer einfacheren
Bibliotheks-API gestrichen. Consumer müssen diese Ports tatsächlich umsetzen.

Characterization vor Extraktion: leeres/neues Register, Tätigkeitskennungen,
Änderungen und Nachfolgerfassung, unbeantwortete Fragen, Schwellen-/Risikofälle,
Maßnahmenwirkung, Begründungspflicht, unzulässige Freigabe, veraltete Version,
Export und mandantenfremder Zugriff. Die Bewertungen bleiben Vorschläge mit
explizitem menschlichem Review. Quelleigene externe Vorlagenhinweise
(insbesondere BfDI/CC-BY-SA 4.0) benötigen Rechte-/Attributionsprüfung;
die MIT-Freigabe der zwei Generatoren gilt nicht automatisch für diese Inhalte.

### H0 — Gemeinsamer Datenharvest: `auditcore_harvest`

**Ausdrücklich gewünschter gemeinsamer Kern für alle angebundenen Datenharvester.**
Dieser Teil war bislang bedingt vorgesehen und ist nun als eigener technischer
Bibliotheksvertrag konkretisiert. Die unterschiedlichen Quellenadapter verwenden
denselben Ablauf und dieselben Nachweis-/Fortschrittsverträge. Das Kernpaket
installiert keine komplette Sammlung aller Quellen oder deren Spezialabhängigkeiten.

Gemeinsame Fähigkeiten:

- `Source`, `HarvestRequest`, `HarvestRecord`, `HarvestResult` und quellenbezogene
  Cursor/Checkpoints als versionierte Datenverträge; Originalquelle, Abrufzeit,
  Profilversion und Contenthash bleiben pro Datensatz erhalten.
- Ablauf Abruf → Parse → Validierung/Normalisierung → Übergabe an eine Senke;
  Quellenparser und fachliche Datenmodelle bleiben im jeweiligen Adapter.
- Pagination, Timeouts, begrenzte Wiederholungen, Rate-Limits und `Retry-After`,
  Abbruch-/Fortsetzungszustände und erkennbare Teilfehler.
- Inkrementelle Aktualisierung, stabile Identitäten, Dublettenmechanik und
  idempotente Senkenverträge. Checkpoints erst nach bestätigter Verarbeitung
  fortschreiben; keine unbelegte Exactly-once-Zusage. Snapshot-/Löschsemantik
  ausdrücklich pro Quellenprofil erhalten.
- Injektionsfähiger HTTP-/Dateitransport, Uhr/Zufallsquelle für Backoff,
  StateStore und Sink; kein fester Anwendungs-ORM oder Mandantenkontext.
- Einheitliche strukturierte Ergebnisse/Fehler und begrenzte, secretfreie Logs;
  Zugangsdaten über den Consumer bzw. Credential-Provider.
- Optionale CLI für konfigurierte Abrufe und lokal replaybare Fixtures;
  Scheduling, produktive Speicherung und Berechtigungen bleiben Integrationsaufgaben.

Belegte Ausgangspunkte sind die wiederkehrenden `BaseHarvester`-/`HarvestResult`-
Verträge in auditdatabase und audit_designer sowie `BaseConnector`/`HarvestResult`
in regulierung. Ihre bestehenden Anwendungs-/DB-Bindungen müssen vorher
charakterisiert und über Schnittstellen abgetrennt werden. Eine identische
Bezeichnung belegt noch keine kompatible Semantik.

Abhängigkeitsrichtung: die Quellenadapter in `auditcore_procurement`,
`auditcore_legal_sources`, `auditcore_funding_sources`,
`auditcore_registry_sources` und weitere begründete Quellenfamilien nutzen
`auditcore_harvest`; der Kern importiert diese Familien nicht obligatorisch.
Anwendungen installieren nur ihre Quellenpakete. `auditcore` bleibt die Plattform
zur Herstellung/Prüfung und ist keine Pflicht-Laufzeitabhängigkeit dieses Kerns.

Alle **angebundenen** Quellen können damit über einen einheitlichen Einstieg
abgerufen werden. Eine neue API, Website, Datei oder ein Portal braucht weiterhin
einen passenden Adapter mit tatsächlich getesteten Parser-/Zugriffsregeln.
Fachliche Analyseverfahren verwenden die Ergebnisse über ihre Datenverträge;
Bewertung, DSFA-Berechnung und Prüfentscheidungen gehören nicht in den Harvestkern.

Erster Nachweis: mindestens zwei reale Quellenadapter aus unterschiedlichen
Familien durch denselben Kern betreiben, Originalantworten replayen und
Pagination, Wiederanlauf nach Teilfehler, Dubletten, idempotente Übergabe und
Checkpoint-Konsistenz testen. Ein konfigurierter zulässiger externer Smoke-Test
wird separat ausgewiesen. Status: **geplant, noch nicht implementiert**.

#### Verbindliche Adapterdokumentation und Quellenkatalog

Zum Lieferumfang von `auditcore_harvest` gehören eine mitgelieferte
Adapteranleitung, eine referenzierte öffentliche Schnittstelle und ausführbare
Referenzadapter. Die unten genannten Verträge sind Implementierungsanforderungen,
noch keine importierbare API. Die endgültigen Signaturen werden anhand der
Characterization der ersten zwei Quellen festgelegt und anschließend versioniert.

Die Anleitung muss konkret zeigen:

1. Quellenkennung, Adapter-/Profilversion, unterstützte Filter, Datenformat und
   Fähigkeiten deklarieren (Pagination, inkrementeller Abruf, vollständiger
   Snapshot, Löschmeldungen). Unbekannte Fähigkeiten ausdrücklich kennzeichnen.
2. Konfiguration validieren, Zugangsdaten über den Credential-Provider beziehen
   und mit injiziertem Transport genau eine begrenzte Seite abrufen. Ein
   Seitenergebnis enthält Datensätze, den nächsten Cursor und einen expliziten
   Abschluss-/Teilfehlerstatus; der Kern steuert Wiederholungen und Seitenfolge.
3. Quellantworten in Datensätze mit stabiler Quellen-ID, Rohwert-/Normalisierungs-
   vertrag und Provenienz übersetzen. Fehlende Felder und Parserfehler dürfen
   nicht als erfolgreicher leerer Datenbestand erscheinen.
4. Authentifizierungs-, Konfigurations-, Rate-Limit-, Transport- und Parserfehler
   unterscheidbar zurückgeben. Retry-Informationen müssen maschinenlesbar sein;
   irreversible fachliche Entscheidungen trifft kein allgemeiner Retry-Handler.
5. Adapter explizit registrieren, aus einer Consumer-Anwendung aufrufen und die
   Ergebnisse an eine austauschbare Senke liefern. Wiederanlauf, Abbruch und
   Checkpoint-Bestätigung anhand eines ausführbaren Beispiels erklären.
6. Eine wiederverwendbare Contract-Test-Suite gegen eigene Adapter ausführen:
   Fixtures, Paging, leere/fehlerhafte Antworten, Limits, Teilfehler, Cursor-
   Fortschritt, stabile IDs und Wiederholung nach fehlgeschlagener Speicherung.

Ein versionierter Quellenkatalog wird zusammen mit den Adapterpaketen gepflegt.
Pro Quelle enthält er Herkunftsrepository und Commit, bestehenden Consumer,
Quellenprofil, Authentifizierungsbedarf, Lizenz-/Zugangsprüfung, Konfigurations-
schema ohne Secrets, Fixtures und letzten tatsächlichen Prüfstatus. Unterstützt,
nur geplant und nicht konfiguriert müssen im Katalog unterscheidbar bleiben.

**Die bereits in den Anwendungen angebundenen Quellen sind Ausgangsbestand**,
keine erst später zu entdeckende optionale Ergänzung:

| Familie | Bereits belegte Quellen/Anbindungen, für Adapterübernahme vorgesehen |
|---|---|
| Recht und Prüfung | DIP, EUR-Lex, CURIA, ECA, OLAF, Gesetze im Internet, Hessenrecht, Bundes-/Landesrechnungshöfe, Prüfverbände und vorhandene RSS-Profile |
| Vergabebekanntmachungen (`auditcore_procurement`) | TED, HAD und weitere Vergabequellen; Online-Harvester, Dateiimport und Normalisierung aus Audit-Portal sowie Clients aus Flowinvoice/Designer vergleichen |
| Förderung | EU-Begünstigtendaten, State Aid und das gesonderte De-minimis-/eAidRegister-Profil aus Flowsearch, Flowworkshop und Designer |
| Register | Bestehende OpenRegister-, Handelsregister-, Sanktions- und PEP-Clients; tatsächlichen Provider und Zugang je Profil verifizieren |
| Preis und Energie | Bundesbank, Destatis, EIA, EU Oil Bulletin, Tankerkoenig und MTSK aus regulierung; mögliche Überschneidungen anhand der Verträge prüfen |
| Geo | Overpass sowie vorhandene Natura-/Geocoding-Anbindungen mit getrennten Profilen |
| Immobilien | Vorhandene Bienici-, Citya-, Paruvendu-, Kleinanzeigen-, InBerlinWohnen- und ZVG-Parser, vorbehaltlich konkreter Zugangs-/Rechteprüfung |

Die Belege und Abgrenzungen stehen in H1–H5. Diese Liste bestätigt vorhandenen
Code, nicht die heutige Erreichbarkeit aller Dienste oder einen bereits
erfolgreichen Live-Abruf. Weitere im Inventar belegte Quellen werden in den
Katalog aufgenommen; keine Quelle allein wegen dieser Übersicht entfernen.
Die Umsetzung beginnt mit einem Legal- und einem Funding-Adapter und erweitert
danach die vorhandenen Familien. Abweichende Quellregeln bleiben explizit.

### H1 — Rechts-, Prüf- und Publikationsquellen: `auditcore_legal_sources`

- `auditdatabase/backend/app/harvester/base.py`: `HarvestedDocument`,
  `HarvestResult`, `BaseHarvester`; konkrete Adapter in `dip.py`, `eurlex.py`,
  `rechnungshoefe.py`, `landesrechnungshoefe.py`, `rss.py`.
- `audit_designer/backend/app/modules/vp_ai/harvester/`: wesentlich umfangreichere
  Familie einschließlich BundestagDIP, EUR-Lex, CURIA, ECA, OLAF, Gesetze im
  Internet, Hessenrecht, Rechnungshöfen und Prüfverbänden. Nicht auf die früher
  ausgewählten sieben Fachrepositories begrenzen. Im vorhandenen Symbolinventar
  liegen in diesem Verzeichnis 59 Klassen einschließlich Basis-/Schedulerklassen;
  dies ist keine Behauptung von 59 unabhängig funktionierenden Quellenadaptern.
- Belegte Consumer: auditdatabase `services/scheduler_service.py` ruft
  `get_harvester(source_id, db=db)` und `harvest()` auf; Designer
  `harvester/scheduler.py` tut dies mit eigenen Timeouts. Beide Scheduler und
  ihre Persistenz bleiben anwendungseigene Adapter.
- Tatsächliche Abhängigkeiten: unter anderem `httpx`, `feedparser`,
  `SPARQLWrapper`, BeautifulSoup und teilweise Playwright; vorhandene Basen
  binden SQLAlchemy beziehungsweise Anwendungsmodelle ein. Eine unveränderte
  Übernahme dieser Basisklassen wäre keine frameworkunabhängige Bibliothek.
- Zuerst gemeinsame Dokument-/Quellenverträge und ein konkretes DIP- oder
  EUR-Lex-Profil mit aufgezeichneten Antwortfixtures; danach weitere Adapter
  innerhalb derselben Familie. HTTP-Transport injizieren, DB-Ausleitung getrennt.
  Characterization: Paging, Feed-/HTML-Varianten, Dubletten, Contenthash,
  Publikationsdatum, Zeitüberschreitung, Rückfallpfad und unvollständiger Abruf.

### H2 — Fördertransparenz und Beihilfen: `auditcore_funding_sources`

- `flowsearch/backend/app/services/eu_beneficiary_harvester_v2.py`:
  `EUBeneficiaryHarvesterV2`; außerdem `StateAidHarvester` und
  `HarvestSourceManager`. Die CLI-Skripte `harvest_eu_beneficiaries_v2.py`
  und `harvest_state_aid.py` instanziieren diese Klassen tatsächlich.
- `flowworkshop/auditworkshop/backend/services/beneficiary_harvester.py`:
  `parse_xlsx_or_csv`, `compute_record_hash`; `state_aid_service.py`:
  `parse_amount`, `parse_date`, `normalize_company_name`, `detect_sa_reference`.
  Der Begünstigten-Harvester importiert und verwendet die Betrags-/Datumsparser.
- `audit_designer/backend/app/core/shared/research/register/beneficiaries.py`
  und `state_aid.py` enthalten verwandte, **nicht automatisch gleichartige**
  Parser/Hashes; AST-Fingerprints von `parse_amount` und `compute_record_hash`
  unterscheiden sich zwischen Workshop und Designer.
- Der Kern sollte zunächst Quellenzeilen, Rohwerte, normalisierte Werte und
  Provenienz liefern. XLSX als klar deklarierter optionaler `openpyxl`-Adapter;
  HTTP-Clients getrennt. SQLAlchemy-Upserts, Snapshot-Freigabe und UI bleiben
  bei den Anwendungen. Methoden `smart`, `full-refresh`, `force`, `snapshot`
  dürfen wegen unterschiedlicher Lösch-/Bestandssemantik nicht vereinheitlicht
  oder als gewöhnliche Parseroption behandelt werden.
- Gute nächste Extraktion: datensatzbezogene Parser/Hashes aus einem fixierten
  Profil; Tests für Komma/Punkt/Tausenderzeichen, Betragsintervalle, Datum,
  fehlende Namen, Postleitzahlen, Headererkennung, Snapshot-Grenzen und stabile
  Identität. Keine stillen Änderungen der Hashfelder oder Nullwertsemantik.

#### De-minimis ausdrücklich als eigenes Quellenprofil

De-minimis ist im Plan zusätzlich zu State Aid zu führen. Konkreter vorhandener
Code in `audit_designer/backend/app/core/shared/research/register/`:
`de_minimis.py` mit `EAidRegisterClient`, `Suchkriterien`,
`DeMinimisRegisterProvider`, `DeMinimisCumulationProvider` und
`berechne_kumulierung`; `de_minimis_ernte.py` mit `ernte`, `bestandsstand` und
Feldnormalisierung sowie `de_minimis_models.py` für die Anwendungspersistenz.
Das sind Codebelege am inventarisierten Stand, kein aktueller Live-Nachweis.

Der Registerabruf gehört als eigenes Profil in `auditcore_funding_sources`
auf Basis von `auditcore_harvest`. State-Aid- und De-minimis-Bestände behalten
getrennte Quellenidentitäten, Filter, Abdeckungs- und Vollständigkeitsangaben.
Bestehende ORM-Modelle und Freigaben nicht unverändert in den Kern übernehmen.
Characterization umfasst Paging, Länder-/Datumsfilter, Dezimalbeträge,
Quellenidentitäten, Teilabbrüche und Bestandsstände. Unvollständige Abrufe
dürfen keinen vollständigen leeren Bestand vortäuschen.

Die vorhandene Kumulierungsberechnung ist separat zu charakterisieren und als
fachlicher Vertrag zu planen: Regelprofil, Gültigkeitszeitraum, Unternehmens-
zuordnung, berücksichtigte Beihilfen, Berechnung und Begründung explizit halten.
Abweichende Schwellen-/Zeitraumregeln im Legacy-Code verlangen fachlichen Review;
keine automatische Harmonisierung oder Ableitung einer Freigabe aus einem
Registerabruf. Keine ungeprüfte Übernahme alter Konstanten als aktuelle Rechtslage.

### H2a — Vergabebekanntmachungen: `auditcore_procurement`

Verbindlicher fachlicher Zuschnitt: TED, HAD und weitere Vergabebekanntmachungen
gehören gemeinsam mit den Vergabedatenmodellen und Prüfverfahren in
`auditcore_procurement`. `auditcore_legal_sources` bleibt für Rechts- und
Prüfpublikationen vorgesehen. Kein separates TED-/HAD-Paket erzeugen.

`audit-portal/backend/app/services/ted_harvester_service.py` enthält
`build_ted_query`, seitenweisen Online-Abruf und Re-Exports der vorhandenen
Normalisierung aus `audit_prep.ted_normalize`. Die vorhandenen Tests in
`backend/tests/test_ted_harvest.py` behandeln unter anderem Feature-Flag,
Netzwerk-/HTTP-Fehler, Paging, Dubletten, Mengenbegrenzung und Normalisierung.
Diese Tests wurden bei dieser Planergänzung gelesen, nicht ausgeführt.
Weitere konkrete Vergleichsquellen sind `_TEDClient` in
`flowinvoice/company_records.py` und die Company-Clients im Designer.

Für HAD sind `HADNotice` und `_HADClient` in `flowinvoice/company_records.py`
und im Designer unter
`backend/app/modules/vp_ai/services/company/company_records.py` belegt.
Die Clients verwenden unterschiedliche Suchpfade; Parser, Suchfilter,
Archivumfang und Dublettenverhalten vor einer Zusammenführung charakterisieren.
Weitere Vergabeportale als eigene Quellenprofile derselben Bibliothek erfassen.

Die Vergabeadapter verwenden `auditcore_harvest` für den gemeinsamen Ablauf.
Innerhalb von `auditcore_procurement` bleiben reine Modelle, Normalisierung und
fachliche Prüfungen von Netzwerkadaptern getrennt. Quellenabhängigkeiten über
deklarierte Extras laden, sodass reine Vergabeberechnungen keine HTTP-/Browser-
Installation benötigen. Adapter und Bewertungsfunktionen teilen dokumentierte
Datenverträge, aber ein erfolgreicher Abruf bedeutet keine bestandene Prüfung.
Das vorhandene Paket `audit_prep` zuerst auf Wiederverwendung prüfen. Online-
Abruf und Dateiimport müssen denselben dokumentierten Datensatzvertrag erfüllen.
Bekanntmachungstyp, CPV, Datums-/Länderfilter, Gewinnerbezug, Sprache, Beträge,
Währung und Versions-/Korrekturbezug charakterisieren. Den bisherigen
Zuschlags-/Gewinnerfilter nicht still als vollständige TED-Abdeckung ausgeben.
Anwendungsseitige Offline-Sperren und Zugriffsrechte erhalten; Vergabebewertung
bleibt ein separater Fachvertrag. Übernahme und Veröffentlichung bleiben von
Quellrechten und tatsächlicher Verifikation abhängig.

### H3 — Entitätsabgleich und Register: getrennte Mechanik und Quellen

`auditcore_entity_matching` ist ein möglicher reiner Kern für Unicode-/Namens-
Normalisierung, LEI-Prüfung und nachvollziehbare Match-Komponenten.
`flowworkshop/services/entity_resolution.py:is_valid_lei`,
`services/state_aid_service.py:normalize_company_name`,
`services/sanctions_service.py:normalize_name` sowie Designer
`register/sanctions.py:normalisiere_name` sind konkrete Ausgangspunkte.
`rapidfuzz` ist tatsächlich vorhanden; ORM, Datenbank-Resolve und Persistenz
werden nicht zur Paketpflicht. Der kleine LEI-/Normalisierungskern ist vor
einem kompletten Entity-Resolution-Service extrahierbar.

Register-/Sanktionsclients bleiben in einem passend abgegrenzten Adapterteil,
vorläufig `auditcore_registry_sources` mit Quellenprofilen. Flowsearch hat
konkrete `OpenRegisterAPIClient`, `HandelsregisterAPIClient`,
`SanctionsAPIClient` und `PEPScreeningAPIClient`; Workshop, Designer, Riskanalysis
und Portal enthalten weitere Screeningpfade. Schwellen, Geburtsdatum-/Land-
Gewichtungen und UBO/KMU-Urteile sind **fachliche Profile**, keine allgemein
gültigen Hilfsfunktionen. Sie verlangen getrennte Characterization und
`HUMAN_DECISION_REQUIRED`, wenn Varianten widersprechen. Datenlizenzen,
Provider-Zugang und Aktualitätsnachweise gehören zusätzlich zur Quellanbindung.

### H4 — Preis-, Energie- und Geodaten

`regulierung/backend/app/services/external_apis/` hat `BaseConnector`,
`HarvestResult` und konkrete Bundesbank-, Destatis-, EIA-, EU-Oil-Bulletin-,
Tankerkoenig-, MTSK- und Overpass-Adapter. Der tatsächliche Consumer
`api/admin/external_apis.py` wählt über `CONNECTORS` und ruft `connector.run()`.
Die Basis verwendet `httpx`, SQLAlchemy, Secret-Umgebungsvariablen und
anwendungsspezifische Laufprotokolle; sie ist deshalb kein direkt kopierbarer
reiner Bibliothekskern.

Planungsfamilie `auditcore_price_sources`: Quellen-Snapshots, Einheiten,
Zeitbezug und explizite Datenadapter. Davon getrennt bleibt eine mögliche
`auditcore_price_analysis` mit den Decimal-Funktionen `calculate_wasser`,
`calculate_nahwaerme` und Staffelberechnung aus `services/calculator.py`.
Tarife, Gültigkeitsdaten, Rundung und Freigabestatus brauchen eigene Profile.
Die vorhandene LLM-Extraktion, Plausibilisierung, Reviewqueue und Scheduler
bleiben zunächst in der Anwendung; keine automatische Preisfreigabe.

Ein kleiner `auditcore_geo`-Kern ist über OSINT `ortsdienst/dienst.py:haversine_km`
und `werkzeuge/bundeslaender_holen.py:utm_nach_wgs84`, `wkb_polygone`,
`douglas_peucker` sowie Natura-/Geocodingpfade in Flowsearch/Workshop prüfbar.
Coordinate Reference System, Achsenfolge, Distanzmaß, Randpunkte und Einheiten
charakterisieren. HTTP-Dienste, Geocoder-Budgets und PostGIS bleiben Adapter;
nicht jede Geometriefunktion benötigt eine eigene Distribution.

**Umgesetzt (23.09.2026):** `packages/auditcore_geo` 0.1.0 mit Erdmodell-Profilen,
Umkreis, Punkt in Fläche mit Rand, UTM, GeoPackage, Douglas-Peucker und
Nominatim-Adapter (Extra `geocoder` auf `auditcore_harvest`); 290 charakterisierte
Originalfälle, Consumer geplant (Nutzerentscheidung). Bericht:
[GEO_PACKAGE_REPORT.md](../reports/GEO_PACKAGE_REPORT.md).

### H5 — Immobilien- und Finanzmarktdaten bleiben eigene Domänen

`wohnungsmonitor` enthält konkrete Portalparser, beispielsweise
`immobilien_export.py:parse_page`, `normalise`, sowie Bienici-, Citya-,
Paruvendu-, Kleinanzeigen- und InBerlinWohnen-Varianten. `versteigerung` ergänzt
`backend/app/crawler/zvg_crawler.py:ZvgPortal` und Gutachten-/POI-Ingest.
Ein `auditcore_property_sources` mit getrennten Quellprofilen ist ein Kandidat;
Preis-/Flächen-/Adress-Normalisierung und Statuswechsel benötigen Fixtures.
Ein HTTP-Client allein beweist keine gleiche Fachsemantik der Portale.

**Umsetzung (2026-09-23): `auditcore_property_sources` 0.1.0** unter
`packages/auditcore_property_sources` – sieben getrennte Quellprofile
(immobilien.de, inberlinwohnen, Kleinanzeigen, bienici, Citya, ParuVendu,
ZVG-Portal) mit Harvest-Adaptern (Extra `sources`), reinem ZVG-Lebenszyklus
(`erfasst`/`terminiert`/`abgehalten`/`aufgehoben`, gegen die Original-SQL auf
PostgreSQL charakterisiert) und Zugangskatalog. Characterization auf
synthetischen, strukturabgeleiteten Seiten (in beiden Repos liegen keine
gespeicherten Portalseiten), 228 Funktionsfälle exakt. Consumer
wohnungsmonitor und versteigerung: **geplant** (Nutzerentscheidung
2026-09-23: „der mehrfache Nutzen kommt noch“); je Quelle heute ein Consumer.
Befunde: robots.txt sperrt die Kleinanzeigen-Suchadresse (`/*/preis:*`) und die
ZVG-Detail-/Anhangsseiten – HUMAN_DECISION_REQUIRED; Nutzungsbedingungen aller
Portale REVIEW_REQUIRED. Bericht:
[PROPERTY_SOURCES_PACKAGE_REPORT](../reports/PROPERTY_SOURCES_PACKAGE_REPORT.md).

`krypto` enthält zahlreiche Provideradapter und einen Polars-basierten
Indikatorkern `backend/app/services/indicators/base.py` mit `returns`,
`log_returns`, `sma`, `ema`, `rsi`, `atr`, `adx`. Ein spezifischer
`auditcore_market_indicators`-Kern ist prüfbar; Datenabruf, Portfolioentscheidungen
und Trading bleiben getrennt. Finanzmarkt- und Energiepreisadapter werden
wegen gleicher HTTP-Technik nicht zu einem pauschalen Markt-Harvester vereinigt.

**Umgesetzt (23.09.2026):** `packages/auditcore_market_indicators` 0.1.0 aus
`krypto@34d6017` – Kern nur mit Standardbibliothek, polars als Extra, vier
quellengebundene Profile (`indicators_base`, `scoring_rsi_macd`,
`scoring_confluence`, `regime_hmm`) für EMA-Start, Wilder-/EMA-/SMA-Glättung,
Lücken und Summationsreihenfolge; 1922 tatsächlich ausgeführte Originalaufrufe
nachgespielt. Repositoryübergreifender Mehrfachnutzen ist nicht belegt; das
Paket entsteht auf Nutzerentscheidung („der mehrfache Nutzen kommt noch“),
Consumer krypto ist **geplant** und in einer Kopie mit 1345/1345 Tests geprüft.
Bericht: [MARKET_INDICATORS_PACKAGE_REPORT.md](../reports/MARKET_INDICATORS_PACKAGE_REPORT.md).

### A — Weitere Analysen, Dokumente und Berichte

Der bestehende Plan für `auditcore_statistics`, `auditcore_sampling`,
`auditcore_risk`, `auditcore_privacy`, `auditcore_documents` und
`auditcore_procurement` bleibt relevant, wird aber mit vollständigen Quellen
ergänzt: Flowstat, Designer/Portal-Flowstat-Kopien, Statistik, auswertungjkb,
Riskanalysis, Regulierung, Auditdatabase und OSINT.

- `flowstat/backend/app/services/analysis_core_service.py:run_benford` und
  `sampling_service.py:run_mus_standard` werden von den API-Routen tatsächlich
  aufgerufen. NumPy/Pandas/SciPy sind beobachtete Abhängigkeiten. Designer und
  Portal enthalten namensgleiche eingebettete Module; `run_benford` ist dort
  AST-identisch, gegenüber eigenständigem Flowstat aber verschieden. Das ist
  Varianten-/Kopienbeleg, keine Bestätigung identischer fachlicher Ergebnisse.
- `Statistik/analyse.py` mit `run_sektion_01a_descriptive_stats`,
  `run_sektion_02_grundzahlen` und `analyse_modules/base.py:AnalysisSection`
  ergänzt den Bestand. Excelimport, Diagrammaufbau und Berichtsausgabe von den
  eigentlichen Kennzahlen trennen. Revisions-/Versionsanalysen bleiben ein
  benanntes Prüfprofil, keine unspezifische Analysebibliothek.
- Auditdatabase besitzt bereits `packages/docformatter` und `packages/humanizer`.
  `docformatter.word.converter:EFREConverter` und
  `docformatter.excel.analyzer:ExcelAnalyzer` zuerst gegen QCHESS_PRINT
  `EFREConverter`/`ExcelFormatter` abgleichen. Bestehende Paketverträge nutzen,
  keine gleichzeitige zweite Implementierung unter neuem Namen anlegen.
- PDF-Editor, Seminar-Beleggeneratoren, Flowinvoice und Portal liefern
  zusätzliche Dokument-/Renderer-Kandidaten. Unterrichtsszenarien und
  EFRE-/Rechtsregeln bleiben versionierte Profile; eine Portal-Rechnung ist
  nicht automatisch das bereits veröffentlichte Flowinvoice-Demoprofil.

### T — Werkzeuge und technische Dienste

- `graphify-kira`: bestehender Consolidator-Provider; `KiraPublisher`, Extraktor
  und Konfiguration weiterverwenden. Keine fachliche Bibliothek daraus machen.
- `qchess-src`: bestehendes `legacy_office_quality` mit CLI und VBA-/C#-/Office-
  Analyse. Als Quality-Adapter/Plugin integrieren; nicht mit Fachberechnung
  vermischen. Bei späteren VBA-Änderungen bleibt die vorgeschriebene vollständige
  FlowAudit-Prüfung zusätzlich verbindlich.
- `flowaudit` enthält `module_converter` mit `RepoAnalyzerService`,
  `FileParserService`, `GitService`, `GapAnalyzer` und Pluginmanifesten:
  Kandidaten für Consolidator-/AppRefactor-Adapter. API, DB und LLM-Ausführung
  bleiben getrennt; kein unkontrollierter Universalagent.
- `system-migrate:InventoryRunner`, Cockpit, NUC-Admin, Spoke-Agent und Flow-Agent
  liefern Betriebs-/Inventur-/Deployment-Integrationen. Bestehende
  Authentifizierung, Hostrechte, Secretgrenzen und Audit-Trails erhalten.
- AI-/LLM-Router, Reranker-, Whisper-, Vision- und eGPU-Dienste bleiben eigene
  technische Dienste. Vorhandene Clients/Contracts können separat konsumiert
  oder als Provider angebunden werden; GPU-/Modellbetrieb gehört nicht in
  eine obligatorische auditcore-Domain-Runtime.
- Frontends, Swift-/Rust-Clients, Präsentationen und Landingpages bleiben ihre
  Projekte. Designsystem-/TypeScript-Wiederverwendung wäre ein eigener
  sprachspezifischer Vertrag und wird nicht als Python-Bibliothek behauptet.

## Vollständige Repository-Zuordnung

Jede der 71 aktuellen Repositoryidentitäten erscheint genau einmal.
Kategorien: **A** Anwendung mit potenziellem Fachkern, **H** Quellen/Harvester,
**B** vorhandene Bibliothek, **T** technischer Dienst/Werkzeug, **V** Office/VBA,
**U** Oberfläche/Medien/Präsentation, **P** Plattform/Policy, **D** nur
Dokumentation, **E** tatsächlich leer. Kombinationen bezeichnen mehrere Rollen.
Ein Pfad ist Quellenbeleg für die Einordnung, keine vollständige Codeabnahme.

| Repository / aktuelle Revision | Kategorie | Konkreter Quellenbeleg | Vorgeschlagene Behandlung |
|---|---|---|---|
| [3dprint / 0e05fe1c6192](https://github.com/janpow77/3dprint/tree/0e05fe1c61927f9c05c719da7eb9b9634561ec49) | U | `led-filter-designer/package.json` | 3D-Webanwendung behalten; kein Python-Fachkern belegt |
| [ai-router / 426cd78e86df](https://github.com/janpow77/ai-router/tree/426cd78e86df9f822452af035b8d58a19f7aa820) | T | `src/llm_router; egpu-manager/clients/python` | Routerdienst/Clients behalten; Providerabgleich mit llm-router und eGPU |
| [audit-portal / d8eefa426826](https://github.com/janpow77/audit-portal/tree/d8eefa426826bdecb67036774f3128ae05e7d0d0) | A/H | `backend/app/modules/flowstat; services/generator; services/fraud_detection` | Statistik/Sampling, Dokumente, Screening; Varianten statt Kopien harmonisieren |
| [audit_designer / 030a71e083ef](https://github.com/janpow77/audit_designer/tree/030a71e083ef0feddc14545b095a4945bc0bbd7a) | A/H/T | `backend/app/modules/vp_ai/harvester; core/shared/research/register` | H1–H3 und Analysekerne priorisieren; Workflows/KI/DB bleiben Anwendung |
| [auditcore / e0279d23a42f](https://github.com/janpow77/auditcore/tree/e0279d23a42fdf392f6d33929cb97d0316ecc2d6) | P/B | `packages/; src/auditcore/tools` | Plattform und drei vorhandene Fachdistributionen weiterpflegen |
| [auditdatabase / bba911e918e1](https://github.com/janpow77/auditdatabase/tree/bba911e918e102426d4ca2f88fd377fe8ca585e4) | A/H/B | `backend/app/harvester; packages/docformatter; packages/humanizer` | H1 plus vorhandene Dokumentpakete wiederverwenden |
| `auditinvoice` / `UNKNOWN` (leer) | E | `GitHub isEmpty=true; kein Default-Branch` | Kein Codekandidat; nicht als bestehender Invoice-Consumer zählen |
| [Ausgabenliste / 9b9eda8f6367](https://github.com/janpow77/Ausgabenliste/tree/9b9eda8f6367e55c9380e56f0eb86afb79366075) | V | `funktionen:Aggregier_Belege` | Extensionloser VBA-Bestand; fachliche Aggregation charakterisieren, Office-Adapter behalten |
| [auswertungjkb / 3e250425bac5](https://github.com/janpow77/auswertungjkb/tree/3e250425bac59a64da9f6d1c9dde966665d7a65e) | A | `audit_statistik.py; audit_abweichungsanalyse.py; audit_excel_report.py` | Analyse-/Reportingprofile abgrenzen; abweichende Formatregeln erhalten |
| [Beleglisten / f21211a86b87](https://github.com/janpow77/Beleglisten/tree/f21211a86b87b339faba88bd2826ab08c493da50) | V | `mo_Print_all_files_in_folder.bas; Dateien_modifizieren.bas` | Office-Datei-/Druckautomatisierung behalten; Dokumentadapter nur bei echtem Vertrag |
| [Blendertool / 34c79f69ef49](https://github.com/janpow77/Blendertool/tree/34c79f69ef49812f753efe2be9a1be29158fa9c1) | T | `geometry_utils.py; operators.py; pyproject.toml` | Blender-Plugin behalten; isolierbare Geometrie erst bei Consumerbeleg |
| [Checkboxes / 28a393379b76](https://github.com/janpow77/Checkboxes/tree/28a393379b761390c9a2b5b40b6789a1778b6394) | V | `code:ClearCheckBoxes` | Kleines Office-Makro; kein neues Python-Paket |
| [cockpit / 2dd001fc041a](https://github.com/janpow77/cockpit/tree/2dd001fc041a69c25f515833f215c23a099a4be5) | T | `src/cockpit/main.py; models.py` | Betriebs-/Inventuranbindung als Provider, Host-/Secretrechte bewahren |
| [Drucknachweise / 58e6426e1640](https://github.com/janpow77/Drucknachweise/tree/58e6426e16400c8913347d85ba1f183bd49d3355) | D | `README.md` | Kein implementierter Paketkern im aktuellen Tree |
| [e-invoice-preparer / b3d64459c4bf](https://github.com/janpow77/e-invoice-preparer/tree/b3d64459c4bfa3a7e45799205bbf948ed2219133) | U | `src; package.json` | Frontend behalten; Rechnungs-Datenvertrag prüfen, kein belegter Pythonkern |
| [EGPU_EVO-X2_Manager / 722788ded5f7](https://github.com/janpow77/EGPU_EVO-X2_Manager/tree/722788ded5f70178d52ea8193da207f7d7b29a56) | T | `crates; clients/python/egpu_llm_client.py` | Rust-Dienst und Pythonclient getrennt betreiben; keine Pflichtabhängigkeit |
| [evo-x2-setup / acfc8b28965a](https://github.com/janpow77/evo-x2-setup/tree/acfc8b28965ad9241015fd749aa7d80a3a5298ca) | T | `betrieb/; setup/config/*.service` | Setup-/Betriebsskripte als Deployer-Referenz, nicht Fachbibliothek |
| [flow-agent / 864b2a7d5822](https://github.com/janpow77/flow-agent/tree/864b2a7d582269f3e6f45e1d3f6eca22c50674c1) | T/B | `packages/contracts; packages/client; apps/control-plane-api` | Vorhandene Client-/Vertragspakete nutzen; Agent/Betriebsrechte getrennt |
| [flowaudit / d8107f6b4287](https://github.com/janpow77/flowaudit/tree/d8107f6b4287228974bc3b0f405bdd95182a66d5) | A/T | `backend/flowaudit/modules/module_converter; services/ml_service.py` | Quality/Consolidator/AppRefactor-Adapter und benannte Analyseprofile |
| [flowaudit-landingpage / d7e5f2768b4d](https://github.com/janpow77/flowaudit-landingpage/tree/d7e5f2768b4d1494352d95605e8bffd7e4903741) | U | `react-app; assets` | Webauftritt behalten; kein Domainpaket belegt |
| [flowaudit_testdatengenerator_docker / 5987ab7731ea](https://github.com/janpow77/flowaudit_testdatengenerator_docker/tree/5987ab7731eabfc998b639bcedebeee4ac5c6349) | D/T | `docs/claude.md; docs/startup.md` | Betriebsdokumentation; keine zweite Generatorimplementierung |
| [flowaudit_testdatengenerator_frontend / 05bc5ac560df](https://github.com/janpow77/flowaudit_testdatengenerator_frontend/tree/05bc5ac560dfff3bc7181323240745215492d09a) | A | `backend/generator.py; backend/main.py` | Bestehendes auditcore_dummygenerator konsumieren; echte Appmigration noch offen |
| [flowinvoice / fb2d18568d2e](https://github.com/janpow77/flowinvoice/tree/fb2d18568d2eaf64574d131ceae51a936b9aac02) | A/H | `docs/demo_data/generate_demo_invoices.py; backend/app/services/generator` | Vorhandenes Invoicepaket nutzen; Dokument-/Rechercheadapter separat prüfen |
| [flowlib / aca2dc6aad25](https://github.com/janpow77/flowlib/tree/aca2dc6aad25aea0720312dbcc6da00b0bcba330) | B | `python/flowlib; typescript; vba` | Bestehende Bibliothek nutzen; Reporting extrahiert, HTTP/Auth-Clients getrennt |
| [flownavigator / 9dff858d3772](https://github.com/janpow77/flownavigator/tree/9dff858d3772e59533886dfbae70c672d574a1d4) | A | `apps/backend/app/core/module_manager.py; models/audit_case.py` | Anwendungs-/Modulverträge prüfen; kein pauschaler Workflow-Kern ohne Consumer |
| [flowpiano / 07ed41736f36](https://github.com/janpow77/flowpiano/tree/07ed41736f36d4e7a8aaaaa54cef6ff60a278365) | U | `Sources; web; project.yml` | Swift/Web-Musikanwendung behalten; außerhalb Auditdomain |
| [flowsearch / 10cb2a3ead38](https://github.com/janpow77/flowsearch/tree/10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4) | A/H | `backend/app/services/eu_beneficiary_harvester_v2.py; api_clients` | H2/H3 priorisieren; Rechercheorchestrierung und DB bleiben App |
| [flowstat / d665ac221f50](https://github.com/janpow77/flowstat/tree/d665ac221f50ba1f465b7337bdd4aa218d78ec8a) | A | `backend/app/services/analysis_core_service.py; sampling_service.py` | Statistik/Sampling extrahieren; vorhandener Test-Parsefehler bleibt PARTIAL |
| [flowvoice / 28f5623ab30f](https://github.com/janpow77/flowvoice/tree/28f5623ab30ff392531fd870013961e1e1529013) | T/A | `backend/app/audio; inference; core/ai_router.py` | Sprachdienst/Audioadapter behalten; separat charakterisierbare Audiohilfen prüfen |
| [flowworkshop / a05bb2143bd9](https://github.com/janpow77/flowworkshop/tree/a05bb2143bd96d5e981f9462f05b965e1658be36) | A/H | `auditworkshop/backend/services/beneficiary_harvester.py; state_aid_service.py` | H2/H3 und Entity-Matching priorisieren; Unterrichts-/Reviewworkflow bleibt App |
| [Formular_Callcenter / 9380b10478ce](https://github.com/janpow77/Formular_Callcenter/tree/9380b10478ce0de57bed5a2f4b834a8a486a89ec) | V | `m_Main.bas; csvimportieren.bas; m_Email.bas` | Office-Anwendung behalten; Import-/Dokumentverträge erst charakterisieren |
| [graphify-kira / 1714914ba37c](https://github.com/janpow77/graphify-kira/tree/1714914ba37cdd7c47f2febc3c548166563b5d41) | T/B | `src/graphify_kira/kira_publisher.py; extractor.py` | Bestehender Consolidator-Provider; keine neue Fachdistribution nötig |
| [ki-pilotprogramm / dac4b137bfb4](https://github.com/janpow77/ki-pilotprogramm/tree/dac4b137bfb443d36bdf3f4c8350f9f3dabb85bc) | U | `src; package.json` | Frontend/Pilotanwendung behalten; kein Python-Fachkern belegt |
| [kino / 3e73a7194313](https://github.com/janpow77/kino/tree/3e73a71943131ac75171605facf795fc0476f893) | A/U | `backend/app/models.py; frontend` | Kino-/Abstimmungsanwendung behalten; derzeit kein Audit-Domainzuschnitt |
| [kiraclaw / 43cd98e90f03](https://github.com/janpow77/kiraclaw/tree/43cd98e90f03f124701ee53541b5f358c5e7eeae) | T/A | `server/ai_client.py; realtime.py; market_client.py` | KI-Orchestrierungsdienst und Clients als technische Adapter behandeln |
| [krypto / 34d601726227](https://github.com/janpow77/krypto/tree/34d601726227f913548a118e144de5519eee0f3f) | A/H | `backend/app/adapters; services/indicators/base.py` | H5-Marktdaten und benannter Indikatorkern; Portfolioentscheidungen getrennt |
| [llm-rag-audit-presentation / c59fe09e05f6](https://github.com/janpow77/llm-rag-audit-presentation/tree/c59fe09e05f6d44bdc7ef1a92280f8deebe5ca75) | U | `erstelle_llm_praesentation.py; llm-rag-animation` | Präsentationsprojekt; kein Paketzwang, Parsefehler update_app.py offen |
| [llm-router / 2dade44643df](https://github.com/janpow77/llm-router/tree/2dade44643df50523c5ec23b41c9cfd803013b2f) | T | `src/llm_router; pyproject.toml` | Technischer Routerdienst; Beziehung zu ai-router zuerst revisionsgebunden klären |
| [nuc-admin / 751df0edaf5d](https://github.com/janpow77/nuc-admin/tree/751df0edaf5d8a78e22d2d187056a2b9c3a5b651) | T | `backend/app/core/audit.py; config.yaml` | Betriebs-/Inventur-/Deploymentprovider; Auth und Audit beibehalten |
| [openclaw / 55ada5d38a60](https://github.com/janpow77/openclaw/tree/55ada5d38a60a82f566f8fd25ef2a70a96976d44) | T/D | `deploy/docker-compose.yml; skills/*/SKILL.md` | Deployment-/Agentintegration; keine eigenständige Fachlogik belegt |
| [osint / d361ddb9a502](https://github.com/janpow77/osint/tree/d361ddb9a502bb899065e799d50104f306cfdc89) | A/H | `ortsdienst/dienst.py; werkzeuge/bundeslaender_holen.py; nachrichten/dienst.py` | H4-Geo und Quellenadapter; Portal/Auth/Scheduler getrennt |
| [pdf-editor / ce3441312975](https://github.com/janpow77/pdf-editor/tree/ce34413129751dfd72fac6cefa55b02718bff27b) | A | `backend/app; frontend` | Dokumentbearbeitung als App; reine PDFoperationen gezielt prüfen |
| [python_diagramm / 9b68539303f7](https://github.com/janpow77/python_diagramm/tree/9b68539303f71488f4b4b7a3be79f22e0a0e0aad) | D | `README.md` | Kein implementierter Diagrammkern im aktuellen Tree |
| [qaaudit / c78be5c86454](https://github.com/janpow77/qaaudit/tree/c78be5c86454d457e5c66d0c65b5117a8528d462) | A | `backend/app/models/assessment.py; models/cycle.py` | Bewertungs-/Maßnahmenmodelle nur mit fachlichem Vertrag extrahieren |
| [QCHESS / d794ad4dcfe9](https://github.com/janpow77/QCHESS/tree/d794ad4dcfe9b402da6ef4132012b1eb77e7f836) | V/T | `FlowCodeInspector; Mo_VBA_Format.bas; m_Tabellen.bas` | Legacy Office/C#; Qualityadapter statt neues Allzweckpaket |
| [qchess-src / 902ed69dde67](https://github.com/janpow77/qchess-src/tree/902ed69dde6720e557af5fe372054577d7fe6167) | T/B | `analyzer/legacy_office_quality; pyproject.toml` | Vorhandenes Analysepaket als Qualityplugin weiterverwenden |
| [QCHESS_Bericht / 59e029384cdf](https://github.com/janpow77/QCHESS_Bericht/tree/59e029384cdf93e98cac9370f2ffd85ef72e06b6) | V | `Mo_Userform_Bericht.bas; m_save_as_doc.bas` | Office-Berichtsworkflow behalten; Vorlagen/Exportcharakterisierung nötig |
| [QCHESS_PRINT / 51f7883dff4b](https://github.com/janpow77/QCHESS_PRINT/tree/51f7883dff4b7816e010dad80764081c3262edc2) | A/B | `Auditdatabase/backend/efre_converter.py; excel_formatter.py` | Mit vorhandenem docformatter abgleichen; keine blinde Doppelbibliothek |
| [rechnungslegung-seminar / 31fc51d52ac9](https://github.com/janpow77/rechnungslegung-seminar/tree/31fc51d52ac978c5d960e5c8df61d0739b8f4e11) | A | `app/backend/app/generator/beleg_pdf_generator.py; exports` | Beleg-/Aufgabenrenderer als Profile/Adapter; Lehraufgaben bleiben App |
| [regulierung / a5d48ea4b90a](https://github.com/janpow77/regulierung/tree/a5d48ea4b90a410210ec25e707781ef9e21ad743) | A/H | `services/dsfa; mandant_dsgvo_service.py; external_apis; calculator.py` | Datenschutzregister/DSFA-Erstellung priorisieren; H4 und Preisanalysen getrennt |
| [Report_new / e78cf50f6ede](https://github.com/janpow77/Report_new/tree/e78cf50f6ede1ac36a39f6168b4ec9635cde8910) | V | `2025-05-28_m_Bericht_formatieren.txt; *.frx` | 21 Office-Exportdateien inventarisieren; kein leerer Bestand |
| [reranker-service / 5ca0e67a1c41](https://github.com/janpow77/reranker-service/tree/5ca0e67a1c41df2fdfeb30d890ded6f825aa0f18) | T | `src/reranker_service/model.py; compose.gpu.yaml` | Modellservice behalten; expliziter Retrievalprovider |
| [riskanalysis / b5c523bf7eaa](https://github.com/janpow77/riskanalysis/tree/b5c523bf7eaa326153778d9751f176f03d4d56ed) | A/H | `backend/app/services/indicator_calculator.py; pipeline; sanctions_screening.py` | Risiko-/Privacy-/Screeningprofile; MDBimport und fachliche Gewichte getrennt |
| [router / bd2c2c2ba47f](https://github.com/janpow77/router/tree/bd2c2c2ba47f420fe66f317d5c39a4501d9d8d3b) | T | `Cargo.toml; src; configs` | Rust-/Netzwerkbetrieb behalten; Deployeradapter unter Rechteprüfung |
| [router-tray / ace87d030a6a](https://github.com/janpow77/router-tray/tree/ace87d030a6ab61b43e3c4c277a545f479a73333) | T/U | `tray/state.py; pyproject.toml` | Desktop-Bedienung bleibt eigener Client |
| [SAP_Auswertung / 48ea66ada4cf](https://github.com/janpow77/SAP_Auswertung/tree/48ea66ada4cf460a4a53f2775bf0c41d43a48bd1) | D | `README.md` | Kein implementierter SAP-Analysekern im aktuellen Tree |
| [spoke-agent / a133aeeb0637](https://github.com/janpow77/spoke-agent/tree/a133aeeb0637f46dae0b9b27630e46d440aa3ed9) | T | `src/spoke_agent/docker_ops.py; registration.py` | Hostagent/Deploymentintegration; keine Domain-Runtime |
| [spoke-stack / a98008feea48](https://github.com/janpow77/spoke-stack/tree/a98008feea482526460d89bddccd060dadb28dfe) | T | `compose.yaml; compose.amd.yaml; compose.gpu.yaml` | Betriebsmanifestfamilie als Deployerreferenz |
| [spoke-widget / a179562c67fd](https://github.com/janpow77/spoke-widget/tree/a179562c67fdbcd285eba8b428de7e592f759693) | T/U | `src-tauri; ui; Cargo.toml` | Rust/Desktopclient behalten; Protokollvertrag mit Spoke prüfen |
| [Statistik / 15aeef34ffbf](https://github.com/janpow77/Statistik/tree/15aeef34ffbf6b1f05b237af4f75a0b5176d5525) | A | `analyse.py; analyse_modules/base.py; bericht.py` | Benannte Statistik-/Versionsanalyseprofile und Reportingadapter |
| [Statistik_Vorhabenpruefung / 13d104c22bd2](https://github.com/janpow77/Statistik_Vorhabenpruefung/tree/13d104c22bd238b053ec741a2ba5b3cf0c7b4f4d) | V/A | `Auswertung_20251113_090353__m_Auswerten.bas; weitere Module` | VBA-Fachberechnung zuerst vollständiges Projekt charakterisieren |
| [system-migrate / 2f9afa4572f6](https://github.com/janpow77/system-migrate/tree/2f9afa4572f66b2ea984c901e652eee6b8b5a633) | T | `app/inventory/runner.py:InventoryRunner; bootstrap` | Inventur-/Migrationsadapter; Systemzustand/Privilegien getrennt |
| [VBA_Excel_tools / a11cede1097d](https://github.com/janpow77/VBA_Excel_tools/tree/a11cede1097d34a5895b5684abece8502757314f) | D | `README.md` | Kein implementierter Werkzeugkern im aktuellen Tree |
| [versteigerung / e4ad7af0eaee](https://github.com/janpow77/versteigerung/tree/e4ad7af0eaee0b151cc5e3358f95b961d7f3a448) | A/H | `backend/app/crawler/zvg_crawler.py; ingest/gutachten_ingest.py` | H5-Immobilienadapter; Bewertung/DB/OCR-Orchestrierung bleibt App |
| [verwaltung-app-framework / 15f5338f783f](https://github.com/janpow77/verwaltung-app-framework/tree/15f5338f783f2c7d5760a9bb299be06d27326be0) | P | `docs/pruefkatalog.md; framework/core/vvt.py` | Verbindliche Policyquelle, zusätzlich VVT-Vertrag prüfen; kein Ersatz der Quelle |
| [VideoArchivAssistent / 8dcc0ee94f17](https://github.com/janpow77/VideoArchivAssistent/tree/8dcc0ee94f174fb174c24e0f285b13a197a1a820) | A/T | `app/services/library_service.py; job_service.py` | Medien-/Jobdienst behalten; isolierte Metadatenparser nur bei belegtem Nutzen |
| [vision-service / 4c249036c5eb](https://github.com/janpow77/vision-service/tree/4c249036c5eb91b87f650c4e73239d6e195b39c7) | T | `src/vision_service/models/{chandra,donut,easyocr,tesseract}.py` | OCR-Modellbetrieb separat, Dokumentpaket nutzt Providervertrag |
| [wesenszug / a27c963b2062](https://github.com/janpow77/wesenszug/tree/a27c963b20623e45ce8228dfe3fa0fb9c2a081bb) | A | `backend/app/models/auth.py; core/rate_limit.py` | Eigenständige Anwendung; Schutz-/Einwilligungslogik nicht ungeprüft verallgemeinern |
| [whisper-service / a7c9612933d7](https://github.com/janpow77/whisper-service/tree/a7c9612933d71aad474225c5018f84b3595d1fef) | T | `src; pyproject.toml; compose.yaml` | Transkriptionsservice als Provider; keine Modellgewichte in Fachruntime |
| [wohnungsmonitor / 76571bfaa343](https://github.com/janpow77/wohnungsmonitor/tree/76571bfaa3435bfc6858b3cbaae8c4ea3969ef91) | A/H | `immobilien_export.py; bienici_export.py; umfeld.py` | H5-Portalparser und H4-Geo; Quellenprofile getrennt |
| [x_chat / 2ef4138ba140](https://github.com/janpow77/x_chat/tree/2ef4138ba14002ab4bd1401970336a53b8a2b29b) | A/T | `love-ai/api/app; middleware/rate_limit.py` | Chat-/KI-Anwendung behalten; Clients nur nach tatsächlichem Mehrfachbedarf |

## Umsetzungsfolge und verbleibende Nachweise

| Folge | Konkretes Ergebnis | Abschlusskriterium vor Consumer-Umstellung |
|---|---|---|
| Bereits vorhanden | Dummy, Invoice und Reporting weiterpflegen | Bestehende Wheel-/APT-/Characterization-Nachweise; reale Consumer-Migration separat |
| 1 | `auditcore_dataprotection`: eigenes Register erstellen und DSFA erstellen/berechnen/pflegen | Register-/DSFA-Vertrag, charakterisierte Bewertung, Fassungs-/Reviewübergänge, Export und sichere Consumer-Ports |
| 2 | `auditcore_harvest` mit einem Funding- und einem Legal-Quellenadapter | Gemeinsamer Ablauf, Originalfixtures, Cursor-/Teilfehler-/Snapshotsemantik, erster realer Consumer |
| 3 | `auditcore_legal_sources`: Dokumentvertrag plus ein DIP-/EUR-Lex-Adapter | Paging-/Fehler-/Provenienzfälle und injizierter Transport; keine App-DB im Paket |
| 4 | Statistik/Sampling und Entity-Matching | Getrennte Methodenprofile, echte Legacy-Vergleiche; fachliche Konflikte dokumentiert |
| 5 | Preis-/Geo-/Immobilienquellen und spezielle Analysekerne | Tatsächlicher Mehrfachnutzen, Daten-/Quellenrechte, Ressourcen-/Zeitlimits und benannte Consumer |
| Parallel | Bestehende Quality-/Inventur-/Deploymentwerkzeuge als Provider anbinden | Tatsächlicher vorhandener Vertrag, passende Rechte, keine neue Universalagent-Komponente |

Diese Reihenfolge priorisiert die ausdrücklich gewünschte Datenschutzfähigkeit
und schließt Harvester nicht aus. Sie legt keine endgültige Zahl neuer Pakete
fest. Kleine ausschließlich intern benötigte Helfer bleiben in ihrer Familie.
Der gemeinsame Harvest-Vertrag wird als `auditcore_harvest` anhand mindestens
zweier Quellenfamilien charakterisiert. Die ausdrücklich gewünschte gemeinsame
Nutzung und die belegten wiederkehrenden Abrufverträge begründen diese
technische Distribution; sie entsteht nicht allein aus einem Namensschema.

Offene Nachweise werden bei der jeweiligen Extraktion bearbeitet:

- Vollständige Characterization der neu vorgeschlagenen Familien:
  **NOT_EXECUTED** in dieser Inventur. Separat hat der DSFA-Berechnungskern
  inzwischen 19 Originaltests und 129 zusätzliche beobachtete Fälle mit exaktem
  Replay bestanden; seine vollständige Register-/Workflowintegration ist noch offen.
  Gelesene Tests oder APIs sind keine ausgeführten Tests; keine Aussage über die aktuelle Erreichbarkeit der Quellen.
- Genaue Abhängigkeitsclosure und Runtime-/Optionale-Extras pro neuem Paket:
  noch zu messen. Hier genannte Imports sind beobachtete Kandidaten, keine
  fertigen minimalen Requirements.
- Tatsächliche Installation der neuen Pakete in Consumer-Anwendungen:
  **NOT_EXECUTED**. Gleicher Code in Designer und Portal ist ohne zusätzlichen
  Beleg keine bereits konsolidierte Bibliotheksabhängigkeit.
- Unbekannte Lizenzmetadaten werden nicht zur pauschalen Ablehnung lokaler
  autorisierter Arbeit. Sie begründen aber keine öffentliche MIT-Umlizenzierung;
  Quellcode-/Vorlagen-/Datenrechte bleiben getrennt. Dieses Dokument enthält
  nur Metadaten, Pfade und Symbolnamen, keine privaten Quelltextkopien.
- VBA, Rust, C#, TypeScript, Swift und extensionlose/als Text exportierte
  Module benötigen passende Inventuradapter. Bei späteren VBA-Änderungen sind
  vollständige Projektprüfung über FlowAudit und Office-Ausführung getrennt
  auszuweisen; hier wurde kein VBA-Code geändert oder geprüft.
- Die globale KIRA-/Graphify-Abdeckung wird durch diesen Bericht nicht
  nachträglich vollständig. GitHub-Metadaten sind aktuell bestätigt; bisherige
  Symbol-/Graphinventare und tatsächliche neue Ausführungen bleiben getrennt.

**Abdeckungsprüfung:** 71 aktuelle Repositoryidentitäten, 71 Tabellenzeilen,
keine fehlende oder doppelte Zuordnung. Das ist eine vollständige
Repository-Zuordnung innerhalb des abgefragten Owner-Bestands, keine Behauptung,
jede Zeile aller 71 Projekte fachlich geprüft oder jede mögliche Bibliothek
bereits abschließend identifiziert zu haben.
