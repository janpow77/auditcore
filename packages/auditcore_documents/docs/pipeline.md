# Dokumentpipeline (`auditcore_documents.pipeline`)

Quelle: `janpow77/flowinvoice@fb2d18568d2e` (`backend/app/pipeline`, Blobs in
`provenance.json`), gegen GitHub geprüft (`main` = `fb2d185`). Tatsächlich
ausgeführt mit `tools/capture_pipeline.py` in einem Wegwerf-Container mit den
flowinvoice-Produktionsabhängigkeiten (Python 3.11.16, pydantic 2.11.9,
SQLAlchemy 2.0.43, python-magic 0.4.27/libmagic, pypdf 6.16.2, pypdfium2 4.30.0,
Pillow 11.3.0). Die 164 Originaltests (`tests/pipeline/*`, Watchdog, Profile)
bestehen dort gegen eine Wegwerf-PostgreSQL.

Eingaben: drei synthetische Rechnungs-PDF aus `auditcore_invoicegenerator`
(Seed 42, Fehler `wrong_total`/`missing_vat_id`), ein 1×1-PNG, eine Textdatei
und fünf frei erfundene deutsche Rechnungstexte (`tools/build_pipeline_fixtures.py`).
Aufgezeichnet: 30 vollständige Pipeline-Läufe (Gateway-OCR mit Seitenrasterung,
Ausfall, Seitenfehler, Einzelaufruf für Bilder, lokales Chandra/Tesseract mit
Rückfällen, Backend `none`, ungültiger MIME-Typ, fehlende Datei, S3, HTTP mit
Wiederholungen, Stufenfilter, LLM-Wiederherstellung, unerwarteter Fehler,
Exportziele) sowie Einzelfälle für Feldextraktion (8), IBAN (10), USt-IdNr. (12),
Summen (6), OCR-Konfidenz, Betrugsregel, Compute-Profile (16), Hashing,
Artefakt-JSON, Modellgrenzen (26), Aufbewahrung (5 Läufe) und Dateiexport.

Die Bibliothek reproduziert alle 30 Läufe exakt: Kontext einschließlich
**Stufen-Hashes** (SHA-256 über `artifacts.model_dump_json()`, ohne pydantic
bytegleich nachgebildet), Audit-Ereignisse in Reihenfolge und Inhalt,
Gateway-Aufrufe, Wartezeiten, abgelegte Artefaktdateien und Exporte. Zeiten und
das Datum im Speicherschlüssel sind in beiden Fällen maskiert.

## Vertrag

| Baustein | Original | Bibliothek |
|---|---|---|
| Kontext/Modelle | pydantic | Datenklassen mit gleichen Feldern, Vorgaben, Wertebereichen, Enum-Übernahme; `to_dict`, `artifacts_json`; Uhr injizierbar |
| Stufen | `PipelineStage` mit Vor-/Nachlauf | gleich; Audit über Port `AuditSink`, kein `logging` |
| Ablauf | `PipelineOrchestrator`, `ComputeProfileEnforcer` | gleich; `sleep` und `GpuQuota` als Ports |
| Einlesen | aiofiles, python-magic, httpx, pypdf | Datei; HTTP über Port `fetch_url`; MIME per Signatur (`sniff_mime`) oder `libmagic_detector` (Extra `mime`); pypdf-Seitenzahl |
| Vorverarbeitung | Platzhalter (Winkel 0.0) | gleich; Port `angle_detector` |
| OCR | ai-router, Chandra (torch), Tesseract | Ports `RouterOcr`, `ChandraPort`, `TesseractPort`, `Rasterizer` (`pdfium_rasterizer`, Extra `ocr-raster`); Routing und Normalisierung rein |
| Nachverarbeitung | Regex-Felder | unverändert, rein |
| Validierung | Regeln + FraudDetectionManager (DB) | Regeln unverändert; Betrugsprüfung als Port `FraudChecker` |
| Persistenz | SQLAlchemy + Dateien | Ports `RunRepository`, `ArtifactStore`; `FileArtifactStore`; reine Feld-/Dateiabbildung |
| Export | httpx-Webhook, Dateien | Port `post` für Webhooks, `FileExport` |
| Aufbewahrung | SQLAlchemy-Service | `RetentionSweeper` mit Port `RetentionStore` (alle fünf Fristen über `ArtifactRetentionStore`), reine Kriterien |
| Watchdog | `services/extraction_quality_watchdog.py` | `auditcore_documents.pipeline.watchdog` (C-01…C-13, Standardbibliothek, Meldungen mit Umlauten) |
| Profile | – | `LEGACY_PIPELINE` (`flowinvoice.pipeline` 1.0.0), `CORRECTED_PIPELINE` = `RECOMMENDED_PIPELINE` (`auditcore.pipeline` 2026.09.2) |

