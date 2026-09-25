# App-Hilfsfunktionen (Python) – Inventur und Zuordnung zu auditcore

Stand 25.09.2026. Maschinenlesbar: [`app-helfer-python.json`](app-helfer-python.json). TypeScript-Gegenstück: `app-helfer-ts.*`.

## Vorgehen

- **sources**: Standardzweig je Repo (origin/main bzw. origin/master) per git archive; keine -wt-Worktrees; auditcore origin/main packages/*/src.
- **ast**: Top-Level-Funktionen und Methoden (ohne verschachtelte, ohne Tests/Migrationen), Docstring entfernt, Argumente/lokale Namen positionsnormalisiert, lange Stringkonstanten maskiert; exakt = SHA-1 des normalisierten AST; nah = MinHash-LSH (5er-Shingles, 16×4) + Indel-Ähnlichkeit der normalisierten Token ≥ 0,85, nur repo-übergreifende Paare; Kandidaten ≥ 25 Token und ≥ 2 Anweisungen.
- **graphify**: graphify-MCP war nicht erreichbar (ECONNREFUSED); graphify-out/graph.json je Repo direkt gelesen: calls/indirect_call-Kanten ohne Tests → Aufruferdateien (fan-in), god nodes, Hilfsfunktions-Communities.
- **callers**: callers_name_based = Zahl der Aufrufe mit diesem Funktionsnamen im Nicht-Test-Code des Repos (Obergrenze, Namenskollisionen möglich); caller_files_graphify = Aufruferdateien laut graphify; test_refs = Aufrufe/Importe des Namens in Testdateien.
- **vendored**: flow-agent/services/ai-router → ai-router, flow-agent/packages/graphify → graphify-kira, flowaudit/flowaudit_docker → flowaudit (nicht als eigene App gezählt).

Untersuchte Stände: flowaudit@d8107f6b, flowinvoice@5d5d8c5a, audit_designer@4b629dd9, vision-service@4c249036, wohnungsmonitor@47c50cd2, flowsearch@9ac5e0dd, ai-router@426cd78e, audit-portal@72cc4b1a, kiraclaw@43cd98e9, flownavigator@9dff858d, graphify-kira@1714914b, versteigerung@729f9a10, flowlib@aca2dc6a, flow-agent@b4c02e6c, cockpit@df203d4c, qaaudit@c78be5c8, riskanalysis@dace0f66, regulierung@ce76e48c, auditcore@26f75d17.

Erfasst wurden 28956 Funktionen/Methoden (davon 2563 in auditcore).

## Ergebnis in Zahlen

- Duplikatgruppen gesamt: 2930
- davon **Fork-Kopien** ganzer Module: 1775 – audit-portal ↔ flowinvoice: 977; audit-portal ↔ audit_designer: 625; flowinvoice ↔ riskanalysis: 147; ai-router ↔ cockpit: 26
- app-übergreifende Hilfsfunktions-Gruppen (ohne Forks): 129 – (a) existiert in auditcore: 57, (b) generisch, ≥ 2 Apps → auditcore_common: 29, (c) fachlicher Cluster → neue/erweiterte Bibliothek: 43
- nur innerhalb einer App dupliziert, Klasse (d): 1026

Wichtigster Strukturbefund: **audit-portal** ist im Backend im Wesentlichen eine Kopie von flowinvoice (services/api/worker/rag) und des flowstat-Moduls von audit_designer; **riskanalysis** enthält eine Kopie von flowinvoice/verwk; **cockpit** enthält den Admin-Teil von ai-router. Diese Fork-Kopien sind kein Hilfsfunktions-Thema, sondern eine Konsolidierungsfrage – sie verdecken sonst in jeder Duplikatliste die eigentlichen Helfer und sind unten getrennt ausgewiesen.

Die automatische Klassifizierung (Themen per Namensmuster) ist grob; die Top-20 unten sind von Hand geprüft (Quelltexte der Varianten verglichen).

## Top-20-Gruppen

| # | Gruppe | Klasse | Apps (Aufrufe namensbasiert / Aufruferdateien graphify / Testreferenzen) | Ziel |
|---|---|---|---|---|
| 1 | JWT-Erzeugung/-Prüfung und Passwort-Hashing (core/security.py) | c | audit_designer (49/6/184); flownavigator (9/8/38); flowsearch (4/4/0); qaaudit (8/6/8); versteigerung (3/3/0); regulierung (17/1/20); flowinvoice (8/0/4); audit-portal (2/2/0); flowlib (0/0/0) | neue Bibliothek auditcore_auth (flowlib.auth als Ausgangspunkt) |
| 2 | AI-Router-Client (RouterHealth, Circuit-Breaker, API-Key-Auflösung) | c | audit_designer (44/3/19); flowinvoice (29/4/10); audit-portal (22/2/0); cockpit (0/0/0) | neue Bibliothek auditcore_llm_client (Modul airouter) |
| 3 | IBAN/BIC/USt-IdNr./Steuer-ID-Prüfung | c | flowinvoice (8/7/30); audit-portal (7/5/26) | neue Bibliothek auditcore_identifiers (bündelt auch die Kopien in auditcore_invoicesynth und auditcore_documents) |
| 4 | Deutsche Zahlen und Beträge parsen („1.234,56“) | c | audit_designer (30/9/26); audit-portal (5/1/0); flowinvoice (6/2/0); regulierung (8/1/0) | auditcore_common (Modul numbers_de) mit expliziter Mehrdeutigkeitsregel + legacy-Aliase |
| 5 | Deutsche Zahl-/Euro-Formatierung für Berichte | c | flowinvoice (58/3/0); riskanalysis (46/2/0); audit_designer (21/3/2); audit-portal (19/1/0); versteigerung (5/2/0); regulierung (3/1/0) | auditcore_common (Modul format_de) – Fehlwert-Darstellung als Parameter |
| 6 | audit-portal Extraktions-Pipeline (Kontext, Stages, Watchdog, Hash-Kette) | a | audit-portal (24/5/59) | auditcore_documents 0.2.1 (pipeline.context, pipeline.hashing.HashingService, watchdog.validate_extraction_quality, check_supplier_concentration) |
| 7 | Förder-/Beihilferegister-Helfer (beneficiaries, state_aid, de_minimis) | a | audit_designer (53/15/54); flowsearch (7/1/0) | auditcore_funding_sources 0.1.1 (parse_datum, parse_date, harvest_amount, as_amount, coerce_float, stringify, stringify_plz, normalize_name, normalize_company_name_simple, compute_record_hash, record_hash, amount_is_range, country_code, harvest_fields) |
| 8 | Kanonischer JSON-Hash / Profil-Fingerprint | a | audit_designer (9/3/2); audit-portal (0/0/6); regulierung (6/0/0) | heute auditcore_harvest 0.1.0 `canonical_hash` bzw. auditcore_dataprotection 0.4.1 `canonical_sha256` (identisch); Ziel auditcore_common.hashing.canonical_sha256 – ersetzt auch die ~9 fingerprint()-Kopien in auditcore |
| 9 | Datei-SHA-256 gestreamt (sha256_file/_file_sha256/hash_file) | a | audit_designer (16/3/0); audit-portal (8/2/2); flowinvoice (2/1/0); riskanalysis (2/1/0) | auditcore_documents 0.2.1 `compare.sha256_file` bzw. `pipeline.hashing.HashingService.hash_file`; mittelfristig nach auditcore_common.hashing verschieben |
| 10 | Tolerante Zahl-Koerzierung (_to_float/_als_zahl/_safe_float …) | a | audit_designer (34/4/0); audit-portal (18/1/0); flowinvoice (57/1/0); regulierung (6/1/0); versteigerung (4/1/0); cockpit (3/1/0) | auditcore_common (as_float/as_decimal); heute nur privat in auditcore_registry_sources._number bzw. auditcore_funding_sources.coerce_float 0.1.1 |
| 11 | Upload begrenzt lesen, MIME/PDF erkennen | c | audit_designer (2/1/0); regulierung (14/5/7); qaaudit (2/2/0); versteigerung (1/1/0) | neue Bibliothek auditcore_uploads (oder auditcore_documents-Erweiterung: libmagic_detector/looks_like_pdf existieren dort bereits) |
| 12 | Objekt laden oder HTTP 404 (FastAPI) | b | audit-portal (28/3/0); flowinvoice (4/1/0); regulierung (24/1/0); flownavigator (17/1/0); audit_designer (3/9/0) | auditcore_common (web.get_or_404, generisch über Modellklasse) |
| 13 | Dateinamen säubern (Download/Export) | b | audit_designer (35/3/9); audit-portal (6/1/0); regulierung (1/1/0) | auditcore_common (filenames.safe_filename mit Profil ascii oder unicode) |
| 14 | Client-IP aus X-Forwarded-For | b | ai-router (14/1/0); cockpit (27/5/0); audit_designer (36/2/0) | auditcore_common (Modul web, optionales Extra fastapi/starlette) |
| 15 | Coroutine synchron ausführen (Celery/Thread) | b | audit_designer (12/1/0); flowaudit (32/1/0); flowinvoice (52/2/4) | auditcore_common (asyncio.run_sync) |
| 16 | LegalChunker (Gesetzestext in Artikel/Absätze zerlegen) | c | audit_designer (3/2/0); flowinvoice (2/2/0); audit-portal (2/2/0) | Erweiterung auditcore_legal_sources (Modul chunking) – nicht auditcore_documents.article_law (das wendet Änderungsbefehle an) |
| 17 | MUS-Stichprobenumfang (flowstat sampling_service) | a | audit_designer (8/1/20); audit-portal (8/1/10) | auditcore_sampling 0.2.0 `portal_mus_size` / `flowstat_mus_size` |
| 18 | Haversine/Entfernung und Punkt-im-Polygon | a | audit_designer (9/3/0); wohnungsmonitor (9/3/0); flowsearch (1/1/3) | auditcore_geo 0.2.0 (designer_register_entfernung_km, designer_company_haversine_m, flowsearch_calculate_distance_km, _designer_im_ring) |
| 19 | Anteil/Quote in Prozent mit Nullschutz | b | audit_designer (8/1/0); flowinvoice (14/1/0); riskanalysis (11/1/0); regulierung (2/1/7) | auditcore_common (numbers.share / percent) |
| 20 | Kira-Memory-Client und geschichtete .env-Konfiguration | c | ai-router (7/3/4); graphify-kira (5/2/4); flowlib (0/0/0) | flowlib (memory.py) als gemeinsamer Ort – nicht auditcore (Infrastruktur, kein Prüfungsfachwissen) |

Klassen: (a) existiert in einer auditcore-Bibliothek → App soll sie nutzen; (b) generisches Duplikat über ≥ 2 Apps → auditcore_common; (c) fachlicher Cluster → neue Bibliothek oder Erweiterung; (d) app-spezifisch, bleibt.

### 1. JWT-Erzeugung/-Prüfung und Passwort-Hashing (core/security.py) – Klasse c

**Ziel:** neue Bibliothek auditcore_auth (flowlib.auth als Ausgangspunkt)

**Fundstellen:**

- audit_designer: `backend/app/core/security.py` – `create_access_token` (Z. 35), `decode_token` (Z. 51), `get_password_hash` (Z. 30), `verify_password` (Z. 25)
- flownavigator: `apps/backend/app/core/security.py` – `create_access_token` (Z. 25), `decode_access_token` (Z. 38), `get_password_hash` (Z. 20), `verify_password` (Z. 15)
- flowsearch: `backend/app/core/security.py` – `create_access_token` (Z. 36), `get_password_hash` (Z. 27), `verify_password` (Z. 19)
- qaaudit: `backend/app/core/security.py` – `create_access_token` (Z. 33), `decode_access_token` (Z. 54), `hash_password` (Z. 19), `verify_password` (Z. 24), `generate_csrf_token` (Z. 64), `verify_csrf` (Z. 106)
- versteigerung: `backend/app/core/security.py` – `create_access_token` (Z. 29), `hash_password` (Z. 16), `verify_password` (Z. 21)
- regulierung: `backend/app/core/security.py` – `create_access_token` (Z. 21), `create_refresh_token` (Z. 69), `get_password_hash` (Z. 112), `verify_password` (Z. 104)
- flowinvoice: `backend/app/core/security.py` – `get_password_hash` (Z. 71), `verify_password` (Z. 57)
- audit-portal: `backend/app/core/security.py` – `verify_password` (Z. 93)
- flowlib: `python/flowlib/auth.py` – `create_access_token` (Z. 31), `decode_token` (Z. 57), `get_password_hash` (Z. 23), `verify_password` (Z. 18)

**Unterschiede der Varianten:**

- JWT-Bibliothek: python-jose (audit_designer, flownavigator, flowsearch, qaaudit, flowlib) vs. PyJWT (regulierung, versteigerung).
- Hash-Verfahren: passlib-bcrypt (audit_designer mit bcrypt>=4.1-Shim, flownavigator, qaaudit, flowlib), bcrypt direkt (flowsearch, regulierung), passlib-**argon2** (versteigerung) – Hashes sind nicht austauschbar.
- Zeitbasis: `datetime.utcnow()` naiv (audit_designer, flowsearch) vs. zeitzonenbewusst (flownavigator, qaaudit, regulierung, flowlib); audit_designer setzt zusätzlich `iat`.
- Ablauf: Minuten aus Settings (audit_designer, flownavigator, flowsearch), Stunden (qaaudit, regulierung), fest 24 h (flowlib); nur regulierung hat Refresh-Token, nur qaaudit Cookie-/CSRF-Helfer.
- Rückgabe bei ungültigem Token: `None` (flownavigator, flowlib) vs. Exception (qaaudit `jwt.decode` ungefangen).

**Tests:** audit_designer create_access_token 132 Testreferenzen, flownavigator 19, regulierung 11, qaaudit 4; flowsearch, versteigerung, flowlib ohne Tests.

### 2. AI-Router-Client (RouterHealth, Circuit-Breaker, API-Key-Auflösung) – Klasse c

**Ziel:** neue Bibliothek auditcore_llm_client (Modul airouter)

**Fundstellen:**

- audit_designer: `backend/app/utils/ai_router_client.py` – `record_failure` (Z. 124), `record_success` (Z. 118), `_api_key` (Z. 264)
- flowinvoice: `backend/app/clients/ai_router_client.py` – `record_failure` (Z. 160), `record_success` (Z. 154), `_unwrap_secret` (Z. 276), `_redact_error_message` (Z. 110)
- audit-portal: `backend/app/clients/ai_router_client.py` – `record_failure` (Z. 154), `record_success` (Z. 148)
- cockpit: `src/cockpit/services/ai_router_client.py` – ganze Datei

**Unterschiede der Varianten:**

- flowinvoice (1186 Z.) redigiert Fehlermeldungen vor dem Cachen (`_redact_error_message`: DSN, Bearer, sk-/ghp-Token, X-Api-Key; max. 160 Zeichen); audit_designer (957 Z.) hat das nicht.
- Singleton: flowinvoice Double-Checked-Locking mit injizierbarer Uhr (`self._now`), audit_designer sperrt bei jedem `instance()`-Aufruf und nutzt `time.time()` direkt.
- API-Key: audit_designer `_api_key()` liest `settings.LLM_ROUTER_API_KEY` selbst, flowinvoice `_unwrap_secret(value)` bekommt den Wert übergeben – der SecretStr-Entpackungsrumpf ist identisch (Ähnlichkeit 0,868).
- audit-portal ist eine Kopie des flowinvoice-Stands (Fork, 1003 Z.), cockpit hat einen eigenen, schlanken Client (218 Z., nur Modell-/Health-Abfrage).

**Tests:** flowinvoice und audit_designer: RouterHealth über Health-Tests abgedeckt (Name-Referenzen in Tests: record_failure 9/17); cockpit ohne.

### 3. IBAN/BIC/USt-IdNr./Steuer-ID-Prüfung – Klasse c

**Ziel:** neue Bibliothek auditcore_identifiers (bündelt auch die Kopien in auditcore_invoicesynth und auditcore_documents)

**Fundstellen:**

- flowinvoice: `backend/app/services/validators.py` – `validate_german_tax_id` (Z. 50), `validate_german_vat_id` (Z. 92), `validate_eu_vat_id` (Z. 161), `validate_uk_vat_id` (Z. 227), `validate_iban` (Z. 280), `validate_bic` (Z. 335)
- audit-portal: `backend/app/services/validators.py` – `validate_german_tax_id` (Z. 50), `validate_german_vat_id` (Z. 92), `validate_eu_vat_id` (Z. 161), `validate_iban` (Z. 280), `validate_bic` (Z. 335)
- flowinvoice: `backend/app/services/risk_checker.py` – `_normalize_vat_id` (Z. 400)
- auditcore: `packages/auditcore_invoicesynth/src/auditcore_invoicesynth/identifiers.py` – `iban_valid` (Z. 46), `de_vat_check_digit` (Z. 65), `at_uid_check_digit` (Z. 83), `vat_id_valid` (Z. 92)
- auditcore: `packages/auditcore_documents/src/auditcore_documents/pipeline/stages/validation_base.py` – `validate_iban` (Z. 32)
- auditcore: `packages/auditcore_documents/src/auditcore_documents/pipeline/stages/donut_values.py` – `de_vat_check_digit` (Z. 110), `at_uid_check_digit` (Z. 119)

**Unterschiede der Varianten:**

- flowinvoice/audit-portal `validate_iban` prüft nur Format und Länderlänge, **keine Modulo-97-Prüfziffer**; auditcore_invoicesynth.iban_valid und auditcore_documents.validate_iban prüfen Mod-97 – eine Umstellung ändert Ergebnisse (legacy-Variante nötig).
- flowinvoice `validate_german_vat_id`: nur Muster DE+9 Ziffern; auditcore_invoicesynth.vat_id_valid prüft zusätzlich die Prüfziffer (ISO 7064 MOD 11,10) und ATU.
- Rückgabetypen: `ValidationResult` mit Status MISSING/VALID/INVALID und deutscher Meldung (flowinvoice) vs. `bool` (invoicesynth) vs. `(bool, englische Meldung)` (documents).
- flowinvoice/services/validators.py und audit-portal/services/validators.py sind byte-identisch; de_vat_check_digit/at_uid_check_digit existieren in auditcore doppelt (invoicesynth und documents).

**Tests:** flowinvoice tests/test_validators.py (validate_german_tax_id 8, vat_id 7, iban 6 Referenzen); auditcore-Varianten mit Paket-Tests.

### 4. Deutsche Zahlen und Beträge parsen („1.234,56“) – Klasse c

**Ziel:** auditcore_common (Modul numbers_de) mit expliziter Mehrdeutigkeitsregel + legacy-Aliase

**Fundstellen:**

- audit_designer: `backend/app/modules/flowstat/services/de_numbers.py` – `parse_de_number` (Z. 39)
- audit_designer: `backend/app/modules/flowstat/services/node_handlers/timeseries.py` – `_parse_de_number` (Z. 38)
- audit_designer: `backend/app/modules/flowstat/services/his_oracle_value_gate_service.py` – `parse_zahl` (Z. 103)
- audit_designer: `backend/app/core/shared/research/register/beneficiaries.py` – `parse_betrag` (Z. 303)
- audit-portal: `backend/app/services/parser.py` – `_parse_german_number` (Z. 1187)
- flowinvoice: `backend/app/services/parser.py` – `_parse_german_number` (Z. 1345)
- flowinvoice: `backend/app/services/external_data_parser.py` – `parse_number_de` (Z. 442)
- regulierung: `backend/app/services/harvesting/pipeline.py` – `_parse_german_number` (Z. 2738)
- auditcore: `packages/auditcore_property_sources/src/auditcore_property_sources/zvg.py` – `parse_de_number` (Z. 203)
- auditcore: `packages/auditcore_funding_sources/src/auditcore_funding_sources/designer.py` – `parse_betrag` (Z. 59)

**Unterschiede der Varianten:**

- Mehrdeutiger Einzelpunkt „11.047“: audit_designer de_numbers → 11047 (Tausenderpunkt, bewusst); regulierung → 11.047 (Dezimalpunkt, bewusst dokumentiert wegen ct/kWh-Preisen); flowinvoice → 11.047 (float-Standard).
- flowinvoice/audit-portal `_parse_german_number` erkennt US-Format (1,234.56) über die Position des letzten Trennzeichens und entfernt €/$/£; regulierung und audit_designer nicht.
- audit_designer entfernt %-Suffix und Fehlwertzeichen (–, ., x …) und nimmt pandas-NaN an; auditcore_property_sources sucht die Zahl per Regex im Text (max. 2 Nachkommastellen).
- Rückgabe float (fast alle) vs. Decimal (parse_betrag in audit_designer und auditcore_funding_sources).

**Tests:** audit_designer parse_de_number 18 Testreferenzen, parse_zahl 6; regulierung/flowinvoice-Parser ohne direkte Tests.

### 5. Deutsche Zahl-/Euro-Formatierung für Berichte – Klasse c

**Ziel:** auditcore_common (Modul format_de) – Fehlwert-Darstellung als Parameter

**Fundstellen:**

- flowinvoice: `backend/app/verwk/services/report.py` – `_de` (Z. 650), `_eur` (Z. 672)
- riskanalysis: `backend/app/services/report.py` – `_de` (Z. 480), `_eur` (Z. 502)
- audit_designer: `backend/app/modules/reporting/cd_report_service.py` – `_de_num` (Z. 99)
- audit_designer: `backend/app/modules/flowstat/services/report_llm_text_service.py` – `_format_de` (Z. 441)
- audit_designer: `backend/app/core/shared/research/register/beneficiaries.py` – `format_eur` (Z. 245)
- flowinvoice: `backend/app/services/procurement_generator.py` – `_format_eur` (Z. 250)
- audit-portal: `backend/app/services/procurement_generator.py` – `_format_eur` (Z. 250)
- versteigerung: `backend/app/api/routers/auctions.py` – `_format_number_de` (Z. 65), `_format_money_de` (Z. 72)
- regulierung: `docs/kpang/build_handout_diagramme.py` – `de` (Z. 31)
- auditcore: `packages/auditcore_invoicesynth/src/auditcore_invoicesynth/formats.py` – `format_amount` (Z. 67), `format_money` (Z. 86)
- auditcore: `packages/auditcore_dataprotection/src/auditcore_dataprotection/legacy_report.py` – `format_datetime_de` (Z. 43)

**Unterschiede der Varianten:**

- Fehlwert: „–“ (flowinvoice/riskanalysis `_de`), „k.A.“ (audit_designer format_eur), `None` (versteigerung), Exception (audit_designer `_de_num`, flowinvoice `_format_eur`).
- Euro-Suffix: „ €“ ganzzahlig (flowinvoice `_eur`, audit_designer format_eur) vs. „ EUR“ mit 2 Nachkommastellen (procurement_generator).
- Platzhalter-Trick beim Tauschen von , und .: „§“ (flowinvoice), „\x00“ (audit_designer), „X“ (procurement_generator) – Ergebnis identisch.

**Tests:** keine direkten Tests in den Apps (nur indirekt über Berichtstests); auditcore_invoicesynth.formats getestet.

### 6. audit-portal Extraktions-Pipeline (Kontext, Stages, Watchdog, Hash-Kette) – Klasse a

**Ziel:** auditcore_documents 0.2.1 (pipeline.context, pipeline.hashing.HashingService, watchdog.validate_extraction_quality, check_supplier_concentration)

**Fundstellen:**

- audit-portal: `backend/app/pipeline/context.py` – `complete` (Z. 419), `fail` (Z. 405), `complete_stage` (Z. 383)
- audit-portal: `backend/app/pipeline/stages/base.py` – `validate_context` (Z. 186)
- audit-portal: `backend/app/pipeline/orchestrator.py` – `enforce` (Z. 430), `_try_recovery` (Z. 309)
- audit-portal: `backend/app/pipeline/hashing.py` – `compute_chain_hash` (Z. 127), `hash_json` (Z. 53), `hash_file` (Z. 76)
- audit-portal: `backend/app/services/extraction_quality_watchdog.py` – `validate_extraction_quality` (Z. 1068), `_check_supplier_concentration` (Z. 617)

**Unterschiede der Varianten:**

- Ähnlichkeit 0,85–1,0; auditcore_documents wurde aus flowinvoice/audit-portal geerntet. Nur Import-Umstellung.

**Tests:** validate_extraction_quality 31 Testreferenzen in audit-portal.

### 7. Förder-/Beihilferegister-Helfer (beneficiaries, state_aid, de_minimis) – Klasse a

**Ziel:** auditcore_funding_sources 0.1.1 (parse_datum, parse_date, harvest_amount, as_amount, coerce_float, stringify, stringify_plz, normalize_name, normalize_company_name_simple, compute_record_hash, record_hash, amount_is_range, country_code, harvest_fields)

**Fundstellen:**

- audit_designer: `backend/app/core/shared/research/register/beneficiaries.py` – `parse_datum` (Z. 374), `parse_satz` (Z. 261), `normalisiere_beguenstigtenname` (Z. 231), `compute_record_hash` (Z. 2762), `_als_text` (Z. 2493), `_als_float` (Z. 2515), `_fuer_hash` (Z. 2751)
- audit_designer: `backend/app/core/shared/research/register/state_aid.py` – `parse_date` (Z. 660), `betrag_ist_spanne` (Z. 653)
- audit_designer: `backend/app/core/shared/research/register/de_minimis.py` – `landeskennung` (Z. 58), `_als_betrag` (Z. 283)
- audit_designer: `backend/app/core/shared/research/register/de_minimis_ernte.py` – `_normalisiere` (Z. 44), `_felder` (Z. 78)
- audit_designer: `backend/app/modules/vp_ai/services/belegliste_import_service.py` – `_betrag`
- flowsearch: `backend/app/services/eu_beneficiary_harvester.py` – `_parse_amount` (Z. 495), `_parse_location`

**Unterschiede der Varianten:**

- Ursprung der Bibliothek (provenance): Funktionen sind exakt bzw. ≥ 0,94 gleich; die App trägt ihre Originale weiter. Umstellung verhaltensgleich über die designer_/flowsearch_-Legacy-Namen.

**Tests:** audit_designer `_betrag` 38, parse_satz 7, record_hash 7 Testreferenzen.

### 8. Kanonischer JSON-Hash / Profil-Fingerprint – Klasse a

**Ziel:** heute auditcore_harvest 0.1.0 `canonical_hash` bzw. auditcore_dataprotection 0.4.1 `canonical_sha256` (identisch); Ziel auditcore_common.hashing.canonical_sha256 – ersetzt auch die ~9 fingerprint()-Kopien in auditcore

**Fundstellen:**

- audit_designer: `backend/app/modules/flowstat/services/his_native_source_onboarding_service.py` – `_canonical_reference_hash` (Z. 503), `_fingerprint` (Z. 987)
- audit_designer: `backend/app/modules/flowstat/services/monthly_content_registry_service.py` – `registry_hash` (Z. 113)
- audit_designer: `backend/app/modules/flowstat/services/monthly_native_onboarding_service.py` – `_spec_fingerprint` (Z. 2089)
- audit-portal: `backend/app/pipeline/hashing.py` – `hash_json` (Z. 53)
- regulierung: `backend/app/services/cache.py` – `make_params_hash` (Z. 59)
- auditcore: `packages/auditcore_dataprotection/src/auditcore_dataprotection/hashing.py` – `canonical_sha256` (Z. 10)
- auditcore: `packages/auditcore_harvest/src/auditcore_harvest/model.py` – `canonical_hash` (Z. 134)
- auditcore: `packages/auditcore_risk/src/auditcore_risk/profiles.py` – `fingerprint` (Z. 128)

**Unterschiede der Varianten:**

- audit_designer `_fingerprint` und `registry_hash` sind wortgleich mit auditcore_harvest.canonical_hash / auditcore_dataprotection.canonical_sha256 / auditcore_risk.fingerprint (sort_keys, ensure_ascii=False, kompakte Separatoren) → direkt ersetzbar.
- Abweichend (NICHT hash-kompatibel, legacy-Variante nötig): audit_designer `_canonical_reference_hash` **ohne sort_keys**; audit-portal `HashingService.hash_json` mit ensure_ascii=True und `default=str`; regulierung `make_params_hash` mit Standard-Separatoren („, “/„: “) und `default=str`.

**Tests:** audit_designer registry_hash/fingerprint über flowstat-Tests (22 Name-Referenzen); regulierung ohne direkte Tests.

### 9. Datei-SHA-256 gestreamt (sha256_file/_file_sha256/hash_file) – Klasse a

**Ziel:** auditcore_documents 0.2.1 `compare.sha256_file` bzw. `pipeline.hashing.HashingService.hash_file`; mittelfristig nach auditcore_common.hashing verschieben

**Fundstellen:**

- audit_designer: `backend/app/modules/flowstat/services/monthly_content_registry_service.py` – `_file_sha256` (Z. 53)
- audit_designer: `backend/app/modules/flowstat/services/workshop_dashboard_service.py` – `_sha256_file` (Z. 132)
- audit_designer: `backend/app/modules/flowstat/services/testdata_config_service.py` – `_file_sha256` (Z. 1101)
- audit_designer: `backend/app/modules/vp_ai/models/document_cache.py` – `compute_hash` (Z. 78)
- audit-portal: `backend/audit_prep/model_fetch.py` – `_sha256_file` (Z. 51)
- audit-portal: `backend/audit_prep/source_fetch.py` – `_sha256_file` (Z. 113)
- audit-portal: `backend/app/pipeline/hashing.py` – `hash_file` (Z. 76)
- flowinvoice: `backend/app/verwk/services/pseudonymization.py` – `_sha256` (Z. 224)
- riskanalysis: `backend/app/services/pseudonymization.py` – `_sha256` (Z. 223)
- auditcore: `packages/auditcore_documents/src/auditcore_documents/compare.py` – `sha256_file` (Z. 48)
- auditcore: `packages/auditcore_invoicesynth/src/auditcore_invoicesynth/fonts.py` – `sha256_file` (Z. 82)

**Unterschiede der Varianten:**

- Ergebnis-kompatibel (SHA-256-Hex): alle Varianten; Blockgröße 1 MiB (audit_designer, audit-portal/audit_prep, auditcore_documents.compare) bzw. 8 KiB (HashingService.hash_file) – ohne Einfluss auf das Ergebnis; Eingabe `Path` vs. `str`.
- Achtung: audit_designer `VpDocumentCache.compute_hash` ist **MD5** (4 KiB-Blöcke) und liefert bei Fehlern "" – nicht austauschbar, bleibt als legacy-Variante bzw. (d).
- In auditcore selbst 5 Kopien (documents ×3, invoicesynth ×2) – Konsolidierung in auditcore_common empfohlen.

**Tests:** audit-portal hash_file über Pipeline-Tests; audit_designer-Varianten ohne direkte Tests.

### 10. Tolerante Zahl-Koerzierung (_to_float/_als_zahl/_safe_float …) – Klasse a

**Ziel:** auditcore_common (as_float/as_decimal); heute nur privat in auditcore_registry_sources._number bzw. auditcore_funding_sources.coerce_float 0.1.1

**Fundstellen:**

- audit_designer: `backend/app/core/shared/research/register/state_aid.py` – `_als_zahl` (Z. 3942), `_als_float` (Z. 1233)
- audit_designer: `backend/app/modules/vp_ai/services/pdb_import_service.py` – `_float` (Z. 41)
- audit_designer: `backend/app/core/shared/research/register/beneficiaries.py` – `_als_float` (Z. 2515)
- audit-portal: `backend/app/modules/company_research/read_model_service.py` – `_to_float` (Z. 63)
- flowinvoice: `backend/app/verwk/services/modellguete.py` – `_zahl` (Z. 42)
- regulierung: `backend/scripts/import_tankerkoenig_history.py` – `_safe_float` (Z. 188)
- versteigerung: `backend/app/api/routers/auctions.py` – `_money_float` (Z. 56)
- cockpit: `src/cockpit/models.py` – `_decode_json` (Z. 669)
- auditcore: `packages/auditcore_registry_sources/src/auditcore_registry_sources/ownership.py` – `_number` (Z. 216)
- auditcore: `packages/auditcore_funding_sources/src/auditcore_funding_sources/designer.py` – `coerce_float`

**Unterschiede der Varianten:**

- Nahe Duplikate (Ähnlichkeit ≥ 0,857): alle liefern `float | None` und fangen TypeError/ValueError; Unterschiede nur in Vorprüfungen ("" explizit → None, Decimal-Sonderzweig) – Ergebnis gleich. Keine Variante verwirft NaN/inf.
- Ein Paar ist nach normalisiertem AST exakt gleich (audit_designer `_als_float` ↔ versteigerung `_to_float`).

**Tests:** keine direkten Tests in den Apps.

### 11. Upload begrenzt lesen, MIME/PDF erkennen – Klasse c

**Ziel:** neue Bibliothek auditcore_uploads (oder auditcore_documents-Erweiterung: libmagic_detector/looks_like_pdf existieren dort bereits)

**Fundstellen:**

- audit_designer: `backend/app/api/presentations.py` – `_read_upload_limited` (Z. 69)
- regulierung: `backend/app/api/admin/datenquellen.py` – `_lies_begrenzt` (Z. 66)
- regulierung: `backend/app/services/harvesting/pipeline.py` – `_looks_like_pdf_bytes` (Z. 2040)
- qaaudit: `backend/app/utils/mime_check.py` – `detect_mime` (Z. 88), `validate_upload` (Z. 121)
- versteigerung: `backend/app/ingest/gutachten_ingest.py` – `is_pdf` (Z. 310)
- auditcore: `packages/auditcore_documents/src/auditcore_documents/pipeline/stages/ocr_results.py` – `looks_like_pdf` (Z. 120)
- auditcore: `packages/auditcore_documents/src/auditcore_documents/pipeline/stages/ingestion.py` – `libmagic_detector` (Z. 45)

**Unterschiede der Varianten:**

- Überschreitung: audit_designer wirft HTTP 413 mit deutscher Meldung; regulierung liefert `None` (Aufrufer entscheidet) – Chunkgröße jeweils 1 MiB.
- qaaudit: libmagic mit Signatur-Fallback, MIME-Familienvergleich Header/Endung – umfassendste Variante, aber ohne Größenlimit.

**Tests:** regulierung `_lies_begrenzt` 4 Testreferenzen, `_looks_like_pdf_bytes` 3; qaaudit ohne direkte Tests.

### 12. Objekt laden oder HTTP 404 (FastAPI) – Klasse b

**Ziel:** auditcore_common (web.get_or_404, generisch über Modellklasse)

**Fundstellen:**

- audit-portal: `backend/app/api/projects.py` – `_get_project_or_404` (Z. 32)
- audit-portal: `backend/app/api/documents.py` – `_get_document_or_404` (Z. 85)
- audit-portal: `backend/app/api/tenants.py` – `_get_tenant_or_404` (Z. 64)
- flowinvoice: `backend/app/api/mandanten.py` – `_get_or_404` (Z. 33)
- regulierung: `backend/app/api/kpang/vollzug.py` – `_vorgang_oder_404` (Z. 3768)
- flownavigator: `apps/backend/app/api/findings.py` – `get_audit_case_or_404` (Z. 35)
- audit_designer: `backend/app/api/qchess_reports/_common.py` – `_load_template_or_404` (Z. 427)

**Unterschiede der Varianten:**

- Gleiches Muster `select(Model).where(Model.id == id)` + `scalar_one_or_none()` + `HTTPException(404)`; Unterschiede nur im Meldungstext („Project … not found“, „Mandant '…' nicht gefunden“, „Vorgang nicht gefunden“) und im ID-Typ (str vs. UUID).
- graphify: audit_designer `_load_template_or_404` ist god node (10 Aufruferdateien), `get_project_or_404` 14.

**Tests:** indirekt über API-Tests.

### 13. Dateinamen säubern (Download/Export) – Klasse b

**Ziel:** auditcore_common (filenames.safe_filename mit Profil ascii oder unicode)

**Fundstellen:**

- audit_designer: `backend/app/modules/vp_ai/utils/filenames.py` – `sanitize_filename` (Z. 82)
- audit_designer: `backend/app/api/document_comparisons.py` – `_safe_filename` (Z. 115)
- audit_designer: `backend/app/api/vpai_notebook/jupyter.py` – `_safe_filename` (Z. 2222)
- audit_designer: `backend/app/services/presentation_export_service.py` – `_safe_filename` (Z. 315)
- audit-portal: `backend/app/api/vvt_templates.py` – `_safe_filename` (Z. 616)
- audit-portal: `backend/app/services/help_export_service.py` – `safe_filename` (Z. 207)
- regulierung: `backend/app/api/kpang/vollzug.py` – `_safe_filename_part` (Z. 1553)

**Unterschiede der Varianten:**

- Zeichensatz: Unicode inkl. Umlaute erhalten (audit_designer document_comparisons, sanitize_filename) vs. nur alnum→„_“ klein (audit-portal) vs. alnum/„-“ (regulierung).
- Länge: 255 / 200 (Stamm) / 80 / 48; Fallback-Namen „datei“, „vvt“, „tankstelle“, „download“.

**Tests:** audit_designer sanitize_filename getestet (2 Referenzen), übrige ohne.

### 14. Client-IP aus X-Forwarded-For – Klasse b

**Ziel:** auditcore_common (Modul web, optionales Extra fastapi/starlette)

**Fundstellen:**

- ai-router: `src/llm_router/admin/auth.py` – `client_ip` (Z. 151)
- cockpit: `src/cockpit/auth.py` – `client_ip` (Z. 126)
- audit_designer: `backend/app/api/auth.py` – `get_client_ip` (Z. 57)
- audit_designer: `backend/app/api/admin.py` – `get_client_ip` (Z. 49)

**Unterschiede der Varianten:**

- Fallback ohne Peer: `None` (ai-router, cockpit, audit_designer admin.py – trotz Annotation `-> str`) vs. "unknown" (audit_designer auth.py).
- Header-Schreibweise egal (Starlette case-insensitive); keine Variante prüft vertrauenswürdige Proxys (Spoofing-Risiko bei Rate-Limits).

**Tests:** keine direkten Tests.

### 15. Coroutine synchron ausführen (Celery/Thread) – Klasse b

**Ziel:** auditcore_common (asyncio.run_sync)

**Fundstellen:**

- audit_designer: `backend/app/modules/vp_ai/api/runs.py` – `_run_async_in_thread` (Z. 34)
- flowaudit: `backend/flowaudit/modules/module_converter/api/protocol.py` – `run_async` (Z. 21)
- flowinvoice: `backend/app/worker/tasks.py` – `run_async` (Z. 1297)
- flowinvoice: `backend/app/worker/pipeline_tasks.py` – `run_async` (Z. 77)

**Unterschiede der Varianten:**

- audit_designer und flowaudit exakt gleich (`get_event_loop()`, sonst neuer Loop) – unter Python ≥ 3.12 mit DeprecationWarning.
- flowinvoice (und Fork audit-portal) hält einen Loop je Thread und prüft die PID (fork-sicher für Celery-prefork) – diese Variante sollte die Referenz sein.
- flowaudit hat 4 identische Kopien in einem Repo.

**Tests:** keine direkten Tests.

### 16. LegalChunker (Gesetzestext in Artikel/Absätze zerlegen) – Klasse c

**Ziel:** Erweiterung auditcore_legal_sources (Modul chunking) – nicht auditcore_documents.article_law (das wendet Änderungsbefehle an)

**Fundstellen:**

- audit_designer: `backend/app/modules/vp_ai/services/legal_chunker.py` – `_split_into_articles` (Z. 438), `_split_into_paragraphs` (Z. 457)
- flowinvoice: `backend/app/services/legal_chunker.py` – `_split_into_articles` (Z. 286), `_split_into_paragraphs` (Z. 314)
- audit-portal: `backend/app/services/legal_chunker.py` – `_split_into_articles` (Z. 286), `_split_into_paragraphs` (Z. 314)

**Unterschiede der Varianten:**

- audit_designer-Fassung 789 Z. (weiterentwickelt), flowinvoice/audit-portal 560 Z. (identisch); Ähnlichkeit der Split-Funktionen 0,885.

**Tests:** audit_designer: LegalChunker in 2 Testdateien referenziert; flowinvoice/audit-portal ohne Tests.

### 17. MUS-Stichprobenumfang (flowstat sampling_service) – Klasse a

**Ziel:** auditcore_sampling 0.2.0 `portal_mus_size` / `flowstat_mus_size`

**Fundstellen:**

- audit_designer: `backend/app/modules/flowstat/services/sampling_service.py` – `_calculate_mus_sample_size` (Z. 237)
- audit-portal: `backend/app/modules/flowstat/services/sampling_service.py` – `_calculate_mus_sample_size` (Z. 240)

**Unterschiede der Varianten:**

- Ähnlichkeit 0,894 zu auditcore_sampling.portal_mus_size; die Bibliothek hält die App-Semantik bereits als Profil – reine Umstellung.

**Tests:** audit_designer 24 Testreferenzen, audit-portal 10.

### 18. Haversine/Entfernung und Punkt-im-Polygon – Klasse a

**Ziel:** auditcore_geo 0.2.0 (designer_register_entfernung_km, designer_company_haversine_m, flowsearch_calculate_distance_km, _designer_im_ring)

**Fundstellen:**

- audit_designer: `backend/app/core/shared/research/register/geocoding.py` – `_entfernung_km` (Z. 202), `_punkt_in_ring` (Z. 379)
- audit_designer: `company_records_distance.py` – `_haversine_m` (Z. 1104)
- wohnungsmonitor: `frankreich_gebiet.py` – `entfernung` (Z. 58)
- flowsearch: `backend/app/api/eu_beneficiaries.py` – `calculate_distance` (Z. 49)

**Unterschiede der Varianten:**

- wohnungsmonitor `entfernung` 0,991 ähnlich zu designer_register_entfernung_km (Erdradius 6371 km). flowsearch `calculate_distance` ist bereits auf auditcore_geo.grosskreis_km umgestellt (Vorbild).

**Tests:** keine App-Tests; auditcore_geo mit Charakterisierungstests.

### 19. Anteil/Quote in Prozent mit Nullschutz – Klasse b

**Ziel:** auditcore_common (numbers.share / percent)

**Fundstellen:**

- audit_designer: `backend/app/modules/ecohesion/community/metrics.py` – `_anteil` (Z. 60)
- flowinvoice: `backend/app/verwk/pipeline/datenqualitaet.py` – `_anteil` (Z. 89)
- riskanalysis: `backend/app/pipeline/datenqualitaet.py` – `_anteil` (Z. 64)
- regulierung: `backend/app/api/kpang/monitoring.py` – `_quote_pct` (Z. 123)

**Unterschiede der Varianten:**

- Rundung: 1 Nachkommastelle (audit_designer) vs. 2 (flowinvoice, riskanalysis, regulierung); Nenner ≤ 0 → 0.0 überall. Rechenreihenfolge teil*100/ganzes vs. teil/ganzes*100 kann in der letzten Binärstelle abweichen.

**Tests:** regulierung 7 Testreferenzen; übrige ohne.

### 20. Kira-Memory-Client und geschichtete .env-Konfiguration – Klasse c

**Ziel:** flowlib (memory.py) als gemeinsamer Ort – nicht auditcore (Infrastruktur, kein Prüfungsfachwissen)

**Fundstellen:**

- ai-router: `rag-tuner/src/kira_rag_tuner/config.py` – `_layered_env` (Z. 47), `_normalize_kira_url` (Z. 34)
- graphify-kira: `src/graphify_kira/config.py` – `_layered_env` (Z. 50), `_normalize_kira_url` (Z. 37)
- ai-router: `rag-tuner/src/kira_rag_tuner/kira_sync.py` – `_request` (Z. 217)
- graphify-kira: `src/graphify_kira/publisher.py` – `_request`
- flowlib: `python/flowlib/memory.py` – ganze Datei

**Unterschiede der Varianten:**

- `_layered_env` und `_normalize_kira_url` exakt gleich; flow-agent enthält zusätzlich vendorte Kopien beider Repos (services/ai-router, packages/graphify).
- HTTP `_request`: Ähnlichkeit 0,935 – beide mit retries=2 und Backoff; nur graphify-kira erkennt die 422-Blacklist-Ablehnung der Memory-API (Sentinel `_BLACKLISTED`).

**Tests:** _normalize_kira_url je 12 Testreferenzen.

### 21. python-docx-Tabellenformatierung (Zellschattierung, Ränder) – Klasse c

**Ziel:** Erweiterung auditcore_reporting (Modul docx) bzw. auditcore_documents.render_docx

**Fundstellen:**

- regulierung: `docs/kpang/render_documents.py` – `set_cell_shading` (Z. 55), `set_cell_margins` (Z. 64)
- riskanalysis: `backend/scripts/create_wibank_vermerk.py` – `shade` (Z. 17), `cell_margins` (Z. 26)

**Unterschiede der Varianten:**

- Gleicher OOXML-Code (w:shd, w:tcMar); einziger Unterschied sind die Standardränder (regulierung 70/80/70/80 dxa, riskanalysis 80/120/80/120 dxa).
- Liegt jeweils in Skripten, nicht im Anwendungscode – geringe Dringlichkeit.

**Tests:** keine.

## Empfehlung: Erweiterungen für auditcore_common

An den common-Agenten (Branch feat/auditcore-common). Jede Funktion mit Charakterisierungstests der App-Varianten und legacy-Profilen, wo die Varianten fachlich abweichen:

| Modul/Funktion | Inhalt |
|---|---|
| `numbers_de.parse_de_number` | Deutsche Zahlen parsen; Parameter `ambiguous_single_dot='thousands' oder 'decimal'`, `strip_currency`, `accept_us_format`, `missing_markers`; legacy-Aliase für audit_designer (thousands), regulierung (decimal), flowinvoice (US-Erkennung). |
| `format_de.format_number / format_eur / format_percent` | Deutsche Ausgabe mit `missing='–', 'k.A.' oder None`, `decimals`, `suffix=' €' oder ' EUR'`. |
| `numbers.as_float / as_decimal / share_percent` | Tolerante Koerzierung (optional NaN/inf → None) und Prozentanteil mit Nullschutz und `ndigits`. |
| `hashing.sha256_file / canonical_json_bytes / canonical_sha256` | Gestreamter Datei-Hash (1 MiB) und kanonischer JSON-Hash (sort_keys, ensure_ascii=False, kompakt) – ersetzt auch die ~9 fingerprint()-Kopien in auditcore; legacy-Varianten für hash_json (default=str) und make_params_hash. |
| `filenames.safe_filename` | Profile `unicode` (Umlaute erhalten, 255) und `ascii_slug` (alnum/_, Länge, Fallback). |
| `aio.run_sync` | Coroutine synchron ausführen, Loop je Thread mit PID-Prüfung (flowinvoice-Variante). |
| `web (Extra `fastapi`)` | client_ip (mit optionaler Proxy-Allowlist), get_or_404, read_upload_limited (413 oder None). |

## Vorschläge für neue Bibliotheken bzw. Erweiterungen

| Name | Zweck | Nutzer | Nutzen |
|---|---|---|---|
| auditcore_auth | JWT (PyJWT, zeitzonenbewusst, iat/exp, optional Refresh), Passwort-Hashing mit Profilen bcrypt und argon2 und Verifikation alter Hashes, CSRF-Cookie-Helfer (aus qaaudit). | audit_designer, flownavigator, flowsearch, qaaudit, versteigerung, regulierung, flowinvoice, audit-portal, flowlib (9) | Sicherheitsrelevanter Code einmal gepflegt; python-jose (unmaintained) und passlib (unmaintained, bcrypt-4.1-Shim) werden an einer Stelle ersetzt. |
| auditcore_identifiers | IBAN (Mod-97), BIC, USt-IdNr. DE/AT mit Prüfziffer, EU-Formatmuster, Steuer-ID (11 Ziffern), LEI (aus auditcore_entity_matching), Ergebnis mit Status MISSING/VALID/INVALID und deutscher Meldung; `legacy_flowinvoice`-Profil ohne Mod-97. | flowinvoice, audit-portal; intern auditcore_invoicesynth, auditcore_documents, auditcore_entity_matching | Beseitigt 4 Implementierungen, davon 2 in auditcore selbst; fachlich schärfere Prüfung (Prüfziffern) wird wählbar. |
| auditcore_llm_client | AI-Router-Client: RouterHealth (Circuit-Breaker, thread-sicher), Secret-Entpackung, Fehler-Redaktion, Health-Status für /api/health. | flowinvoice, audit_designer, audit-portal, cockpit | ~3 100 Zeilen fast gleicher Code in drei Apps; die Redaktion von Tokens in Fehlermeldungen fehlt heute in audit_designer. |
| Erweiterung auditcore_legal_sources (chunking) | LegalChunker (Artikel/Absatz-Zerlegung für RAG). | audit_designer, flowinvoice, audit-portal | Weiterentwickelte audit_designer-Fassung (789 Z.) wird Referenz. |
| Erweiterung auditcore_reporting (docx) | Zellschattierung/-ränder und weitere python-docx-Helfer. | regulierung, riskanalysis (Skripte), audit_designer word_cd | gering; erst bei weiterem Bedarf. |
| Upload-Modul (auditcore_common.web oder auditcore_documents) | Größenbegrenztes Lesen, MIME-Erkennung (libmagic + Signatur-Fallback aus qaaudit, looks_like_pdf aus auditcore_documents), Endungs-/Header-Konsistenz. | audit_designer, regulierung, qaaudit, versteigerung | Schutz gegen CWE-400 und MIME-Spoofing einheitlich. |

Nicht nach auditcore: Kira-Memory-Client und geschichtete .env-Konfiguration (ai-router/rag-tuner, graphify-kira, flow-agent) – das ist Infrastruktur; gemeinsamer Ort ist flowlib (`flowlib.memory` existiert bereits).

## Klasse (a): Apps, die vorhandene auditcore-Funktionen nachbauen

Maschinelle Liste (≥ 0,85). Treffer auf private auditcore-Funktionen (führender Unterstrich) oder mit fachfremden Namen (z. B. `validate_code` ↔ `_check_query`) sind reine Strukturähnlichkeit kurzer Funktionen und kein Umstellungsziel; maßgeblich sind die geprüften Gruppen oben.

| App | Funktion(en) in der App | auditcore-Funktion (Paket, Version) | Ähnlichkeit |
|---|---|---|---|
| audit-portal | `execute` | auditcore_documents 0.2.1: `execute` | 0.929 |
| audit-portal, audit_designer, cockpit, flowinvoice, regulierung, versteigerung | `_als_zahl`, `_decode_json`, `_float`, `_money_float`, `_safe_float`, `_to_float`, `_zahl` | auditcore_registry_sources 0.2.0: `_number` | 0.857 |
| audit-portal, audit_designer | `_snapshot_dict`, `get_step_config` | auditcore_registry_sources 0.2.0: `_text` | 0.877 |
| audit-portal, audit_designer, flowinvoice, riskanalysis | `_file_sha256`, `_sha256_file`, `_sha256`, `compute_hash`, `hash_file`, `sha256_file` | auditcore_documents 0.2.1: `hash_file`, auditcore_documents 0.2.1: `sha256_file`, auditcore_invoicesynth 0.1.0: `_sha256`, auditcore_invoicesynth 0.1.0: `sha256_file` | 0.903 |
| audit-portal, audit_designer, regulierung | `_canonical_reference_hash`, `_fingerprint`, `_spec_fingerprint`, `canonical_sha`, `hash_json`, `make_params_hash`, `registry_hash` | auditcore_dataprotection 0.4.1: `canonical_sha256`, auditcore_documents 0.2.1: `hash_json`, auditcore_entity_matching 0.2.1: `fingerprint`, auditcore_funding_sources 0.1.1: `fingerprint`, auditcore_ha | 0.884 |
| regulierung | `save` | auditcore_harvest 0.1.0: `save` | 0.905 |
| audit-portal | `_safe_text` | auditcore_registry_sources 0.2.0: `_text` | exakt |
| audit-portal, audit_designer | `_calculate_mus_sample_size`, `mus_sample_size` | auditcore_sampling 0.2.0: `portal_mus_size` | 0.894 |
| audit-portal, flowinvoice | `_to_list` | auditcore_registry_sources 0.2.0: `flowinvoice_to_list` | 0.935 |
| audit_designer, wohnungsmonitor | `_entfernung_km`, `entfernung` | auditcore_geo 0.2.0: `designer_register_entfernung_km` | 0.991 |
| audit-portal | `_to_date` | auditcore_funding_sources 0.1.1: `as_date` | 0.863 |
| audit-portal, audit_designer | `_datum`, `_iso_date` | auditcore_funding_sources 0.1.1: `harvest_date` | exakt |
| audit_designer | `content_hash` | auditcore_legal_sources 0.1.1: `content_hash` | exakt |
| audit-portal, audit_designer | `validate_code` | auditcore_registry_sources 0.2.0: `_check_query` | 0.931 |
| audit_designer | `_als_text` | auditcore_funding_sources 0.1.1: `stringify` | exakt |
| audit-portal, audit_designer | `_als_plz`, `_cell_to_str` | auditcore_funding_sources 0.1.1: `stringify_plz` | 0.881 |
| flowsearch | `_parse_amount` | auditcore_funding_sources 0.1.1: `parse_amount` | 0.901 |
| audit-portal | `parse_sanctions_csv` | auditcore_registry_sources 0.2.0: `portal_parse_sanctions_csv` | 0.895 |
| audit_designer | `_betrag`, `_to_decimal` | auditcore_funding_sources 0.1.1: `harvest_amount` | exakt |
| audit_designer | `_dekodiere` | auditcore_funding_sources 0.1.1: `_decode` | 0.87 |
| audit-portal | `enforce` | auditcore_documents 0.2.1: `enforce` | 0.95 |
| audit-portal | `_check_supplier_concentration` | auditcore_documents 0.2.1: `check_supplier_concentration` | 0.972 |
| audit_designer | `_als_float` | auditcore_funding_sources 0.1.1: `coerce_float` | 0.972 |
| audit_designer | `parse_satz` | auditcore_funding_sources 0.1.1: `parse_satz` | exakt |
| audit-portal | `validate_context` | auditcore_documents 0.2.1: `validate_context` | exakt |
| audit_designer | `parse_datum` | auditcore_funding_sources 0.1.1: `parse_datum` | 0.99 |
| audit-portal | `fail` | auditcore_documents 0.2.1: `fail` | 0.935 |
| audit_designer | `_extract_title` | auditcore_procurement 0.2.1: `_designer_title` | 0.935 |
| flowsearch | `_parse_location` | auditcore_funding_sources 0.1.1: `parse_location` | 0.974 |
| regulierung | `_bytes` | auditcore_dataprotection 0.4.1: `_to_bytes` | exakt |
| audit-portal | `_try_recovery` | auditcore_documents 0.2.1: `_try_recovery` | 0.857 |
| audit_designer | `_felder` | auditcore_funding_sources 0.1.1: `harvest_fields` | 0.955 |
| audit-portal | `complete` | auditcore_documents 0.2.1: `complete` | 0.923 |
| audit-portal | `_extract_position` | auditcore_registry_sources 0.2.0: `flowinvoice_extract_position` | exakt |
| flowlib | `get_number_format` | auditcore_reporting 0.2.0: `get_number_format` | exakt |
| audit-portal | `validate_extraction_quality` | auditcore_documents 0.2.1: `validate_extraction_quality` | exakt |
| audit-portal | `complete_stage` | auditcore_documents 0.2.1: `complete_stage` | 0.927 |
| audit_designer | `parse_date` | auditcore_funding_sources 0.1.1: `parse_date`, auditcore_funding_sources 0.1.1: `state_aid_parse_date` | exakt |
| audit_designer | `landeskennung` | auditcore_funding_sources 0.1.1: `country_code` | 0.983 |
| audit_designer | `_punkt_in_ring` | auditcore_geo 0.2.0: `_designer_im_ring`, auditcore_geo 0.2.0: `_register_im_ring` | 0.919 |
| audit_designer | `_normalisiere` | auditcore_funding_sources 0.1.1: `normalize_name` | exakt |
| audit-portal | `extract_vat_ids` | auditcore_registry_sources 0.2.0: `portal_vat_ids` | 0.977 |
| regulierung | `_json` | auditcore_risk 0.3.1: `plain` | 0.959 |
| audit_designer | `_beruecksichtige_geburtsdatum_und_land` | auditcore_registry_sources 0.2.0: `designer_dob_country`, auditcore_registry_sources 0.2.0: `workshop_dob_country` | 0.955 |
| audit-portal | `_join_ids` | auditcore_registry_sources 0.2.0: `_join` | 0.937 |
| audit-portal | `compute_chain_hash` | auditcore_documents 0.2.1: `compute_chain_hash` | 0.854 |
| audit_designer | `_haversine_m` | auditcore_geo 0.2.0: `designer_company_haversine_m`, auditcore_geo 0.2.0: `flowsearch_calculate_distance_km` | 0.884 |
| audit-portal | `strip_accents` | auditcore_entity_matching 0.2.1: `_strip_combining` | exakt |
| audit-portal | `_extract_fields` | auditcore_documents 0.2.1: `extract_fields` | 0.93 |
| audit_designer | `normalisiere_beguenstigtenname` | auditcore_funding_sources 0.1.1: `normalize_company_name_simple` | 0.984 |
| audit_designer | `_fuer_hash` | auditcore_funding_sources 0.1.1: `_for_hash` | exakt |
| audit_designer | `compute_record_hash` | auditcore_funding_sources 0.1.1: `compute_record_hash` | 0.944 |
| audit_designer | `_als_betrag` | auditcore_funding_sources 0.1.1: `as_amount` | 0.942 |
| audit_designer | `satz_hash` | auditcore_funding_sources 0.1.1: `record_hash` | 0.983 |
| audit_designer | `betrag_ist_spanne` | auditcore_funding_sources 0.1.1: `amount_is_range` | 0.96 |
| versteigerung | `parse_property_types` | auditcore_registry_sources 0.2.0: `split_multivalue` | 0.917 |
| audit_designer | `read_document` | auditcore_documents 0.2.1: `read_document` | exakt |

## Geschätzter Migrationsaufwand je App

PT = Personentage inkl. Charakterisierungstests; setzt voraus, dass auditcore_common/auditcore_auth/auditcore_identifiers bereitstehen.

| App | Aufwand | Schätzung | Umfang |
|---|---|---|---|
| audit_designer | hoch | 5–8 PT | Register-Helfer → auditcore_funding_sources/geo (verhaltensgleich über designer_-Namen), Hash/SHA/Fingerprint → common, security.py → auditcore_auth, AI-Router-Client, de_numbers → common (Mehrdeutigkeitsregel „Tausenderpunkt“ als Profil), 5 Dateinamen-Varianten. |
| audit-portal | hoch | 6–10 PT | Fork aus flowinvoice (978 Duplikatgruppen) und audit_designer/flowstat (630): Pipeline/Watchdog → auditcore_documents, Sanktionen/PEP/USt-IdNr. → auditcore_registry_sources, validators.py → auditcore_identifiers. Größter Hebel: Fork-Module durch Bibliotheken ersetzen statt parallel pflegen. |
| flowinvoice | mittel | 3–5 PT | validators.py (IBAN ohne Mod-97 → legacy-Profil), AI-Router-Client als Referenzimplementierung abgeben, _parse_german_number/_de/_eur → common, run_async (Referenz), LegalChunker. |
| regulierung | mittel | 2–3 PT | security.py (PyJWT/bcrypt) → auditcore_auth, _parse_german_number (Dezimalpunkt-Regel!) → common, Upload-Limit, get_or_404, make_params_hash (legacy-Hash), docx-Zellformat. |
| riskanalysis | niedrig–mittel | 1–2 PT | Kopie von flowinvoice/verwk (147 Gruppen) – Konsolidierung mit flowinvoice klären; _de/_eur/_anteil → common. |
| flownavigator | niedrig | 0,5–1 PT | security.py → auditcore_auth; get_or_404. |
| flowsearch | niedrig | 0,5–1 PT | security.py → auditcore_auth; Alt-Harvester v1 (_parse_amount/_parse_location) auf auditcore_funding_sources umstellen (v2 nutzt es bereits). |
| qaaudit | niedrig | 0,5–1 PT | security.py inkl. CSRF-Cookies → auditcore_auth (qaaudit liefert die Cookie/CSRF-Helfer), mime_check → Upload-Modul. |
| versteigerung | niedrig | 0,5 PT | security.py (argon2!) → auditcore_auth mit argon2-Profil; _to_float/_format_number_de → common. |
| cockpit | niedrig | 0,5–1 PT | client_ip → common; Admin-Code als Kopie aus ai-router (26 Gruppen) – bewusst oder konsolidieren. |
| ai-router | niedrig | 0,5 PT | client_ip → common; rag-tuner-Konfiguration/Kira-Client → flowlib. |
| graphify-kira | niedrig | 0,5 PT | _layered_env/_normalize_kira_url/KiraPublisher → flowlib. |
| flow-agent | niedrig | 0,5 PT | vendorte Kopien von ai-router und graphify-kira nachziehen bzw. als Abhängigkeit beziehen. |
| flowlib | niedrig | 1 PT | excel/formats.get_number_format ist wortgleich mit auditcore_reporting → dorthin verweisen; auth.py ist Kern von auditcore_auth. |
| flowaudit | niedrig | 0,5 PT | run_async (4 Kopien) → common; flowaudit_docker/ ist eine Volldublette des Backends. |
| wohnungsmonitor | niedrig | 0,25 PT | entfernung → auditcore_geo (nutzt auditcore_property_sources bereits). |
| kiraclaw | keiner | 0 PT | keine app-übergreifenden Duplikate gefunden. |
| vision-service | keiner | 0 PT | keine app-übergreifenden Duplikate gefunden. |

## Hilfsfunktions-Cluster je App (graphify)

God nodes = Funktionen mit den meisten Aufruferdateien (ohne Tests). Die Graphen wurden am 25.09. aus den Arbeitskopien erzeugt; bei audit-portal enthalten sie auch lokale worktrees/-Verzeichnisse.

- **audit_designer** (11123 Funktionsknoten): `require_flowstat_view()` (35), `require_flowstat_execute()` (28), `get_project_or_404()` (14), `_load_input_df()` (12), `assert_can_view()` (12)
- **flowinvoice** (2751 Funktionsknoten): `get_settings()` (26), `ensure_worker_running()` (7), `get_vectorstore()` (6), `prozent()` (4), `router_health()` (4)
- **riskanalysis** (359 Funktionsknoten): `plausibel_mask()` (3), `_auc()` (3), `resolve_mdb_path()` (2), `add_gj()` (2), `_name_match()` (2)
- **regulierung** (2065 Funktionsknoten): `get_settings()` (15), `lade_parameter()` (6), `berechne_nahwaerme_zeile()` (5), `berechne_wasser_zeile()` (5), `lade_musterfall()` (5)
- **audit-portal** (12956 Funktionsknoten): `get_settings()` (45), `_require_roles()` (13), `ensure_worker_running()` (9), `get_vectorstore()` (7), `run_async()` (6)
- **flowsearch** (276 Funktionsknoten): `get_password_hash()` (2), `._normalize_name()` (1), `._parse_amount()` (1), `._create_risk_matrix()` (1), `calculate_distance()` (1)
- **cockpit** (481 Funktionsknoten): `_secret_value()` (8), `client_ip()` (5), `letzter_stand()` (4), `_ziel()` (3), `normalisiere()` (2)
- **qaaudit** (120 Funktionsknoten): `require_iau_access()` (6), `hash_password()` (2), `_disposition()` (1), `_resolve_lang()` (1), `_load_json()` (1)
- **flowaudit** (1358 Funktionsknoten): `get_provider()` (2), `get_protocol_service()` (1), `run_async()` (1), `safe_jsonify()` (1), `get_db_connection()` (1)
- **flownavigator** (298 Funktionsknoten): `log_audit_event()` (3), `get_session_factory()` (3), `get_password_hash()` (2), `verify_password()` (2), `create_access_token()` (2)
- **flowlib** (32 Funktionsknoten): `._request()` (1), `safe_filename()` (1), `get_number_format()` (1), `auto_fit_columns()` (1), `.close()` (1)
- **versteigerung** (205 Funktionsknoten): `fix_text()` (5), `latest_market_value_amount()` (3), `next_auction_date()` (3), `last_auction_date()` (3), `termin_conditions()` (3)
- **wohnungsmonitor** (189 Funktionsknoten): `entfernung()` (3), `wbs_stufen()` (2), `hole()` (2), `schreibe()` (2), `pfad()` (1)
- **ai-router** (472 Funktionsknoten): `identify_app()` (6), `get_session_factory()` (6), `route_for_model()` (5), `proxy()` (3), `_extract_model_from_payload()` (3)
- **flow-agent** (944 Funktionsknoten): `identify_app()` (7), `route_for_model()` (6), `proxy()` (3), `normalize_http_base_url()` (3), `_extract_model_from_payload()` (3)
- **vision-service** (39 Funktionsknoten): `get_config()` (6), `resolve_device()` (3), `get_donut()` (2), `collect_backend_info()` (2), `_load_image()` (1)
- **kiraclaw** (295 Funktionsknoten): `_store()` (2), `_openclaw_client()` (2), `._connect()` (1), `_format_timestamp()` (1), `._get_json()` (1)
- **graphify-kira** (84 Funktionsknoten): `graph_json_path()` (4), `detect()` (3), `_graphify_exe()` (2), `_short_label()` (1), `_module_map()` (1)

## Themen-Cluster (Funktionsnamen, alle Apps, ohne Tests/Skripte/Vendor-Kopien)

| Thema | ai-router | audit-portal | audit_designer | auditcore | cockpit | flow-agent | flowaudit | flowinvoice | flowlib | flownavigator | flowsearch | graphify-kira | kiraclaw | qaaudit | regulierung | riskanalysis | versteigerung | vision-service | wohnungsmonitor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| auth_jwt_passwort | 8 | 34 | 49 |  | 6 | 1 | 7 | 25 | 4 | 10 | 6 |  | 2 | 9 | 14 |  | 5 | 1 |  |
| betrag_ust_geld |  | 37 | 26 | 52 |  |  | 2 | 24 |  |  | 3 |  |  |  | 7 | 1 | 4 |  | 1 |
| config_settings | 5 | 15 | 31 | 8 | 5 | 9 | 2 | 20 |  | 1 |  | 1 | 1 | 2 | 6 |  | 1 | 3 |  |
| datum_frist_kalender | 15 | 269 | 541 | 94 | 33 | 23 | 76 | 103 |  | 33 | 5 |  | 11 | 5 | 103 | 9 | 7 |  | 3 |
| db_session | 6 | 9 | 17 | 1 | 5 |  | 23 | 7 |  | 6 | 2 |  |  | 3 | 1 |  | 1 |  |  |
| deutsche_zahl_format | 3 | 10 | 59 | 2 | 1 | 3 | 1 | 21 |  |  | 2 |  | 1 |  | 7 | 4 | 1 |  | 1 |
| docx_office |  | 11 | 106 | 12 |  |  |  | 6 |  |  |  |  |  | 2 | 5 | 1 |  |  |  |
| email |  | 1 | 3 |  |  |  | 1 | 1 |  | 1 |  |  |  |  |  |  |  |  |  |
| excel_csv |  | 47 | 119 | 21 |  | 2 | 5 | 47 | 1 |  | 17 |  | 5 | 7 | 18 | 2 |  |  |  |
| geo_distanz |  | 3 | 17 | 17 |  |  |  | 3 |  |  | 8 |  |  |  | 1 |  | 3 |  | 2 |
| hash_checksumme |  | 15 | 39 | 29 |  | 1 |  | 3 |  |  |  |  |  |  | 9 | 3 |  |  |  |
| http_client_retry | 12 | 50 | 82 | 45 | 4 | 12 | 6 | 17 | 2 | 7 | 6 | 1 | 13 | 1 | 15 |  | 5 |  | 3 |
| iban_ustid_steuerid |  | 18 | 47 | 25 | 2 | 1 |  | 21 | 1 |  |  |  |  |  | 15 | 5 |  |  | 1 |
| json_serialisierung | 13 | 74 | 204 | 93 | 4 | 2 | 29 | 31 |  | 4 |  | 2 | 3 | 1 | 10 | 3 | 1 |  |  |
| llm_embedding | 25 | 101 | 162 | 1 | 1 | 11 | 7 | 57 |  | 10 |  | 1 |  |  | 18 |  |  |  |  |
| logging |  | 27 | 24 | 8 | 2 | 1 | 5 | 6 |  | 5 | 3 |  |  |  | 3 |  |  |  |  |
| namensabgleich_fuzzy | 2 | 28 | 56 | 24 | 1 | 2 | 20 | 15 |  | 7 | 4 |  |  |  | 4 | 5 |  |  | 1 |
| pagination |  |  |  | 2 |  |  | 3 |  |  |  |  |  |  |  |  | 1 |  |  |  |
| pdf |  | 29 | 149 | 16 |  |  | 3 | 21 |  |  | 3 |  |  | 1 | 20 |  | 3 |  |  |
| statistik_stichprobe |  | 39 | 52 | 26 | 2 | 2 | 1 | 16 |  |  |  |  |  |  | 4 | 2 |  |  | 1 |
| text_normalisierung | 6 | 59 | 108 | 56 | 2 | 5 | 3 | 20 |  |  | 3 | 2 | 3 |  | 6 | 3 | 3 |  | 5 |
| upload_datei_mime |  | 24 | 77 | 2 |  |  | 5 | 10 |  | 2 |  |  | 4 | 3 | 9 |  |  |  |  |
| xml_erechnung |  | 10 | 46 | 7 |  | 1 |  | 8 |  |  | 1 |  | 2 |  | 6 |  |  |  |  |

Namensbasierte Zählung; sie zeigt, wo Themen gehäuft auftreten, nicht, dass es sich um Duplikate handelt.

