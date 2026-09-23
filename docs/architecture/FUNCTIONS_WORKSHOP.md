# Funktionsübersicht Flowworkshop

Stand: 22. September 2026. Codequelle: `janpow77/flowworkshop`, Commit
[`a05bb2143bd96d5e981f9462f05b965e1658be36`](https://github.com/janpow77/flowworkshop/tree/a05bb2143bd96d5e981f9462f05b965e1658be36).

Dies ist eine statische Funktionsinventur des eingecheckten Codes, keine Aussage
über die Erreichbarkeit oder Funktionsfähigkeit der produktiven Anwendung.
Die Anwendung bleibt ein eigenständiges Repository. Bibliotheksnamen unten sind
Extraktionsziele bzw. Kandidaten, keine bereits fertiggestellten Bibliotheken.
Es werden ausschließlich Pfade, Symbolnamen und eigene Beschreibungen wiedergegeben,
keine privaten Quelltextauszüge, Personen-/Betriebsdaten oder Secrets.

## Umfang und Methode

Gelesen wurden README und Szenarienübersicht aus Git, die Routerregistrierung in
`auditworkshop/backend/main.py`, das Frontend-Routing in
`auditworkshop/frontend/src/App.tsx`, Dienstimplementierungen der Fachbereiche,
Testinventar und CI. Alle 33 Backend-Routermodule sowie 44 Servicemodule wurden
zusätzlich per Python-AST auf Modul-, Klassen- und Funktionsdefinitionen erfasst.
Gezählt wurden 282 Funktionen mit HTTP-Routerdekoratoren (keine Behauptung von
282 unterschiedlichen Laufzeit-URLs). Syntaxeinlesen dieser Module: ausgeführt.
Backend-/Frontend-/Integrations-/Live-Tests: **NOT_EXECUTED**.

Der lokale Checkout ist teilweise sparse; fehlende Dokumentdateien wurden mittels
`git show HEAD:<Pfad>` aus demselben Commit gelesen. Keine versionierte AGENTS.md
oder LICENSE/LICENCE-Datei wurde in diesem Repository gefunden. Öffentliche
Übernahme von Code und Daten benötigt daher eine gesonderte Rechteprüfung; die
frühere MIT-Freigabe der Dummy-/Rechnungskerne gilt hier nicht automatisch.

Alle folgenden Backendpfade sind relativ zu `auditworkshop/backend/`,
Frontendpfade relativ zu `auditworkshop/frontend/src/`.

## Fachliche und technische Funktionsgruppen

| Bereich | Nachgewiesene Funktion und Codebeleg | Tatsächliche Consumer / mögliche Auslagerung |
|---|---|---|
| Workshop-Szenarien | `routers/workshop.py`: `workshop_stream`, `parse_file`; sechs Szenarien für Dokumentenanalyse, Checklistenassistenz, RAG-Vergleich, Berichtsentwurf, Wissensupload und Begünstigtenanalyse. Neben LLM-Streaming existieren deterministische Direktantworten. | `pages/ScenarioPage.tsx`, `components/workshop/*`. Szenarien, Präsentation und didaktische Antworten bleiben Anwendung; Parser nach `auditcore_documents`, Berichtsausgabe nach `auditcore_reporting`. |
| Datei- und PDF-Analyse | `services/file_parser.py:extract`: PDF, XLSX/XLS/XLSM, DOCX/DOCM, HTML, RTF, TXT. `services/pdf_parser.py:extract` mit PDF-Text-/Layout-/OCR-Fallback; `services/pdf_vorhabenliste.py:lies_vorhabenliste` und `lies_tabelle` für strukturierte Listen. | Upload/Workshop/Wissensaufnahme; Kandidat `auditcore_documents` mit optionalen Office/PDF/OCR-Abhängigkeiten. Nicht nur ein PDF-Harvester. |
| Wissensdatenbank / RAG | `services/knowledge_service.py`: `ingest`, `search`, `rerank`, `get_chunks`, `reembed_all`; lokale PostgreSQL/pgvector-Basis. `router_knowledge_service.py` bindet zentrale Knowledge-API mit lokalem Fallback an. | `routers/knowledge.py`, Workshop und Assessment; `pages/KnowledgePage.tsx`, `KbResearchPage.tsx`. Provider-/Retrieval-Vertrag prüfen; kein automatisches neues KI-Gesamtpaket. |
| LLM-Betrieb und Nachvollziehbarkeit | `services/ollama_service.py:stream`, `check_ollama`, `warmup_gateway_model`; `llm_usage_context.py:record_call`, `collect`; Modell-/Routen-/Latenzstatistiken. | Workshop, Assessment, State-Aid-Zusammenfassung und Match-Verifikation; Gateway, Authentifizierung und Deployment bleiben Infrastruktur. |
| Projekte und ausgefüllte Prüflisten | `routers/projects.py` CRUD; `routers/checklists.py` Prüflisten, Fragen, Bulk-Anlage und CSV-Export; Modelle `project.py`, `checklist.py`. | `ProjectsPage`, `ProjectDetailPage`, `ChecklistPage`; reiner Prüflistenvertrag als zusätzlicher Kandidat, Projektverwaltung bleibt App. |
| KI-gestützte Prüfungsbemerkungen | `routers/assessment.py`: `assess_question`, `assess_all`, `accept_remark`, `reject_remark`, `edit_remark`; Evidence und Entscheidungsstatus werden gespeichert. | Fragen-/Checklistenworkflow; fachliches Ergebnis niemals durch LLM-Treffer ersetzen. Entkopplung nur mit menschlichem Review und Provenienz. |
| Checklisten-Designer | `routers/checklist_templates.py`: Baumknoten, Verschieben, Antwortsets/-optionen, Kategorien, Templates; Mitgliederrollen und Einladungen. | `ChecklistsPage`, `ChecklistDetailPage`, `components/checklist/TreeEditor.tsx`; Kandidat **gemeinsamer Checklisten-Kern**, Paketname noch festzulegen, gemeinsam mit audit_designer prüfen. |
| Checklisten-Kollaboration | `checklist_collab.py`, `services/checklist_events.py:ChecklistEventBroker`: Events, Sperren, Anwesenheit. `checklist_discussion.py`: Status, Kommentare, ungelesene Einträge, Referenzdokumente. | Designer-UI mit Presence/History/Discussion; Berechtigungen, Locks, DB und Streaming bleiben App-Adapter. Pure Status-/Konfliktverträge ggf. gemeinsamer Kern. |
| Historie, Versionen, Übersetzung | `checklist_history.py:restore_history`; `checklist_versions.py:compare_versions`, `freeze_version`, `restore_version`; `checklist_translate.py`. | `HistoryPanel`, `VersionsMenu`, `VersionDiffModal`; Snapshot-/Diffvertrag als Checklisten-Kandidat, Übersetzungsprovider separat. |
| Checklisten-Paketinterop und Exporte | `services/checklist_package_service.py:ChecklistPackageService`: Import/Validierung/Export, kanonische Abbildung des Workshop- und audit_designer-Formats mit ID-Neuzuordnung; `checklist_export_service.py` DOCX/XLSX/PDF und Diskussionsexport. | `checklist_package.py`, `checklist_export.py`, PackageImportDialog/PackageExportModal. **Konkreter repoübergreifender Wiederverwendungsbeleg**, nicht bloß Namensähnlichkeit. Formatvertrag im Checklisten-Kern, Rendering `auditcore_reporting`. |
| Tabellenimport und Analyse | `dataframe_service.py`: `ingest_dataframe`, `get_summary_stats`, `query_dataframe`, `analyze_beneficiary_records`, `build_beneficiary_analysis_answer`; speichert importierte Tabellen in PostgreSQL und erzeugt verdichteten LLM-Kontext. | `routers/dataframes.py`, `beneficiaries.py`, DataFramePage und BeneficiaryAnalyticsPanel. Reine Aggregate → `auditcore_statistics`; SQL-/Upload-/Quotenverwaltung bleibt App. |
| Begünstigten-/Transparenzlisten | `beneficiary_harvester.py:run_beneficiary_harvest`, `parse_xlsx_or_csv`, `validate_beneficiary_rows`, `compute_record_hash`; `transparenzlisten_links.py:finde_datei_link`, `finde_portalseite`. Smart/additiv, Full-Refresh und Force unterscheiden sich ausdrücklich. | CLI-Skripte, Scheduler, Admin-Quellenverwaltung und `routers/beneficiaries.py`. `auditcore_funding_sources` auf `auditcore_harvest`; DB-Sink injizieren, Force nicht unbemerkt zum Standard machen. |
| Beihilfe-/State-Aid-Daten | `state_aid_harvester.py`: `TamSession`, `parse_award_detail`, `run_harvest`; `state_aid_service.py`: Beträge/Datum/Firmenname/NUTS, Fuzzy-Suche und Kartenaggregate; `state_aid_validator.py:run_validation`. | `routers/state_aid.py`, StateAidRegisterPage, CLI und Scheduler; `auditcore_funding_sources`, technische Abrufbasis `auditcore_harvest`. Kein Nachweis eines eigenständigen De-minimis-Kumulierungsrechners in diesen Workshop-Diensten. |
| Beihilfe-Fragen und Statistiken | `state_aid_llm.py`: `parse_question`, `relax_filters`, `compute_stats`, `stream_summary`; UI StateAidAskPanel/SearchPanel/ResultsTable. | Beihilferecherche; reine statistische Bausteine prüfen, Suchfilterlockerung und fachliche Warnungen erhalten. Nicht jede Zusammenfassung ist eine belastbare Prüfentscheidung. |
| Sanktionslisten | `sanctions_service.py`: `SanctionsListIndex`, `MultiSanctionsService`, `normalize_name`, `load_from_csv_to_db`; fünf Profile EU FSF, UN, OFAC SDN, UK FCDO/OFSI, CH SECO über OpenSanctions-CSV. Aktive/entfernte Datensätze, Quellenstatus und Export vorhanden. | `routers/sanctions.py`, SanktionslistenPage, Scheduler und Audit-Report. Adapter → `auditcore_registry_sources`, Namensvergleich → `auditcore_entity_matching`. Quell-/Datenlizenzen separat prüfen. |
| Unternehmensregister / Konzernbeziehungen | `corporate_registry.py`: `CorporateEntity`, `CorporateGroup`, `lookup_corporate_group_cached`; GLEIF- und Wikidata-Abfragen mit Quellenständen und Coverage-Hinweisen. `routers/reference_data.py` importiert zusätzliche Registertabellen. | Unternehmenssuche, Beihilfedossier und Audit-Report. `auditcore_registry_sources` mit optionalen Quellenadaptern; Cache und Session bleiben Ports. |
| Entitätenauflösung / semantische Suche | `entity_resolution.py`: `is_valid_lei`, `resolve_entity`, `link_record`, Rebuild für Beihilfen/Begünstigte/Sanktionen; `entity_embeddings.py`: Embeddingtext, Index, Suche; `entity_match_llm_verifier.py:run_batch_verification`. | `routers/entities.py` mit manueller Bestätigung/Ablehnung, `routers/embeddings.py`, EntityResolutionPanel. Deterministische Normalisierung/Matching → `auditcore_entity_matching`; Embeddings/LLM als optionale Provider, Schwellen nicht fachlich vereinheitlichen. |
| Quellenübergreifender Prüfbericht | `state_aid_audit_report.py:build_audit_report`, strukturierte Sections für Beihilfe/Begünstigte/Sanktionen/Konzern/Personen/Coverage und CrossReferences; `audit_match_verifier.py:verify_cross_references`; PDF, Karte und Audit-Log. | StateAidAuditReportPage, AuditReportPreview, AuditReportTrailPage. Rendering → `auditcore_reporting`; fachliche Dossierzusammenstellung zunächst App-Orchestrierung, keine automatische rechtliche Schlussfolgerung aus Treffern. |
| Geo und Karten | `geocoding_service.py`: PLZ/Stadt/NUTS, Spaltenerkennung, `geocode_single`, `get_beneficiary_map_data`; `country_profiles.py` DE/AT-Profile; `state_aid_audit_map.py:render_audit_map`. | BeneficiaryMap/StateAidMap, Choroplethen, Berichts-PDF. `auditcore_geo` für Koordinaten-/Regionsmodelle und Adapter; Leaflet-UI bleibt App. |
| Allgemeine Excel-Berichte | `services/excel_export.py`: `write_data_sheet`, `write_notes_sheet`, `make_xlsx`, `make_xlsx_multi_sheet`. | Beihilfe-/Sanktions-/Begünstigtenexport und weitere Router. Abgleich mit existierendem `auditcore_reporting` statt zweitem Workbookpaket; Response-Header bleiben Webadapter. |
| Sicherheitsprüfung von Webzielen | `services/security_scan/engine.py:perform_scan`; HTTP-/Port-/TLS-/Versions-CVE-Prüfer, `target_validation.py:validate_public_host`, `validate_public_url`, Bericht/PDF/Architekturbild und externer Screenshotdienst. | `routers/security_scan.py`, SecurityCheckPage, `auditworkshop/security-screenshot/server.py`. Eigenständiges Tool/Provider-Kandidat; nicht in Fachharvester oder allgemeinen HTTP-Helfer aufgehen lassen. SSRF-/Ziel-/Berechtigungsgrenzen müssen erhalten bleiben. Keine aktiven Scans ausgeführt. |
| Veranstaltung / Community | `routers/event.py`: Agenda/Timer/Phasen, Registrierung, Themen/Votes, Vorstellungsrunde, Einladungen, Anhänge; `forum.py`: Kategorien/Threads/Posts, Reaktionen, Moderation, Lösung markieren. | Agenda-, Register-, Forum-, Thread-, Vorstellungsrunde- und Archivseiten. Anwendungsspezifisch; kein Bedarf für ein neues Fachpaket allein aufgrund vorhandener CRUD-Funktionen. |
| Dokumentablage / Benachrichtigung / Mail | `routers/docs.py`: Ordner, Upload/Download, Dateiversionen, Nutzung; `notifications.py`; `mail_templates.py` und `services/email_service.py`. | DocumentsPage, NotificationBell, AdminMailTemplatesPanel. Speicher-/Mailprovider ggf. bestehend wiederverwenden; ACL/Quoten/Versionsführung nicht entfernen. |
| Benutzer und Betrieb | `routers/auth.py`: Session-/QR-/Passwortlogin, Signup/Freigabe/Sperre/Rollen/Reset/Einladungen, Audit-Log; `admin_access.py`: Zugriffe und LLM-Metriken; `automation.py`, `scheduler.py`, `system.py`, Health/Logging und Migrationen. | Account/Login/Admin/HarvestMonitoring; bleibt App-/Betriebsadapter. Wiederverwendbare Beobachtbarkeit separat anhand bestehender Plattform prüfen. |
| Demo, statische Inhalte, Betriebsskripte | `routers/demo_data.py` Seed/Reset und `documents.py` Demo-Dokumente; AiActPage ist ein statisches Merkblatt, kein implementierter Rechts-/Risikorechner. Compose/Docker, Backup/Restore, Lifecycle, Smoke- und Seed-Skripte vorhanden. | Workshop-Demonstration und Deployment. Kein Beleg eines `auditcore_dataprotection`-Rechenkerns oder eines eigenständigen AI-Act-Prüfmoduls aus dieser UI. |

## Konkrete Prioritäten für Wiederverwendung

1. **Checklisten-Paketvertrag:** Der Dienst benennt und behandelt bereits die
   unterschiedlichen Hierarchien und Antwortsets von Workshop und audit_designer.
   Vor Extraktion beide Richtungen mit realen, freigegebenen Fixtures
   charakterisieren; Rollen-/Versionsschutz bleiben erhalten.
2. **Funding + gemeinsamer Harvest-Kern:** TAM und Transparenzlisten sind echte
   unterschiedliche Quellenabläufe. Paging, Retry, Status und Provenienz können
   gemeinsame Ports nutzen; Update-/Löschsemantik je Quelle dokumentieren.
3. **Entity-Matching + Register/Sanktionen:** Pure Normalisierung und LEI-Prüfung
   von ORM, Remote-Zugriff und LLM-Verifikation trennen. Score ist ein Hinweis,
   keine Wahrscheinlichkeit oder rechtlich bestätigte Identität.
4. **Dokumente/Reporting/Geo:** Bestehende Pakete erweitern; Rendering nicht erneut
   als konkurrierende Bibliothek bauen. Länderprofile und Datenrechte prüfen.
5. **Security-Scanner und RAG:** Erst die existierenden Dienste/Provider abgleichen.
   Kein zusätzliches Paket ohne abgegrenzten Vertrag und zweiten belegten Consumer.

TED/HAD und andere Vergabebekanntmachungen gehören gemäß Benutzerentscheidung
zu `auditcore_procurement`, auch wenn zukünftig die Workshop-Oberfläche sie nutzt.
Diese Inventur belegt keinen eigenständigen TED-/HAD-Adapter in Flowworkshop.
Ebenso wird der De-minimis-Kern aus audit_designer nicht allein wegen gemeinsamer
State-Aid-Oberflächen als bereits hier vorhanden ausgegeben.

## Tests, Vertrauensgrenzen und offene Prüfung

32 Backend-Testdateien sind vorhanden, darunter Harvest/State Aid, Sanktionen,
Matching/Embeddings, Checklistenpakete, Security-Zielvalidierung, Auth, Wissen und
Projekte. Zehn Playwright-`*.spec.ts`-Dateien decken als vorhandene Testdefinitionen
Navigation, Agenda, Registrierung, Checklisten, Szenarien, Wissen, Tabellen,
Administration, Unternehmenssuche und AI-Act-Seite ab. Es gibt außerdem fünf
Frontend-`*.test.tsx`-Dateien. **Keiner dieser Tests wurde für diese Inventur ausgeführt.**
Die gelesene `.github/workflows/ci.yaml` definiert Frontend-Tests/TypeScript/ESLint/
Build, Backend-Ruff und Docker-Builds; sie führt nicht selbst die Backend-pytests
oder Playwright-End-to-End-Suite aus. Vorhandene Tests sind kein aktueller PASS-Nachweis.

Die zentrale RAG-Anbindung filtert markierte interne Vorgänge und besitzt lokalen
Fallback. Dies ist eine vorhandene Kontrollabsicht im Code, keine vollständige
Berechtigungsprüfung: Verhalten bei fehlender Klassifikation, alternative
Datenpfade und Isolation des lokalen Index müssen vor Extraktion gezielt geprüft
werden. Auch SSRF-Prüfer, Session-/Rollenfunktionen und Versionssperren wurden nur
statisch erfasst, nicht als sicher oder vollständig zertifiziert.

Nicht durchgeführt: produktive UI-Durchläufe, Datenbank-/Migrationstests, echter
Quellenharvest, aktive Netzwerkscans, Vergleich aller LLM-Ausgaben, vollständige
fachliche Bewertung jedes Templates, Sichtung personenbezogener Daten, Audit aller
Dateiformate und Fehlerzweige oder Lizenzfreigabe. KIRA/RAG- und Graphify-Abfragen
werden im übergeordneten Inventurbericht gesondert mit Status dokumentiert;
diese Workshop-Datei behauptet keinen eigenen Toolaufruf dieser Dienste.

## Vollständigkeitsregister der Backend-Router

Dieses Register verhindert, dass ein vorhandenes Routermodul allein wegen fehlender
Bibliothekswürdigkeit aus der Übersicht verschwindet. Es ist eine statische
Oberflächenabdeckung, keine vollständige Verifikation aller Geschäftsregeln.

| Routermodul | Erfasste öffentliche Funktionen und Modelle |
|---|---|
| `routers/admin_access.py` | `access_summary`, `access_timeseries`, `access_top_paths`, `access_top_users`, `access_recent`, `llm_summary`, `llm_by_model`, `llm_by_route`, `llm_latency_buckets`, `llm_recent`, `access_stats_state_aid` |
| `routers/assessment.py` | `AssessmentRemarkPayload`, `assess_question`, `assess_all`, `accept_remark`, `reject_remark`, `edit_remark` |
| `routers/auth.py` | `LoginRequest`, `LoginResponse`, `QrLoginRequest`, `PasswordChangeRequest`, `AccountOut`, `GeneratedPasswordOut`, `require_session`, `require_moderator`, `require_moderator_or_worker`, `require_admin`, `login`, `qr_login`, `get_me`, `logout`, `get_account`, `update_password`, `generate_password`, `rotate_qr_secret`, `list_sessions`, `log_action`, `get_audit_log`, `SignupRequest`, `SignupResponse`, `signup`, `UserListEntry`, `UserListResponse`, `admin_list_users`, `UserActionResponse`, `admin_approve_user`, `UserRejectRequest`, `admin_reject_user`, `admin_suspend_user`, `RoleChangeRequest`, `admin_change_role`, `ResetTokenResponse`, `admin_create_reset_token`, `InviteResponse`, `admin_send_invite`, `SetupPasswordRequest`, `setup_password` |
| `routers/automation.py` | `harvest_monitoring`, `list_harvest_runs`, `trigger_harvest`, `list_sanctions_runs`, `trigger_sanctions`, `llm_stats`, `llm_logs` |
| `routers/beneficiaries.py` | `invalidate_map_cache`, `get_cached_map_payload`, `warm_map_cache`, `list_countries`, `upload_beneficiary_list`, `list_sources`, `get_map_data`, `beneficiaries_summary`, `search_beneficiaries`, `analyze_beneficiaries`, `get_nuts_regions`, `get_nuts_geojson`, `get_choropleth`, `delete_source`, `export_beneficiaries` |
| `routers/beneficiaries_sources.py` | `BeneficiarySourceConfigIn`, `BeneficiarySourceConfigUpdate`, `list_sources`, `get_source`, `create_source`, `update_source`, `delete_source`, `test_run_source`, `harvest_source`, `list_runs` |
| `routers/checklist_collab.py` | `stream_events`, `acquire_lock`, `release_lock`, `list_locks`, `list_presence` |
| `routers/checklist_discussion.py` | `NodeStatusUpdate`, `NodeStatusOut`, `CommentCreate`, `CommentUpdate`, `CommentOut`, `RefDocCreate`, `RefDocOut`, `set_node_status`, `list_comments`, `create_comment`, `edit_comment`, `delete_comment`, `unread_counts`, `mark_read`, `list_refdocs`, `create_refdoc`, `delete_refdoc` |
| `routers/checklist_export.py` | `export_word`, `export_excel`, `export_pdf`, `export_discussion`, `download_source_document` |
| `routers/checklist_history.py` | `HistoryEntryOut`, `HistoryDetailOut`, `RestoreRequest`, `RestoreResult`, `get_template_history`, `get_node_history`, `get_history_detail`, `restore_history` |
| `routers/checklist_package.py` | `export_package`, `validate_package`, `import_package` |
| `routers/checklist_templates.py` | `create_template`, `list_templates`, `list_global_answer_sets`, `create_global_answer_set`, `get_template`, `update_template`, `delete_template`, `list_members`, `update_member_role`, `remove_member`, `list_invites`, `create_invite`, `revoke_invite`, `accept_invite`, `decline_invite`, `get_tree`, `list_nodes`, `create_node`, `update_node`, `delete_node`, `move_node`, `list_template_answer_sets`, `create_template_answer_set`, `update_answer_set`, `delete_answer_set`, `add_answer_option`, `update_answer_option`, `delete_answer_option`, `list_categories`, `create_category`, `update_category`, `delete_category` |
| `routers/checklist_translate.py` | `TranslateRequest`, `TranslatedNodeOut`, `TranslateResultOut`, `translate_template_nodes`, `translate_single_node` |
| `routers/checklist_versions.py` | `VersionCreate`, `VersionListItem`, `VersionDetail`, `CompareNodeBrief`, `CompareChangedNode`, `CompareVersionInfo`, `CompareSummary`, `CompareResult`, `list_versions`, `compare_versions`, `get_version`, `create_version`, `freeze_version`, `RestoreResult`, `restore_version` |
| `routers/checklists.py` | `create_checklist`, `list_checklists`, `get_checklist`, `update_checklist`, `delete_checklist`, `add_question`, `add_questions_bulk`, `list_questions`, `get_question`, `update_question`, `delete_question`, `export_csv` |
| `routers/dataframes.py` | `list_tables`, `ingest`, `table_info`, `table_summary`, `query_table`, `delete_table` |
| `routers/demo_data.py` | `list_templates`, `seed_demo_data`, `reset_demo_data` |
| `routers/docs.py` | `FolderOut`, `FileOut`, `VersionOut`, `list_folders`, `list_files`, `upload_file`, `download_file`, `delete_file`, `list_versions`, `system_usage`, `create_folder` |
| `routers/documents.py` | `list_demos`, `get_demo` |
| `routers/embeddings.py` | `embeddings_search`, `embeddings_stats`, `embeddings_rebuild` |
| `routers/entities.py` | `EntitySearchHit`, `EntityMatchInfo`, `EntityDetail`, `search_entities`, `get_entity`, `confirm_match`, `reject_match`, `admin_rebuild`, `LlmVerifyBatchRequest`, `admin_llm_verify_batch`, `admin_llm_runs` |
| `routers/event.py` | `MetaOut`, `PhaseChange`, `MetaUpdate`, `AgendaItemOut`, `AgendaItemCreate`, `AgendaItemUpdate`, `RegistrationCreate`, `InviteOut`, `TopicCreate`, `TopicOut`, `AgendaForumPostCreate`, `AgendaForumPostOut`, `AgendaForumThreadOut`, `AgendaForumSummaryEntry`, `AgendaForumSummaryOut`, `IcebreakerOut`, `IcebreakerCreate`, `IcebreakerUpdate`, `AdminAuth`, `get_meta`, `get_agenda`, `get_agenda_by_days`, `get_invite`, `register`, `upload_attachment`, `submit_topic`, `list_topics`, `vote_topic`, `get_forum_summary`, `get_agenda_forum`, `get_agenda_material`, `AgendaMaterialUpdate`, `update_agenda_material`, `create_agenda_forum_post`, `delete_agenda_forum_post`, `admin_auth`, `MailTestRequest`, `admin_mail_test`, `update_meta`, `update_phase`, `create_agenda_item`, `reorder_agenda`, `update_agenda_item`, `delete_agenda_item`, `toggle_visible`, `set_agenda_status`, `start_agenda_item`, `reset_timer`, `adjust_time`, `reset_agenda_status`, `list_registrations`, `generate_invites`, `list_all_topics`, `get_icebreaker`, `create_icebreaker`, `update_icebreaker`, `delete_icebreaker`, `reorder_icebreaker` |
| `routers/forum.py` | `CategoryOut`, `ThreadSummary`, `PostOut`, `ThreadDetailOut`, `CreateThread`, `CreatePost`, `list_categories`, `list_threads`, `get_thread`, `create_thread`, `create_post`, `pin_thread`, `lock_thread`, `mark_solution`, `toggle_reaction`, `edit_post`, `delete_post` |
| `routers/knowledge.py` | `KbGenerateRequest`, `get_groups`, `get_stats`, `search`, `generate`, `ingest_document`, `get_source_chunks`, `delete_source` |
| `routers/mail_templates.py` | `TemplateListEntry`, `TemplateDetail`, `TemplateUpdate`, `TemplatePreviewRequest`, `TemplatePreviewResponse`, `list_templates`, `get_template`, `update_template`, `preview_template`, `reset_template`, `seed_default_templates` |
| `routers/notifications.py` | `push_notification`, `list_notifications`, `mark_read`, `mark_all_read` |
| `routers/projects.py` | `create_project`, `list_projects`, `get_project`, `update_project`, `delete_project` |
| `routers/reference_data.py` | `import_reference_data`, `list_reference_sources`, `search_reference_data`, `delete_reference_source` |
| `routers/sanctions.py` | `ListEntry`, `SanctionsListResponse`, `SanctionsSourceStatus`, `SanctionsSourcesResponse`, `SearchHitOut`, `SearchResponse`, `get_lists`, `get_sources`, `get_method`, `get_stats`, `search_get`, `export_sanctions_search`, `refresh` |
| `routers/security_scan.py` | `ScanRequest`, `start_scan`, `scan_status`, `scan_report`, `scan_pdf`, `scan_screenshot`, `scan_architecture` |
| `routers/state_aid.py` | `HarvestRequest`, `get_status`, `get_validation_last`, `post_validation_run`, `list_sources`, `search`, `get_award`, `get_map`, `get_stats`, `export_stats`, `company_dossier`, `export_awards`, `admin_harvest`, `AskRequest`, `ask`, `PersonInput`, `AuditReportPdfRequest`, `get_audit_report_json`, `get_corporate_group`, `post_audit_report_pdf`, `get_audit_report_log`, `export_audit_report_log`, `admin_delete_source_awards` |
| `routers/system.py` | `get_gpu`, `get_info`, `get_ollama_status`, `get_profile` |
| `routers/workshop.py` | `StreamRequest`, `workshop_stream`, `parse_file`, `supported_formats` |
