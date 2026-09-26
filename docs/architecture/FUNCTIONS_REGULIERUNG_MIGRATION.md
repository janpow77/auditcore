# Regulierung: Funktionsübersicht und nächster Refactoring-/Debian-Schritt

Codequelle: `janpow77/regulierung`, Commit
[`a5d48ea4b90a410210ec25e707781ef9e21ad743`](https://github.com/janpow77/regulierung/tree/a5d48ea4b90a410210ec25e707781ef9e21ad743).
Analyse: 22.09.2026. Auftrag ist die Vorbereitung des **nächsten** Umsetzungsschritts;
Anwendungscode, Datenbank, Deployment und Produktionsserver wurden nicht verändert.

> **Stand 26.09.2026:** Die hier als offen beschriebene Consumer-Umstellung ist
> umgesetzt (regulierung PR #9): Datenschutz, Preisanalyse/-quellen, Harvest,
> Reporting, common und auth kommen als hashgebundene Release-Wheels v0.4.0;
> Parität alt ↔ Bibliothek ist getestet, das native Paket ist gebaut und im
> QEMU-Lebenszyklus geprüft. Nachweise: `docs/validation/regulierung-apt/`.
> Die Inventur unten beschreibt den Ausgangsstand vom 22.09.2026.

## Aussage und Umfang

Regulierung bleibt eine eigene Anwendung und soll echte versionierte Libraries aus
auditcore konsumieren. Heute stehen dort nur Dummy-, Rechnungs- und Reportingpaket
als implementierte Fachpakete zur Verfügung; aus geplanten Paketnamen folgt keine
Installierbarkeit. Insbesondere Datenschutz-, Preis-, Harvest- und Geo-Kerne müssen
vor der entsprechenden Consumer-Migration erst vollständig erstellt und geprüft werden.
Reporting 0.2 wurde implementiert, ist aber nicht mit einer bereits veröffentlichten
0.2-Auslieferung gleichzusetzen. Der Plattform-Release-/Inventurbericht bleibt dafür
maßgeblich.

Statisch erfasst: alle 56 Python-Dateien unter `backend/app/api` und 112 unter
`backend/app/services`, einschließlich `__init__.py`, mit erfolgreichem AST-Einlesen.
Vertieft gelesen: Rechen-/Cluster-/DSFA-/Harvest-/Vollzugs-/Paketdienste,
Routerregistrierung, Dockerfiles, Requirements sowie Behörden-/Updateranleitung aus
versionierten Git-Blobs. Kein Funktions-, Integrations-, Installations- oder
Produktionstest wurde für diese Übersicht ausgeführt (**NOT_EXECUTED**).
Keine privaten Quelltextauszüge oder fachlichen Daten werden veröffentlicht.
Die vorhandene MIT-Freigabe zweier Generatorquellen deckt regulierung nicht ab.

## Funktionsübersicht und Extraktionsgrenzen

Backendpfade in dieser Tabelle relativ zu `backend/app/`.

| Funktionsgruppe | Konkrete vorhandene Belege | Bibliotheksziel und verbleibende Anwendung |
|---|---|---|
| Wasser-/Nahwärmeberechnung | `services/calculator.py`: `calculate_wasser`, `calculate_nahwaerme`, Staffelberechnung, `calculate_delta`, `determine_compliance`; `api/calculate_routes.py` | `auditcore_price_analysis`: Decimal-, Einheiten-, Rundungs- und Preisbestandteilvertrag charakterisieren. API/DB/Anbieterberechtigungen bleiben Anwendung. Fehlend ist nicht null. |
| Vergleichsgruppen / Rankings | `clustering.py:bestimme_cluster`, `ClusterZuordnung`, `vergleichsgruppe_key`; `cluster_comparison.py:build_cluster_statistics_map`, `apply_cluster_benchmarks`; `preisauswahl.py` | `auditcore_price_analysis`; Raumstruktur **und** privatrechtliches Entgelt/öffentlich-rechtliche Gebühr bestimmen Gruppe. Mindestgruppengröße und nicht zuordenbare Gruppe erhalten, nicht global zusammenrechnen. |
| Preiswarnungen und Indizes | `flagging.py:check_multi_index_anomaly`, `validate_preisgleitklausel`, `generate_and_persist_alerts`; `external_indices.py`, `genesis_sync.py` | Pure Preis-/Indexregeln im Preisanalysepaket, Generieren/Speichern von Alerts bleibt App. Indexrevision, Quartal, Alter und Methodenprofil mitführen; Priorisierungshinweis ist keine Rechtsentscheidung. |
| Anbieter / Tarife / Dokumentbelege | `api/provider_routes.py`, `api/admin/providers.py`, `prices.py`, `registry.py`, `documents.py`; Modelle Wasser/Nahwärme/Preisvarianten/SourceDocument | Fachmodelle/Validatoren als Kandidaten; Mandanten-/Stammdatenverwaltung und ORM bleiben App. Historische Preisstände und Belegbeziehung erhalten. |
| Preiserhebung | `services/harvesting/pipeline.py:run_harvesting`, `extract_multiple_variants`; `link_discovery.py`, `plausibility.py`, `validators.py`, `quellenklassen.py`, `review_queue.py`, `scheduler.py`, `llm_extractor.py` | Technischer Kern `auditcore_harvest`, fachliche Quellen-/Tarifadapter `auditcore_price_sources`. CPU/OCR, Quellenhash, No-change, methodenspezifische Confidence und Freigabequeue getrennt; keine automatische Freigabelogik entfernen. |
| Externe Quellen | `external_apis/base.py:BaseConnector`, `HarvestResult`, `get_connector`; Bundesbank, Destatis GENESIS, EIA Brent, EU Oil Bulletin, Tankerkönig, MTSK, Overpass, Geoportal Hessen, Handelsregister, VID-Secondary | Adapter nach Preis/Funding/Registry/Geo-Vertrag auf gemeinsamem Harvest-Kern. Nicht jeder Connector gehört ins Preis-Paket. Keine Zugangsdaten oder private Lieferdaten als Fixture übernehmen. |
| Verarbeitungsverzeichnis | `mandant_dsgvo_service.py`: `speichere_entwurf`, `freigeben`, `taetigkeiten_mit_kennung`, `baue_verarbeitungsverzeichnis_workbook`; Admin `mandant_dsgvo.py` | `auditcore_dataprotection`: erstellen, bearbeiten, Tätigkeitsschlüssel, Versionen, Status und Export; kein bloßer Importer. DB-/Benutzer-/Mandantadapter verbleiben. |
| DSFA vollständig | `dsfa/bewertung.py`: `werte_schwellwert_aus`, `werte_risiko_aus`, `erstelle_vorschlag`; `katalog.py`, `verwaltung.py`, `export.py`; Admin `dsfa.py` | `auditcore_dataprotection`: Schwellenprüfung, Brutto-/Nettorisiko, Maßnahmen, begründeter Vorschlag und versionierte Profile sowie Anlage/Bearbeitung/Review. Aktuelle Methoden zunächst exakt charakterisieren; keine rechtliche Richtigkeit aus Altcode ableiten. |
| DSFA-Freigabe und Neubewertung | `dsfa/verwaltung.py`: `pruefe_regime`, `entscheide`, `dsb_stellungnahme`, `dsb_folgerung`, `freigeben`, `pruefe_auf_aenderungen`, `neubewertung`; MandantDsfa/MandantDsgvoModelle | Mandantentrennung, Vier-Augen, DSB-Beteiligung, gesperrte Fassungen und Neubewertung bei VVT-Änderung müssen auch nach Extraktion wirksam bleiben. Ein reiner Risikorechner ersetzt diese Anwendungskontrollen nicht. |
| Kraftstoff-Marktbeobachtung | `kraftstoff/markt/cluster.py`, `korrelation.py`, `marktfenster.py`, `preisindex.py`, `auffaelligkeit_meldungen.py`; API `kpang/markt.py` | Reine Markt-/Korrelationskerne ggf. Preisanalyse/Statistik; Marktbeobachtung ist ausdrücklich vom Vollzugsmodul getrennt. Keine automatische Verdachts-/Verfahrensübernahme aus Marktindikatoren. |
| Kraftstoffimport / Datenqualität | `mtsk_import/detection.py`, `mtsk_xml.py`, `dry_run.py`, `transform.py`, `plausibilitaet.py`, `produktivimport.py`; Importprofile/Feldreferenz/Quarantäne | Dokument-/Quellenadapter möglich; Originaldaten, Einheiten, Quarantäne, Dry-run und kontrollierte Übernahme erhalten. Produktivdaten dürfen nicht still als Testdaten weitergegeben werden. |
| KPAnG-Prüfung / Tatbildung | `kraftstoff/vollzug/verstosslogik.py:pruefe_meldungen`, `bilde_taten`, `PruefParameter`; `tatbildung.py`, `classifier.py`, `kpang_fenster.py`, `preis_einheit.py`, `datenluecken.py`, `pruefung_je_tattag.py` | Zunächst in regulierung belassen bzw. eigener fachlich begründeter Kern erst nach Review. **Nicht** pauschal nach `auditcore_risk`/`procurement` verschieben. Auslegungs-/Aufgriffsprofile, Stichtage, Ausgangspreis-Gegenprobe, Quelleneinheit, unklare Fälle, Tages-/Zeitgrenzen sind versionierte fachliche Verträge. |
| KPAnG-Verfahren / Vollzug | `bearbeitungsstatus.py`, `prozessstand.py`, `verfahrens_checkliste.py`, `verfahrens_sicherheit.py`, `kosten.py`, `tateinheit_zumessung.py`, `zustellungsempfaenger.py`; APIs Verfahren/Vollzug/Zweitkontrolle | Verfahrensübergänge, Anhörung, Entscheidung, Zeichnung, Zustellung, Zweitkontrolle und Rechte verbleiben im Fachverfahren. Keine Optimierung darf Aktenstandbindung, Vier-Augen oder Auditpflicht umgehen. |
| Regelwerk / Fachadministration | `regelwerk_parameter.py`, `rulebook_service.py`, `regelwerk_report.py`; Admin Rulebook; API `kpang/rulebook.py`; ParameterHistory | Rückwirkungs-/Wirksamkeitsgrenzen und freigegebene Parameterstände schützen. Rechtsauslegung oder Schwellenänderung benötigt HUMAN_DECISION_REQUIRED; Methodendifferenzen nicht automatisch harmonisieren. |
| Beweismittel und Dokumenterzeugung | `beweismittel_generator.py`, `dokument_erzeugung.py`, `anhoerung_serienbrief.py`, `anlage_taten.py`, `gesamtakte_pdf.py`, `aktenexport.py`, `schriftstueck_entwurf.py`, Vorlagenmodule | Reine Dokument-/Renderingbausteine → `auditcore_documents`/`auditcore_reporting`. Verfahrenssicherheit, Beweismittelsignaturen, Zeichnung und konkrete Formulare bleiben kontrollierte Consumerlogik. |
| Datenpakete Wasser/Nahwärme | `pakete/archiv.py`, `daten.py`, `excel.py`, `werkzeuge.py`; API Admin `pakete.py` | Archiv-/Manifest-/Excel-Bausteine als Dokumentkandidaten. Belege, Größenlimit, keine Formeln, explizite Preisbestandteile, Zuordnung und andere freigebende Person beibehalten; Konflikte mit gleichem Tarifbeginn nicht überschreiben. |
| Signierte Programmupdates | `pakete/programm.py`, `update_transport.py`, `updater.py`, `einrichten.py`; Admin `programmupdates.py`; `deploy/updater/einrichten.py` | Deployment-Provider/-Verträge für auditcore prüfen; vorhandene Signatur-/Versions-/Architektur-/Revisionsprüfung nicht durch nacktes Entpacken oder `pip install -U` ersetzen. |
| Sicherheit / Betrieb / Mandanten | `core/auth/*`, `core/security.py`, `core/rate_limit.py`, `api/deps.py`, Mandantservices, Audit-/Access-Modelle, `betrieb.py`, `betrieb_backup.py`, Wartung, Schnittstellenkatalog | Bleibt Anwendung/Betriebsadapter. Auth JWT/OIDC, Rollen, Mandanten, Redis-Limits, Backup und manipulationsgeschützte Historien bei Integration erneut prüfen. |
| Frontend und Administration | `frontend/src/pages`: Wasser/Nahwärme, Cluster/Ranking/Anbieter, Karten, Fachadministration, Kraftstoffmarkt/Vollzug, VVT/DSFA, Signaturen/Updates, Profil/Hilfe | React-Anwendung bleibt regulierung; keine UI in die Python-Libraries verschieben. Tatsächliche API-Verträge sowie Lade-/Fehler-/Rechtezustände regressionsprüfen. |

## Heute vorhandene Auslieferung: Containerarchiv, kein natives App-DEB

`deploy/behoerde/README.md`, `install.sh` und `docker-compose.yml` liefern ein
offline verwendbares `hpp-behoerde-<VERSION>.tar.gz`. Images werden mit Docker
Load eingespielt; Docker Compose betreibt Backend, Frontend, PostgreSQL, Redis und
optional Caddy. Der separate Updater ist ein **systemd-Hostdienst für Compose**;
daraus folgt nicht, dass die Fachanwendung bereits als systemd-App oder `.deb`
vorliegt. `deploy/behoerde/update.sh` lehnt den alten unsignierten Updateweg ab.

Nachgewiesene technische Anforderungen:

- Backend: Python 3.12, Uvicorn/FastAPI; `backend/requirements.txt` pinnt direkte
  Python-Abhängigkeiten, aber noch keine vollständige Hash-Lockdatei aller transitiven
  Dependencies. Testabhängigkeiten stehen teils im Runtime-Requirementsfile.
- Frontend: Node 20 nur in der Buildstufe, `npm ci`/Build aus Lockfile;
  ausgelieferte `dist`-Dateien werden mit Nginx bedient. Das Muster ist für DEB
  wiederzuverwenden, Node gehört nicht auf den Zielserver.
- Datenbank: PostgreSQL 16 **mit PostGIS und TimescaleDB**, siehe
  `infra/postgres/Dockerfile`, `backend/alembic/versions/*` und Compose.
  Redis 7 für Cache/Rate-Limits. Ein normales SQLite-Demo-Setup ist kein Ersatz.
- Native Laufzeit: WeasyPrint benötigt Pango/Cairo/GLib/GDK-Pixbuf und MIME-Daten;
  OCR benötigt Tesseract einschließlich Deutsch und Poppler. PostgreSQL-16-
  Clientwerkzeuge `pg_dump`/`pg_restore` werden für Backup/Restore verwendet.
  Build-essential/libpq-dev/libffi-dev aus dem Dockerfile gehören nur soweit
  tatsächlich erforderlich in die Buildumgebung, nicht pauschal in Runtime-Depends.
- Persistenz: Datenbank-/Redis-/Uploads-Volumes, Konfiguration `.env`, Zertifikate,
  Signaturschlüssel-/Secretmount, Backup-Schlüssel; keine davon darf ein Paketupgrade
  oder normales Remove still löschen.
- `/api/health` gibt derzeit lediglich einen konstanten Status zurück.
  **Das ist kein Nachweis von DB-, Redis-, Schema- oder fachlicher Betriebsbereitschaft.**
  Bestehender Updater ergänzt eigene Revisions-/Auth-/Frontendprüfungen.

`pakete/ANLEITUNG.md` dokumentiert beim Updater Ed25519, Hashes, genaue
Dateiliste, Ausgangs-/Zielversion, Architektur, Datenbankrevision, Wartungssperre,
verschlüsselte Sicherung mit Restoreprobe und Rollback auf vorherige Images.
Nur als abwärtskompatibel geprüfte Migrationen werden akzeptiert; automatischer
produktiver Datenbankrestore und Infrastruktur-Hauptversionswechsel sind ausdrücklich
nicht implementiert. Diese Garantien sind Mindestverträge des neuen Deploymentpfads.

## Konkreter nächster Arbeitsablauf

| Schritt | Umsetzung / Artefakt | Nachweis vor Fortsetzung |
|---|---|---|
| 1. Ausgangsstand sichern | Separater regulierung-Branch/Worktree auf obigem SHA; Requirements, Migration-Heads, fachliche Profile, API-Snapshot, Konfigurationsschema und anonymisierte/synthetische Referenzfälle erfassen. Bestehendes auditcore-Framework für Inventur, Quality und MigrationPlan verwenden. | Unveränderter Baseline-Lauf mit tatsächlichen Resultaten; keine Altfehler als neue Migration maskieren. Aktuelle Quell-SHAs vor Beginn erneut vergleichen. |
| 2. Rechte und Geltung klären | Provenienz-/Lizenzprüfung für jeden extrahierten regulierung-Kern, DSFA-Katalog und Vorlagen/Daten. Ungeklärte Quellen bleiben privat. ApplicabilityContext und fachliche Reviewliste versionieren. | Öffentliche Extraktion erst mit konkreter Freigabe/kompatibler Lizenz; unabhängige private Charakterisierung darf fortfahren. |
| 3. Datenschutzpaket zuerst | `auditcore_dataprotection` mit VVT-/DSFA-Erstellung, Bearbeitung, Versionierung, Schwellwert-/Risiko-/Maßnahmenberechnung und Export bauen. Vorhandene lokale DSFA-Charakterisierung (19 Originaltests plus 129 beobachtete Fälle) als Teilbeleg nutzen, nicht als vollständigen Workflowtest. | Neue Unit-/Boundary-/Characterizationtests; fehlende/unklare Antworten und fachlich fragliche Alt-Ausgaben ausdrücklich reviewen; Regime-/Vier-Augen-/DSB-/Versionsfälle müssen abgedeckt sein. |
| 4. Preis-/Harvestpakete passend aufbauen | Reine Berechnung/Cluster/Indexlogik in `auditcore_price_analysis`, Connectorverträge in `auditcore_harvest`, Tarifadapter in `auditcore_price_sources`; Geo/Registry nur bei belegtem Bedarf ergänzen. | Preis-/Rundungs-/Staffel-/Gruppengrenzfälle und Quellenfixtures; alte und neue Ergebnisse vergleichbar. Kein Paket nur aus leeren Ports/Beispielcode. |
| 5. Echte Consumerumstellung | regulierung verlangt freigegebene, genau versionierte Wheels über Requirements. `services/dsfa/bewertung.py`, Rechenkern und ausgewählte Parser werden kontrollierte Kompatibilitätsadapter mit echten `auditcore_*`-Imports. ORM, Auth, Mandant, Review und Aktenführung bleiben App. | Installierte Wheels statt zufälligem Workspace-PYTHONPATH testen; Dependency-/Importgraph belegt Nutzung. Keine doppelten weiter auseinanderlaufenden Rechenimplementierungen. |
| 6. Framework-/Appprüfung | ApplicabilityContext aktualisieren; FrameworkPolicyProvider, anwendbare Prüfkatalogfälle, Library-/App-Unit-, Regression-, Integrationstests, Ruff, Typprüfung, Security-/Dependencychecks ausführen. | Fachliche Abweichung → MIGRATION_BLOCKED. Ungeprüft → NOT_EXECUTED; unklare Anwendbarkeit → REVIEW_REQUIRED. Alle notwendigen Gates müssen nachweisbar erfüllt sein. |
| 7. Nativen Debianplan konkretisieren | Ziel-OS/Architektur/Python-ABI festlegen und dokumentieren; DeploymentPlan für Backend-Service und vorgebautes Frontend. PostgreSQL16/PostGIS/TimescaleDB/Redis als explizit versionierte Laufzeitdienste bzw. freigegebene externe Dienste. | Verträgliche Debianpakete/Repos oder offline bereitgestellte Abhängigkeiten belegt; keine Annahme, Standard-Debian liefere automatisch PostgreSQL16/TimescaleDB. |
| 8. Reproduzierbar bauen | Backend-Appwheel plus Domainwheels mit vollständigem Hash-Lock und passend gebautem Wheelhouse; Frontend aus npm-Lock bauen; SBOM, Provenienz, BuildManifest, Signaturen. Native Libraries als saubere Debian-Depends; Python-Runtime kontrolliert mitliefern bzw. abhängig machen. | Installation ohne PyPI/Node/npm/uv/Poetry/Compiler. Keine unkontrollierten Downloads oder Compile-Schritte in postinst. Wheelhouse allein ohne ABI-/Closureprüfung reicht nicht. |
| 9. Paket und Upgradevertrag | `auditcore.tools.deployer` um den konkreten Appplan nutzen/ergänzen. Serviceuser, `/etc/regulierung` (Konfiguration), `/var/lib/regulierung` (Daten), schreibgeschützte Runtime z. B. `/usr/lib/regulierung`, Static Assets und systemd-Unit. | Fileownership/Secrets/Start-/Stop-/Restart-/Proxy-/Readiness prüfen. Pfade sind Zielvorschlag, vorhandene relative Pfade müssen vorher tatsächlich aufgelöst werden. |
| 10. Migration/Update/Restore | Migration als eigener fail-closed Schritt vor Start, Ausgangsrevision prüfen, Wartung/Jobs stoppen, Backup+Restoreprobe, Upgradejournal und Wiederaufnahme. DEB/APT wird alleiniger Schreiber der paketverwalteten Runtime; alter Compose-Updater für diese Installation nicht parallel aktiv. | Bestehende Signatur-/Freigabe-/Versions-/Architektur-/Auditgarantien funktional erhalten. Release-Schlüssel außerhalb App; keine breite root-/APT-Berechtigung für Webprozess. Nicht kompatible DBmigration blockiert, kein behaupteter automatischer Datenrollback. |
| 11. Installation wirklich testen | Frische VM mit systemd und echter DB; Installation vN, synthetische Datensätze/Uploads/Schlüssel, Upgrade vN+1, Reboot, fehlgeschlagenes Upgrade, Remove und Neuinstallation; Offlinephase erzwingen. | Daten/Config/Historien unverändert, API+Frontend+authgeschützte Pfade funktionieren, Migration korrekt, Restore erfolgreich. Container ohne systemd ist kein vollwertiger Serviceabnahmetest. |
| 12. Freigabe und Wissen | Erst nach Betriebs-/Backup-/Policy-/Supply-Chainfreigabe READY_FOR_DEPLOYMENT und signiertes APT-Repository. KIRA: neue Symbole, Consumer, entfernte Legacykerne, Migration, Quality/Policy und API-Snapshot aktualisieren. | Tatsächlicher Install-/Upgradebericht, getrennte Restblocker; keine Produktivfreigabe aus Unit-Tests allein. |

Die erste Migrationswelle sollte Datenschutz plus einen begrenzten Preisberechnungspfad
umfassen. KPAnG-Verfahrenslogik wird nicht nebenbei harmonisiert. Eine vollständige
Anwendungsfreigabe umfasst trotzdem Regressionen über alle aktivierten Module.

## Anwendbarkeit vor Policy-Gates

Aus Code belegbar: Fachanwendung, Mandanten/Rollen, JWT/OIDC, Uploads, externe
Schnittstellen, personenbezogene Verwaltungs-/Nutzerdaten und mehrstufige
Freigaben. Das ist ein Verfahrenskontext, kein Bibliotheksprofil. Konkreter Schutzbedarf,
Betriebsziel, aktiviertes AI-/Harvest-Profil, realer Datenraum, Testdatennutzung und
Netzfreigaben sind für die Zielinstallation zu erheben und bleiben bis dahin UNKNOWN
bzw. REVIEW_REQUIRED. Keine pauschale Annahme, Demo und produktives Vollzugsverfahren
hätten dieselbe Anwendbarkeit. DSFA-Werte und KPAnG-Kommentare werden hier als
vorhandene Implementierung beschrieben, nicht als geprüfte Rechtsauslegung.

## Offene Blocker / Entscheidungen

- Rechtefreigabe für öffentliche regulierung-Extraktionen fehlt; keine Übertragung
  der früheren Generator-MIT-Freigabe auf diese Quellen.
- Datenschutz-, Preis- und Harvestlibraries noch nicht vollständig implementiert und
  veröffentlicht; neue Consumerimports daher noch nicht möglich.
- Methoden-/Schwellen-/Profilentscheidungen dürfen nicht automatisch vereinheitlicht
  werden. Insbesondere DSFA-Eingabevalidierung, fehlende Antworten sowie KPAnG-
  Verfolgungs-/Zeit-/Quellenprofile benötigen dokumentierte Verträge.
- Native App-DEB/systemd-Migration ist neue Implementierung, kein Umpacken des
  vorhandenen Containerarchivs. OS/ABI/DB-Extensionverfügbarkeit muss nachgewiesen sein.
- Alter Compose-Updater und neuer APT-Pfad benötigen klaren gegenseitigen Ausschluss
  pro Installation. Signatur-/Backup-/Freigabefunktionalität darf dabei nicht entfallen.
- API-Health allein genügt nicht; belastbare Readiness und Restoreprobe fehlen als
  Nachweis für das neue Paket. Installation/Upgrade/Remove sind NOT_EXECUTED.
- Keine vollständige Produktionsmigration oder fachliche Abnahme in dieser Inventur.

## Vollständigkeitsregister

Alle nachfolgend aufgeführten API-/Dienstmodule wurden statisch eingelesen. Eine
Aufzählung bestätigt Existenz/Struktur, nicht Verhaltenskorrektheit oder Testabdeckung.

### api

- `api/admin/alerts.py`: `list_alerts`, `alert_stats`, `update_alert_status`, `generate_alerts_endpoint`
- `api/admin/betrieb.py`: `status`, `plan`, `LaufAnfrage`, `start`, `Zugang`, `pruefe_verbindung`, `verbindung`, `test`, `download`, `verarbeitung`, `UmgebungEingabe`, `umgebung`, `einstellungen_zuruecksetzen`, `neustart_entwurf`, `neustart_anwenden`, `Schluesselwechsel`, `schluessel_erneuern`, `quellen_nachtragen`, `regelwerk_nachtragen`, `hessen_grenze_nachtragen`, `RueckdatierungAnfrage`, `regelwerk_profile_rueckdatieren`
- `api/admin/clustering.py`: `ClusterConfigUpdate`, `update_cluster_config`
- `api/admin/datenquellen.py`: `feldreferenzen`, `feldreferenz_lesen`, `feldreferenz_seed`, `NeueFassung`, `fassung_anlegen`, `ZeileIn`, `ZeilenErsetzen`, `zeilen_ersetzen`, `Freigabe`, `fassung_freigeben`, `entwurf_verwerfen`, `ProfilPruefung`, `profil_pruefen`, `dateien_hochladen`
- `api/admin/documents.py`: `list_source_documents`, `download_source_document`
- `api/admin/dsfa.py`: `Stand`, `Entscheidung`, `Stellungnahme`, `Folgerung`, `fragenkatalog`, `taetigkeiten`, `fassungen`, `vorschau`, `speichern`, `entscheiden`, `stellungnahme`, `folgerung`, `freigeben`, `bericht`, `uebersicht`, `neubewertung`
- `api/admin/external_apis.py`: `ExternalApiOut`, `ExternalApiUpdate`, `HarvestRunOut`, `list_apis`, `get_api`, `update_api`, `trigger_health_check`, `trigger_harvest`, `list_runs`
- `api/admin/features.py`: `list_features`, `update_feature`
- `api/admin/harvesting.py`: `harvesting_status`, `harvesting_run_all`, `harvesting_run_single`, `harvesting_job_status`, `list_harvesting_jobs`, `get_review_queue`, `ReviewAction`, `process_review`, `get_harvesting_log`, `run_discovery_all`, `run_discovery_single`, `llm_status`
- `api/admin/indices.py`: `sync_destatis_indices`, `monitoring_destatis`, `get_index_trend_endpoint`, `standardserien`, `indexwerte_importieren`
- `api/admin/kpang_dms.py`: `optionen`, `DmsAnfrage`, `vorschlag`, `preview`, `liste`, `DmsStatus`, `bestaetigen`, `export`
- `api/admin/mandant_dsgvo.py`: `EntwurfSpeichern`, `FreigabeRequest`, `DokumentResponse`, `verarbeitungsverzeichnis_xlsx`, `entwurf_oder_aktuelle_lesen`, `versionen_lesen`, `entwurf_speichern`, `entwurf_freigeben`, `vorbelegen`
- `api/admin/mandanten.py`: `MandantCreate`, `MandantUpdate`, `MandantResponse`, `list_mandanten`, `get_mandant`, `create_mandant`, `update_mandant`, `deactivate_mandant`, `set_standard_mandant`, `upload_mandant_wappen`, `get_mandant_wappen`
- `api/admin/monitoring.py`: `monitoring`, `list_audit_log`
- `api/admin/mtsk_import.py`: `ProfilCreate`, `VersionCreate`, `VersionUpdate`, `detect_datei`, `list_lieferungen`, `get_lieferung`, `create_profil`, `list_profile`, `get_profil`, `create_version`, `update_version`, `dry_run_version`, `freigeben_version`, `aktivieren_version`, `get_importlauf`
- `api/admin/mtsk_produktivimport.py`: `produktivimport_lieferung`, `get_abstimmung`
- `api/admin/pakete.py`: `ExportAnfrage`, `Zuordnung`, `bounded`, `download`, `vorlage`, `bestand`, `aus_excel`, `liste`, `hochladen`, `get_row`, `detail`, `archiv`, `beantragen`, `freigeben`, `ablehnen`
- `api/admin/prices.py`: `create_nahwaerme_preis`, `create_wasser_preis`
- `api/admin/programmupdates.py`: `available`, `audit`, `status`, `werkzeuge`, `UploadAnfrage`, `start`, `upload_files`, `offset`, `chunk`, `complete`, `install`
- `api/admin/providers.py`: `create_provider`, `update_provider`, `delete_provider`, `create_variante`, `delete_variante`
- `api/admin/quarantaene.py`: `liste`, `Entscheidung`, `freigeben`, `verwerfen`
- `api/admin/registry.py`: `ManualPriceUpload`, `manual_price_upload`
- `api/admin/rulebook.py`: `RegelCreate`, `RegelUpdate`, `rulebook_editierstand`, `regel_anlegen`, `regel_aendern`, `regel_loeschen`, `ParameterUpdate`, `parameter_lesen`, `parameter_aendern`, `FreigabeRequest`, `rulebook_freigeben`, `rulebook_ersteinrichtung_status`, `rulebook_karenzzeiten_einspielen`
- `api/admin/settings.py`: `SettingsUpdate`, `effektive_settings`, `get_settings_values`, `update_settings`
- `api/admin/signaturschluessel.py`: `SchluesselAnlegen`, `SchluesselEintragen`, `uebersicht`, `erzeugen`, `eintragen`, `freigeben`, `vertrauensliste`, `selbsttest`
- `api/admin/users.py`: `UserCreate`, `UserUpdate`, `UserResponse`, `rollen_liste`, `list_users`, `create_user`, `update_user`, `upload_profilbild`, `get_profilbild`, `delete_user`, `reset_password`
- `api/admin/wiki.py`: `ArtikelCreate`, `ArtikelUpdate`, `create_artikel`, `update_artikel`, `delete_artikel`, `seed_ausfuehren`, `seed_wiki`
- `api/auth_routes.py`: `Token`, `RefreshRequest`, `UserInfo`, `login`, `get_current_user_info`, `get_own_profilbild`, `update_own_profile`, `upload_own_profilbild`, `refresh_token`, `logout`, `ModulWechselPayload`, `log_module_switch`
- `api/calculate_routes.py`: `calculate_nahwaerme_endpoint`, `calculate_wasser_endpoint`, `nahwaerme_sensitivity`, `wasser_sensitivity`, `nahwaerme_heatmap`, `wasser_heatmap`, `ranking`, `kreis_statistik`
- `api/dashboard_routes.py`: `dashboard_stats`
- `api/deps.py`: `get_current_user`, `get_authenticated_user`, `require_admin`, `pruefe_rolle`, `require_vollzug_schreibrecht`, `require_bescheid_freigabe`, `require_datenpakete`, `verify_admin_auth`, `check_feature`, `is_feature_enabled`
- `api/export_routes.py`: `TabellenExport`, `export_tabelle`, `export_preview`, `export_csv`, `export_xlsx`, `export_html`, `export_docx`, `export_pdf`, `export_behoerdenakte`
- `api/kpang/_sql_utils.py`: `escape_like`
- `api/kpang/akte.py`: `akte_verzeichnis`, `akte_export`
- `api/kpang/akteneinsicht.py`: `AkteneinsichtIn`, `EntscheidungIn`, `GewaehrungIn`, `AkteneinsichtOut`, `OffenesGesuchOut`, `lade_akteneinsicht`, `get_akteneinsicht_katalog`, `akteneinsicht_erfassen`, `list_akteneinsicht`, `akteneinsicht_entscheiden`, `akteneinsicht_gewaehren`, `list_offene_akteneinsicht`
- `api/kpang/auswertung.py`: `AuswertungFilter`, `VerstossOut`, `AuswertungSummary`, `AuswertungResponse`, `BetreiberZeile`, `BetreiberSummary`, `BetreiberAuswertungResponse`, `auswerten`, `auswerten_export`, `auswerten_betreiber`, `auswerten_betreiber_export`, `verfahrensgruppe`, `phi_quelle`, `PhiVerfahrenFilter`, `PhiVerfahrenZeile`, `PhiVerfahrenSummary`, `PhiVerfahrenResponse`, `auswerten_verfahren_phi`, `auswerten_verfahren_phi_export`
- `api/kpang/bevollmaechtigte.py`: `BevollmaechtigterIn`, `BevollmaechtigterPatch`, `BeendigungIn`, `BevollmaechtigterOut`, `ZustellungsempfaengerOut`, `lade_bevollmaechtigte`, `get_bevollmaechtigten_katalog`, `bevollmaechtigten_erfassen`, `list_bevollmaechtigte`, `bevollmaechtigten_aendern`, `bevollmaechtigten_beenden`, `get_zustellungsempfaenger`
- `api/kpang/beweismittel.py`: `BeweismittelMetaOut`, `beweismittel_erzeugen`, `beweismittel_liste`, `beweismittel_bericht`
- `api/kpang/demo.py`: `aufbau_stand`, `DemoAufbauIn`, `stand`, `aufbauen`, `entfernen`
- `api/kpang/markt.py`: `RohstoffpreisOut`, `WechselkursOut`, `MarktauffaelligkeitCreate`, `MarktauffaelligkeitOut`, `HinweisBKartA`, `KorrelationOut`, `MarktStats`, `list_rohstoffpreise`, `list_wechselkurse`, `list_auffaelligkeiten`, `AuffaelligkeitKopfOut`, `AuffaelligkeitTankstelleOut`, `AuffaelligkeitMeldungOut`, `AuffaelligkeitFensterOut`, `AuffaelligkeitMeldungenOut`, `get_auffaelligkeit_meldungen`, `create_auffaelligkeit`, `hinweis_an_bkarta`, `list_korrelationen`, `KorrelationsPunktOut`, `get_korrelation_punkte`, `BatchResult`, `trigger_brent_korrelation`, `trigger_synchronizitaet`, `trigger_cluster`, `trigger_konzern_parallelitaet`, `get_markt_stats`, `PreisindexPunktOut`, `get_preisindex`
- `api/kpang/monitoring.py`: `DurchlaufzeitTage`, `VerjaehrungItem`, `MonatsPunkt`, `VollzugStatsErweitert`, `get_vollzug_stats_erweitert`
- `api/kpang/plausiprotokoll.py`: `get_plausiprotokoll`, `PlausiUpdate`, `get_verwerfungsgruende`, `patch_plausiprotokoll`, `offene_plausizeilen`, `NeuberechnungIn`, `neuberechnung`, `export_plausiprotokoll`
- `api/kpang/pruefung.py`: `uhrzeit_zu_toleranz`, `toleranz_zu_uhrzeit`, `PruefFilter`, `Verantwortlicher`, `phi_gruppe`, `phi_schluessel_von`, `filtere_phi`, `VerstossTrefferOut`, `DatenlueckeOut`, `UnklarOut`, `BetreiberZusammenfassungOut`, `BetreiberErgebnisOut`, `FassungAbschnittOut`, `KarenzSpalteOut`, `PruefSummaryOut`, `PruefResponse`, `baue_betreiber_ergebnisse`, `tage_des_zeitraums`, `tagesgrenzen`, `pruefparameter_fuer`, `nachfilter_fuer`, `baue_abschnitte`, `PruefAuswertung`, `werte_aus`, `baue_summary`, `fassungen_im_zeitraum`, `pruefe_verstoesse`, `schreibe_kennzahlen_blatt`, `pruefe_verstoesse_export`
- `api/kpang/rulebook.py`: `rulebook_lesen`, `rulebook_parameter`, `rulebook_report`, `rulebook_versionen`, `rulebook_versionen_vergleich`
- `api/kpang/sammelanlage.py`: `SammelanlageFilter`, `TatOut`, `StationOut`, `GruppeOut`, `VorschauOut`, `GruppeAnlegen`, `AnlegenIn`, `AngelegtOut`, `GruppenFehlerOut`, `AnlegenOut`, `AnhoerungKandidatOut`, `AnhoerungenIn`, `AnhoerungErgebnisOut`, `AnhoerungenOut`, `vorschau`, `anlegen`, `anhoerung_kandidaten`, `anhoerungen_erzeugen`
- `api/kpang/verfahren.py`: `DiagrammPdfAnfrage`, `ProzessNotizUpdate`, `abgleich`, `prozessstand`, `soll_bpmn`, `ist_bpmn`, `diagramm_pdf`, `ist_svg`, `prozessstand_vorgaenge_pdf`, `prozessstand_notiz_setzen`
- `api/kpang/verfahren_dokumente.py`: `QuellsystemUpdate`, `get_vollzugsquelle`, `set_vollzugsquelle`, `DokumentVersionOut`, `DokumentOut`, `list_vorgang_dokumente`, `download_dokument`, `get_gesamtakte_pdf`, `AnhoerungRueckmeldungIn`, `patch_anhoerung_rueckmeldung`, `get_anhoerung_rueckmeldungen`, `AusgangsbetraegeIO`, `get_ausgangsbetraege`, `AusgangsbetraegeEntwurfOut`, `AusgangsbetraegeFreigabeIn`, `get_ausgangsbetraege_entwurf`, `put_ausgangsbetraege`, `post_ausgangsbetraege_freigeben`, `PhiStationOut`, `PhiZuordnungOut`, `RegelsatzOut`, `KostenPositionOut`, `KostenOut`, `vorgang_kosten`, `get_regelsatz`, `TatZumessungIn`, `TatZumessungSpeichern`, `TatZumessungZeileOut`, `TatZumessungOut`, `get_zumessung_taten`, `put_zumessung_taten`, `DokumentErzeugen`, `vorgang_checkliste`, `erzeuge_dokument`, `SerienbriefErzeugen`, `SerienbriefSchreibenOut`, `SerienbriefOut`, `serienbrief_vorschau`, `erzeuge_serienbrief_anhoerung`, `SchriftstueckEntwurfIn`, `SchriftstueckEntwurfOut`, `VorlagenInfoOut`, `ZumessungStandOut`, `DokumentVorschauOut`, `get_schriftstueck_entwurf`, `put_schriftstueck_entwurf`, `vorschau_dokument`
- `api/kpang/vollzug.py`: `pruefe_legacy_zielstatus`, `code_fuer_zielstatus`, `pruefe_anhoerung_vor_bescheid`, `TankstelleOut`, `VerdachtsfallOut`, `VorgangCreate`, `AktenzeichenVorschlagResponse`, `VerantwortlicherVorschauRequest`, `VerantwortlicherVorschauResponse`, `VorgangUpdate`, `VorgangOut`, `PreismeldungPunkt`, `KartenPreisPunkt`, `KartenPreisResponse`, `TankstellenAnalyseTankstelle`, `TankstellenPreisBucket`, `TankstellenVerstossSummary`, `TankstellenVerstossDetail`, `TankstellenAnalyseSummary`, `TankstellenAnalyseResponse`, `TankstellenMeldungZeile`, `TankstellenMeldungenResponse`, `list_tankstellen`, `export_tankstellen`, `get_karten_preisentwicklung`, `get_tankstellen_analyse`, `list_tankstellen_meldungen`, `export_tankstellen_analyse`, `list_verdachtsfaelle`, `export_verdachtsfaelle`, `get_verdachtsfall`, `aktenzeichen_vorschlag`, `verantwortlicher_vorschau`, `vorgang_eroeffnen`, `list_vorgaenge`, `get_vorgang`, `update_vorgang`, `VorgangResetRequest`, `vorgang_zuruecksetzen`, `TriageRequest`, `vorgang_triage`, `KassendatenEntscheidungRequest`, `vorgang_kassendaten_entscheiden`, `GewinnschaetzungRequest`, `vorgang_gewinnschaetzung_abschliessen`, `VorgangVdfRequest`, `VorgangVdfEntfernenRequest`, `vorgang_verdachtsfaelle_hinzufuegen`, `vorgang_verdachtsfall_entfernen`, `get_statuskatalog`, `VorgangAuditOut`, `get_vorgang_audit`, `ProzessverlaufKnoten`, `ProzessverlaufOut`, `get_vorgang_prozessverlauf`, `VorgangFristCreate`, `VorgangFristUpdate`, `VorgangFristOut`, `FaelligeFristOut`, `create_vorgang_frist`, `list_vorgang_fristen`, `update_vorgang_frist`, `ZustellungIn`, `ZustellungOut`, `get_zustellungs_katalog`, `unterbrechung_verspaetet`, `zustellung_erfassen`, `UnterbrechungIn`, `UnterbrechungOut`, `VerjaehrungOut`, `aktualisiere_verjaehrungsfrist`, `get_unterbrechungs_tatbestaende`, `get_verjaehrung`, `unterbrechung_erfassen`, `list_faellige_fristen`, `StammdatenHistorieCreate`, `StammdatenHistorieOut`, `list_stammdaten_historie`, `create_stammdaten_historie`, `get_preisreihe`, `VollzugStats`, `get_vollzug_stats`, `ImportKalenderTag`, `ImportKalenderResponse`, `get_import_kalender`
- `api/kpang/vorlagen.py`: `VersionOut`, `VorlageOut`, `extrahiere_platzhalter`, `dokument_volltext`, `list_vorlagen`, `get_platzhalter_schema`, `seed_vorlagen`, `list_versionen`, `upload_version`, `freigeben_version`, `vorschau_version`, `download_version`
- `api/kpang/wiki.py`: `list_artikel`, `get_artikel`, `list_versionen`, `vergleiche_versionen`
- `api/kpang/zweitkontrolle.py`: `VorlegenIn`, `ZeichnenIn`, `ZurueckgebenIn`, `NotizIn`, `ZweitpruefungOut`, `PostfachEintrag`, `PostfachOut`, `vorlegen`, `zeichnen`, `zurueckgeben`, `notiz_anlegen`, `list_zweitpruefungen`, `get_postfach`, `get_postfach_anzahl`
- `api/provider_routes.py`: `list_providers`, `plz_lookup`, `get_provider`, `soft_delete_provider`, `get_provider_historie`, `list_source_documents_for_provider`, `download_source_document_for_provider`, `get_clusters`, `get_cluster_methodenkarte`, `get_provider_term_mapping`, `get_index_korrelation`, `validate_preisgleitklausel_endpoint`, `get_anbieter_index_trend`, `get_wetzlar_benchmark`
- `api/schnittstellen.py`: `liste`, `openapi`, `download`, `detail`

### services

- `services/app_settings.py`: `get_numeric_setting`, `get_setting`, `aktive_vollzugsquelle`
- `services/betrieb.py`: `Zeitplan`, `Verbindung`, `Verarbeitung`, `Umgebung`, `laufzeit`, `gespeicherte_gruppe`, `cipher`, `lesen`, `speichern`, `geheimnis`, `zugang`, `einstellung`, `runtime_settings`, `Neustartwerte`, `neustartwerte`, `schluessel_erneuern`, `aktualisiere_zeitplaene`, `lauf`
- `services/betrieb_backup.py`: `key`, `encrypt`, `decrypt`, `pg_env`, `command`, `pack`, `inventory`, `backup`, `restore_test`
- `services/cache.py`: `make_params_hash`, `get_cached_result`, `set_cached_result`, `invalidate_sektor`, `invalidate_provider`, `invalidate_pattern`, `close_redis`
- `services/calculator.py`: `calculate_nahwaerme`, `calculate_wasser`, `calculate_delta`, `determine_compliance`, `calculate_cluster_statistics`
- `services/cluster_comparison.py`: `build_cluster_statistics_map`, `apply_cluster_benchmarks`
- `services/clustering.py`: `get_rechtsform_for_provider`, `normalisiere_rechtsform`, `vergleichsgruppe_key`, `split_vergleichsgruppe`, `vergleichsgruppe_bezeichnung`, `ClusterZuordnung`, `bestimme_cluster`, `get_cluster_for_provider`, `calculate_cluster_median`, `get_outliers`
- `services/dsfa/bewertung.py`: `vorschlag_text`, `Antwort`, `Szenario`, `Schwellwertergebnis`, `Risikoergebnis`, `Vorschlag`, `risikostufe`, `vorbelegung_aus_taetigkeit`, `werte_schwellwert_aus`, `werte_risiko_aus`, `erstelle_vorschlag`, `vorschlag_als_json`
- `services/dsfa/export.py`: `baue_bericht_html`, `baue_bericht_pdf`, `baue_uebersicht_workbook`
- `services/dsfa/katalog.py`: `norm`, `Frage`, `Massnahme`, `fundstelle`, `katalog_als_json`
- `services/dsfa/verwaltung.py`: `taetigkeiten`, `referate`, `lade`, `fassungen`, `offene_fassung`, `berechne_vorschlag`, `pruefe_regime`, `regime_vorschlag`, `speichere`, `entscheide`, `dsb_stellungnahme`, `dsb_folgerung`, `freigeben`, `vergleiche_taetigkeit`, `pruefe_auf_aenderungen`, `neubewertung`, `als_json`
- `services/external_apis/base.py`: `HarvestResult`, `BaseConnector`, `get_connector`
- `services/external_apis/bundesbank.py`: `BundesbankConnector`
- `services/external_apis/destatis_genesis.py`: `DestatisGenesisConnector`
- `services/external_apis/eia_brent.py`: `EiaBrentConnector`
- `services/external_apis/eu_oil_bulletin.py`: `EuOilBulletinConnector`
- `services/external_apis/geoportal_hessen.py`: `GeoportalHessenConnector`
- `services/external_apis/handelsregister.py`: `HandelsregisterConnector`
- `services/external_apis/mtsk.py`: `MtskConnector`
- `services/external_apis/overpass.py`: `OverpassConnector`
- `services/external_apis/tankerkoenig.py`: `TankerkoenigConnector`
- `services/external_apis/vid_secondary.py`: `MehrTankenConnector`, `CleverTankenConnector`, `AdacConnector`
- `services/external_indices.py`: `ensure_default_external_series`, `upsert_external_index_value`
- `services/flagging.py`: `flag_provider`, `check_index_anomaly`, `generate_alerts`, `check_multi_index_anomaly`, `validate_preisgleitklausel`, `generate_and_persist_alerts`, `get_alert_stats`
- `services/genesis_sync.py`: `pruefe_indexreihe`, `sync_indices`, `get_index_trend`, `check_api_health`
- `services/harvesting/link_discovery.py`: `DiscoveredLink`, `DiscoveryResult`, `discover_links_for_provider`, `run_link_discovery`
- `services/harvesting/llm_extractor.py`: `baue_quelltext_block`, `baue_system_prompt`, `prepare_content_for_llm`, `check_ollama_status`, `parse_llm_response`, `extract_prices_with_llm`
- `services/harvesting/pipeline.py`: `run_harvesting`, `extract_multiple_variants`
- `services/harvesting/plausibility.py`: `NW`, `WA`
- `services/harvesting/quellenklassen.py`: `Quellenklasse`, `gueltige_definitionen`, `definition`, `basis_confidence`, `ist_bekannte_klasse`, `als_markdown_tabelle`
- `services/harvesting/review_queue.py`: `get_pending_reviews`, `approve_review`, `reject_review`, `correct_review`
- `services/harvesting/scheduler.py`: `purge_access_log`, `setup_scheduler`, `trigger_manual_run`, `get_scheduler_status`
- `services/harvesting/validators.py`: `validate_nahwaerme`, `validate_wasser`, `check_delta`, `cross_validate_nahwaerme`
- `services/kpang_mandant.py`: `KpangEinstellungen`, `anhoerungsfrist`
- `services/kraftstoff/markt/auffaelligkeit_meldungen.py`: `FensterParameter`, `Meldung`, `TankstellenZeile`, `sekunden_seit_tagesbeginn`, `im_erwartbaren_fenster`, `bewerte_meldung`, `baue_meldung`, `aggregiere_tankstellen`, `lokaler_tag_utc`, `lade_fensterparameter`, `lade_meldungen`
- `services/kraftstoff/markt/cluster.py`: `sortiere_kraftstoffe`, `sorten_kurz_text`, `erkenne_konzern_parallelitaet`, `erkenne_raeumliches_cluster`
- `services/kraftstoff/markt/korrelation.py`: `berechne_brent_korrelation`, `berechne_wechselkurs_korrelation`, `berechne_wettbewerber_korrelation`, `hole_korrelation_punkte`, `berechne_synchronizitaet`
- `services/kraftstoff/markt/marktfenster.py`
- `services/kraftstoff/markt/preisindex.py`: `ZeitraumFehler`, `PreisindexPunkt`, `pruefe_zeitraum`, `standard_zeitraum`, `umrechnungsfaktor`, `zeilen_zu_punkten`, `berechne_preisindex`
- `services/kraftstoff/vollzug/aktenexport.py`: `Aktendatei`, `Akte`, `dateiname_teil`, `endung_fuer`, `sammle_akte`, `baue_aktenspiegel_html`, `rendere_aktenspiegel_pdf`, `baue_verzeichnis`, `baue_pruefsummen`, `baue_akte_zip`, `dateiname_akte`
- `services/kraftstoff/vollzug/anhoerung_serienbrief.py`: `PhiGruppe`, `phi_identitaet`, `gruppiere_nach_phi`, `PhiAdresse`, `phi_adresse`, `phi_schluessel_aus_wert`, `gemeinsamer_phi`, `SerienbriefErgebnis`, `serienbrief_anhoerung`
- `services/kraftstoff/vollzug/anlage_taten.py`: `baue_anlage`
- `services/kraftstoff/vollzug/bearbeitungsstatus.py`: `ist_konzernzweig`, `anhoerungsstatus_fuer`, `label`, `beschreibung`, `legacy_status`, `code_fuer_status`, `ist_uebergang_erlaubt`, `ist_endzustand`, `ist_ruecksetzbar`, `ist_komposition_aenderbar`, `katalog`, `ist_entwurf_aenderbar`
- `services/kraftstoff/vollzug/beweismittel_generator.py`: `BeweismittelFehler`, `ist_beweistauglich`, `kanonische_serialisierung`, `SignaturErgebnis`, `lade_privaten_schluessel`, `signiere_snapshot`, `verifiziere_signatur`, `lade_vertrauensschluessel`, `verifiziere_vertrauenskette`, `erzeuge_beweismittel_snapshot`
- `services/kraftstoff/vollzug/classifier.py`: `Klassifikation`, `Auslegungsprofil`, `profil_aus_parameter`, `profil_label`, `KlassifikationsErgebnis`, `klassifiziere`, `DoppelErgebnis`, `klassifiziere_beide_profile`
- `services/kraftstoff/vollzug/datenluecken.py`: `Tageszaehlung`, `Datenluecke`, `bewerte_tage`, `lade_datenluecken`
- `services/kraftstoff/vollzug/demo_faelle.py`: `DemoAufbauFehler`, `DemoSzenario`, `DemoSchritt`, `DemoFallErgebnis`, `DemoAufbauErgebnis`, `Kandidat`, `waehle_kandidaten`, `demo_entfernen`, `demo_stand`, `demo_aufbauen`
- `services/kraftstoff/vollzug/dokument_erzeugung.py`: `frist_ende`, `fristanker`, `frist_beschreibung`, `Ausgangsbetraege`, `Tat`, `TateinheitTat`, `buendle_taten`, `RegelsatzVorschlag`, `berechne_regelsatz`, `beweismittel_satz`, `taten_kontext`, `gebuehr_owig`, `hoechstmass_eur`, `pruefe_hoechstmass`, `pruefe_einzelbussen`, `baue_kontext`, `kombinierte_station`, `baue_serienbrief_kontext`, `sandbox_jinja_env`, `rendere_vorlage`, `passender_bescheid_schluessel`
- `services/kraftstoff/vollzug/geo_bundesland.py`: `bestimme_bundesland`, `backfill_bundesland`
- `services/kraftstoff/vollzug/gesamtakte_pdf.py`: `Gesamtakte`, `sammle_gesamtakte`, `baue_gesamtakte_html`, `rendere_gesamtakte_pdf`, `dateiname_gesamtakte`
- `services/kraftstoff/vollzug/ingestion.py`: `IngestionStats`, `ingest_tankerkoenig_payload`
- `services/kraftstoff/vollzug/kosten.py`: `gebuehr_einzel`, `gebuehr`, `AuslagenPosition`, `Kosten`, `auslagen_positionen`, `berechne`
- `services/kraftstoff/vollzug/kpang_fenster.py`: `fenster_beginn_sek`, `fenster_beginn`, `fenster_ende_sek`, `fenster_ende_exklusiv`, `fenster_ende_inklusiv`, `im_fenster`
- `services/kraftstoff/vollzug/phi_zuordnung.py`: `HistorieEintrag`, `PhiZuordnung`, `name_aus_wert`, `zuordnung_zur_zeit`, `zuordnungen_je_fall`
- `services/kraftstoff/vollzug/plausiprotokoll.py`: `plausicode`
- `services/kraftstoff/vollzug/preis_einheit.py`: `Einheit`, `einheit_fuer_quelle`, `SkalenFehler`, `euro_zu_einheit`, `zu_euro`, `umrechnen`, `erkenne_einheit`, `pruefe_einheit`, `pruefe_stichprobe`, `mtsk_bestand_ist_verdaechtig`, `formatiere_ct`, `formatiere_eur_je_liter`
- `services/kraftstoff/vollzug/prozessstand.py`: `Schritt`, `where_clause`, `verteile`, `ermittle_prozessstand`
- `services/kraftstoff/vollzug/pruefung_je_tattag.py`: `tattag`, `TattagGruppen`, `gruppiere_je_tattag`, `TattagErgebnis`, `pruefe_je_tattag`, `normiert`, `phi_schluessel`, `Zaehlung`, `zaehle`, `KarenzVergleich`
- `services/kraftstoff/vollzug/regelwerk_parameter.py`: `RegelwerkParameter`, `als_pruefparameter`, `lade_pruefparameter`, `pruefe`, `aus_konfiguration`, `lade_parameter`, `Fassung`, `waehle_fassung`, `fassung_am_tattag`, `lade_fassungen`, `entwurfsparameter`, `als_anzeige`, `plausi_grenzen`
- `services/kraftstoff/vollzug/regelwerk_report.py`: `parameter_block_aus`, `baue_parameter_block`, `render_regelwerk_docx`, `render_regelwerk_pdf`
- `services/kraftstoff/vollzug/rulebook_service.py`: `RulebookFehler`, `VierAugenVerletzung`, `KeineFreigebbareAenderung`, `RulebookNichtInitialisiert`, `ist_vier_augen_gewahrt`, `pruefe_vier_augen`, `naechste_nummer`, `regel_als_rule`, `regel_als_admin`, `version_als_dict`, `baue_snapshot`, `diff_snapshots`, `lade_aktive_regeln`, `lade_wirksame_version`, `lade_produktive_regeln`, `lade_laufende_version`, `lade_versionen`, `lade_version`, `ersteinrichtung_aktiv`, `bestimme_wirksamkeit`, `markiere_version_als_entwurf`, `freigabe_durchfuehren`, `lade_parameter_entwurf`, `speichere_parameter_entwurf`, `freigebe_parameter`, `lade_karenzzeiten`, `karenz_fassungen`, `karenzzeiten_einspielen`
- `services/kraftstoff/vollzug/sammelanlage.py`: `eintrag_zur_zeit`, `anschrift_aus_wert`, `FallEingabe`, `TatVorschau`, `StationVorschau`, `GruppeVorschau`, `Vorschau`, `bilde_gruppen`, `phi_schluessel`
- `services/kraftstoff/vollzug/schriftstueck_entwurf.py`: `bereinige_felder`, `diff_felder`, `ist_platzhalter_wert`, `offene_platzhalter`, `dokument_bloecke`, `enthaelt_rohe_platzhalter`, `lade_entwurf`, `speichere_entwurf`
- `services/kraftstoff/vollzug/signaturschluessel_service.py`: `SchluesselFehler`, `verschluesseln`, `entschluesseln`, `key_id_aus_public`, `fingerabdruck`, `liste`, `aktiver_schluessel`, `aktiver_privatschluessel`, `vertrauensliste`, `erzeugen`, `eintragen`, `freigeben`, `selbsttest`
- `services/kraftstoff/vollzug/stammdaten_zeitpunkt.py`: `gueltig_zum_zeitpunkt`, `tankstelle_zur_tatzeit`, `tankstellen_zur_tatzeit`, `stammdatenfeld_zur_tatzeit`, `verantwortlicher_zur_tatzeit`
- `services/kraftstoff/vollzug/tankerkoenig_csv.py`: `preis_zu_cent`, `parse_zeitstempel`, `lese_stationen`, `lese_preisereignisse`
- `services/kraftstoff/vollzug/tatbildung.py`: `gruppiere_taten`
- `services/kraftstoff/vollzug/tateinheit_zumessung.py`: `ZumessungFehler`, `TatZeile`, `tat_fingerprint`, `passende_zumessung`, `tat_schluessel`, `baue_zeilen`, `summe`, `vollstaendig`, `lade_zumessungen`, `speichere_zumessungen`, `einzelbussen_aus_zumessung`, `begruendungen_aus_zumessung`
- `services/kraftstoff/vollzug/verfahrens_checkliste.py`: `verjaehrung_jahre`, `Verjaehrung`, `berechne_verjaehrung`, `ChecklistPunkt`, `Checkliste`, `baue_checkliste`, `rendere_docx`, `rendere_pdf`
- `services/kraftstoff/vollzug/verfahrens_sicherheit.py`: `pruefe_uebergang`, `pruefe_entscheidung_aenderbar`, `pruefe_anhoerung_gezeichnet`, `entscheidungsstand`, `pruefe_dokumentstand`
- `services/kraftstoff/vollzug/verstosslogik.py`: `PruefParameter`, `PreisEreignis`, `meldeauffaelligkeit`, `Verstoss`, `UnklarerFall`, `Zusammenfassung`, `Tat`, `PruefErgebnis`, `massgeblicher_ausgangspreis`, `im_toleranzfenster`, `pruefe_meldungen`, `bilde_taten`
- `services/kraftstoff/vollzug/vorlagen_builder.py`: `baue_anhoerung`, `baue_bescheid_einzel`, `baue_bescheid_mehrfach`, `baue_zumessungsrichtlinie`, `baue_anhoerung_konzern`, `baue_bescheid_konzern`, `baue_einstellungsverfuegung`
- `services/kraftstoff/vollzug/vorlagen_schema.py`: `validiere_tags`, `Pflichttext`, `validiere_pflichttexte`, `validiere_vorlage`, `Abschnitt`, `abschnitte_fuer`
- `services/kraftstoff/vollzug/vorlagen_vorschau.py`: `testkontext`, `rendere_vorschau`
- `services/kraftstoff/vollzug/worker.py`: `klassifiziere_neue_meldungen`, `reklassifiziere_zeitraum`
- `services/kraftstoff/vollzug/zustellungsempfaenger.py`: `Zustellungsempfaenger`, `ist_aktiv`, `aktive`, `ermittle_zustellungsempfaenger`, `Adressatenpruefung`, `pruefe_zustellungsadressat`
- `services/mandant_dsgvo_service.py`: `KeinEntwurfError`, `lade_entwurf`, `lade_aktuelle_freigegebene`, `lade_versionen`, `taetigkeit_kennung`, `taetigkeiten_mit_kennung`, `speichere_entwurf`, `freigeben`, `baue_verarbeitungsverzeichnis_workbook`, `fuelle_platzhalter`, `vorbelegen`
- `services/mandant_service.py`: `get_standard_mandant`, `get_standard_mandant_namen`
- `services/mtsk_import/demo_import.py`: `DemoImportError`, `rueckdatiere_demo_stammdaten`, `importiere_demo_excel`
- `services/mtsk_import/detection.py`: `erkenne_format`, `analyze_csv`, `lade_xlsx_blatt`, `analyze_xlsx`, `waehle_zip_datei`, `analyze_zip`
- `services/mtsk_import/dry_run.py`: `run_dry_run`
- `services/mtsk_import/feldreferenz_seed.py`: `seed_feldreferenzen`
- `services/mtsk_import/mtsk_xml.py`: `ist_mtsk_xml`, `publikationstyp`, `lies_preise`, `lies_stammdaten`, `analyze_xml`
- `services/mtsk_import/plausibilitaet.py`: `PlausiGrenzen`, `grenzen_aus_konfiguration`, `Befund`, `pruefe_zeile`, `ist_abgelehnt`, `protokoll`, `pruefe_band_gegen_skalenwaechter`
- `services/mtsk_import/produktivimport.py`: `ProduktivimportError`, `LieferungNichtGefunden`, `ProfilVersionNichtVerwendbar`, `ZeilenEntscheidung`, `klassifiziere_zeile`, `berechne_abstimmung`, `pruefe_abstimmungs_konsistenz`, `importiere_lieferung`
- `services/mtsk_import/transform.py`: `t_trim`, `t_lower`, `t_upper`, `t_wertetabelle`, `t_eur_in_cent`, `t_eur_in_zehntelcent`, `t_preisfaktor`, `t_datum_zeit_kombinieren`, `t_zeitzone_setzen`, `t_leer_zu_null`, `t_bool_normalisieren`, `t_fuehrende_nullen_erhalten`, `t_fester_wert`, `apply_transformations`
- `services/overview_metrics.py`: `get_latest_price_stichtage`, `get_current_harvesting_provider_stats`, `get_harvesting_run_stats`
- `services/pakete/archiv.py`: `digest`, `canonical`, `inspect_zip`, `build_zip`
- `services/pakete/daten.py`: `validate_manifest`, `read_package`, `generate`, `lock`, `audit`, `stable_key`, `export_database`, `upload`, `mapping_key`, `candidates`, `validate_mapping`, `request_approval`, `approve`
- `services/pakete/einrichten.py`: `exclusive`, `main`
- `services/pakete/excel.py`: `columns`, `template`, `from_excel`
- `services/pakete/programm.py`: `sha_file`, `verify`
- `services/pakete/update_transport.py`: `shared_path`, `maintenance`
- `services/pakete/updater.py`: `atomic`, `Updater`, `main`
- `services/pakete/werkzeuge.py`: `dateien`, `schreiben`
- `services/preisauswahl.py`: `waehle_preis_deterministisch`, `waehle_wasser_preis`, `lade_wasser_preis`, `lade_nahwaerme_preis`
- `services/profilbild.py`: `bild_upload_speichern`, `profilbild_speichern`
- `services/report_generator.py`: `generate_html_report`, `generate_csv_report`, `generate_docx_report`, `generate_pdf_report`, `generate_behoerdenakte`, `generate_beweisbericht_pdf`
- `services/schnittstellen/katalog.py`: `katalog`, `typ`, `tabellen`, `grafik`, `detail`, `markdown`, `pdf`, `download`
- `services/schnittstellen/vertraege.py`: `Vertrag`, `Anbieter`, `Quelle`, `Preisstand`, `WasserPreisstand`, `NahwaermePreisstand`, `Versorgungspaket`, `Programmdatei`, `Programmpaket`
- `services/wartung.py`: `quellen_einspielen`, `regelwerk_seed`, `hessen_grenze_laden`, `regelwerk_profile_rueckdatieren`
- `services/wiki_service.py`: `slugify`, `artikel_als_dict`, `version_als_dict`, `wiki_diff`