## Korrekturen (PL-C)

| ID | Original | Bibliothek |
|---|---|---|
| PL-C01 | Jede Stufe setzt beim Start RUNNING; ein REVIEW_NEEDED aus OCR oder Validierung wird von der nächsten Stufe überschrieben und am Ende als **OK** gemeldet (Läufe `router_review`, `router_ok` mit Regelbefund, `de_sum_mismatch`, `de_unknown_country`, `llm_unavailable_recovery`). | `CORRECTED_PIPELINE` (`preserve_review=True`) meldet REVIEW_NEEDED. `LEGACY_PIPELINE` bleibt unverändert. |
| PL-C02 | IBAN-Muster `[A-Z0-9\s]{11,30}` mit IGNORECASE läuft über Zeilenumbrüche („DE89…3000\nNettobetrag“ → `…NETTOB`), gültige IBAN werden ungültig und der Beleg wird REJECTED (`de_valid`). | `CORRECTED_PIPELINE`: Muster endet am Zeilenende. |
| PL-C03 | Datei wird vollständig gelesen, danach Größenprüfung. | Größe vor dem Lesen geprüft (gleicher Fehlercode). |
| PL-C04 | MIME über libmagic (Systembibliothek). | Vorgabe `sniff_mime` für die zulässigen Typen; für unzulässige Dateien kann der gemeldete Typ abweichen (`application/octet-stream` statt `text/plain`); `libmagic_detector` hält das Original. |
| PL-C05 | „Hash-Kette“ ist eine Liste unabhängiger Stufen-Hashes. | Unverändert; zusätzlich `HashingService.linked_chain` (verkettet). |
| PL-C06 | Artefaktschlüssel werden ungeprüft an einen Pfad gehängt. | `FileArtifactStore` weist Schlüssel außerhalb des Ablageverzeichnisses ab. |
| PL-C07 | Dateiexport und `INVALID_MIME_TYPE`-Details abhängig von Gebietsschema/Hash-Seed (`list(set)`). | UTF-8 und sortierte Liste. |
| PL-C08 | Fehlende Ports: HTTP und Gateway sind fest verdrahtet. | `HTTP_NOT_CONFIGURED`, `ROUTER_NOT_CONFIGURED` statt Netzwerkzugriff. |

## Beibehaltene Befunde (PL-L)

| ID | Befund | Status |
|---|---|---|
| PL-L01 | Englische Zahlenformate werden deutsch normalisiert: `18251.04` → `1825104.0`; „Subtotal: …“ trifft das Muster für `total`; „INVOICE\nDocument:“ ergibt Rechnungsnummer `Document` (Rechnungen aus auditcore_invoicegenerator). | **DECIDED** (D5): in `CORRECTED_PIPELINE` korrigiert, in `LEGACY_PIPELINE` beibehalten. |
| PL-L02 | Unlesbare Datumsangaben bleiben als Text; ein Summenwert 0 gilt als „fehlend“ (`all([...])`). | beibehalten |
| PL-L03 | Gateway-Ausfall ergibt Konfidenz 0 und damit REJECTED statt eines technischen Fehlers. | **DECIDED** (D6): in `CORRECTED_PIPELINE` wiederholbarer Fehler, in `LEGACY_PIPELINE` beibehalten. |
| PL-L04 | Vorverarbeitung ist ein Platzhalter; PIL-Hilfen werden nicht aufgerufen. | beibehalten, Port vorhanden |
| PL-L05 | Nur `processing_logs_days` wird durchgesetzt; Aufbewahrungsfristen für Originale, OCR-Rohdaten, Extraktionen und Audit-Ereignisse sind konfigurierbar, aber wirkungslos. | **DECIDED** (D7): mit `categories=ALL_CATEGORIES` bzw. `build_retention_sweeper(profile=CORRECTED_PIPELINE, …)` wirksam; Voreinstellung des `RetentionSweeper` bleibt originalgetreu. |
| PL-L06 | Probelauf zählt Einträge als „gelöscht“; weich gelöschte Läufe ohne `deleted_at` erhalten `marked_for_deletion` und werden danach nie mehr ausgewählt. | beibehalten, dokumentiert |
| PL-L07 | `decimal.InvalidOperation` („1.234,5“) verlässt die Betrugsregel und wird als `ERROR_VAL_FRAUD_DETECTION` gewertet. | beibehalten |
| PL-L08 | Betrugsregel ohne Dienst: Meldung „No database session…“ bzw. bei fehlendem Modul „service not available“ (umgebungsabhängig). | Bibliothek meldet stets die erste Variante |
| PL-L09 | `to_audit_details` liefert Verweise auf die Kontextlisten. | beibehalten |
| PL-L10 | OCR-Timeout-Wiederherstellung stellt das Backend nach Erfolg nicht zurück. | beibehalten |

## Entscheidungen

Entschieden am **2026-09-23** durch den Nutzer (Zitat: „alle empfehlungen“).
Status vorher: HUMAN_DECISION_REQUIRED, jetzt **DECIDED**. `LEGACY_PIPELINE`
bleibt bitgenau (alle 30 aufgezeichneten Läufe, Fingerabdruck unverändert).

| Nr. | Entscheidung | Umsetzung in `CORRECTED_PIPELINE` 2026.09.2 (`RECOMMENDED_PIPELINE`, Status `DECIDED_RECOMMENDED`) |
|---|---|---|
| D4 | `CORRECTED_PIPELINE` ist das empfohlene Pipeline-Profil. | PL-C01 (REVIEW_NEEDED bleibt erhalten) und PL-C02 (gültige IBAN werden angenommen). |
| D5 | Beträge gebietsschemabewusst lesen; mehrdeutige Fälle als Review markieren statt raten. | `amount_mode="locale-aware"` mit `parse_amount`: bei beiden Trennzeichen ist das letzte das Dezimalzeichen (`1.234,56`, `1,234.56`); `18251.04` bleibt `18251.04`; gültige Tausendergruppen (`1.234.567`) werden gelesen; ein einzelnes Trennzeichen vor genau drei Ziffern (`1.234`, `1,234`) ist **mehrdeutig** → Wert `None`, Regel `VAL_AMOUNT_FORMAT` (WARN) setzt REVIEW_NEEDED. Seit 0.3.2 geht der Befund nicht mehr verloren, wenn nur normalisiert wird: `normalize_fields_checked` liefert je auf `None` gesetztem Betrag `{"raw", "state": "ambiguous"|"invalid"}`, die Nachverarbeitungsstufe setzt `AMOUNT_AMBIGUOUS_<FELD>`/`AMOUNT_INVALID_<FELD>` in `validation_flags`; `normalize_fields` selbst liefert unverändert nur die Werte (`None` unterscheidet „fehlt“ nicht von „mehrdeutig“). Feldmuster überspringen keine Zeilenumbrüche und beginnen nicht mitten im Wort („Subtotal“ trifft nicht mehr `total`, „INVOICE\nDocument:“ ergibt keine Rechnungsnummer `Document`). Beleg `router_ok`: Nettobetrag 18251.04, kein Befund `FAIL_VAL_TOTAL_PLAUSIBILITY` mehr. |
| D6 | Gateway-Ausfall ist Fehler mit Wiederholung, nicht REJECTED. | `OcrStage.gateway_outage_is_error`: Fehlercode `OCR_GATEWAY_UNAVAILABLE` (wiederholbar); Orchestrator `retry_gateway`: drei Wiederholungen nach 5/10/15 s, danach `FAILED` mit `retryable=True` (Lauf `router_down`). |
| D7 | Alle fünf Aufbewahrungsfristen wirksam. | `retention_categories=ALL_CATEGORIES` (`original_documents`, `ocr_raw_output`, `structured_extraction`, `processing_logs`, `audit_events`); die Anwendung liefert `find_expired_artifacts(category, cutoff, limit)`; fehlt der Port, meldet der Lauf je Kategorie einen Fehler statt still zu übergehen. |
| D8 | Watchdog übernehmen, Meldungstexte mit korrekten Umlauten. | `auditcore_documents.pipeline.watchdog`; einzige Abweichung vom Original sind die Umlaute in `message_de`, `block_reason` und der Mängelliste. Nachweis: 18 aufgezeichnete Originalläufe (`tools/capture_watchdog.py`, `tests/fixtures/watchdog_observed.json`) stimmen nach Rückumschrift exakt überein; die 30 Originaltests laufen unverändert gegen die Bibliothek. |

## Consumer flowinvoice

Belegte Nutzung: `app/worker/pipeline_tasks.py:_run_pipeline_async`
(Stufenliste, Orchestrator, Enforcer, Audit), `app/api/pipeline.py`
(Enforcer, Audit), `app/api/retention.py` (Aufbewahrung), `app/api/review_queue.py`
(Audit). Befunde beim Consumer (nicht Teil der Bibliothek): Der Worker erzeugt
eine neue `run_id`, obwohl die API den Lauf bereits angelegt hat; die
Profil-Einstellungen (`ocr_settings`, `parser_settings`) werden den Stufen nicht
übergeben; `PIPELINE_STARTED/COMPLETED` werden doppelt protokolliert; das Modell schreibt in
`pipeline_audit_events`, das keine Migration anlegt (nur `create_all`), während der
WORM-Trigger der Migration 011 nur `audit_events` schützt – die Audit-Tabelle der
Pipeline ist damit nicht gegen UPDATE/DELETE gesichert (SECURITY_OR_POLICY_REVIEW_REQUIRED).

### Getestete Integrationsvariante

Checkout-Kopie `flowinvoice@fb2d185`, Branch `feat/auditcore-documents-pipeline`,
lokaler Commit `bfe3d78` (nicht gepusht): neues Modul
`app/pipeline/auditcore_runner.py` mit Ports (`GatewayOcr` → `safe_call_ocr`,
`OrmRunRepository` → `PipelineRun`, `FileArtifactStore(settings.exports_path)`,
Chandra-Port, `libmagic_detector`); `app/worker/pipeline_tasks.py` baut statt der
eigenen Stufenliste `run_document_pipeline(session, context, audit=AuditService(session))`
mit `LEGACY_PIPELINE`; `_update_final_pipeline_status` bleibt. Die bisherigen
Module `app/pipeline/*` bleiben vorerst für API, Aufbewahrung und Tests bestehen.

Nachweis im Wegwerf-Container mit den Produktionsabhängigkeiten und einer
Wegwerf-PostgreSQL (keine Produktionsdaten), Wheel per `pip install --no-deps`:
`tests/pipeline/*`, `test_extraction_quality_watchdog.py`,
`test_pipeline_profiles.py` und der neue Integrationstest
`tests/pipeline/test_auditcore_worker.py` (Dokument anlegen, Worker ausführen,
`PipelineRun` mit SHA-256 und fünf Stufen-Hashes, Audit-Ereignisse in
`pipeline_audit_events`) → **165 passed** (vorher 164). Auflösung von
`auditcore_documents[mime,ocr-raster,pdf-text]` in derselben Umgebung: `pip check` ohne Befund.

### Umstellungsanleitung

1. `backend/requirements-production.txt`:
   `auditcore_documents[mime,ocr-raster,pdf-text]==0.1.0` (nach Release v0.3.0).
2. `app/pipeline/auditcore_runner.py` wie in der Integrationsvariante anlegen.
3. In `_run_pipeline_async` die Stufenliste und `PipelineOrchestrator` durch
   `run_document_pipeline` ersetzen; einen `pl.PipelineContext` aus den
   vorhandenen Werten bilden; `_export_pipeline_result_async` nutzt
   `pl.ExportStage` (bisher `NameError` durch undefiniertes `hashing`).
4. Danach schrittweise `app/pipeline/{context,hashing,orchestrator,stages}` durch
   Importe aus `auditcore_documents.pipeline` ersetzen (API-Schemas prüfen);
   ORM-Modelle, AuditService-Abfragen, QuotaService und Aufbewahrungs-API bleiben.
5. Profil: `LEGACY_PIPELINE` hält das bisherige Verhalten; empfohlen und
   entschieden (D4, 2026-09-23) ist `RECOMMENDED_PIPELINE` (= `CORRECTED_PIPELINE`).
   Der Wechsel erfolgt mit der Umstellung nach Release v0.3.0.

`services/extraction_quality_watchdog.py` ist als
`auditcore_documents.pipeline.watchdog` übernommen (D8); `api/fraud_detection.py`
importiert nach der Umstellung von dort (gleiche Namen und Signaturen, Meldungen
mit Umlauten). `services/chandra_ocr.py` bleibt als GPU-Engine in
der Anwendung und wird über `ChandraPort` angebunden.
