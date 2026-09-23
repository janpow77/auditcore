# Funktionsübersicht Audit-Designer, FlowStat und FlowAudit-MCP

Stand: 22. September 2026. Diese Übersicht beschreibt vorhandenen Quellcode und mögliche Bibliotheksgrenzen, nicht bereits ausgelieferte neue Pakete.

## Quellen und Analysetiefe

| Repository | Untersuchte Revision | Getrackte Dateien | Python-Dateien |
|---|---|---:|---:|
| `janpow77/audit_designer` | `030a71e083ef0feddc14545b095a4945bc0bbd7a` | 5483 | 2123 |
| `janpow77/flowstat` | `d665ac221f50ba1f465b7337bdd4aa218d78ec8a` | 561 | 134 |

Sämtliche getrackten Python-Dateien wurden statisch geparst; Router, Services, öffentliche Symbole, Modulbereiche und MCP-Registrierungen wurden erfasst. Repräsentative Implementierungen und Aufrufer wurden zusätzlich gelesen. **Das ist keine vollständige fachliche Prüfung jeder Funktion und kein Laufzeittest.** Frontend-, Rust-, R-, VBA-, Notebook- und Office-Artefakte sind nicht mit einer vollständigen semantischen Prüfung abgedeckt. Die folgenden Anhänge verhindern, dass nicht vertieft gelesene Services unsichtbar werden. Es wurden keine fremden Anwendungen gestartet, keine MCP-Fachtools ausgeführt, keine VBA-Module geändert und keine privaten Quelltexte übernommen.

Die Designer-Dateien ließen sich vollständig als Python parsen. In FlowStat bleibt `backend/tests/fix_tests.py:69` syntaktisch ungültig. Das ist ein vorhandenes Test-Reparaturskript; aus diesem Befund folgt weder, dass alle Anwendungstests fehlschlagen, noch dass sie bestehen. Tests dieser Repositories: `NOT_EXECUTED`.

Die lokale Prüfung ist auf diese SHAs festgelegt. GitHub-Fortschreibungen, KIRA/RAG und Graphify werden im übergeordneten Inventar getrennt ausgewiesen; dieser Teilbericht behauptet keine selbst durchgeführten RAG- oder Graphify-Abfragen.

## Fachliche Landkarte

Pfade in dieser Tabelle sind relativ zu `audit_designer/backend/app`, soweit nicht anders angegeben. Kandidaten sind keine automatische Freigabe zur Veröffentlichung; Rechteprüfung und Characterization bleiben Voraussetzung.

| Funktionsgruppe | Implementierung und nachvollziehbarer Consumer | Bibliotheksgrenze / Verbleib |
|---|---|---|
| Prüflisten und Prüfstrategie | `services/tree_service.py`, `validation_service.py`, `bulk_edit_service.py`, `pruefstrategie_export_service.py`; Consumer `api/nodes.py`, `api/bulk_edit.py`, `api/strategy_documents.py` | Reine Baum-/Validierungsregeln Kandidaten; Projektverwaltung, Historie, Berechtigungen bleiben Anwendung. Kein pauschales Utils-Paket. |
| QChess-Import und Berichte | `services/qchess_checkliste_import.py`, `services/qchess_report/` mit DOCM-Parser, SQL-Generator, Antwort-/Textbaustein-/Wordexport; Consumer `api/qchess_reports.py` | Parser in `auditcore_documents`, Ausgabe in `auditcore_reporting`; QChess-Datenbank-/Access-Integration als Adapter. |
| Signierte QChess-Pakete | `services/qchess_paket/` mit Manifest, Kanonisierung, Signatur, Ledger, Validierung, Anwendung/DB-Write; Consumer `api/paket.py` | Format-/Prüfkern prüfen; DB-Write, Schlüsselbetrieb und Zielautorisierung nicht in fachfremde Bibliothek verschieben. |
| PDF, DOCX, Präsentationen | `services/pdf_tools_service.py`, `pdf_editor_service.py`, `pdf_converter_service.py`, `docx_import_service.py`, `docx_export_service.py`, `presentation_export_service.py`, `word_cd/`; gleichnamige API-Consumer | `auditcore_documents` für Verarbeitung, `auditcore_reporting` für Renderer; externe OCR-/Office-/Konverterprozesse bleiben explizite optionale Adapter. |
| Dokumentvergleich und Gesetzessynopse | `modules/document_compare/{service,parsing,matching,article_law,rendering}.py`; Consumer `api/document_comparisons.py`, Modul-CLI und `modules/ecohesion/comparisons/worker.py` | Sehr konkreter Kandidat für `auditcore_documents`; bereits eigene Facade ohne Web-/DB-Importe, optionale KI-Begründung getrennt. Mehrere Einstiegspunkte sind belegt. |
| Belegprüfung und Vorhabenprüfung | `modules/vp_ai/services/{calculation_service,ausgabenbilanz_service,beleg_ai_validator,rule_validation_service,answer_validation_service,scorecard_service,feststellung_service,auflage_service}.py`; Consumer VP-AI-API | Berechnungen, Abgleich und fachliche Profile einzeln `auditcore_risk`/Fachpaketen zuordnen; Vieraugen-/Freigabe-/Journal-/Projektlogik bleibt Anwendung. |
| Rechts- und Prüfquellen | `modules/vp_ai/harvester/` inklusive Basis, Scheduler, DIP, EUR-Lex, CURIA, OLAF, ECA, Landesrechnungshöfe, Hessenrecht; Consumer Harvest-Tasks/Queue/Staging | `auditcore_harvest` technischer Kern; Quellenadapter `auditcore_legal_sources`. Fachliche Förderperioden-/Relevanzfilter nicht unbemerkt allgemeiner Harvesterstandard. |
| TED/HAD und Vergaben | Recherchekatalog/Provider unter `core/shared/research/`; konkrete Bekanntmachungsquellen repositoryübergreifend abgleichen | Verbindliches Ziel `auditcore_procurement`; keine Zuordnung nach `auditcore_legal_sources`. Vorhandener Katalogeintrag allein beweist keinen funktionsfähigen Abrufadapter. |
| State Aid und Begünstigte | `core/shared/research/register/{state_aid,beneficiaries}.py`, Modelle und `modules/vp_ai/harvester/state_aid.py`; Registry und ECOHESION-Recherchedienst als Consumer | `auditcore_funding_sources` über `auditcore_harvest`; State-Aid-/Begünstigtenbestände getrennt modellieren. |
| De-minimis-Register und Kumulierung | `core/shared/research/register/de_minimis.py`: `EAidRegisterClient`, `DeMinimisRegisterProvider`, `DeMinimisCumulationProvider`, `berechne_kumulierung`; dazu `_ernte.py`, `_zuordnung.py`; Registry ruft Provider auf | `auditcore_funding_sources` mit getrenntem deterministischem Berechnungsmodul. Code behandelt fehlende Daten als offene Fälle und stellt keine frei verfügbare Förderreserve fest. Diese Semantik charakterisieren; Schwellen/Zeiträume versionierte Profile, keine ungeprüfte allgemeine Rechtsregel. |
| Sanktionen, Unternehmen, Geocoding | `core/shared/research/register/{sanctions,entities,dedupe,geocoding}.py`; Recherche-Registry/ECOHESION und VP-AI-Unternehmensdienste | `auditcore_registry_sources`, `auditcore_entity_matching`, `auditcore_geo`; Quellenstand, Trefferunsicherheit und False Positives bleiben sichtbar. |
| Statistik und Stichproben | Eigenständiges FlowStat `backend/app/services/{analysis_core_service,sampling_service}.py`; Consumer `api/routes/{analysis,sampling}.py`; umfangreichere Varianten im Designer-FlowStat | `auditcore_statistics` + `auditcore_sampling`. Beide Varianten vor Übernahme differenziell charakterisieren; gleicher Dateiname ist kein Gleichheitsbeweis. |
| Datenqualität, Transformation, Matching | Designer-FlowStat `data_manipulation_service`, `field_statistics_service`, `data_quality_contract_service`, `fuzzy_match_service`, `match_compare_service`, `semantic_roles`; API und Pipeline-Handler als Consumer | Statistische Profile in statistics, Entitätenabgleich in entity_matching; eigene Datenqualitätsbibliothek erst nach Vertrags-/Consumervergleich beschließen. |
| Prognose, ML, AutoML | Designer-FlowStat `forecast_service`, `automl_forecast_service`, `ml_service`, `automl_service`, `explainability_service`, `model_registry_service`; zugehörige APIs/Handler | Kandidaten, kein Beschluss eines universellen KI-Pakets. Deterministische Auswertung von Modellregistrierung, Training, Rechenressourcen und Freigabe trennen; schwere Abhängigkeiten optional. |
| BPMN, Personal- und ESI-Bewertung | Beide FlowStat-Varianten `bpmn_analyzer`, `bpmn_export`, `esi_analysis_service`; APIs `bpmn`, `personnel_costs`, `core_requirements` | Rechenkern und Parser mögliche Fachmodule; Tariftabellen, Kriterienfassungen, Rechte und DB-Lookups bleiben explizite Profile/Adapter. Nicht einfach als allgemeine Statistik behandeln. |
| VVT und DSFA-Arbeitsdokumente | Designer-FlowStat `processing_record_service.py`, `dsfa_service.py`; Consumer `api/intake_briefings.py`; vorhandene `test_processing_record_service.py`, `test_dsfa_service.py` | `auditcore_dataprotection` plus optionale Renderer. VVT-XLSX/DSFA-DOCX sind hier **Erstellung/Export**, kein Nachweis einer vollständigen DSFA-Brutto-/Netto-Risikoberechnung. Mit Berechnungskern aus `regulierung` zusammenführen, ohne fachliche Unterschiede still zu harmonisieren. |
| Intake, Testdaten und Datenschutzkontext | Designer-FlowStat `intake_*`, `testdata_*`, `audit_trail_service`, `evidence_retention_service` | Testdatenerzeugung mit `auditcore_dummygenerator` abgleichen. Intakefreigaben, Echtdaten-Zugriff, Aufbewahrung und Audit-Trails bleiben Anwendungs-Sicherheitsgrenzen. |
| HIS, Monatsberichte, CO2 und Kartenberichte | Designer-FlowStat `his_*`, `monthly_*`, `co2_auswertung_service`, `chart_service`, `geo/`, Reporting-Modul | Reine Fachberechnungen statistics/risk/geo, Renderer reporting; Datenvintage, Quellenbeleg, Parität, Freigabe und konkret benannte Berichtsvorlagen erhalten. HIS ist kein einzelner generischer Export. |
| Pipelines, Notebook und Skripte | FlowStat-Pipeline-Executor/Node-Handler; `core/shared/notebook_runtime/`, `services/vpai_notebook/`, Sandbox/Plugin/Job/Schedule-Dienste | Ausführungsplattform und anwendungsspezifische Orchestrierung. Bibliotheken werden von Handlern benutzt; Sandbox, Zugriffsrechte und DB-Persistenz nicht aus Optimierungsgründen entfernen. |
| ECOHESION | `modules/ecohesion/` Projekte, Organisationen, Mitglieder, Themen, Meetings, Findings, Artefakte, Aktionspläne, Recherche, Notebooks und Dokumentvergleich | Eigene Anwendung im Repository mit eigenem Datenraum; nutzt gemeinsame Recherchekerne. Keine Repository-/Mandantenzusammenlegung. |
| Schulung und Lernmodule | `modules/schulung/` Import, Markdown, Zertifikate; `modules/lernmodule/` Projekte, Medien, Marker | Parser/Renderer als Kandidaten; Kurs-, Rollen-, Medien- und Lernfortschrittsverwaltung bleibt Anwendung. |
| Registratur, Standards und Humanizer | `modules/registratur/`, `modules/standards/`, VP-AI-Humanizer; MCP/HTTP-Anbindungen | Versionierte Regelversorgung als Provider; Text-/Terminologie-/Dokumentprüfer einzeln wiederverwenden. Fachstandards und MCP-Dienst nicht zu einer globalen immer anwendbaren Policy erklären. |
| Memory und Knowledge/RAG | `modules/memory/`, VP-AI Chunking/Embedding/RAG/Reranker/Knowledge-Ingestion, Notebook-RAG | KIRA-/RAG-Provider und Austauschverträge; DB, Vektorspeicher, Benutzerisolation und Modellbetrieb bleiben Dienste. RAG-Erinnerung ersetzt keinen SHA-belegten Quellcode. |

## Statistik: tatsächlich vorhandene Rechenfamilien

Die Standalone-Analyse registriert Gruppierung, Schichtung, Altersanalyse, Heatmap, Benford, Dubletten, Lücken, Ausreißer und einfache Stichproben (`backend/app/api/routes/analysis.py`, `CORE_ANALYSES`). `sampling_service.py` ergänzt Wesentlichkeit, MUS konservativ/Standard/geschichtet/zweiperiodig, SRS Standard/geschichtet/zweiperiodig, Differenzen-/Ratio-/Regressionsschätzung, nichtstatistische Auswahlen, PPS, Fehlerhochrechnung, Präzision, Chi-Quadrat, t-Test, Normalität und Populationssegmentierung.

Im Designer kommen Feldstatistik mit robusten Kennzahlen/Konfidenzintervallen, Korrelation, lineare/logistische Regression, ANOVA, Mann-Whitney, Wilcoxon, Bootstrap, Power und Bayes-Fehlerquote sowie Forecast/ML hinzu. Einige APIs laden DataFrames über SQLAlchemy; `stratification_service.stratify_pure` zeigt bereits eine getrennte reine Funktion. Diese Grenze ist vor Extraktion systematisch herzustellen. Vorhandene Default-Wesentlichkeitsprozente sind beobachtetes Verhalten, keine universell freigegebenen Prüfmethoden.

## FlowAudit-MCP: registrierte Schnittstellen

Der HTTP-Server liegt in `backend/app/modules/memory/mcp_http_server.py`; `register_vba_tools(mcp)` bindet die VBA-/Access-Werkzeuge vor dem HTTP-App-Aufbau ein. Statisch belegt sind **35 Werkzeuge**: 24 direkt dekorierte und 11 registrierte VBA-/Access-Werkzeuge. Drei der Access-Werkzeuge werden dynamisch durch `register_access` registriert; eine Suche nur nach Dekoratoren würde sie übersehen. Ob alle in der laufenden Serverkonfiguration angeboten werden, wurde hier nicht durch `tools/list` verifiziert.


`backend/app/modules/memory/mcp_http_server.py`:

- `skills_list` (Zeile 323)
- `vorschlag_einreichen` (Zeile 358)
- `memory_search` (Zeile 390)
- `memory_add` (Zeile 425)
- `memory_stats` (Zeile 457)
- `knowledge_search` (Zeile 586)
- `knowledge_get` (Zeile 747)
- `knowledge_health` (Zeile 871)
- `knowledge_capabilities` (Zeile 1031)
- `humanizer_get_rules` (Zeile 1136)
- `humanizer_get_persona` (Zeile 1147)
- `humanizer_list_profiles` (Zeile 1155)
- `humanizer_check` (Zeile 1168)
- `standards_list` (Zeile 1195)
- `standards_get` (Zeile 1211)
- `standards_diff` (Zeile 1228)
- `asset_get` (Zeile 1246)
- `deviation_report` (Zeile 1263)
- `document_compare_reason` (Zeile 1288)
- `check_terminologie` (Zeile 1312)
- `check_document` (Zeile 1332)
- `check_workbook` (Zeile 1362)
- `check_workbook_schema` (Zeile 1383)
- `humanizer_humanize` (Zeile 1395)

`backend/app/modules/vba_analyzer/mcp_tools.py`:

- `vba_check_source` (Zeile 166)
- `vba_check_project` (Zeile 205)
- `vba_project_symbols` (Zeile 248)
- `vba_list_rules` (Zeile 273)
- `vba_check_csv` (Zeile 288)
- `vba_status` (Zeile 309)
- `access_export_manifest` (Zeile 318)
- `access_check_sql` (Zeile 330)
- `access_check_schema` (Zeile 373)
- `access_check_ui` (Zeile 378)
- `access_check_project` (Zeile 383)

Der separate Stdio-Server `modules/memory/mcp_server.py` registriert acht Memory-Tools: `memory_search`, `memory_add`, `memory_update`, `memory_delete`, `memory_list`, `memory_get_project_context`, `memory_import_chat_history`, `memory_stats`. Das ist ein anderer Transport-/Funktionsumfang, nicht die behauptete Tool-Liste des HTTP-Dienstes. `modules/vp_ai/humanizer_mcp_server.py` ist ein weiterer Humanizer-Einstieg; dessen Implementierung ist kein zusätzlicher Beweis für Deployment am selben Host.

Die fachlichen MCP-Kerne sind Bibliothekskandidaten; OAuth, HTTP/SSE, Rate-Limit, Benutzerkontext und Tool-Schema bleiben Adapter/Dienst. Besonders VBA-/Access-Regeln gehören in eine gezielt abgegrenzte Office-Prüfkomponente bzw. Quality-Providerintegration. Native Office-Kompilierung und Office-Funktionstests sind dadurch nicht ausgeführt.

## Vollständiger statischer Pfadindex: audit_designer

Dieser Index enthält sämtliche getrackten Python-Dateien mit API-/Services-Pfad unter `backend/app`, außerdem die getrackten gemeinsamen Recherche- und Modulkerne. Test-, Modell-, Schema- und Frontend-Dateien sind damit nicht als eigene Funktionen gezählt. Dateipfade belegen Auffindbarkeit; nicht jeder Eintrag wurde im Detail fachlich bewertet.


### backend/app/api

- `backend/app/api/admin.py`: `require_admin`, `get_client_ip`, `create_user_direct`, `invite_user`, `activate_user`, `list_users`, `get_user`, `update_user`, `generate_new_password`, `delete_user`, `resend_invite`, `admin_reset_password`, `unlock_user`, `get_audit_logs`, `get_user_storage`, `update_user_storage_quota`, `get_all_users_storage`
- `backend/app/api/auth.py`: `MFACode`, `get_client_ip`, `check_rate_limit`, `record_login_attempt`, `get_current_user`, `assert_admin`, `require_admin`, `require_schulung_admin`, `require_vp_ai_access`, `get_current_user_websocket`, `register`, `login`, `mfa_status`, `mfa_setup`, `mfa_enable`, `request_password_reset`, `confirm_password_reset`, `get_me`, `update_me`, `list_users`, `change_password`
- `backend/app/api/bulk_edit.py`: `InlineUpdateRequest`, `BulkUpdateNodeRequest`, `AddTeamNoteRequest`, `NewNodeRequest`, `export_for_bulk_edit`, `import_bulk_edit`, `get_grid_data`, `update_node_inline`, `update_node_bulk`, `add_team_note`, `create_node`, `delete_node`
- `backend/app/api/categories.py`: `list_categories`, `create_category`, `get_category`, `update_category`, `get_available_icons`, `delete_category`, `add_category_item`, `delete_category_item`, `update_category_item`
- `backend/app/api/cover_templates.py`: `CoverTemplateBase`, `CoverTemplateCreate`, `CoverTemplateUpdate`, `CoverTemplateResponse`, `list_templates`, `get_default_template`, `get_template`, `create_template`, `update_template`, `delete_template`, `upload_logo`, `remove_logo`, `duplicate_template`
- `backend/app/api/diagrams.py`: `require_diagrams_access`, `list_my_diagrams`, `list_templates`, `create_my_diagram`, `get_my_diagram`, `update_my_diagram`, `delete_my_diagram`, `duplicate_my_diagram`, `list_my_versions`, `restore_my_version`, `export_my_json`, `export_my_svg`, `export_my_png`, `export_my_pdf`, `import_my_json`
- `backend/app/api/document_comparisons.py`: `ComparisonRowUpdate`, `ComparisonPreviewUpdate`, `ComparisonLayoutPayload`, `ComparisonSettingsPayload`, `ComparisonPresetPayload`, `get_comparison_settings`, `update_personal_settings`, `update_department_settings`, `export_personal_settings`, `import_personal_settings`, `save_preset`, `delete_preset`, `list_source_documents`, `create_comparison`, `list_comparisons`, `get_comparison`, `update_preview`, `download_comparison`, `delete_comparison`
- `backend/app/api/exports.py`: `get_checklist_cover_template`, `export_report`, `export_full`, `export_package`, `export_hierarchy`, `validate_project`, `export_excel`, `export_qchess_excel`, `export_pdf`, `export_docx`, `export_notes`
- `backend/app/api/health.py`: `health_check`
- `backend/app/api/imports.py`: `import_html`, `import_excel`, `import_docx`, `import_json`, `validate_package`, `import_package`, `download_template`
- `backend/app/api/llm_settings.py`: `ModelInfo`, `ProviderInfo`, `TaskTypeInfo`, `LLMSettingsResponse`, `LLMSettingsUpdate`, `ModelForTaskRequest`, `get_or_create_settings`, `get_model_for_task`, `check_provider_configured`, `get_models_for_provider`, `get_llm_settings`, `update_llm_settings`, `list_available_models`, `list_task_types`, `set_model_for_task`, `reset_to_defaults`
- `backend/app/api/mcp_humanizer.py`: `list_tools`, `call_tool`, `health`, `humanize_rest`, `handle_sse`
- `backend/app/api/mcp_memory.py`: `verify_api_key`, `list_tools`, `call_tool`, `verify_auth`, `health`, `handle_sse`
- `backend/app/api/node_history.py`: `NodeHistoryEntryResponse`, `NodeHistoryListResponse`, `RestoreVersionRequest`, `RestoreDeletedRequest`, `VersionComparisonResponse`, `ProjectHistoryStatsResponse`, `get_node_history`, `compare_node_versions`, `get_node_version`, `restore_node_version`, `get_version_history`, `get_history_stats`, `list_deleted_nodes`, `restore_deleted_node`
- `backend/app/api/nodes.py`: `check_edit_permission`, `create_node`, `update_node`, `delete_node`, `move_node`, `add_team_note`, `update_team_note_timestamp`, `edit_team_note`, `delete_team_note`, `update_node_status`, `duplicate_node`, `copy_node_from_project`, `renumber_titles`, `get_tree`, `get_tree_hierarchy`
- `backend/app/api/note_reads.py`: `get_unread_notes`, `get_unread_counts`, `mark_notes_as_read`, `mark_node_notes_as_read`
- `backend/app/api/paket.py`: `paket_erzeugen`, `paket_import`
- `backend/app/api/pdf_converter.py`: `PdfInfoResponse`, `TablePreview`, `TablePreviewResponse`, `ConversionRequest`, `DependenciesResponse`, `check_status`, `get_pdf_info`, `get_thumbnails`, `preview_tables`, `convert_to_word`, `convert_to_excel`, `preview_excel_extraction`
- `backend/app/api/pdf_editor.py`: `read_toc`, `write_toc`, `auto_detect_toc`, `get_text_blocks`, `apply_annotations`, `add_page_numbers`, `add_header_footer`, `insert_text`, `search_text`, `replace_text`, `ocr_pdf`, `compare_pdfs`, `flatten_annotations`
- `backend/app/api/pdf_tools.py`: `FeaturesResponse`, `MetadataResponse`, `WordDiffResponse`, `WordMetadataResponse`, `ExcelMetadataResponse`, `check_status`, `get_thumbnails`, `merge_pdfs`, `split_pdf`, `rotate_pages`, `pdf_to_images`, `compress_pdf`, `add_watermark`, `images_to_pdf`, `page_operations`, `read_metadata`, `set_metadata`, `word_to_pdf`, `word_merge`, `word_diff`, `read_word_metadata`, `set_word_metadata`, `read_excel_metadata`, `set_excel_metadata`
- `backend/app/api/presentations.py`: `extract_pdf_page_count`, `CreatePresentationRequest`, `UpdatePresentationRequest`, `PresentationResponse`, `AssignPresenterRequest`, `CreateAnnotationRequest`, `UpdateAnnotationRequest`, `AnnotationAttachmentItem`, `AnnotationResponse`, `list_presentations`, `create_presentation`, `list_categories`, `get_presentation`, `update_presentation`, `delete_presentation`, `assign_presenter`, `create_annotation`, `get_annotations`, `update_annotation`, `delete_annotation`, `download_presentation`, `export_presentation_with_annotations`, `AttachmentResponse`, `upload_attachment`, `list_attachments`, `download_attachment`, `delete_attachment`
- `backend/app/api/presentations_ws.py`: `ConnectionManager`, `websocket_endpoint`
- `backend/app/api/project_auth.py`: `ensure_owner_membership`, `create_owner_membership`, `project_role`, `can_access_project`, `visible_project_query`, `get_visible_project_or_404`, `require_project_view`, `require_project_review`, `require_project_edit`, `require_project_owner`, `require_project_edit_lock`
- `backend/app/api/projects.py`: `get_used_categories`, `get_project_with_lock_info`, `list_projects`, `create_project`, `get_all_tags`, `get_project`, `update_project`, `delete_project`, `list_versions`, `compare_versions`, `compare_versions_excel`, `list_sonderberichte`, `export_sonderbericht`, `get_version`, `get_current_version`, `create_version`, `update_version_tree`, `freeze_version`, `acquire_lock`, `release_lock`, `get_project_history`
- `backend/app/api/qchess_reports/_common.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/api/qchess_reports/action_import.py`: `import_actions`
- `backend/app/api/qchess_reports/actions.py`: `list_rule_actions`, `create_rule_action`, `update_rule_action`, `delete_rule_action`, `reorder_rule_actions`, `list_rule_answer_options`, `get_template_actions_bulk`, `list_aktions_arten`, `list_template_aktions_formatvorlagen`
- `backend/app/api/qchess_reports/auto_bind.py`: `auto_bind_propose`, `auto_bind_apply`, `auto_bind_manual`
- `backend/app/api/qchess_reports/chapters.py`: `list_chapters`, `create_chapter`, `update_chapter`, `delete_chapter`, `reorder_chapters`
- `backend/app/api/qchess_reports/deployment.py`: `download_deployment_zip`, `validate_template`, `deploy_ready`
- `backend/app/api/qchess_reports/export.py`: `download_word`, `export_report`, `export_textbausteine`, `export_checkliste`, `export_checkliste_baum`, `download_qchess_snapshot_export_macro`
- `backend/app/api/qchess_reports/library.py`: `library_search`, `library_suggest`, `library_seed`, `library_sachverhalt_list`, `library_sachverhalt_create`, `library_sachverhalt_get`, `library_sachverhalt_update`, `library_sachverhalt_delete`, `library_sachverhalt_extract`, `library_sachverhalt_apply`, `list_default_sets_endpoint`, `library_seed_async`, `library_seed_status`, `auto_prefill_from_hints`
- `backend/app/api/qchess_reports/rules.py`: `list_rules`, `get_rule`, `update_rule`, `set_answer_action_mode`, `preview_rule_actions`, `preview_rule_html`, `preview_template_all`, `bulk_confirm_rules`, `bulk_prefill_rules`
- `backend/app/api/qchess_reports/sections.py`: `list_sections`, `create_section`, `update_section`, `auto_assign_aggregate`, `delete_section`, `reorder_sections`, `bulk_move_mergefields`, `set_mergefield_node_binding`
- `backend/app/api/qchess_reports/skeleton.py`: `upload_skeleton`, `apply_skeleton_proposals`, `parse_skeleton`, `get_docm_manifest`, `upload_vba`, `list_template_word_styles`
- `backend/app/api/qchess_reports/snapshot.py`: `import_qchess_fragen`, `preview_qchess_fragen`, `confirm_qchess_fragen`, `get_qchess_fragen_snapshot`, `get_qchess_fragen_snapshot_questions`, `delete_qchess_fragen_snapshot`
- `backend/app/api/qchess_reports/templates.py`: `create_template`, `list_templates`, `get_template`, `update_template`, `delete_template`, `insert_ausgabenliste_rows`, `set_qchess_reportid`
- `backend/app/api/qchess_reports/test_deploy.py`: `get_test_deploy_health`, `run_test_deploy`, `get_test_deploy_status`
- `backend/app/api/reference_documents.py`: `ReferenceDocBase`, `ReferenceDocCreate`, `ReferenceDocUpdate`, `ReferenceDocResponse`, `NodeReferenceDocCreate`, `NodeReferenceDocResponse`, `NodeDocsVisibilityUpdate`, `NodeDocsWithGrundsatzResponse`, `check_admin`, `check_project_access`, `list_templates`, `create_template`, `delete_template`, `update_template`, `list_project_documents`, `upload_project_document`, `delete_project_document`, `update_project_document`, `toggle_grundsatz`, `get_node_documents`, `link_document_to_node`, `update_node_docs_visibility`, `unlink_document_from_node`, `get_user_from_token_or_header`, `download_document`
- `backend/app/api/strategy_documents.py`: `get_document_or_404`, `list_documents`, `create_document`, `import_from_docx`, `import_docx_to_existing`, `get_document`, `update_document`, `update_content`, `delete_document`, `list_versions`, `create_version`, `get_version`, `restore_version`, `get_version_diff`, `upload_image`, `list_images`, `get_image_file`, `delete_image`, `export_to_docx`, `export_to_markdown`, `export_pruefstrategie_docx`, `export_pruefstrategie_pdf`, `export_version_to_docx`
- `backend/app/api/system.py`: `llm_status`
- `backend/app/api/vpai_notebook/canvas.py`: `CanvasDocumentUpsert`, `AssetUpload`, `RemoveBackgroundRequest`, `LabelTemplateCreate`, `LabelTemplateUpdate`, `DatasetCreate`, `PreviewRequest`, `CanvasExportCreate`, `CanvasBrandKitUpdate`, `CanvasLayoutPreferencesUpdate`, `CanvasColorPreferencesUpdate`, `canvas_health`, `get_color_preferences`, `update_color_preferences`, `get_layout_preferences`, `update_layout_preferences`, `get_brand_kit`, `update_brand_kit`, `list_canvas_documents`, `get_document_by_page`, `upsert_document`, `upload_asset`, `list_assets`, `remove_background`, `get_image_job`, `create_label_template`, `list_label_templates`, `get_label_template`, `update_label_template`, `create_dataset`, `list_datasets`, `preview_template`, `export_document`, `get_export`, `download_export`
- `backend/app/api/vpai_notebook/clipper.py`: `ClipContent`, `ClipRequest`, `ClipResponse`, `detect_domain`, `html_to_markdown`, `extract_main_content`, `clipper_health`, `get_notebooks_for_clipper`, `get_domains_for_clipper`, `save_clip`, `generate_page_embedding`, `quick_save`
- `backend/app/api/vpai_notebook/comments.py`: `CommentCreate`, `CommentUpdate`, `list_comments`, `create_comment`, `update_comment`, `delete_comment`, `toggle_resolve_comment`
- `backend/app/api/vpai_notebook/files.py`: `MkdirRequest`, `RenameRequest`, `get_file_tree`, `upload_workspace_file`, `download_workspace_file`, `create_subdirectory`, `delete_workspace_file`, `rename_workspace_file`
- `backend/app/api/vpai_notebook/findings.py`: `FindingCreate`, `FindingUpdate`, `list_findings`, `get_findings_stats`, `get_finding`, `create_finding`, `update_finding`, `delete_finding`, `add_response`, `close_finding`
- `backend/app/api/vpai_notebook/gis/_common.py`: `GisLayerCreate`, `GisLayerUpdate`, `GisFeatureCreate`, `GisFeatureUpdate`, `GisBulkUpdateRequest`, `GisFeaturesBulkCreate`, `GisExportCreate`, `ReferenceLayerCreate`, `GisReferenceAttachRequest`, `GisAnalysisMeasure`, `GisAnalysisFilters`, `GisAnalysisSort`, `GisAnalysisRunRequest`, `GisMaterializeLayerRequest`, `GisAnalysisTemplateCreate`, `ImportReportExportCreate`, `GisAnalysisExportCreate`, `NaturaDistanceAnalysisRequest`, `JupyterBookExportRequest`
- `backend/app/api/vpai_notebook/gis/analytics.py`: `get_analytics_fields`, `run_analysis`, `export_analysis`, `materialize_analysis_layer`, `list_analysis_templates`, `create_analysis_template`
- `backend/app/api/vpai_notebook/gis/db_browser.py`: `list_db_tables`, `preview_db_table`, `export_jupyter_book`
- `backend/app/api/vpai_notebook/gis/geocode.py`: `geocode_layer`, `rebuild_nuts`
- `backend/app/api/vpai_notebook/gis/import_excel.py`: `import_excel_files`, `get_import_report`, `export_import_report`
- `backend/app/api/vpai_notebook/gis/layers.py`: `gis_health`, `create_layer`, `list_layers`, `get_layer`, `update_layer`, `create_features`, `list_features`, `update_feature`, `bulk_update_features`, `get_filter_values`
- `backend/app/api/vpai_notebook/gis/map_render.py`: `get_aggregate`, `get_nuts_geojson`, `export_layer`, `get_export`, `download_export`
- `backend/app/api/vpai_notebook/gis/natura.py`: `autoload_natura_results`, `autoload_results`, `run_natura_distance_analysis`, `get_natura_distance_summary`
- `backend/app/api/vpai_notebook/gis/reference.py`: `list_service_presets`, `get_layer_reference_layers`, `attach_reference_layers`, `create_reference_layer`, `list_reference_layers`
- `backend/app/api/vpai_notebook/gis/workspace_io.py`: `list_workspace_files`, `download_workspace_file`
- `backend/app/api/vpai_notebook/gis_proxy.py`: `proxy_wfs`, `proxy_wms`, `proxy_wfs_capabilities`, `proxy_wms_capabilities`, `get_nuts_hessen`, `get_proxy_whitelist`
- `backend/app/api/vpai_notebook/gis_sync.py`: `GisSyncConnectionManager`, `gis_sync_websocket`, `get_gis_sync_status`, `kernel_select_features`, `push_layer_to_map`, `push_layer_for_page`
- `backend/app/api/vpai_notebook/import_router.py`: `ImportSessionCreate`, `FileDecision`, `FinalizeRequest`, `list_import_sessions`, `create_import_session`, `get_import_session`, `delete_import_session`, `list_session_files`, `update_file_decision`, `upload_files`, `import_google_keep_direct`, `import_onenote_direct`, `import_obsidian_direct`, `finalize_import`, `import_all_pending`, `classify_with_llm`, `import_desktop_zip`
- `backend/app/api/vpai_notebook/jupyter.py`: `CellCreate`, `CellUpdate`, `CellRestore`, `CellDebugRequest`, `CellReorder`, `TemplateCell`, `TemplateCreate`, `KernelSelection`, `KernelLayerPush`, `notebook_storage_status`, `notebook_storage_sync`, `kernel_api_layers`, `kernel_api_layer_features`, `kernel_api_select`, `kernel_api_push_layer`, `list_cells`, `get_cell`, `create_cell`, `update_cell`, `list_cell_versions`, `restore_cell_version`, `debug_cell`, `delete_cell`, `reorder_cells`, `execute_cell`, `execute_all_cells`, `execute_cell_stream`, `CompletionRequest`, `kernel_complete`, `KernelStartRequest`, `start_kernel`, `restart_kernel`, `interrupt_kernel`, `stop_kernel`, `kernel_status`, `get_variables`, `export_ipynb`, `export_notebook_html`, `export_notebook_pdf`, `import_ipynb`, `list_templates`, `get_template`, `create_template`, `delete_template`, `apply_template`, `reload_templates`, `list_files`, `download_file`, `view_file`, `save_file`, `upload_file`, `create_directory`, `delete_file`, `rename_file`
- `backend/app/api/vpai_notebook/notebooks.py`: `NotebookCreate`, `NotebookUpdate`, `ShareCreate`, `list_notebooks`, `create_notebook`, `get_notebook`, `update_notebook`, `list_notebook_pages`, `delete_notebook`, `list_notebook_shares`, `share_notebook`, `update_notebook_share`, `revoke_notebook_share`
- `backend/app/api/vpai_notebook/pages.py`: `PageCreate`, `PageUpdate`, `PageReorder`, `FileUpload`, `reorder_pages`, `list_page_templates`, `list_pages`, `create_page`, `search_pages_endpoint`, `search_fulltext_endpoint`, `search_suggestions`, `get_or_create_daily_note`, `get_page`, `update_page`, `delete_page`, `duplicate_page`, `get_page_backlinks`, `get_auto_tag_suggestions`, `apply_auto_tag_suggestions`, `analyze_content`, `get_page_summary`, `get_page_key_points`, `get_ai_tag_suggestions`, `check_ai_status`, `list_page_files`, `get_file`, `get_file_data`, `upload_file`, `delete_file`, `get_file_data_direct`
- `backend/app/api/vpai_notebook/rag.py`: `SemanticSearchRequest`, `AskRequest`, `ConversationCreate`, `MessageCreate`, `semantic_search`, `ask_question`, `get_similar_pages`, `list_conversations`, `create_conversation`, `get_conversation`, `delete_conversation`, `get_embedding_stats`, `embed_page`, `embed_all_pages`, `delete_page_embedding`
- `backend/app/api/vpai_notebook/settings.py`: `DomainCreate`, `DomainUpdate`, `get_domains`, `create_domain`, `update_domain`, `delete_domain`, `reorder_domains`, `AgentUpdate`, `get_agents`, `update_agent`, `FeatureUpdate`, `get_features`, `update_feature`, `TemplateCreate`, `TemplateUpdate`, `get_templates`, `create_template`, `update_template`, `delete_template`, `TemplateInstantiateRequest`, `instantiate_template`, `get_llm_settings`, `LlmSettingsUpdate`, `get_llm_config`, `update_llm_config`
- `backend/app/api/vpai_notebook/vault.py`: `PinSetup`, `PinVerify`, `PinChange`, `EntryCreate`, `EntryUpdate`, `get_vault_service`, `get_vault_status`, `setup_vault`, `verify_pin`, `change_pin`, `list_entries`, `get_entry`, `create_entry`, `update_entry`, `delete_entry`, `get_categories`
- `backend/app/api/vpai_notebook/vba.py`: `ModuleCreate`, `ModuleUpdate`, `TemplateCreate`, `TemplateUpdate`, `ProjectCreate`, `ProjectUpdate`, `list_projects`, `create_project`, `get_project`, `update_project`, `delete_project`, `assign_template_to_project`, `unassign_template_from_project`, `list_modules`, `create_module`, `get_module`, `update_module`, `delete_module`, `import_bas_file`, `list_templates`, `create_template`, `get_template`, `update_template`, `delete_template`, `link_module_template`, `unlink_module_template`, `get_module_history`, `rollback_module`, `get_stats`, `reanalyze_all_modules`, `OptimizeRequest`, `optimize_module`, `AcceptFindingRequest`, `accept_finding`, `list_ai_actions`, `validate_template_endpoint`, `compile_template_endpoint`, `ConfigCreate`, `ConfigUpdate`, `StammdatenCreate`, `list_config`, `create_config`, `update_config`, `delete_config`, `validate_config`, `list_stammdaten`, `create_stammdaten`, `update_stammdaten`, `delete_stammdaten`, `import_daten_xlsx`, `export_daten_xlsx`, `list_daten_table`, `create_daten_row`, `update_daten_row`, `delete_daten_row`, `import_berichtsdaten_xlsx`, `import_office_file`, `search_modules`
- `backend/app/api/vpai_notebook/versions.py`: `list_page_versions`, `restore_page_version`
- `backend/app/api/vpai_notebook/workspace.py`: `WorkspaceTaskCreate`, `WorkspaceTaskUpdate`, `WorkspaceTaskMove`, `WorkspaceFileUpload`, `BoardCreate`, `ShareCreate`, `BoardColumnDef`, `BoardSettingsUpdate`, `list_workspace_boards`, `create_workspace_board`, `toggle_pin`, `get_board_settings`, `update_board_settings`, `delete_workspace_board`, `list_shares`, `share_page`, `update_share`, `revoke_share`, `shared_with_me`, `list_tasks`, `create_task`, `get_task`, `update_task`, `delete_task`, `move_task`, `generate_prompt`, `list_task_files`, `upload_task_file`, `delete_task_file`
- `backend/app/api/vpai_notebook/yjs_ws.py`: `YjsConnectionManager`, `debounced_save`, `schedule_save`, `debounced_save_binary`, `schedule_save_binary`, `yjs_websocket`, `get_yjs_status`
- `backend/app/api/word_templates.py`: `WordTemplateBase`, `WordTemplateCreate`, `WordTemplateUpdate`, `WordTemplateResponse`, `StylesResponse`, `list_templates`, `get_default_template`, `get_template`, `get_template_styles`, `download_template`, `upload_template`, `analyze_template`, `update_template`, `update_template_file`, `delete_template`, `StyleMappingBase`, `StyleMappingCreate`, `StyleMappingUpdate`, `StyleMappingResponse`, `AllStylesResponse`, `get_all_template_styles`, `list_style_mappings`, `get_active_mapping`, `get_style_mapping`, `create_style_mapping`, `update_style_mapping`, `delete_style_mapping`, `get_effective_mappings`, `StyleMappingDetail`, `StyleSuggestionResponse`, `suggest_style_mappings`

### backend/app/core

- `backend/app/core/shared/app_context.py`: `Application`, `ApplicationContext`, `build_context`, `assert_application`, `assert_authenticated`
- `backend/app/core/shared/notebook_runtime/execution.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/core/shared/notebook_runtime/manager.py`: `LaufzeitFehler`, `fordere_an`, `beende`, `abgelaufene`
- `backend/app/core/shared/notebook_runtime/manifest.py`: `fingerabdruck`, `RunManifest`
- `backend/app/core/shared/notebook_runtime/models.py`: `NotebookRuntime`, `NotebookRunManifest`
- `backend/app/core/shared/notebook_runtime/profiles.py`: `Sandboxprofil`, `Ressourcenprofil`, `Umgebungsprofil`, `sandbox`, `ressourcen`, `umgebung`, `pruefe_kombination`, `katalog`
- `backend/app/core/shared/notebook_runtime/runner_client.py`: `RunnerNichtErreichbar`, `RunnerLehntAb`, `verfuegbar`, `bereitschaft`, `erstelle`, `starte`, `halte_an`, `zustand`, `fuehre_aus`, `unterbrich`, `entferne`
- `backend/app/core/shared/notebook_runtime/security.py`: `UnsichereLaufzeit`, `Sicherheitsvorgaben`, `Laufzeitanforderung`, `pruefe_optionen`
- `backend/app/core/shared/notebook_runtime/workspace.py`: `UnzulaessigerArbeitsbereich`, `pfad_fuer_benutzer`, `pfad_fuer_projekt`, `gehoert_zu`, `fremd`
- `backend/app/core/shared/research/contracts.py`: `Quellenstatus`, `Quellenbefund`, `ResearchError`, `ResearchQuery`, `ResearchResult`, `ToolDescriptor`
- `backend/app/core/shared/research/fetcher.py`: `AbrufVerweigert`, `Abrufergebnis`, `hole`, `zwischenablage_leeren`
- `backend/app/core/shared/research/native.py`: `normalise_name`, `matches_name_query`, `DoubleFundingCrossCheck`
- `backend/app/core/shared/research/providers.py`: `ResearchProvider`, `NativeProvider`, `UpstreamProvider`
- `backend/app/core/shared/research/register/beneficiaries.py`: `laendername`, `pruefe_land`, `normalisiere_suchtext`, `fuzzy_score`, `treffergenauigkeit`, `adaptiver_mindestscore`, `normalisiere_beguenstigtenname`, `format_eur`, `de_int`, `parse_satz`, `parse_betrag`, `parse_datum`, `ist_kopfzeilen_artefakt`, `kanonischer_firmenschluessel`, `bereinige_ort`, `klassifiziere_taxonomie`, `ist_kategorie_artefakt`, `kategorie_buendel`, `datenstand`, `bestandskennzahlen`, `zaehle_quellen`, `suche`, `auswertung`, `nuts_regionen`, `regionale_verteilung`, `export_zeilen`, `export_metadaten`, `export_csv`, `normalisiere_ueberschrift`, `erkenne_spalten`, `parse_lieferung`, `compute_record_hash`, `BeneficiaryHarvestParams`, `run_beneficiary_harvest`, `BeneficiaryRegisterProvider`, `BeneficiaryAnalyticsProvider`, `BeneficiaryMapProvider`
- `backend/app/core/shared/research/register/beneficiaries_models.py`: `ResearchBeneficiaryRecord`, `ResearchBeneficiaryHarvestRun`, `ResearchBeneficiarySourceConfig`
- `backend/app/core/shared/research/register/de_minimis.py`: `landeskennung`, `Suchkriterien`, `EAidRegisterClient`, `Kumulierung`, `berechne_kumulierung`, `DeMinimisRegisterProvider`, `DeMinimisCumulationProvider`
- `backend/app/core/shared/research/register/de_minimis_ernte.py`: `ernte`, `bestandsstand`
- `backend/app/core/shared/research/register/de_minimis_models.py`: `satz_hash`, `bestand_hash`, `ResearchDeMinimisHarvestRun`, `ResearchDeMinimisAward`
- `backend/app/core/shared/research/register/de_minimis_zuordnung.py`: `ebene`
- `backend/app/core/shared/research/register/dedupe.py`: `normalisiere_vorhaben`, `Satz`, `widerspruch`, `Dublettenpaar`, `Uebergangen`, `Dublettenplan`, `lade_saetze`, `lade_quellenrang`, `finde_dubletten`, `plane`, `markiere`, `nimm_zurueck`, `nur_sichtbare`, `zaehle`, `pruefe_verweise`
- `backend/app/core/shared/research/register/entities.py`: `RegisterSatz`, `Aufloesung`, `Suchergebnis`, `vergleichsname`, `ist_lei`, `lei_aus_text`, `aehnlichkeit`, `aufloese_entitaet`, `verknuepfe_satz`, `baue_bestand_auf`, `registriere_registerleser`, `saetze_aus_register`, `baue_bestand_aus_registern`, `embeddings_aktiv`, `hole_vektor`, `text_fuer_embedding`, `schreibe_embedding`, `baue_embeddings_auf`, `semantische_treffer`, `suche`, `CompanySearchProvider`
- `backend/app/core/shared/research/register/entities_models.py`: `ResearchCompanyEntity`, `ResearchEntityMatch`, `ResearchEntityEmbedding`
- `backend/app/core/shared/research/register/geocoding.py`: `bundesland_normalisieren`, `PlzEintrag`, `plz_nachschlagen`, `normalisiere_plz`, `NutsGebiet`, `nuts3_fuer_punkt`, `naechste_nuts3`, `nuts3_name`, `bundesland_zu_nuts`, `nuts_einstufung`, `ort_nachschlagen`, `PlzFund`, `plz_kandidaten`, `nuts_aus_text`, `Verortung`, `bekannte_region`, `verorte`, `flaeche_fuer_punkt`
- `backend/app/core/shared/research/register/sanctions.py`: `falte_diakritika`, `normalisiere_name`, `klassifiziere`, `Sanktionsliste`, `liste`, `liste_zu_quelle`, `Sanktionseintrag`, `Sanktionstreffer`, `Listenbefund`, `Listenindex`, `leere_indexablage`, `SanktionslistenDienst`, `ablage`, `hole_liste`, `SanctionsScreeningProvider`, `methodenerlaeuterung`
- `backend/app/core/shared/research/register/sanctions_models.py`: `ResearchSanctionsRefreshRun`, `ResearchSanctionsEntry`
- `backend/app/core/shared/research/register/state_aid.py`: `umschrift`, `normalize_company_name`, `normalize_country_code`, `detect_sa_reference`, `build_competition_search_url`, `parse_amount`, `betrag_ist_spanne`, `parse_date`, `derive_nuts_code`, `nuts_praefix`, `AwardHit`, `fuzzy_match_company`, `adaptive_min_score`, `serialize_award`, `Datenstand`, `datenstand`, `quellenbefund`, `search_awards`, `company_dossier`, `Pruefregel`, `Regelbefund`, `Pruefbericht`, `build_audit_report`, `Pruefbefund`, `Bestandsbericht`, `run_validation`, `Ernteparameter`, `Ernteergebnis`, `wirksames_startdatum`, `parse_award_detail`, `parse_results`, `TamSitzung`, `map_row_to_award`, `run_harvest`, `StateAidRegisterProvider`, `StateAidCompanyDossierProvider`, `StateAidAuditReportProvider`
- `backend/app/core/shared/research/register/state_aid_models.py`: `ResearchStateAidHarvestRun`, `ResearchStateAidAward`, `ResearchStateAidSource`
- `backend/app/core/shared/research/registry.py`: `list_descriptors`, `get_descriptor`, `get_provider`, `run_tool`, `source_route_map`
- `backend/app/core/shared/research/sources.py`: `Quellenkategorie`, `Zugangsart`, `Abrufpolitik`, `Datenklasse`, `SourceDescriptor`, `get_source`, `list_sources`, `resolve`, `hoechstalter_minuten`
- `backend/app/core/shared/versioning.py`: `canonical_payload`, `content_hash`, `next_version`, `FieldChange`, `ArtifactDiff`, `diff_artifacts`
- `backend/app/core/shared/visibility.py`: `Visibility`, `can_view`, `visible_filter_values`, `is_at_least`

### backend/app/modules/document_compare

- `backend/app/modules/document_compare/__main__.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/document_compare/article_law.py`: `LawParagraph`, `apply_commands`, `compare_article_law`
- `backend/app/modules/document_compare/cli.py`: `read_document`, `compare_documents`, `build_parser`, `main`
- `backend/app/modules/document_compare/configuration.py`: `default_config_path`, `sanitise_settings`, `load_settings`, `save_settings`, `merge_settings`
- `backend/app/modules/document_compare/matching.py`: `similarity`, `checklist_matches`, `text_matches`, `erkenne_verschiebungen`, `build_rows`
- `backend/app/modules/document_compare/parsing.py`: `ParseError`, `normalise_for_match`, `normalise_semantic`, `normalise_verbatim`, `word_diff`, `accept_revisions`, `visible_text`, `pdf_text_items`, `detect_mode`, `read_document`
- `backend/app/modules/document_compare/rendering.py`: `render_docx`
- `backend/app/modules/document_compare/service.py`: `CompareError`, `DocumentCompareService`
- `backend/app/modules/document_compare/tasks.py`: `run_document_comparison`, `cleanup_expired_comparisons`
- `backend/app/modules/document_compare/types.py`: `CompareItem`, `CompareRow`, `ComparisonResult`

### backend/app/modules/ecohesion

- `backend/app/modules/ecohesion/action_plan_seed.py`: `MeasureSeed`, `cluster_of`
- `backend/app/modules/ecohesion/api/action_plan.py`: `history`, `overview`, `matrix`, `community`, `cockpit`, `set_status`, `ReviewInput`, `review`
- `backend/app/modules/ecohesion/api/admin.py`: `OrganisationIn`, `MemberIn`, `list_organisations`, `create_organisation`, `list_members`, `create_member`, `seed_action_plan`, `sync_research`
- `backend/app/modules/ecohesion/api/artifacts.py`: `ArtifactCreate`, `VersionCommit`, `LabelSet`, `ForkIn`, `DeprecateIn`, `RelationIn`, `meta`, `facets`, `list_artifacts`, `create_artifact`, `get_artifact`, `get_version`, `commit_version`, `set_label`, `fork_artifact`, `diff`, `deprecate`, `relate`
- `backend/app/modules/ecohesion/api/findings.py`: `FindingIn`, `LinkIn`, `meta`, `list_findings`, `create_finding`, `analysis`, `cycle`, `link_artifact`
- `backend/app/modules/ecohesion/api/me.py`: `logout`, `profile`, `update_profile`, `capabilities`, `set_capability`, `navigation`, `list_views`, `save_view`, `delete_view`
- `backend/app/modules/ecohesion/api/meetings.py`: `list_meetings`, `create_meeting`, `get_meeting`, `presentation`, `update_meeting`, `add_item`, `update_item`, `project_from_item`
- `backend/app/modules/ecohesion/api/notebooks.py`: `LaufzeitIn`, `AusfuehrenIn`, `profile_katalog`, `liste`, `anfordern`, `zustand`, `ausfuehren`, `execution_result`, `unterbrechen`, `beenden`, `protokolle`
- `backend/app/modules/ecohesion/api/projects.py`: `list_projects`, `create_project`, `join_project`
- `backend/app/modules/ecohesion/api/public.py`: `list_public_tools`, `get_public_tool`, `run_public_tool`, `export_public_tool`, `nuts_geojson`, `sources`, `action_plan_overview`, `action_plan_matrix`, `self_assessment`, `documents`, `document`, `redirects`, `status`, `de_minimis_bestand`
- `backend/app/modules/ecohesion/api/serializers.py`: `organisation_out`, `member_out`, `topic_out`, `project_out`, `tool_out`
- `backend/app/modules/ecohesion/api/topics.py`: `meta`, `list_topics`, `bubbles`, `create_topic`, `get_topic`, `update_topic`, `toggle_interest`, `list_comments`, `add_comment`
- `backend/app/modules/ecohesion/artifact_types.py`: `ArtifactArt`, `art`, `pruefe_nutzlast`, `sicherheitsfelder`
- `backend/app/modules/ecohesion/auth.py`: `get_ecohesion_user`, `public_context`, `get_ecohesion_member`, `touch_member`, `get_ecohesion_context`, `require_ecohesion_admin`, `optional_member`, `context_from_optional`
- `backend/app/modules/ecohesion/constants.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/ecohesion/models.py`: `EcohesionOrganisation`, `EcohesionMember`, `EcohesionTopic`, `EcohesionTopicInterest`, `EcohesionTopicComment`, `EcohesionAgMeeting`, `EcohesionAgMeetingItem`, `EcohesionProject`, `EcohesionProjectMember`, `EcohesionActionPlanMeasure`, `EcohesionActionPlanStatus`, `EcohesionOrganisationPermission`, `EcohesionActionPlanRevision`, `EcohesionResearchTool`, `EcohesionResearchToolVersion`, `EcohesionSavedView`, `EcohesionAuditEvent`, `EcohesionArtifact`, `EcohesionArtifactVersion`, `EcohesionArtifactLabel`, `EcohesionArtifactRelation`, `EcohesionFinding`, `EcohesionDocumentComparison`
- `backend/app/modules/ecohesion/schemas.py`: `OrganisationOut`, `MemberOut`, `MemberProfileUpdate`, `CapabilityUpdate`, `CapabilityOut`, `TopicCreate`, `TopicUpdate`, `InterestCounts`, `TopicOut`, `InterestToggle`, `CommentCreate`, `CommentOut`, `MeetingItemIn`, `MeetingItemOut`, `MeetingCreate`, `MeetingUpdate`, `MeetingOut`, `ProjectCreate`, `ProjectOut`, `MeasureOut`, `ClusterOut`, `MeasureStatusIn`, `CommunityMeasureOut`, `ResearchToolOut`, `ToolVersionOut`, `SavedViewIn`, `SavedViewOut`
- `backend/app/modules/ecohesion/services/action_plan_service.py`: `seed_measures`, `overview`, `matrix`, `community_view`, `cockpit`, `set_status`
- `backend/app/modules/ecohesion/services/artifact_service.py`: `UnveraenderlichkeitVerletzt`, `create_artifact`, `commit_version`, `set_label`, `resolve_label`, `fork`, `version_diff`, `deprecate`, `relate`, `search`, `get_artifact`, `facetten`
- `backend/app/modules/ecohesion/services/browser_sessions.py`: `storage`, `key`, `check_origin`, `issue`, `resolve`, `revoke`, `secure_cookie`
- `backend/app/modules/ecohesion/services/common.py`: `guard`, `slugify`, `unique_slug`, `clean_measures`, `clean_tags`, `record_event`
- `backend/app/modules/ecohesion/services/document_service.py`: `Methodenseite`, `liste`, `lies`
- `backend/app/modules/ecohesion/services/findings_service.py`: `kataloge`, `create_finding`, `list_findings`, `link_artifact`, `auswertung`, `kreislauf`
- `backend/app/modules/ecohesion/services/meeting_service.py`: `may_read`, `require_editor`, `require_shared_topic`, `list_meetings`, `get_meeting`, `create_meeting`, `update_meeting`, `add_item`, `update_item`, `project_from_item`
- `backend/app/modules/ecohesion/services/member_service.py`: `ensure_member`, `get_profile`, `update_profile`, `capabilities_for`, `set_capability`, `navigation_for`, `list_organisations`
- `backend/app/modules/ecohesion/services/organisation_reviews.py`: `RevisionConflict`, `permissions`, `require`, `describe`, `change`, `edit`, `review`
- `backend/app/modules/ecohesion/services/project_service.py`: `may_read`, `require_actor`, `validate_topic_link`, `list_projects`, `create_project`, `join_project`
- `backend/app/modules/ecohesion/services/research_pdf.py`: `render_pdf`
- `backend/app/modules/ecohesion/services/research_runs.py`: `storage`, `save`, `load`
- `backend/app/modules/ecohesion/services/research_service.py`: `sync_registry`, `list_tools`, `get_tool`, `version_diff`, `check_public_rate_limit`, `run`, `registry_status`
- `backend/app/modules/ecohesion/services/research_validation.py`: `validate`
- `backend/app/modules/ecohesion/services/topic_service.py`: `list_topics`, `get_topic`, `create_topic`, `update_topic`, `toggle_interest`, `add_comment`, `list_comments`, `bubble_data`

### backend/app/modules/flowstat

- `backend/app/modules/flowstat/api/_sse_auth.py`: `get_user_for_sse`
- `backend/app/modules/flowstat/api/admin_cache.py`: `get_cache_statistics`, `trigger_manual_cleanup`, `delete_dataframe`
- `backend/app/modules/flowstat/api/admin_plugins.py`: `list_all_plugins`, `upload_plugin`, `activate_plugin`, `deactivate_plugin`
- `backend/app/modules/flowstat/api/agent_onboarding.py`: `get_agent_onboarding_contract`, `validate_agent_onboarding_plan`
- `backend/app/modules/flowstat/api/aging.py`: `compute`
- `backend/app/modules/flowstat/api/analysis.py`: `run_analysis`
- `backend/app/modules/flowstat/api/analysis_results.py`: `list_analysis_results`, `get_analysis_stats`, `get_analysis_result`, `create_analysis_result`, `update_analysis_result`, `delete_analysis_result`, `create_version`, `toggle_archive`, `toggle_favorite`, `get_versions`
- `backend/app/modules/flowstat/api/api_connections.py`: `list_api_connection_templates`, `list_api_connections`, `create_api_connection`, `get_api_connection`, `update_api_connection`, `delete_api_connection`, `test_api_connection`, `pull_api_connection`
- `backend/app/modules/flowstat/api/audit_tests.py`: `post_duplicates_exact`, `post_duplicates_alias`, `post_duplicate_alias`, `post_gap`, `post_benford`, `post_round_number`, `post_same_same_different`, `post_same_same_same`, `post_cutoff`, `post_sequence`
- `backend/app/modules/flowstat/api/audit_trail.py`: `list_trail_endpoint`, `replay_blueprint_endpoint`, `replay_blueprint_endpoint_post`, `verify_run_endpoint`, `replay_run_endpoint`, `list_runs_endpoint`, `get_trail_by_run_uuid_endpoint`
- `backend/app/modules/flowstat/api/auto_report.py`: `auto_report_word`, `auto_report_pdf`
- `backend/app/modules/flowstat/api/automl.py`: `run_automl_endpoint`, `list_automl_runs_endpoint`, `get_automl_run_endpoint`
- `backend/app/modules/flowstat/api/bpmn.py`: `validate_bpmn_bva`, `list_bpmn_diagrams`, `create_bpmn_diagram`, `validate_bpmn_xml`, `get_bpmn_diagram`, `update_bpmn_diagram`, `delete_bpmn_diagram`, `validate_bpmn_diagram`, `toggle_archive_bpmn_diagram`, `update_bpmn_header`, `update_bpmn_color_scheme`, `add_bpmn_comment`, `update_bpmn_comment`, `delete_bpmn_comment`, `get_bpmn_esi_requirements`
- `backend/app/modules/flowstat/api/bpmn_export.py`: `get_bpmn_analysis`, `export_bpmn_excel`, `export_bpmn_pdf`
- `backend/app/modules/flowstat/api/capabilities.py`: `read_capabilities`
- `backend/app/modules/flowstat/api/charts.py`: `get_histogram`, `get_scatter`, `get_correlation_matrix`, `get_pareto`, `get_lorenz`, `get_timeseries_decompose`, `get_timeseries_forecast`, `get_missing_data_map`, `get_parallel_coordinates`, `get_calendar_heatmap`, `chart_preview`
- `backend/app/modules/flowstat/api/co2_auswertungen.py`: `get_schwellenwerte`, `put_schwellenwerte`, `plausibilitaet_pius`, `zielerreichung`
- `backend/app/modules/flowstat/api/core_requirements.py`: `list_core_requirements`, `get_core_requirement`, `create_core_requirement`, `update_core_requirement`, `delete_core_requirement`, `list_assessment_criteria`, `create_assessment_criterion`, `update_assessment_criterion`, `delete_assessment_criterion`
- `backend/app/modules/flowstat/api/custom_dashboards.py`: `list_dashboards`, `list_templates`, `generate_project_workshop_dashboard`, `get_dashboard`, `create_dashboard`, `update_dashboard`, `delete_dashboard`, `duplicate_dashboard`
- `backend/app/modules/flowstat/api/custom_nodes.py`: `create_custom_node`, `list_custom_nodes`, `get_catalog`, `get_runtime_schema`, `import_custom_node`, `get_custom_node`, `update_custom_node`, `archive_custom_node`, `create_version`, `update_version`, `validate_version`, `preview_version`, `publish_version`, `retire_version`, `export_version`
- `backend/app/modules/flowstat/api/data_manipulation.py`: `append_dataframes`, `merge_dataframes`, `add_calculated_field`, `validate_calculated_field`, `preview_calculated_field`, `build_pivot`
- `backend/app/modules/flowstat/api/data_quality_contracts.py`: `list_contracts`, `put_contract`, `preflight`
- `backend/app/modules/flowstat/api/data_source_project.py`: `list_dataframes_for_project`
- `backend/app/modules/flowstat/api/data_sources.py`: `list_data_sources`, `import_upload_review_sources`, `list_vp_gj_templates`, `list_vp_gj_bundles`, `link_vp_gj_project_context`, `get_data_source`, `get_data_source_history`, `get_data_source_columns`, `get_data_source_column_statistics`, `get_data_source_diagnostics`, `run_vp_gj_standard_analysis`, `run_vp_gj_project_sheet_analysis`, `get_data_source_preview`, `delete_data_source`
- `backend/app/modules/flowstat/api/dataframes.py`: `get_dataframe_columns`
- `backend/app/modules/flowstat/api/db_connections.py`: `list_db_connections`, `create_db_connection`, `get_db_connection`, `update_db_connection`, `delete_db_connection`, `test_db_connection`, `list_tables_endpoint`, `pull_query_endpoint`
- `backend/app/modules/flowstat/api/export.py`: `export_excel`, `PDFExportRequest`, `AnalysisPDFExportRequest`, `export_pdf`, `export_analysis_pdf`, `CSVExportRequest`, `export_csv`, `PowerPointExportRequest`, `WordExportRequest`, `export_powerpoint`, `export_word`, `export_analysis_powerpoint_get`, `export_analysis_word_get`, `export_field_statistics_excel`, `export_field_statistics_pdf`
- `backend/app/modules/flowstat/api/full_report.py`: `generate_full_report`
- `backend/app/modules/flowstat/api/fuzzy_match.py`: `find_duplicates`, `tune_threshold`, `get_dependencies`
- `backend/app/modules/flowstat/api/geo_sessions.py`: `list_geo_sessions`, `get_geo_session`, `create_geo_session`, `update_geo_session`, `delete_geo_session`, `duplicate_geo_session`, `toggle_pin_geo_session`, `upload_thumbnail`, `get_thumbnail`
- `backend/app/modules/flowstat/api/health.py`: `health_check`
- `backend/app/modules/flowstat/api/history_audit.py`: `list_template_history`, `export_history_audit`, `get_template_history_version`, `restore_template_history_version`, `list_audit_events`, `get_run_log`
- `backend/app/modules/flowstat/api/intake_briefings.py`: `list_intake_briefings`, `export_intake_briefing`, `create_intake_briefing`, `approve_intake_briefing`, `briefing_readiness`, `apply_intake_briefing`
- `backend/app/modules/flowstat/api/intake_documents.py`: `list_intake_documents`, `upload_intake_document`, `analyze_intake_document`, `download_intake_document`, `delete_intake_document`, `approve_processing_register_template`
- `backend/app/modules/flowstat/api/jobs.py`: `create_job_endpoint`, `list_jobs_endpoint`, `get_job_endpoint`, `get_job_status_endpoint`, `update_job_endpoint`, `delete_job_endpoint`, `list_all_jobs_endpoint`, `cleanup_jobs_endpoint`
- `backend/app/modules/flowstat/api/llm_audit.py`: `anomaly_explain_endpoint`, `classify_text_endpoint`, `cluster_texts_endpoint`, `detect_unusual_endpoint`, `LlmNodePreviewRequest`, `LlmNodePreviewResponse`, `llm_preview_node`
- `backend/app/modules/flowstat/api/mapping.py`: `apply_mapping`
- `backend/app/modules/flowstat/api/match_compare.py`: `compare`
- `backend/app/modules/flowstat/api/ml.py`: `decision_tree_endpoint`, `random_forest_endpoint`, `xgboost_endpoint`, `lightgbm_endpoint`, `isolation_forest_endpoint`, `kmeans_endpoint`, `hdbscan_endpoint`, `pca_endpoint`, `predict_endpoint`, `explain_shap_endpoint`, `compare_endpoint`
- `backend/app/modules/flowstat/api/model_registry.py`: `list_runs_endpoint`, `get_run_endpoint`, `create_run_endpoint`, `update_run_endpoint`, `list_artifacts_endpoint`, `download_artifact_endpoint`
- `backend/app/modules/flowstat/api/node_handlers.py`: `list_node_handler_schemas`, `get_node_handler_schema`, `get_node_handler_code_preview`
- `backend/app/modules/flowstat/api/node_templates.py`: `list_node_templates`, `create_node_template`, `get_node_template`, `delete_node_template`
- `backend/app/modules/flowstat/api/personnel_costs.py`: `list_personnel_cost_rates`, `list_available_years`, `list_available_grades`, `create_personnel_cost_rate`, `create_personnel_cost_rates_bulk`, `get_personnel_cost_rate`, `update_personnel_cost_rate`, `delete_personnel_cost_rate`
- `backend/app/modules/flowstat/api/pipelines.py`: `list_pipelines`, `get_pipeline`, `create_pipeline`, `update_pipeline`, `patch_pipeline`, `delete_pipeline`, `run_pipeline_endpoint`, `list_runs_for_pipeline`, `reconcile_runs`, `get_run`, `cancel_run`, `create_stream_ticket`, `stream_run_status`, `get_node_mini_stats`, `get_geo_thumbnail`
- `backend/app/modules/flowstat/api/plugins.py`: `list_plugins`, `get_plugin_parameters`, `run_plugin`, `get_job`
- `backend/app/modules/flowstat/api/portable_packages.py`: `export_package`, `import_package`
- `backend/app/modules/flowstat/api/project_archive.py`: `preview_export`, `export_project`, `import_project`
- `backend/app/modules/flowstat/api/project_history.py`: `list_project_history`, `archive_history_entry`, `export_project_history`
- `backend/app/modules/flowstat/api/projects.py`: `list_flowstat_projects`, `get_flowstat_project`, `create_flowstat_project`, `update_flowstat_project`, `delete_flowstat_project`, `create_pipeline_in_project`, `get_ui_layout`, `patch_ui_layout`, `run_project_pipelines`
- `backend/app/modules/flowstat/api/reports.py`: `list_definitions`, `create_definition`, `get_definition`, `update_definition`, `create_version`, `update_version`, `approve_version`, `list_sources`, `preview_report`, `fill_version`, `refresh_definition`, `historical_reproduction_status`, `prepare_historical_version`, `refresh_his_native_definition`, `get_definition_refresh_status`, `force_release_definition_refresh_lock`, `check_report_run_deletion`, `delete_report_run`, `list_definition_runs`, `report_reference`, `review_run`, `run_evidence`, `export_run`
- `backend/app/modules/flowstat/api/sampling.py`: `run_sampling_procedure`, `list_sampling_templates`, `get_sampling_template`
- `backend/app/modules/flowstat/api/sandbox.py`: `get_sandbox_status`, `get_job_status`, `list_all_jobs`
- `backend/app/modules/flowstat/api/schedules.py`: `FlowStatScheduleResponse`, `FlowStatScheduleUpdate`, `FlowStatScheduleExecutionResponse`, `FlowStatScheduleAlertResponse`, `list_schedules`, `list_operational_alerts`, `list_schedule_runs`, `update_schedule`
- `backend/app/modules/flowstat/api/scripts.py`: `ScriptPreviewRequest`, `ScriptErrorDetailModel`, `ScriptPreviewResponse`, `ScriptStatusResponse`, `ScriptValidateRequest`, `ScriptIssueModel`, `ScriptValidateResponse`, `script_status`, `script_validate`, `script_preview`
- `backend/app/modules/flowstat/api/semantic_mapping.py`: `put_semantic_mapping`, `get_semantic_mapping`, `delete_semantic_mapping_role`
- `backend/app/modules/flowstat/api/semantic_roles.py`: `list_semantic_roles`, `create_semantic_role`, `update_semantic_role`, `delete_semantic_role`
- `backend/app/modules/flowstat/api/sharing.py`: `list_shares`, `create_share`, `delete_share`, `update_visibility`
- `backend/app/modules/flowstat/api/statistics.py`: `get_all_field_statistics`, `get_field_statistics`, `recompute_all`, `invalidate_cache`
- `backend/app/modules/flowstat/api/statistics_inference.py`: `correlation`, `correlation_matrix`, `linear_regression_endpoint`, `logistic_regression_endpoint`, `anova_endpoint`, `mann_whitney_endpoint`, `wilcoxon_endpoint`, `bootstrap_ci_endpoint`, `power_endpoint`, `sample_size_endpoint`, `bayesian_error_rate_endpoint`
- `backend/app/modules/flowstat/api/stratification.py`: `stratify`
- `backend/app/modules/flowstat/api/telemetry.py`: `post_performance`
- `backend/app/modules/flowstat/api/templates.py`: `list_templates_endpoint`, `detect_template_endpoint`, `recommend_template_analyses_endpoint`, `list_known_template_definitions_endpoint`, `get_known_template_definition_endpoint`, `get_template_endpoint`, `instantiate_template_endpoint`
- `backend/app/modules/flowstat/api/testdata.py`: `create_config`, `create_config_from_intake_document`, `list_configs`, `get_config`, `update_config`, `delete_config`, `create_version`, `dependency_check`, `preview`, `generate`, `get_run`, `list_runs`, `download_run`, `register_datasource`, `export_yaml`, `import_yaml`, `transfer_preview`, `transfer_apply`
- `backend/app/modules/flowstat/api/transform.py`: `filter_dataframe`, `join_dataframes`, `apply_feature_engineering`
- `backend/app/modules/flowstat/api/upload.py`: `upload_file`
- `backend/app/modules/flowstat/api/user_preferences.py`: `get_node_library_preferences`, `save_node_library_preferences`, `get_ui_preferences`, `save_ui_preferences`
- `backend/app/modules/flowstat/api/workflow_templates.py`: `list_workflow_templates`, `get_workflow_template`, `create_workflow_template`, `update_workflow_template`, `delete_workflow_template`, `instantiate_workflow_template`
- `backend/app/modules/flowstat/permissions.py`: `check_flowstat_access`, `require_flowstat_execute`, `require_flowstat_view`, `require_flowstat_admin`, `require_flowstat_verify`, `require_flowstat_replay`, `require_flowstat_export`, `get_owner_id`, `filter_by_ownership`, `assert_can_view`, `assert_can_edit`, `assert_is_owner_or_admin`
- `backend/app/modules/flowstat/runtime.py`: `health`, `status`
- `backend/app/modules/flowstat/services/agent_onboarding_service.py`: `action_plan`, `validate_plan`, `contract_document`
- `backend/app/modules/flowstat/services/aging_service.py`: `compute_aging_pure`, `compute_aging`
- `backend/app/modules/flowstat/services/analysis_core_service.py`: `run_grouping`, `run_stratification`, `run_age_analysis`, `run_heatmap`, `run_benford`, `run_duplicates`, `run_gap_analysis`, `run_outlier_zscore`, `run_outlier_tukey`, `run_outlier`, `run_sampling`
- `backend/app/modules/flowstat/services/api_connection_service.py`: `create_connection`, `list_connections`, `load_connection_or_404`, `update_connection`, `delete_connection`, `parse_delimited_table`, `parse_excel_workbook`, `detect_response_format`, `uses_genesis_job_mode`, `parse_bundesbank_csv`, `parse_eurostat_jsonstat`, `parse_genesis_ffcsv`, `execute_request`, `GenesisJobError`, `GenesisJobConfig`, `GenesisJobRun`, `build_genesis_job_config`, `extract_genesis_job_name`, `submit_genesis_job`, `poll_genesis_job`, `fetch_genesis_job_result`, `run_genesis_job`, `probe_genesis_job`, `test_connection`, `validate_pull_dataframe`, `resolve_pull_project_id`, `pull_api`
- `backend/app/modules/flowstat/services/audit_service.py`: `log_audit_event`, `log_structured_event`, `list_audit_events`, `get_client_info`, `build_change_log`
- `backend/app/modules/flowstat/services/audit_tests_service.py`: `duplicate_exact`, `gap_detection`, `benford_test`, `round_number_test`, `same_same_different`, `same_same_same`, `cutoff_test`, `sequence_test`
- `backend/app/modules/flowstat/services/audit_trail_service.py`: `log_step`, `list_trail`, `replay_pipeline`, `verify_run`, `replay_run`, `list_trail_by_run_uuid`, `list_runs_with_trail`
- `backend/app/modules/flowstat/services/auto_report_service.py`: `generate_word_report`, `generate_pdf_report`
- `backend/app/modules/flowstat/services/automl_forecast_service.py`: `compare_forecasts`
- `backend/app/modules/flowstat/services/automl_service.py`: `run_automl`
- `backend/app/modules/flowstat/services/belegliste_analysis_service.py`: `normalize_label`, `detect_vp_gj_template`, `normalize_belegliste`, `analyze_belegliste`, `read_belegliste_excel`
- `backend/app/modules/flowstat/services/bpmn_analyzer.py`: `TaskProperties`, `ProcessAnalysis`, `BpmnAnalyzer`, `analyze_bpmn`
- `backend/app/modules/flowstat/services/bpmn_export.py`: `BpmnExcelExporter`, `export_bpmn_to_excel`, `export_bpmn_to_pdf`
- `backend/app/modules/flowstat/services/capability_service.py`: `get_capabilities`
- `backend/app/modules/flowstat/services/chart_service.py`: `histogram`, `scatter`, `correlation_matrix`, `pareto`, `lorenz_curve`, `ecdf`, `timeseries_decompose`, `timeseries_forecast`, `missing_data_map`, `parallel_coordinates`, `calendar_heatmap`, `preview_aesthetic`
- `backend/app/modules/flowstat/services/co2_auswertung_service.py`: `Einsparangabe`, `VorhabenEinsparung`, `rechne_in_t_co2`, `bewilligungsjahr_aus_zeitraum`, `lade_vorhaben`, `KohortenStatistik`, `VorhabenBewertung`, `AusgeschlossenesVorhaben`, `PlausibilitaetsErgebnis`, `berechne_plausibilitaet`, `plausibilitaet_pius`, `KohortenZielerreichung`, `ZielerreichungsErgebnis`, `berechne_zielerreichung`, `zielerreichung_co2`
- `backend/app/modules/flowstat/services/custom_dashboard_service.py`: `create_dashboard`, `update_dashboard`, `duplicate_dashboard`, `serialize_dashboard`, `serialize_list_item`
- `backend/app/modules/flowstat/services/custom_node_service.py`: `CustomNodeError`, `CustomNodeValidationError`, `CustomNodeNotFoundError`, `CustomNodePermissionError`, `CustomNodeConflictError`, `can_view_definition`, `is_owner_or_admin`, `assert_can_view_definition`, `assert_owner_or_admin`, `slugify`, `validate_slug`, `uniquify_slug`, `compute_code_sha256`, `compute_schema_sha256`, `validate_param_schema`, `validate_icon_key`, `validate_category`, `validate_language`, `validate_code`, `build_handler_schema`, `list_visible_catalog`, `get_visible_version_by_runtime_uuid`, `validate_params_for_execution`, `create_definition_with_first_version`, `update_definition_metadata`, `archive_definition`, `create_new_draft_version`, `update_draft_version`, `publish_version`, `retire_version`, `get_definition_or_404`, `get_version_or_404`, `build_export_package`, `import_package`
- `backend/app/modules/flowstat/services/data_manipulation_service.py`: `append_dataframes_pure`, `append_dataframes`, `merge_dataframes_pure`, `merge_dataframes`, `evaluate_formula`, `add_calculated_field_pure`, `add_calculated_field`, `preview_calculated_field_pure`, `preview_calculated_field`, `extract_postal_code_pure`, `extract_postal_code`, `map_plz_to_nuts3_pure`, `map_plz_to_nuts3`, `enrich_plz_pure`, `enrich_plz`, `build_pivot_pure`, `unpivot_pure`, `unpivot`, `build_pivot`
- `backend/app/modules/flowstat/services/data_quality_contract_service.py`: `evaluate`, `evaluate_storage`
- `backend/app/modules/flowstat/services/data_source_diagnostics_service.py`: `diagnose_dataframe`
- `backend/app/modules/flowstat/services/data_source_origin.py`: `classify`, `derived_condition`, `origin_expression`, `apply_origin_filter`
- `backend/app/modules/flowstat/services/dataframe_service.py`: `DataFrameCacheEntry`, `cache_dataframe`, `get_dataframe`, `assert_cache_owner`, `load_and_cache`, `apply_mapping`, `cleanup_expired_dataframes`, `get_cache_stats`, `delete_dataframe`, `cache_dataframe_persistent`, `get_dataframe_persistent`, `delete_dataframe_persistent`, `filter_dataframe`, `join_dataframes`, `apply_feature_engineering_operations`
- `backend/app/modules/flowstat/services/dataframe_storage_service.py`: `invalidate_parquet_cache`, `save_dataframe`, `load_dataframe`, `load_dataframe_with_record`, `require_dataframe_view`, `list_dataframes`, `delete_dataframe`, `get_storage_info`, `cleanup_expired`, `lineage_key`, `link_previous_version`, `get_version_history`
- `backend/app/modules/flowstat/services/db_connection_service.py`: `encrypt_connection_string`, `decrypt_connection_string`, `create_connection`, `list_connections`, `load_connection_or_404`, `update_connection`, `delete_connection`, `test_connection`, `update_test_status`, `list_tables`, `assert_read_only_sql`, `pull_query`
- `backend/app/modules/flowstat/services/de_numbers.py`: `parse_de_number`, `klassifiziere_zellen`, `parse_de_series`
- `backend/app/modules/flowstat/services/dsfa_service.py`: `render_dsfa_threshold_analysis_docx`
- `backend/app/modules/flowstat/services/enrichment_service.py`: `columns_param`, `enrich`
- `backend/app/modules/flowstat/services/esi_analysis_service.py`: `ESIAnalysisService`
- `backend/app/modules/flowstat/services/evidence_retention_service.py`: `build_protection_index`, `filter_protected_storage_ids`, `get_retention_status`
- `backend/app/modules/flowstat/services/explainability_service.py`: `compute_shap`, `persist_results`
- `backend/app/modules/flowstat/services/export_service.py`: `build_excel_export`, `build_pdf_export`, `build_analysis_pdf_export`, `build_powerpoint_export`, `build_word_export`
- `backend/app/modules/flowstat/services/field_statistics_export.py`: `build_field_statistics_excel`, `build_field_statistics_pdf`
- `backend/app/modules/flowstat/services/field_statistics_service.py`: `compute_field_statistics`, `compute_all_fields`, `compute_dataframe_hash`, `get_or_compute_field`, `get_or_compute_all`, `invalidate_cache`
- `backend/app/modules/flowstat/services/file_service.py`: `save_upload_file`, `save_testdata_source_file`, `save_testdata_source_bytes`
- `backend/app/modules/flowstat/services/forecast_service.py`: `run_forecast`
- `backend/app/modules/flowstat/services/formula_validation.py`: `FormulaIssue`, `validate_formula`
- `backend/app/modules/flowstat/services/fuzzy_match_service.py`: `kölner_phonetik`, `fuzzy_duplicates`, `threshold_tune`, `get_dependency_status`
- `backend/app/modules/flowstat/services/geo/classifiers.py`: `compute_breaks`
- `backend/app/modules/flowstat/services/geo/polygons.py`: `load_nuts3_polygons`, `load_nuts2_polygons`, `load_nuts1_polygons`, `load_plz_polygons`, `plz_to_centroid`, `data_dir`, `has_real_polygons`
- `backend/app/modules/flowstat/services/geo/rendering.py`: `colors_for_breaks`, `render_choropleth_thumbnail`, `render_marker_thumbnail`
- `backend/app/modules/flowstat/services/geo_session_service.py`: `create_session`, `update_session`, `duplicate_session`, `toggle_pin`, `update_thumbnail`, `build_thumbnail_url`, `serialize_session`
- `backend/app/modules/flowstat/services/his_erhebung_harmonisierung_service.py`: `spalte_ausgaben_jahr`, `spalte_zuwendung_jahr`, `zielspalten`, `Spaltenzuordnung`, `erkenne_spalten`, `regierungsbezirk_aus_nuts`, `bestimme_erhebungsjahr`, `harmonisiere`, `fuehre_zusammen`, `harmonisiere_ruecklaeufe`, `projektion_fuer_berichtsobjekte`
- `backend/app/modules/flowstat/services/his_fact_plan_service.py`: `digest`, `number`, `fmt`, `source_catalog`, `compile_plan`, `validate_fact_plan`, `legend_text`, `generate_fact_plan`
- `backend/app/modules/flowstat/services/his_historical_service.py`: `digest`, `load_package`, `is_historical`, `historical_query`, `validate_version`, `assess`, `create_version`, `build_snapshot`
- `backend/app/modules/flowstat/services/his_native_baseline_builder.py`: `HisNativeBaselineError`, `build_his_native_baseline`, `write_his_native_baseline`
- `backend/app/modules/flowstat/services/his_native_release_service.py`: `HisNativeRenderGateError`, `create_his_native_candidate_run`, `create_his_native_report_run`, `evaluate_his_native_render_gate`, `his_text_claim_findings`, `finalize_his_native_render_gate`
- `backend/app/modules/flowstat/services/his_native_source_onboarding_service.py`: `HisNativeReleaseGateError`, `HisSourcePlanItem`, `HisSourceFinding`, `HisSourceOnboardingResult`, `load_json`, `build_source_plan`, `versioned_object_frame`, `validate_figure_runtime_inputs`, `validate_table_runtime_inputs`, `wire_source_object`, `build_native_release_gate`, `blocked_parity_release_gate`, `source_plan_findings`, `oracle_value_finding`, `prose_number_finding`, `validate_transformable_raw_sources`, `onboard_his_native_sources`
- `backend/app/modules/flowstat/services/his_object_transform_service.py`: `transform_funding_figure`, `published_value_gate`, `transform_bip_growth_table`, `published_table_value_gate`
- `backend/app/modules/flowstat/services/his_oracle_value_gate_service.py`: `Zahl`, `parse_zahl`, `nachkommastellen`, `werte_gleich`, `oracle_tabellenzeilen`, `laufzeit_tabellenzeilen`, `oracle_gedruckte_zahlen`, `abbildungs_sollwerte`, `vergleiche_tabelle`, `vergleiche_abbildung`, `lade_datenstand_katalog`, `datenstand_fuer`, `beurteile_objekt`, `pruefe_wertekontrolle`, `kurzbericht`
- `backend/app/modules/flowstat/services/his_prose_generation_service.py`: `HisProseGenerationError`, `SlotQuelle`, `slot_vertrag`, `correct_his_source_scope`, `resolve_slot_sources`, `generate_his_prose_texts`
- `backend/app/modules/flowstat/services/his_prose_number_gate_service.py`: `aktiver_slotmaster`, `Absatz`, `Textzahl`, `Objektwert`, `Zuordnung`, `lade_slotmaster_absaetze`, `ist_fliesstext`, `textzahlen`, `ist_jahreszahl`, `ordne_objekt_zu`, `objektwerte`, `einheiten_vertraeglich`, `vergleiche_textzahl`, `beurteile_absatz`, `pruefe_prosa_zahlen`, `kurzbericht`, `widerspruchsbericht`
- `backend/app/modules/flowstat/services/his_resolution_service.py`: `resolution_for`
- `backend/app/modules/flowstat/services/his_sector_correction_service.py`: `fmt`, `ratio`, `aggregate`, `fue_rows`, `funding_rows`, `apply_sector_corrections`
- `backend/app/modules/flowstat/services/his_source_deviation_service.py`: `unresolved_source_notices`, `apply_source_deviation_notices`
- `backend/app/modules/flowstat/services/his_statistical_correction_service.py`: `real_growth`, `national_rate`, `apply_corrections`
- `backend/app/modules/flowstat/services/history_audit_export_service.py`: `FlowStatAuditExportFormat`, `FlowStatAuditExportScope`, `prepare_export`, `build_filename`, `build_xlsx`, `build_html`, `build_pdf`
- `backend/app/modules/flowstat/services/history_export_service.py`: `build_xlsx`, `build_csv`, `build_pdf`, `build_docx`
- `backend/app/modules/flowstat/services/indicator_metadata_service.py`: `indicator_metadata`
- `backend/app/modules/flowstat/services/intake_analysis_service.py`: `analyze_document_content`, `run_document_analysis`
- `backend/app/modules/flowstat/services/intake_application_service.py`: `approve_briefing`, `apply_approved_briefing`
- `backend/app/modules/flowstat/services/intake_document_service.py`: `validate_upload`, `create_document_version`, `safe_download_filename`
- `backend/app/modules/flowstat/services/intake_readiness_service.py`: `intake_readiness`
- `backend/app/modules/flowstat/services/job_service.py`: `create_job`, `update_job_status`, `get_job`, `list_jobs`, `cancel_job`, `cleanup_old_jobs`
- `backend/app/modules/flowstat/services/llm_audit_service.py`: `LlmUnavailableError`, `LlmThrottledError`, `LlmTimeoutError`, `anomaly_explain`, `classify_booking_text`, `cluster_booking_texts`, `detect_unusual_text`
- `backend/app/modules/flowstat/services/match_compare_service.py`: `compare_dataframes_pure`, `compare_dataframes`
- `backend/app/modules/flowstat/services/mini_stats_service.py`: `find_latest_node_run`, `build_mini_stats`
- `backend/app/modules/flowstat/services/ml_service.py`: `train_decision_tree`, `train_random_forest`, `train_xgboost`, `train_lightgbm`, `train_isolation_forest`, `train_kmeans`, `train_hdbscan`, `train_pca`, `predict`, `explain_with_shap`, `compare_models`, `load_storage`
- `backend/app/modules/flowstat/services/model_registry_service.py`: `compute_data_hash`, `register_run`, `complete_run`, `store_artifact`, `load_artifact`, `list_runs`, `get_run`, `list_artifacts_for_run`
- `backend/app/modules/flowstat/services/monthly_content_registry_service.py`: `load_registry`, `registry_hash`, `registry_frames`, `validate_runtime_provenance`, `validate_registry`
- `backend/app/modules/flowstat/services/monthly_native_onboarding_service.py`: `berichtsmonat`, `report_ausgabe`, `registry_datenstand`, `eckwerte_board_params`, `konj_board_params`, `GateFinding`, `OnboardingResult`, `LiveReihe`, `live_reihen_konfiguration`, `link_live_series_connections`, `live_connection_finding`, `seed_frames`, `load_and_remap_spec`, `editor_managed_spec`, `validate_oracle_file`, `compute_indicator_boards`, `validate_indicator_board_parity`, `validate_tafel_zeilen`, `validate_seed_frames`, `alq_rohform_beispiel`, `validate_alq_live_shaping`, `validate_live_seed_frames`, `validate_native_spec`, `spec_output_nodes`, `validate_pipeline_wiring`, `validate_pipeline_run_after_wiring`, `seed_reihen_fuer_wiring`, `onboard_monthly_native`
- `backend/app/modules/flowstat/services/node_code_preview_service.py`: `build_code_preview`
- `backend/app/modules/flowstat/services/node_handler_schemas/_params.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/api.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/audit.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/bericht_text.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/data.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/database.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/faker.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/fuzzy.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/geo.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/his_eurostat.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/his_harmonisierung.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/his_official_sources.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/inference.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/kpang.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/llm.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/metrics.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/ml.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/period_metrics.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/plugin.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/prompting.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/reporting.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/sampling.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/table_profile.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handler_schemas/timeseries.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/flowstat/services/node_handlers/aliases.py`: `AutoMLAliasHandler`, `EnrichAliasHandler`
- `backend/app/modules/flowstat/services/node_handlers/analysis.py`: `StatTestHandler`, `build_analysis_handlers`
- `backend/app/modules/flowstat/services/node_handlers/automl_forecast.py`: `AutoMLForecastHandler`
- `backend/app/modules/flowstat/services/node_handlers/base.py`: `NodeResult`, `NodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/bericht_text.py`: `BerichtTextNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/custom.py`: `CustomNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/extension_support.py`: `parameters`, `variant`, `load_input`, `persist`
- `backend/app/modules/flowstat/services/node_handlers/faker_clone.py`: `clone_dataframe_with_faker`, `FakerCloneNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/faker_reference.py`: `build_reference_dummy_frame`, `FakerReferenceNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/forecast.py`: `ForecastNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/fuzzy.py`: `FuzzyDuplicatesNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/geo.py`: `GeoHandler`
- `backend/app/modules/flowstat/services/node_handlers/his_eurostat.py`: `HisEurostatNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/his_harmonisierung.py`: `HisHarmonisierungNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/his_official_sources.py`: `transform_table_10`, `transform_figure_03`, `transform_figure_04`, `transform_table_05`, `transform_figure_06`, `transform_table_22`, `HisOfficialSourcesNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/io.py`: `ApiPullNodeHandler`, `DbPullNodeHandler`, `UploadNodeHandler`, `DataFrameNodeHandler`, `ExportNodeHandler`, `ScheduleNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/kpang_regelwerk.py`: `build_kpang_code`, `KpangRegelwerkNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/llm.py`: `LlmAnalysisNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/metrics.py`: `KpiNodeHandler`, `ComparePeriodsNodeHandler`, `KonzentrationNodeHandler`, `indicator_board_pure`, `IndicatorBoardNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/period_metrics.py`: `calculate_period_metrics`, `PeriodMetricsNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/plugin.py`: `PluginNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/prompting.py`: `build_prompt`, `PromptBuilderNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/sampling.py`: `SamplingNodeHandler`, `build_sampling_handlers`
- `backend/app/modules/flowstat/services/node_handlers/script.py`: `ScriptNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/table_profile.py`: `build_table_profile`, `TableProfileNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/template_handlers.py`: `MappingNodeHandler`, `StratificationNodeHandler`, `GenericSamplingNodeHandler`, `AuditTestsNodeHandler`, `AgingNodeHandler`, `AutoReportNodeHandler`, `run_manifest_frame`, `RunManifestNodeHandler`, `ChartNodeHandler`, `StatisticsInferenceNodeHandler`, `BeleglisteAnalysisNodeHandler`, `VpGjProjectSheetAnalysisNodeHandler`, `VorhabenContextLinkNodeHandler`, `MLNodeHandler`, `DataManipulationNodeHandler`, `AggregateNodeHandler`, `MatchCompareNodeHandler`, `build_template_handlers`
- `backend/app/modules/flowstat/services/node_handlers/testdata_faker.py`: `TestdataFakerNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/timeseries.py`: `calculate_timeseries_metrics`, `TimeseriesMetricsNodeHandler`
- `backend/app/modules/flowstat/services/node_handlers/transform.py`: `FilterNodeHandler`, `JoinNodeHandler`, `FeatureEngineeringHandler`, `ColumnMappingHandler`, `crosstab_flags_pure`, `CrosstabFlagsNodeHandler`, `series_shape_pure`, `SeriesShapeNodeHandler`
- `backend/app/modules/flowstat/services/node_input_validation.py`: `NodeInputValidationError`, `require_columns`, `coerce_numeric`, `require_numeric_column`, `require_numeric_value`
- `backend/app/modules/flowstat/services/pipeline_executor.py`: `PipelineExecutionError`, `PipelineExecutor`
- `backend/app/modules/flowstat/services/pipeline_run_reconcile_service.py`: `verwaiste_laeufe`, `reconcile_abandoned_pipeline_runs`
- `backend/app/modules/flowstat/services/plot_render_service.py`: `normalize_plotly_spec`, `render_plotly_to_png`, `render_plotly_to_svg`, `get_placeholder_png`
- `backend/app/modules/flowstat/services/plugin_loader.py`: `PluginValidationError`, `PluginMetadata`, `LoadedPlugin`, `load_plugin_from_path`
- `backend/app/modules/flowstat/services/plugin_service.py`: `PluginConflictError`, `PluginNotFoundError`, `PluginInactiveError`, `SandboxJobNotFoundError`, `register_plugin_from_bytes`, `list_plugins`, `set_activation_state`, `get_plugin_parameters`, `run_plugin`, `get_job`
- `backend/app/modules/flowstat/services/portable_package_service.py`: `export_portable_package`, `import_portable_package`
- `backend/app/modules/flowstat/services/processing_record_service.py`: `consolidate_processing_record_notes`, `prepare_original_vvt_record`, `prepare_two_pilot_vvt_records`, `original_vvt_row`, `render_two_application_vvt_xlsx`, `render_processing_record_xlsx`
- `backend/app/modules/flowstat/services/project_archive_service.py`: `export_project_to_archive`, `import_project_from_archive`, `get_export_preview`
- `backend/app/modules/flowstat/services/project_history_service.py`: `HistoryExportTooLargeError`, `available_users_for_project`, `list_history`, `compute_list_hash`, `archive_entry`, `export_history`
- `backend/app/modules/flowstat/services/project_sheet_extraction_service.py`: `detect_project_workbook`, `analyze_project_workbook`
- `backend/app/modules/flowstat/services/replay_sandbox.py`: `replay_sandbox`, `active_sandbox`, `apply_to_storage_kwargs`, `is_sandbox_metadata`
- `backend/app/modules/flowstat/services/report_binding_service.py`: `substitute_placeholders`, `materialize_layout_parameters`, `unresolved_layout_placeholders`, `apply_transform_steps`, `binding_to_table`, `binding_to_chart`, `repeat_dimension_values`, `expand_repeat_block`
- `backend/app/modules/flowstat/services/report_contract_service.py`: `collect_indicator_board_summaries`, `validate_report_activation_gate`, `validate_report_contract`
- `backend/app/modules/flowstat/services/report_evidence_service.py`: `report_evidence`, `object_pages`
- `backend/app/modules/flowstat/services/report_llm_text_service.py`: `extract_numbers`, `verify_numbers`, `verify_semantic_claims`, `LlmTextVerificationError`, `source_block_data`, `AbgeleiteterWert`, `derive_facts`, `stilverstoesse_monitoring`, `generate_analysis_text`
- `backend/app/modules/flowstat/services/report_parity_service.py`: `audit_native_parity`
- `backend/app/modules/flowstat/services/report_refresh_lock.py`: `ReportRefreshBusyError`, `claim`, `update_context`, `release`, `force_release`, `status`
- `backend/app/modules/flowstat/services/report_refresh_service.py`: `ReportRefreshError`, `create_report_run`, `render_snapshot`, `render_report_artifact`, `persist_report_artifact`, `persist_report_artifacts`, `latest_pipeline_ids_from_layout`, `RefreshPlan`, `plan_refresh`, `refresh_report`
- `backend/app/modules/flowstat/services/report_review_service.py`: `review_state`, `add_review`
- `backend/app/modules/flowstat/services/report_run_deletion_service.py`: `ReportRunDeletionError`, `Schutz`, `Loeschbefund`, `pruefe`, `loesche`, `loesche_viele`
- `backend/app/modules/flowstat/services/response_utils.py`: `require_columns`, `table_response`
- `backend/app/modules/flowstat/services/runtime_service.py`: `release_hash`
- `backend/app/modules/flowstat/services/sampling_service.py`: `run_materiality_assessment`, `run_mus_conservative`, `run_mus_standard`, `run_mus_stratified`, `run_mus_two_periods_combined`, `run_mus_two_periods_separate`, `run_srs_standard`, `run_srs_stratified`, `run_srs_two_periods_combined`, `run_srs_two_periods_separate`, `run_mus_stratified_two_periods_separate`, `run_srs_stratified_two_periods_separate`, `run_difference_estimation_basic`, `run_difference_estimation_ratio`, `run_difference_estimation_regression`, `run_difference_estimation_stratified`, `run_difference_estimation_two_periods`, `run_non_statistical_top_items`, `run_non_statistical_key_items`, `run_non_statistical_judgmental`, `run_non_statistical_haphazard`, `run_non_statistical_stratified_equal_probability`, `run_non_statistical_pps`, `run_non_statistical_stratified_pps`, `run_error_projection`, `run_precision_calculation`, `run_chi_square_goodness_of_fit`, `run_two_sample_t_test`, `run_normality_test`, `run_population_segmentation`
- `backend/app/modules/flowstat/services/sampling_service_rust.py`: `run_materiality_assessment`, `run_mus_conservative`, `run_mus_standard`, `run_mus_stratified`, `run_mus_two_periods_combined`, `run_mus_two_periods_separate`, `run_srs_standard`, `run_srs_stratified`, `run_srs_two_periods_combined`, `run_srs_two_periods_separate`, `run_srs_stratified_two_periods_separate`, `run_error_projection`, `run_precision_calculation`, `run_difference_basic`, `run_difference_ratio`, `run_difference_regression`, `run_difference_stratified`, `run_difference_two_periods`, `run_top_items`, `run_key_items`, `run_haphazard`, `run_judgmental`, `run_pps`, `run_t_test`, `run_chi_square_test`, `run_normality_test`, `run_segmentation_test`
- `backend/app/modules/flowstat/services/sandbox_runner.py`: `SandboxJobStatus`, `SandboxJob`, `submit_plugin_job`, `get_job`, `list_jobs`, `is_docker_available`, `check_docker_image`
- `backend/app/modules/flowstat/services/schedule_service.py`: `evaluate_operational_alerts`, `reconcile_abandoned_executions`, `data_gate_reason`, `validate_schedule_nodes`, `compute_next_run`, `sync_from_pipeline`, `update_schedule_configuration`, `resolve_report_parameters`, `dispatch_due_schedules`, `run_claimed_schedule`, `run_due_schedules`
- `backend/app/modules/flowstat/services/script_execution_service.py`: `ScriptExecutionError`, `ScriptTimeoutError`, `ScriptImageMissingError`, `ScriptDockerUnavailableError`, `ScriptExecutionResult`, `is_docker_available`, `is_image_available`, `image_for_language`, `execute_python`, `execute_r`, `log_execution_audit`, `parse_error_detail`
- `backend/app/modules/flowstat/services/script_validation.py`: `ScriptIssue`, `validate_python_code`
- `backend/app/modules/flowstat/services/semantic_roles.py`: `SemanticRole`, `invalidate_roles_cache`, `get_active_roles`, `get_role`, `list_roles`, `auto_suggest_columns`, `validate_mapping`, `get_mapping`, `resolve_columns_for_role`, `resolve_column_for_role`, `unit_map_for_storage`, `write_mapping`, `remove_role`, `resolve_amount_column`, `resolve_first_input_storage_id`
- `backend/app/modules/flowstat/services/semantic_roles_admin_service.py`: `SemanticRoleNotFoundError`, `SemanticRoleConflictError`, `HistorySchemaConflictError`, `list_roles`, `create_role`, `update_role`, `delete_role`
- `backend/app/modules/flowstat/services/statistics_inference_service.py`: `compute_correlation`, `compute_correlation_matrix`, `linear_regression`, `logistic_regression`, `anova_test`, `mann_whitney_test`, `wilcoxon_test`, `bootstrap_ci`, `compute_power`, `required_sample_size`, `bayesian_error_rate`, `load_df`
- `backend/app/modules/flowstat/services/storage_binding.py`: `node_storage_id`
- `backend/app/modules/flowstat/services/storage_columns_service.py`: `compute_column_statistics`, `build_preview`, `get_cached_column_statistics`, `store_cached_column_statistics`
- `backend/app/modules/flowstat/services/stratification_service.py`: `stratify_pure`, `stratify`
- `backend/app/modules/flowstat/services/template_definition_service.py`: `TemplateDefinitionNotFoundError`, `list_template_definitions`, `get_template_definition`
- `backend/app/modules/flowstat/services/template_seeder.py`: `seed_workflow_templates`
- `backend/app/modules/flowstat/services/template_service.py`: `TemplateNotFoundError`, `list_templates`, `get_template`, `instantiate_template`
- `backend/app/modules/flowstat/services/testdata_config_service.py`: `create_config`, `create_config_from_intake_document`, `update_config`, `create_new_version`, `list_configs`, `delete_config_group`, `run_dependency_check`, `run_preview`, `create_run`, `execute_generation`, `run_full_generation`, `register_as_datasource`, `synthetic_storage_name`, `synthetic_output_filename`, `read_sheet_for_registration`, `export_yaml`, `import_yaml_into_config`
- `backend/app/modules/flowstat/services/testdata_dependency_service.py`: `analyze_dependencies`, `check_resolved`
- `backend/app/modules/flowstat/services/testdata_generation_service.py`: `DataGenerationError`, `exact_numeric_serialization`, `generate_full`, `generate_preview`, `mask_pattern_preserving`
- `backend/app/modules/flowstat/services/testdata_scan_service.py`: `scan_workbook`, `lookup_sheets`, `detect_preset`, `propose_modes`, `read_headers`, `detect_header_block`, `detect_header_row`, `first_data_row`, `partial_mask`
- `backend/app/modules/flowstat/services/testdata_transfer_service.py`: `propose_transfer`, `apply_transfer`
- `backend/app/modules/flowstat/services/testdata_validation_service.py`: `validate_output`
- `backend/app/modules/flowstat/services/threshold_service.py`: `UnknownScopeError`, `SchwellenwertSatz`, `get_schwellenwerte`, `set_schwellenwerte`
- `backend/app/modules/flowstat/services/upload_review_import_service.py`: `import_upload_review_files`
- `backend/app/modules/flowstat/services/vorhaben_context_service.py`: `compare_project_and_beleglisten`, `analyze_belegliste_df`
- `backend/app/modules/flowstat/services/workflow_template_history_service.py`: `snapshot_template`, `diff_metadata`, `record_template_version`, `list_template_versions`, `get_template_version`, `count_template_versions`
- `backend/app/modules/flowstat/services/workflow_template_service.py`: `WorkflowTemplateNotFound`, `WorkflowTemplateForbidden`, `list_visible`, `get_visible`, `create`, `update`, `restore_version`, `delete`, `instantiate`
- `backend/app/modules/flowstat/services/workshop_dashboard_service.py`: `WorkshopDashboardError`, `build_layout`, `ensure_workshop_dashboard`
- `backend/app/modules/flowstat/services/workshop_protocol_service.py`: `workshop_payload_sha256`, `render_workshop_protocol_docx`, `render_workshop_protocol_html`

### backend/app/modules/lernmodule

- `backend/app/modules/lernmodule/api/markers.py`: `create_marker`, `get_marker`, `update_marker`, `delete_marker`, `reorder_markers`
- `backend/app/modules/lernmodule/api/media.py`: `upload_media`, `get_media_file`, `update_media`, `delete_media`, `reorder_media`, `upload_file`, `download_file`, `delete_file`
- `backend/app/modules/lernmodule/api/projects.py`: `list_projects`, `create_project`, `get_project`, `update_project`, `delete_project`, `upload_pdf`, `get_project_pdf`, `export_project`, `import_project`
- `backend/app/modules/lernmodule/permissions.py`: `get_current_user_for_lernmodule`, `require_lernmodule_access`, `require_lernmodule_editor`, `require_lernmodule_admin`
- `backend/app/modules/lernmodule/services/marker_service.py`: `MarkerService`
- `backend/app/modules/lernmodule/services/media_service.py`: `UploadResult`, `LernmodulMediaService`
- `backend/app/modules/lernmodule/services/project_service.py`: `ProjectService`

### backend/app/modules/memory

- `backend/app/modules/memory/api/memory_router.py`: `search_memory`, `list_entries`, `create_entry`, `get_entry`, `update_entry`, `delete_entry`, `list_chronicle`, `mark_chronicle_distilled`, `knowledge_gaps`, `eval_set`, `list_projects`, `get_project_context`, `get_stats`, `health_check`, `trigger_chat_import`, `trigger_static_import`
- `backend/app/modules/memory/config.py`: `MemoryCategory`, `MemorySourceType`, `normalize_project`
- `backend/app/modules/memory/mcp_http_server.py`: `standard_resource`, `standard_historisch_resource`, `skill_resource`, `skill_historisch_resource`, `vorlage_resource`, `vermerk_erstellen`, `pruefbericht_erstellen`, `terminologie_bereinigen`, `arbeitsmappe_formatieren`, `skills_list`, `vorschlag_einreichen`, `memory_search`, `memory_add`, `memory_stats`, `knowledge_search`, `knowledge_get`, `knowledge_health`, `knowledge_capabilities`, `humanizer_get_rules`, `humanizer_get_persona`, `humanizer_list_profiles`, `humanizer_check`, `standards_list`, `standards_get`, `standards_diff`, `asset_get`, `deviation_report`, `document_compare_reason`, `check_terminologie`, `check_document`, `check_workbook`, `check_workbook_schema`, `humanizer_humanize`, `MCPNutzungsMiddleware`, `health`, `oauth_login`, `register_lenient`
- `backend/app/modules/memory/mcp_login_ratelimit.py`: `client_source`, `LoginVerdict`, `CounterBackend`, `InMemoryCounters`, `RedisCounters`, `make_backend`, `LoginRateLimiter`
- `backend/app/modules/memory/mcp_oauth.py`: `StatelessMemoryOAuthProvider`, `StatelessTokenVerifier`, `check_password`, `decode_ticket`, `make_code_redirect`, `redirect_uri_allowed`
- `backend/app/modules/memory/mcp_server.py`: `list_tools`, `call_tool`, `list_resources`, `read_resource`, `main`
- `backend/app/modules/memory/services/memory_chronicle.py`: `is_chronicle_category`, `add_chronicle`, `list_chronicle`, `mark_distilled`, `chronicle_stats`
- `backend/app/modules/memory/services/memory_embedding.py`: `embed_text`, `embed_texts`
- `backend/app/modules/memory/services/memory_gaps.py`: `knowledge_gaps`, `gaps_markdown`
- `backend/app/modules/memory/services/memory_import.py`: `import_chat_history`, `import_conversations`, `import_static_files`
- `backend/app/modules/memory/services/memory_metrics.py`: `record_entry_created`, `record_hook_execution`, `record_embedding_duration`, `record_api_error`, `record_search_duration`, `record_cache_hit`, `record_cache_miss`, `update_pending_embeddings`
- `backend/app/modules/memory/services/memory_quality.py`: `ValidationError`, `validate_content`, `find_secret`, `validate_project`, `validate_tags`, `validate_category`, `infer_category_from_content`, `extract_semantic_tags`, `enrich_tags`, `calculate_confidence`, `validate_and_enrich`
- `backend/app/modules/memory/services/memory_search.py`: `search`, `invalidate_cache`
- `backend/app/modules/memory/services/memory_service.py`: `add_entry`, `update_entry`, `delete_entry`, `list_entries`, `get_entry`, `get_stats`, `eval_pairs`, `get_project_context`

### backend/app/modules/registratur

- `backend/app/modules/registratur/api.py`: `cockpit_lesen`, `migration_nachweisen`, `audit_pruefen`, `regression_starten`, `global_suchen`, `objekte_lesen`, `objekt_lesen`, `entwurf_ablegen`, `entwurf_loeschen`, `vergleich_lesen`, `objekt_freigeben`, `rueckmeldungen_lesen`, `rueckmeldung_anlegen`, `rueckmeldung_aendern`, `nutzung_lesen`, `nutzung_erfassen`, `einbindungskarten`, `client_zugaenge`, `client_zugang_entziehen`, `vorlagen_lesen`, `anlage_hochladen`, `skill_hochladen`
- `backend/app/modules/registratur/auth.py`: `require_admin`, `require_recent_admin`
- `backend/app/modules/registratur/models.py`: `RegistraturObjekt`, `RegistraturFassung`, `RegistraturRegelanker`, `RegistraturAnlage`, `RegistraturAbhaengigkeit`, `RegistraturRueckmeldung`, `RegistraturNutzungsereignis`, `RegistraturNutzungsMonat`, `RegistraturAuditEintrag`, `RegistraturRegressionstest`, `RegistraturClientToken`
- `backend/app/modules/registratur/reader.py`: `RegistraturLeser`
- `backend/app/modules/registratur/regression.py`: `erstbestand_anlegen`, `ausfuehren`
- `backend/app/modules/registratur/retention.py`: `aufbewahrung_ausfuehren`
- `backend/app/modules/registratur/schemas.py`: `EntwurfSpeichern`, `FreigabeAnfordern`, `RueckmeldungAendern`, `RueckmeldungAnlegen`, `Seitenaufruf`, `SucheTreffer`, `ObjektUebersicht`, `NutzungErfassen`
- `backend/app/modules/registratur/service.py`: `sha256_text`, `skill_sicherheitspruefung`, `tenant_fuer_verwaltung`, `bestand_initialisieren`, `anlagen_initialisieren`, `migrationsnachweis`, `auditieren`, `audit_integritaet`, `objekt_holen`, `entwurf_speichern`, `entwurf_verwerfen`, `freigeben`, `objekt_payload`, `vergleich_payload`, `cockpit`, `suche`, `nutzung_auswertung`
- `backend/app/modules/registratur/skill_migration.py`: `skills_migrieren`
- `backend/app/modules/registratur/tasks.py`: `aufbewahrung`
- `backend/app/modules/registratur/uploads.py`: `UploadAbgelehnt`, `GepruefterUpload`, `anlage_pruefen`, `skill_archiv_pruefen`

### backend/app/modules/reporting

- `backend/app/modules/reporting/cd_report_service.py`: `build_report_body_docx`, `build_cd_docx`, `build_cd_pdf`
- `backend/app/modules/reporting/evidence_annex.py`: `EvidenceContext`, `AnnexOptions`, `validate_evidence_annex_config`, `annex_options_from_snapshot`, `split_manifest`, `append_evidence_annex`
- `backend/app/modules/reporting/his_chart_render_service.py`: `build_his_figure`, `render_his_chart_png`
- `backend/app/modules/reporting/his_hybrid_config.py`: `his_branding_by_page`
- `backend/app/modules/reporting/his_native_slot_report_service.py`: `Slotmaster`, `Zellensatz`, `SlotAbsaetze`, `build_his_native_slot_docx`
- `backend/app/modules/reporting/his_native_titelei.py`: `Titelei`, `titelei_aus_snapshot`, `wende_titelei_an`
- `backend/app/modules/reporting/hybrid_report_service.py`: `BrandingOverlay`, `build_hybrid_pdf`
- `backend/app/modules/reporting/monthly_hybrid_pdf.py`: `MonthlyHybridError`, `build_monthly_hybrid_pdf`
- `backend/app/modules/reporting/render_profiles.py`: `ReportRenderProfileError`, `render_profile_metadata`, `resolve_render_profile`

### backend/app/modules/schulung

- `backend/app/modules/schulung/api/access.py`: `get_visible_course_or_404`, `get_visible_chapter_or_404`, `get_visible_nugget_or_404`, `get_visible_quiz_or_404`
- `backend/app/modules/schulung/api/admin.py`: `get_dashboard_stats`, `list_admin_courses`, `get_course_analytics`, `get_user_reports`, `list_groups`, `create_group`, `get_group`, `update_group`, `delete_group`, `add_group_member`, `remove_group_member`, `create_assignment`, `list_assignments`, `delete_assignment`, `StatsOverview`, `CourseStatsItem`, `UserStatsItem`, `QuizStatsItem`, `ActivityTrendDay`, `get_stats_overview`, `get_course_stats`, `get_user_stats`, `get_quiz_stats`, `get_activity_trend`, `export_reports`, `get_content_gaps`, `list_learning_paths`, `get_learning_path`, `create_learning_path`, `update_learning_path`, `delete_learning_path`, `add_course_to_path`, `remove_course_from_path`, `update_course_order`
- `backend/app/modules/schulung/api/certificates.py`: `CertificateOut`, `CertificateListOut`, `CertificateVerifyOut`, `generate_certificate_number`, `certificate_out_from_model`, `generate_verification_token`, `calculate_course_score`, `check_course_completion`, `log_action`, `get_my_certificates`, `get_certificate`, `generate_certificate`, `download_certificate_pdf`, `verify_certificate`
- `backend/app/modules/schulung/api/chapters.py`: `list_chapters`, `get_chapter`, `create_chapter`, `update_chapter`, `delete_chapter`, `ChapterReorderRequest`, `reorder_chapters`, `upload_chapter_pdf`, `delete_chapter_pdf`, `get_chapter_pdf_info`
- `backend/app/modules/schulung/api/courses.py`: `list_courses`, `list_my_courses`, `get_course`, `create_course`, `update_course`, `delete_course`, `publish_course`, `archive_course`, `get_course_structure`, `duplicate_course`
- `backend/app/modules/schulung/api/gamification.py`: `calculate_level`, `get_or_create_user_stats`, `award_xp`, `check_achievements`, `update_streak`, `get_user_stats`, `get_gamification_dashboard`, `mark_achievement_notified`, `get_all_achievements`, `get_earned_achievements`, `get_leaderboard`, `get_activity_heatmap`, `get_xp_history`, `log_learning_session`
- `backend/app/modules/schulung/api/nuggets.py`: `MarkdownPreviewRequest`, `MarkdownPreviewResponse`, `preview_markdown`, `list_nuggets`, `get_nugget`, `create_nugget`, `update_nugget`, `delete_nugget`, `upload_image`, `delete_image`, `upload_pdf`, `delete_pdf`, `upload_document`, `delete_document`, `ReorderRequest`, `reorder_nuggets`, `PdfHighlight`, `PdfHighlightsUpdate`, `update_pdf_highlights`, `bulk_import_nuggets`
- `backend/app/modules/schulung/api/privacy.py`: `PersonalDataOut`, `ActivityLogItem`, `ConsentItem`, `ConsentUpdate`, `DataRetentionInfo`, `DeletionRequestCreate`, `DeletionRequestOut`, `ExportRequestOut`, `log_action`, `get_client_ip`, `get_personal_data`, `get_retention_info`, `get_activity_log`, `get_consents`, `update_consent`, `request_data_export`, `download_export`, `request_deletion`, `get_deletion_status`
- `backend/app/modules/schulung/api/progress.py`: `get_nugget_progress`, `update_nugget_progress`, `mark_nugget_complete`, `get_course_progress`, `calculate_sm2`, `get_due_reviews`, `submit_review`, `enable_spaced_repetition`, `suspend_spaced_repetition`
- `backend/app/modules/schulung/api/quizzes.py`: `list_quizzes`, `get_quiz`, `create_quiz`, `update_quiz`, `delete_quiz`, `submit_answer`, `check_answer`, `get_quiz_stats`
- `backend/app/modules/schulung/api/repetition.py`: `RepetitionItemOut`, `RepetitionStatsOut`, `ReviewSubmit`, `ReviewResult`, `AddToRepetitionRequest`, `calculate_sm2`, `log_action`, `calculate_streak`, `get_repetition_stats`, `get_due_items`, `get_all_items`, `add_to_repetition`, `submit_review`, `remove_from_repetition`, `suspend_item`, `resume_item`
- `backend/app/modules/schulung/services/bulk_import_service.py`: `import_from_markdown`, `import_from_zip`
- `backend/app/modules/schulung/services/certificate_service.py`: `build_certificate_verification_url`, `get_grade_label`, `generate_certificate_pdf`, `generate_simple_pdf`
- `backend/app/modules/schulung/services/markdown_service.py`: `render_markdown`, `render_quiz_text`
- `backend/app/modules/schulung/services/reorder_contract_service.py`: `ReorderContractError`, `validate_complete_order`

### backend/app/modules/standards

- `backend/app/modules/standards/dokumentpruefung.py`: `erschliesse_nummern`, `pruefe`
- `backend/app/modules/standards/mappenpruefung.py`: `vokabular_aus_markdown`, `pruefe`
- `backend/app/modules/standards/mcp_tools.py`: `standards_list`, `standards_get`, `standards_diff`, `asset_get`, `deviation_report`, `humanizer_get_rules`, `humanizer_check`, `document_compare_reason`, `check_terminologie`, `check_document`, `check_workbook`, `check_workbook_schema`, `kennt`, `namen`, `ausfuehren`, `als_mcp_tools`
- `backend/app/modules/standards/models.py`: `StandardFehler`, `Fassung`, `Anlage`, `Freigabe`, `OffenerPunkt`, `Standard`, `Befund`, `fundstelle`, `umfeld`
- `backend/app/modules/standards/service.py`: `UnbekannterStandard`, `StandardsService`
- `backend/app/modules/standards/stilpruefung.py`: `pruefe`, `pruefe_absaetze`
- `backend/app/modules/standards/terminologie.py`: `Ersetzung`, `Abkuerzungsregel`, `Tabellen`, `tabellen_aus_markdown`, `pruefe`

### backend/app/modules/vba_analyzer

- `backend/app/modules/vba_analyzer/analysis.py`: `AnalysisError`, `rule_hosts`, `list_rules`, `resolve_profile`, `run_check`, `run_symbols`, `run_csv`, `parse_contract_rules`, `run_contract`, `run`, `find_workdir`
- `backend/app/modules/vba_analyzer/contracts.py`: `Verification`, `ErrorObject`, `VbaToolResponse`, `ModuleInput`, `AuxiliaryInput`
- `backend/app/modules/vba_analyzer/extra_rules.py`: `alle_regeln`, `check_extra`
- `backend/app/modules/vba_analyzer/mcp_tools.py`: `build_service_from_env`, `register_vba_tools`
- `backend/app/modules/vba_analyzer/quality_access.py`: `identifier`, `validate_manifest_input`, `normalize_manifest`, `validate_manifest`
- `backend/app/modules/vba_analyzer/quality_container.py`: `project_name_map`, `inspect_package`
- `backend/app/modules/vba_analyzer/quality_flow.py`: `Value`, `merge`, `split_expr`, `evaluate`, `join_env`, `analyze_source`
- `backend/app/modules/vba_analyzer/quality_forms.py`: `BoundedStream`, `read_sites`, `ole_inventories`, `frx_inventory`, `attach_frx`
- `backend/app/modules/vba_analyzer/quality_gate.py`: `catalog`, `parser_versions`, `status`, `finding`, `external_references`, `inspect`, `check_ui`, `envelope`, `run_access`
- `backend/app/modules/vba_analyzer/quality_objects.py`: `object_findings`
- `backend/app/modules/vba_analyzer/quality_prdb.py`: `procedures`, `docx_contract`, `folder_contract`
- `backend/app/modules/vba_analyzer/quality_sql.py`: `Token`, `tokenize`, `text`, `positions`, `split`, `closing`, `field_type`, `Scope`, `SQLInspector`, `sql_check`
- `backend/app/modules/vba_analyzer/quality_ui.py`: `source_columns`, `forms`, `prdb_checks`
- `backend/app/modules/vba_analyzer/quality_ui_metadata.py`: `record_fields`, `inspect_metadata`
- `backend/app/modules/vba_analyzer/rules_access_sql.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/vba_analyzer/rules_objects.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/vba_analyzer/rules_passthrough.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/vba_analyzer/rules_structure.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/vba_analyzer/rules_syntax.py`: `vor_lauf`
- `backend/app/modules/vba_analyzer/rules_types.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/modules/vba_analyzer/service.py`: `VbaAnalyzerError`, `VbaAnalyzerService`
- `backend/app/modules/vba_analyzer/worker.py`: `main`

### backend/app/modules/vp_ai

- `backend/app/modules/vp_ai/api/annotations.py`: `AnnotationPosition`, `TextRange`, `CreateAnnotationRequest`, `UpdateAnnotationRequest`, `AnnotationResponse`, `ReplyRequest`, `ReplyResponse`, `AnnotationStatsResponse`, `create_annotation`, `get_document_annotations`, `get_annotation`, `update_annotation`, `delete_annotation`, `resolve_annotation`, `link_to_question`, `add_reply`, `get_replies`, `update_reply`, `delete_reply`, `get_project_annotations`, `get_annotation_stats`, `get_question_annotations`
- `backend/app/modules/vp_ai/api/auflagen.py`: `extract_obligations`, `create_obligation`, `list_obligations`, `update_obligation`, `delete_obligation`, `abgleich_obligations`
- `backend/app/modules/vp_ai/api/ausgabenbilanz.py`: `get_expenditure_balance`, `update_expenditure_balance`
- `backend/app/modules/vp_ai/api/batch_export.py`: `export_batch_word`, `export_batch_excel`, `export_batch_toc`, `get_result_matrix`, `export_matrix_excel`
- `backend/app/modules/vp_ai/api/belegliste.py`: `import_belegliste`, `import_belegliste_from_document`, `list_belegliste`, `delete_belegliste`
- `backend/app/modules/vp_ai/api/calculations.py`: `create_beleglisten_position`, `list_beleglisten_positionen`, `export_belegliste_xlsx`, `get_beleglisten_position`, `update_beleglisten_position`, `delete_beleglisten_position`, `AiPruefenAlleResponse`, `ai_pruefe_beleg`, `ai_pruefe_alle_belege`, `calc_foerdersumme`, `calc_sek_stunden`, `GkpRequest`, `calc_gkp`, `FristRequest`, `calc_80_tage_frist`, `AuszahlungRequest`, `calc_auszahlung`, `FehlerquoteRequest`, `calc_fehlerquote`, `ZbBlAbgleichRequest`, `calc_zb_bl_abgleich`, `get_calc_summary`
- `backend/app/modules/vp_ai/api/checklist.py`: `import_word_checklist`, `list_designer_projects`, `import_designer_checklist`, `list_checklists`, `delete_checklist`, `list_questions`, `get_question`, `get_checklist_tree`, `submit_answer`, `get_checklist_progress`, `accept_ai_answer`, `reject_ai_answer`, `edit_ai_answer`, `regenerate_ai_answer`, `accept_ai_remark`, `reject_ai_remark`, `edit_ai_remark`, `create_chapter_instruction`, `execute_chapter_instruction`, `list_chapter_instructions`, `batch_accept_ai_answers`, `batch_reject_ai_answers`, `get_question_history`, `export_word_checklist`, `export_excel_checklist`, `export_pdf_checklist`, `list_checklist_profiles`, `create_checklist_profile`, `get_checklist_profile`, `update_checklist_profile`, `clone_checklist_profile`, `seed_default_profile`, `assign_profile_to_checklist`, `get_chapter_defaults`, `suggest_checklist_improvements`, `get_completeness_report`, `get_contradictions`, `generate_project_summary`, `get_project_summary`, `get_question_prompt`
- `backend/app/modules/vp_ai/api/checklist_versions.py`: `create_checklist_version`, `list_checklist_versions`, `diff_checklist_versions`, `get_checklist_version`
- `backend/app/modules/vp_ai/api/company.py`: `CompanySearchRequest`, `CompanySearchResult`, `search_company`, `as_dict_safe`, `asdict_safe`
- `backend/app/modules/vp_ai/api/cover_templates.py`: `hex_to_rgb`, `generate_cover_page_pdf`, `list_cover_templates`, `create_cover_template`, `get_cover_template`, `update_cover_template`, `delete_cover_template`, `upload_template_logo`, `delete_template_logo`, `preview_cover_template`, `preview_saved_template`, `create_default_templates`
- `backend/app/modules/vp_ai/api/diagrams.py`: `list_diagrams`, `create_diagram`, `get_diagram`, `update_diagram`, `delete_diagram`, `duplicate_diagram`, `list_versions`, `restore_version`, `update_version_milestone`, `import_vsdx_upload`, `import_vsdx_confirm`, `import_json`, `export_json`, `export_svg`, `export_png`, `export_pdf`
- `backend/app/modules/vp_ai/api/documents.py`: `search_document_text`, `upload_documents`, `list_documents`, `assign_document`, `unassign_document`, `rename_document`, `apply_rename_patterns`, `reorder_documents`, `toggle_grundsatz`, `assign_document_to_exam_item`, `download_document`, `delete_document`, `preview_document`, `merge_project_pdf`, `get_zip_download_info`, `create_zip_download_ticket`, `download_documents_zip`, `sync_project_documents_to_kb`, `get_project_ocr_status`, `run_project_ocr`, `run_document_ocr`, `get_kb_sync_status`, `get_kb_sync_task_state`, `sync_single_document_to_kb`, `suggest_document_category`, `auto_categorize_documents`
- `backend/app/modules/vp_ai/api/energie_co2.py`: `get_energie_co2_overview`, `upsert_energie_co2_angabe`, `delete_energie_co2_angabe`
- `backend/app/modules/vp_ai/api/exam_items.py`: `get_exam_item_or_404`, `list_exam_items`, `create_exam_item`, `create_exam_items_batch`, `get_exam_item`, `update_exam_item`, `delete_exam_item`, `reorder_exam_item`
- `backend/app/modules/vp_ai/api/feedback.py`: `FeedbackCreate`, `FeedbackResponse`, `BulkFeedbackCreate`, `BulkFeedbackResponse`, `submit_feedback`, `submit_bulk_feedback`, `get_feedback_stats`
- `backend/app/modules/vp_ai/api/feststellungen.py`: `create_finding`, `list_findings`, `get_findings_summary`, `update_finding`, `delete_finding`
- `backend/app/modules/vp_ai/api/folder_import.py`: `detect_vp_folders`, `folder_scan`, `folder_import`
- `backend/app/modules/vp_ai/api/health.py`: `get_health_status`, `get_wissensbasis_health`, `reset_circuit_breaker`
- `backend/app/modules/vp_ai/api/history.py`: `HistoryEntryResponse`, `VersionComparisonResponse`, `RestoreRequest`, `HistoryStatsResponse`, `get_question_history`, `compare_versions`, `get_question_version`, `restore_version`, `get_checklist_history_stats`
- `backend/app/modules/vp_ai/api/humanizer.py`: `HumanizeTextRequest`, `humanize_text`, `humanize_document`, `get_supported_formats`, `extract_text_only`
- `backend/app/modules/vp_ai/api/humanizer_profiles.py`: `HumanizerProfileCreate`, `HumanizerProfileUpdate`, `list_profiles`, `get_profile`, `create_profile`, `update_profile`, `delete_profile`, `duplicate_profile`, `create_default_profiles`
- `backend/app/modules/vp_ai/api/jupyter.py`: `NotebookInfo`, `list_notebooks`, `get_current_notebook`
- `backend/app/modules/vp_ai/api/kb_admin.py`: `get_status`, `get_stats`, `get_harvest_health`, `get_load_modes`, `list_schedules`, `create_schedule`, `get_schedule`, `update_schedule`, `delete_schedule`, `toggle_schedule`, `list_jobs`, `get_active_jobs`, `get_job`, `get_job_progress`, `start_job`, `start_parallel_staging`, `stop_job`, `change_job_load`, `get_all_progress`, `get_celery_beat_status`, `trigger_missed_jobs_check`
- `backend/app/modules/vp_ai/api/knowledge.py`: `get_sources`, `get_source`, `toggle_source`, `update_source_config`, `get_harvest_progress`, `harvest_source`, `harvest_all_sources`, `get_harvest_logs`, `get_keywords`, `create_keyword`, `delete_keyword`, `search_knowledge`, `get_query_stats`, `ask_question`, `list_documents`, `get_document`, `delete_document`, `ingest_document`, `upload_document`, `reindex_document`, `generate_text`, `get_text_topics`, `humanize_text`, `get_humanizer_profiles`, `export_word`, `analyze_excel`, `get_scheduler_status`, `run_scheduler_now`, `start_scheduler`, `stop_scheduler`, `get_current_harvest_report`, `get_harvest_stats`, `list_harvest_reports`, `get_error_report`, `get_harvest_report`, `generate_harvest_report`, `kb_health`, `batch_vectorize`, `get_staging_status`, `deduplicate_documents`, `recategorize_documents`, `redetect_funding_periods`, `list_articles`, `get_article`, `generate_article`
- `backend/app/modules/vp_ai/api/pdb_import.py`: `pdb_preview`, `pdb_import`
- `backend/app/modules/vp_ai/api/progress.py`: `create_progress_stream_ticket`, `subscribe_to_progress`, `get_active_runs`
- `backend/app/modules/vp_ai/api/projects.py`: `create_project`, `list_projects`, `get_project`, `delete_project`, `update_project`
- `backend/app/modules/vp_ai/api/qchess_export.py`: `qchess_answer_export_preview`, `qchess_textbausteine`, `qchess_answer_export_zip`, `qchess_binding_status`, `qchess_binding_import`, `qchess_answer_paket`, `qchess_receipt_import`, `qchess_snapshot_export_macro`, `qchess_snapshot_refresh`
- `backend/app/modules/vp_ai/api/review.py`: `upload_document`, `list_documents`, `get_document`, `delete_document`, `get_document_text`, `add_comment`, `update_comment`, `delete_comment`, `approve_comment`, `reject_comment`, `analyze_document`, `export_document`
- `backend/app/modules/vp_ai/api/rule_validation.py`: `validate_checklist`, `get_validation_results`, `auto_resolve_entfaellt`
- `backend/app/modules/vp_ai/api/runs.py`: `run_ai_remarks_background`, `run_indexing_background`, `create_ai_run`, `get_run_status`, `create_index_run`, `cancel_run`
- `backend/app/modules/vp_ai/api/scheduler_ops.py`: `get_scheduler_status`, `rerun_harvest_for_source`, `reprocess_failed_staging`, `reembed_outdated_chunks`
- `backend/app/modules/vp_ai/api/scheduler_settings.py`: `get_scheduler_settings`, `update_scheduler_settings`, `get_scheduler_status`, `reload_scheduler`, `reset_to_defaults`
- `backend/app/modules/vp_ai/api/scorecard.py`: `get_project_scorecard`
- `backend/app/modules/vp_ai/api/templates.py`: `list_templates`, `get_template`, `save_checklist_as_template`, `apply_template_to_project`, `delete_template`
- `backend/app/modules/vp_ai/api/toc.py`: `get_project_toc`, `seed_project_toc`, `update_toc_item`, `create_toc_group`, `update_toc_group`, `delete_toc_group`, `create_toc_item`, `patch_toc_item`, `delete_toc_item`, `export_toc_docx`, `export_toc_pdf`
- `backend/app/modules/vp_ai/api/toc_structure_templates.py`: `list_structure_templates`, `get_structure_template`, `create_structure_template`, `update_structure_template`, `delete_structure_template`, `duplicate_structure_template`, `set_structure_template_default`
- `backend/app/modules/vp_ai/api/toc_templates.py`: `list_toc_templates`, `get_toc_template`, `create_toc_template`, `update_toc_template`, `delete_toc_template`, `set_toc_template_default`, `duplicate_toc_template`
- `backend/app/modules/vp_ai/api/websocket.py`: `ConnectionManager`, `websocket_endpoint`
- `backend/app/modules/vp_ai/api/word_cd.py`: `list_cover_templates`, `preview_cover`, `preview_document`, `convert`
- `backend/app/modules/vp_ai/api/zgs_checklists.py`: `import_zgs_checklist`, `list_zgs_checklists`, `get_zgs_checklist`, `delete_zgs_checklist`, `abgleich_zgs_checklists`
- `backend/app/modules/vp_ai/humanizer_mcp_server.py`: `list_tools`, `call_tool`
- `backend/app/modules/vp_ai/permissions.py`: `require_kb_enabled`, `get_current_user_vp_ai`, `require_vp_ai_access`, `require_vp_ai_access_or_api_key`, `is_efre_hessen_privileged_user`, `require_role_in`, `require_project_owner`, `get_project_or_404`
- `backend/app/modules/vp_ai/services/_llm_client_mixin.py`: `LlmClientMixin`
- `backend/app/modules/vp_ai/services/ai_service.py`: `GeneratedRemark`, `AiRemarkResult`, `AiService`, `MockAiService`, `get_ai_service`
- `backend/app/modules/vp_ai/services/annotation_service.py`: `AnnotationService`
- `backend/app/modules/vp_ai/services/answer_validation_service.py`: `AnswerValidationError`, `validate_answer`
- `backend/app/modules/vp_ai/services/auflage_service.py`: `extract_auflagen_from_text`, `create_auflage`, `list_auflagen`, `get_auflage`, `update_auflage`, `abgleich_mit_macl`
- `backend/app/modules/vp_ai/services/ausgabenbilanz_service.py`: `get_or_create_ausgabenbilanz`, `update_ausgabenbilanz`
- `backend/app/modules/vp_ai/services/beleg_ai_validator.py`: `BelegPositionAiValidator`
- `backend/app/modules/vp_ai/services/belegliste_export_service.py`: `build_belegliste_xlsx`
- `backend/app/modules/vp_ai/services/belegliste_import_service.py`: `parse_belegliste_xlsx`, `BeleglisteImportService`
- `backend/app/modules/vp_ai/services/cache_service.py`: `get_worker_config`, `CacheStats`, `DocumentCacheService`, `EmbeddingCacheService`, `OptimizedEmbeddingService`, `get_optimized_embedding_service`, `BatchEmbeddingJob`
- `backend/app/modules/vp_ai/services/calculation_service.py`: `CalcResult`, `SekStundenResult`, `ZbBlAbgleichResult`, `CalcSummary`, `CalculationService`
- `backend/app/modules/vp_ai/services/categorization_service.py`: `detect_category_by_keywords`, `detect_category_with_ollama`, `detect_category_with_llm`, `detect_category`, `detect_category_sync`
- `backend/app/modules/vp_ai/services/checklist_ai_fill_service.py`: `ChecklistAiFillService`
- `backend/app/modules/vp_ai/services/checklist_version_service.py`: `create_version`, `list_versions`, `diff_versions`, `compute_diff`
- `backend/app/modules/vp_ai/services/chunker_factory.py`: `get_chunker`
- `backend/app/modules/vp_ai/services/chunking_service.py`: `TokenCounter`, `count_tokens`, `TokenChunkData`, `TokenAwareChunker`, `ChunkingMode`, `ChunkData`, `ChunkingResult`, `ChunkingService`, `SmartChunkingService`
- `backend/app/modules/vp_ai/services/company/company_natura.py`: `run_natura_checks`, `apply_address_selection`, `collect_area_rows`, `collect_location_rows`, `export_interactive_map`, `export_printable_map`, `main`
- `backend/app/modules/vp_ai/services/company/company_records.py`: `TAMAward`, `TEDNotice`, `HADNotice`, `CompanyResult`, `CompanyRecords`
- `backend/app/modules/vp_ai/services/company/natura_local_cache.py`: `NaturaLocalCache`, `get_natura_cache`
- `backend/app/modules/vp_ai/services/completeness_service.py`: `CategoryCoverage`, `TocGroupCoverage`, `CompletenessReport`, `CompletenessService`
- `backend/app/modules/vp_ai/services/content_fetcher.py`: `FetchResult`, `ContentFetcher`, `get_content_fetcher`, `BatchStats`, `ContentFetcherService`
- `backend/app/modules/vp_ai/services/designer_import.py`: `DesignerImportService`
- `backend/app/modules/vp_ai/services/diagram_service.py`: `parse_vsdx`, `import_vsdx_page`, `parse_vsd`, `import_vsd_page`, `generate_svg`, `generate_png`, `generate_pdf`
- `backend/app/modules/vp_ai/services/doc_categorization_service.py`: `CategorySuggestion`, `DocCategorizationService`
- `backend/app/modules/vp_ai/services/document_ocr_service.py`: `DocumentOcrResult`, `BatchOcrResult`, `DocumentOcrService`, `get_document_ocr_service`
- `backend/app/modules/vp_ai/services/document_retrieval_service.py`: `RetrievalContext`, `GroupedChunks`, `DocumentRetrievalService`
- `backend/app/modules/vp_ai/services/document_service.py`: `UploadResult`, `DocumentMetadata`, `DocumentService`
- `backend/app/modules/vp_ai/services/embedding_service.py`: `EmbeddingResult`, `LocalEmbeddingService`, `OpenAIEmbeddingService`, `OllamaGatewayEmbeddingService`, `RouterRemoteEmbeddingService`, `MockEmbeddingService`, `get_embedding_service`
- `backend/app/modules/vp_ai/services/error_codes.py`: `ErrorCategory`, `RetryMethod`, `ErrorDefinition`, `classify_error`, `format_error`, `get_retryable_codes`, `get_codes_by_method`
- `backend/app/modules/vp_ai/services/feststellung_service.py`: `create_feststellung`, `list_feststellungen`, `get_feststellung`, `update_feststellung`, `delete_feststellung`, `get_feststellung_summary`
- `backend/app/modules/vp_ai/services/folder_import_service.py`: `validate_folder_path`, `suggest_filename`, `VpFolderInfo`, `FolderImportService`
- `backend/app/modules/vp_ai/services/harvest_queue_service.py`: `get_redis_client`, `HarvestQueueService`, `get_harvest_queue_service`
- `backend/app/modules/vp_ai/services/harvest_report_service.py`: `ReportConfig`, `HarvestReportService`, `get_harvest_report_service`
- `backend/app/modules/vp_ai/services/harvest_staging_service.py`: `StagingResult`, `ProcessingResult`, `HarvestStagingService`, `get_harvest_staging_service`
- `backend/app/modules/vp_ai/services/history_service.py`: `HistoryService`
- `backend/app/modules/vp_ai/services/humanizer_rules.py`: `anti_ai_block`, `checklisten_formulierung_block`, `personal_style_kombiniert`, `personal_style`, `wissenschaftlich_schreiben`, `get_style_profile`, `normalize_ascii_umlauts`, `find_ai_tells`, `normalize_text_format`, `invariants_preserved`, `full_rules`
- `backend/app/modules/vp_ai/services/humanizer_service.py`: `HumanizeResult`, `HumanizerService`
- `backend/app/modules/vp_ai/services/journal_splitter.py`: `JournalArticle`, `JournalSplitResult`, `JournalSplitter`, `split_journal_pdf`
- `backend/app/modules/vp_ai/services/kb_chunkers.py`: `ChunkData`, `KbChunker`, `LegalTaggingChunker`, `HeadingChunker`, `SectionChunker`, `TocChunker`, `AuditAwareChunker`
- `backend/app/modules/vp_ai/services/kb_context_compressor.py`: `KbContextCompressor`
- `backend/app/modules/vp_ai/services/kb_document_format_service.py`: `WordTemplate`, `WordExportResult`, `ExcelAnalysisResult`, `KbDocumentFormatService`, `get_kb_document_format_service`
- `backend/app/modules/vp_ai/services/kb_fine_tuner.py`: `KbFineTuner`
- `backend/app/modules/vp_ai/services/kb_humanizer_service.py`: `StyleProfile`, `Intensity`, `HumanizedText`, `KbHumanizerService`, `get_kb_humanizer_service`
- `backend/app/modules/vp_ai/services/kb_hyde_service.py`: `KbHydeService`
- `backend/app/modules/vp_ai/services/kb_ingestion_service.py`: `classify_doc_type`, `is_garbage_content`, `enforce_max_chunk_size`, `classify_chunk_type`, `IngestionResult`, `KbIngestionService`, `get_kb_ingestion_service`
- `backend/app/modules/vp_ai/services/kb_job_service.py`: `KbJobService`, `get_load_modes_info`
- `backend/app/modules/vp_ai/services/kb_metadata_extractor.py`: `apply_rules`, `keyword_classify`, `extract_chunk_metadata`, `auto_tag_document`
- `backend/app/modules/vp_ai/services/kb_query_classifier.py`: `QueryIntent`, `IntentResult`, `classify_intent`, `get_hybrid_weights`
- `backend/app/modules/vp_ai/services/kb_query_transformer.py`: `KbQueryTransformer`
- `backend/app/modules/vp_ai/services/kb_rag_service.py`: `SearchMode`, `ChunkSource`, `ContextScope`, `QueryIntent`, `SearchResult`, `RagAnswer`, `SearchResponse`, `KbEmbeddingService`, `KbRagService`, `get_kb_rag_service`
- `backend/app/modules/vp_ai/services/kb_relevanz_filter.py`: `ist_foerderrelevant`, `relevanz_filter_aktiv`
- `backend/app/modules/vp_ai/services/kb_reranker_service.py`: `KbRerankerService`
- `backend/app/modules/vp_ai/services/kb_text_generator_service.py`: `TextType`, `TextLength`, `GeneratedText`, `KbTextGeneratorService`, `get_kb_text_generator_service`
- `backend/app/modules/vp_ai/services/legal_chunker.py`: `NormHierarchy`, `LegalDefinition`, `CrossReference`, `LegalChunk`, `LegalChunkingResult`, `LegalChunker`
- `backend/app/modules/vp_ai/services/ollama_service.py`: `OllamaService`, `get_ollama_service`
- `backend/app/modules/vp_ai/services/pdb_import_service.py`: `PdbImportService`
- `backend/app/modules/vp_ai/services/pdf_merge_service.py`: `MergeResult`, `hex_to_rgb`, `PdfMergeService`
- `backend/app/modules/vp_ai/services/progress_manager.py`: `ProgressType`, `ProgressEvent`, `ProgressManager`
- `backend/app/modules/vp_ai/services/project_deletion_service.py`: `delete_vp_project_cascade`
- `backend/app/modules/vp_ai/services/project_kb_sync_service.py`: `kb_sync_eligibility`, `SyncResult`, `ProjectSyncResult`, `ProjectKbSyncService`, `get_project_kb_sync_service`
- `backend/app/modules/vp_ai/services/query_expansion.py`: `expand_query`
- `backend/app/modules/vp_ai/services/question_key_util.py`: `extract_leading_number`, `derive_question_key`
- `backend/app/modules/vp_ai/services/remote_embedding_client.py`: `RemoteRouterEmbeddingClient`, `get_remote_embedding_client`, `is_remote_backend_enabled`
- `backend/app/modules/vp_ai/services/review_service.py`: `TextExtractionResult`, `AnalysisResult`, `FeedbackExample`, `ReviewService`, `get_review_service`
- `backend/app/modules/vp_ai/services/rule_validation_service.py`: `RuleValidationService`
- `backend/app/modules/vp_ai/services/scorecard_service.py`: `ScorecardService`
- `backend/app/modules/vp_ai/services/sonderbericht_service.py`: `list_reports`, `render_report`
- `backend/app/modules/vp_ai/services/suggestion_service.py`: `GrundsatzContent`, `SuggestionService`, `get_suggestion_service`
- `backend/app/modules/vp_ai/services/summary_service.py`: `ChecklistSummary`, `ProjectSummary`, `SummaryService`
- `backend/app/modules/vp_ai/services/text_extraction.py`: `orientation_score`, `needs_ocr`, `ExtractionQuality`, `PageContent`, `ExtractionResult`, `TextExtractionService`
- `backend/app/modules/vp_ai/services/toc_seeder.py`: `TocItemSchema`, `TocGroupSchema`, `SeedResult`, `TocSeederService`
- `backend/app/modules/vp_ai/services/toc_structure_template_service.py`: `TocStructureTemplateService`
- `backend/app/modules/vp_ai/services/verzeichnis_vorlage.py`: `dateiname`, `spalten_ohne_dokumentenzahl`, `Registerposition`, `VorlageNichtVerfuegbar`, `vorlage_als_docx`, `oeffne_vorlage`, `vorhabenpruefung_bezeichnung`, `dms_aktenzeichen`, `registerpositionen`, `registerzeilen`, `zellen_der_zeile`, `setze_zellentext`, `fuelle_kopftabelle`, `ersetze_registertabelle`, `baue_kopftabelle`, `Dateizeile`, `dateiliste`, `haenge_dateiliste_an`, `erzeuge_verzeichnis`
- `backend/app/modules/vp_ai/services/wissensbasis_client.py`: `CircuitState`, `WissensbasisSearchResult`, `WissensbasisAnswer`, `WissensbasisClient`, `get_wissensbasis_client`
- `backend/app/modules/vp_ai/services/word_export.py`: `ChecklistExportService`
- `backend/app/modules/vp_ai/services/word_import.py`: `ParsedQuestion`, `ImportResult`, `WordImportService`
- `backend/app/modules/vp_ai/services/zgs_import_service.py`: `parse_macl_from_text`, `parse_apcl_from_text`, `ZgsImportService`
- `backend/app/modules/vp_ai/services/zip_auth.py`: `get_user_for_zip_download`

### backend/app/services

- `backend/app/services/audit_service.py`: `AuditService`
- `backend/app/services/bulk_edit_service.py`: `BulkEditService`
- `backend/app/services/checklist_package_service.py`: `ChecklistPackageError`, `ChecklistPackageService`
- `backend/app/services/docx_export_service.py`: `DocxExportService`
- `backend/app/services/docx_import_service.py`: `StyleInfo`, `ImportResult`, `DocxImportService`, `import_docx_file`
- `backend/app/services/export/_common.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export/_docx.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export/_excel.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export/_json.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export/_notes.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export/_pdf.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export/_text_helpers.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/services/export_service.py`: `ExportService`
- `backend/app/services/import_service.py`: `ImportService`
- `backend/app/services/jupyter_service.py`: `JupyterService`
- `backend/app/services/llm_status_service.py`: `get_status`, `invalidate_cache`
- `backend/app/services/node_history_service.py`: `NodeHistoryService`
- `backend/app/services/note_read_service.py`: `NoteReadService`
- `backend/app/services/ocr_router.py`: `should_use_router`, `ocr_image_bytes`
- `backend/app/services/pdf_converter_service.py`: `PageInfo`, `TableData`, `ConversionResult`, `ExtractionTemplate`, `PdfConverterService`, `get_pdf_converter`
- `backend/app/services/pdf_editor_service.py`: `PdfEditorService`, `get_pdf_editor`
- `backend/app/services/pdf_tools_service.py`: `PdfToolResult`, `PdfToolsService`, `get_pdf_tools`
- `backend/app/services/presentation_export_service.py`: `get_circle_number`, `PresentationExportService`, `export_presentation_with_annotations`
- `backend/app/services/pruefstrategie_export_service.py`: `DocumentMetadata`, `PruefstrategieExportService`, `extract_metadata_from_markdown`
- `backend/app/services/qchess_checkliste_import.py`: `QchessImportError`, `ImportReport`, `build_tree_data`
- `backend/app/services/qchess_paket/apply.py`: `ApplyResult`, `apply_paket`
- `backend/app/services/qchess_paket/canonical.py`: `canonical_bytes`, `loads`
- `backend/app/services/qchess_paket/container.py`: `OpenedPaket`, `build_qpaket`, `open_qpaket`
- `backend/app/services/qchess_paket/crypto.py`: `gen_nonce`, `sign`, `verify`, `seal`, `unseal`
- `backend/app/services/qchess_paket/dbwrite.py`: `WriteConn`
- `backend/app/services/qchess_paket/errors.py`: `PaketError`, `PaketFinding`, `Fehlerlog`
- `backend/app/services/qchess_paket/header.py`: `build_header`, `validate_header`, `check_validity`
- `backend/app/services/qchess_paket/keys.py`: `fingerprint`, `Identity`, `generate_identity`, `Peer`, `TrustStore`
- `backend/app/services/qchess_paket/ledger.py`: `initialize_tables`, `require_tables`, `already_applied`, `lock_target_state`, `record_target_state`, `log_versuch`, `record_applied`
- `backend/app/services/qchess_paket/manifest.py`: `sha256_hex`, `build_manifest`, `validate_manifest`, `verify_payload_checksums`
- `backend/app/services/qchess_paket/operations.py`: `OpResult`, `current_review_state_hash`, `ReviewergebnisUpsert`, `ReviewergebnisUpsertByFrage`, `get_operation`
- `backend/app/services/qchess_paket/target.py`: `validate_target`, `sha256_obj`, `database_fingerprint`, `answer_state_hash`
- `backend/app/services/qchess_paket/validate.py`: `validate`
- `backend/app/services/qchess_report/action_builder.py`: `UnknownDefaultSetError`, `build_actions_for_rule`, `build_actions_for_answer`
- `backend/app/services/qchess_report/action_import_service.py`: `ActionImportError`, `ImportedAktion`, `ImportedMergefield`, `ActionImportResult`, `parse_export_json`, `import_report_actions`
- `backend/app/services/qchess_report/answer_export.py`: `AnswerMapping`, `SkippedAnswer`, `Snapshot`, `ExportResult`, `checkliste_id_override`, `detect_cl_id`, `load_snapshot`, `load_verified_snapshot`, `textbausteine_map`, `baustein_for_answer`, `combine_textbaustein`, `pruefobjekt_id_override`, `map_answers`, `build_bundle`, `build_zip`, `build_preview`, `render_snapshot_export_macro`
- `backend/app/services/qchess_report/ausgaben_report_rows.py`: `get_bezeichner`, `AusgabenRowsResult`, `ensure_ausgaben_rows`
- `backend/app/services/qchess_report/auto_bind_service.py`: `map_clref_to_ex`, `AutoBindCandidate`, `AutoBindProposal`, `AutoBindSkipped`, `AutoBindResult`, `extract_frage_nummer`, `derive_default_action_set`, `QchessAutoBindService`
- `backend/app/services/qchess_report/auto_prefill.py`: `HintType`, `classify_hint`, `extract_fundstelle_und_soll`, `normalize_fundstelle`, `derive_wertung_class`, `derive_ueberschrift`, `build_sachverhalt_typ_a`, `auto_prefill_rule`, `auto_prefill_template`
- `backend/app/services/qchess_report/checkliste_baum_export.py`: `build_checkliste_baum_docx`, `checkliste_baum_filename`
- `backend/app/services/qchess_report/checkliste_export.py`: `build_checkliste_docx`, `checkliste_filename`
- `backend/app/services/qchess_report/cli_seed_library.py`: `main`
- `backend/app/services/qchess_report/constants.py`: `antwort_map_for_set`, `strip_akten_referenz`, `mergefeldtyp`, `strip_frage_nummer`, `frage_nummer_from_code`, `effective_zeile_typ`, `default_formatvorlage`
- `backend/app/services/qchess_report/default_sets.py`: `load_default_sets`, `get_default_set`
- `backend/app/services/qchess_report/docm_parser.py`: `DocmManifest`, `QchessDocmParser`
- `backend/app/services/qchess_report/excel_import_service.py`: `ParsedFrage`, `ParsedAntwortSet`, `ParsedReviewantwort`, `ParsedQchessExport`, `QchessExcelParseError`, `QchessExcelImporter`, `QchessExcelTooLarge`
- `backend/app/services/qchess_report/fill_vp_report_rows.py`: `FillPlanItem`, `FillResult`, `fill_vp_report_rows`
- `backend/app/services/qchess_report/library.py`: `search_library_fulltext`, `search_library_semantic`, `suggest_sachverhalt_from_hints`
- `backend/app/services/qchess_report/library_seeder.py`: `infer_wertung_class`, `seed_library_from_bestand`
- `backend/app/services/qchess_report/library_service.py`: `create_entry`, `get_entry`, `update_entry`, `soft_delete_entry`, `search`, `increment_usage`, `apply_library_entry_to_rule`, `extract_from_action`
- `backend/app/services/qchess_report/naming.py`: `parse_node_number`, `derive_mergefield_code`
- `backend/app/services/qchess_report/preview_cache.py`: `PendingSnapshotEntry`, `put`, `get`, `delete`
- `backend/app/services/qchess_report/preview_renderer.py`: `RuleRenderBlock`, `RuleRenderResult`, `SectionRenderResult`, `TemplateRenderResult`, `QchessPreviewRenderer`
- `backend/app/services/qchess_report/prompts.py`: `build_sachverhalt_user_prompt`
- `backend/app/services/qchess_report/report_export.py`: `SofficeUnavailableError`, `ParaSpec`, `build_filled_docx`, `docx_to_pdf`, `export_report_docx`, `export_report_pdf`, `export_filename`
- `backend/app/services/qchess_report/snapshot_service.py`: `SnapshotResult`, `SnapshotMetaResponse`, `AntwortOption`, `AntwortSetInfo`, `BindingRisk`, `AntwortsetChange`, `FrageChange`, `SnapshotDiff`, `compute_antwortset_signature`, `compute_snapshot_content_hash`, `QchessSnapshotService`
- `backend/app/services/qchess_report/sql_generator.py`: `sql_escape`, `resolve_cl_version`, `build_deployment_files`, `build_deployment_bundle`, `compute_bundle_hash`
- `backend/app/services/qchess_report/test_deploy_service.py`: `TestDeployResult`, `QchessTestDeployService`
- `backend/app/services/qchess_report/textbausteine_export.py`: `build_textbausteine_docx`, `textbausteine_filename`
- `backend/app/services/qchess_report/validate_service.py`: `ValidateIssue`, `ValidateScoreBreakdown`, `ValidateStatistics`, `ValidateResult`, `QchessValidateService`
- `backend/app/services/qchess_report/word_generator.py`: `extract_placeholders`, `build_word_with_mergefields`, `parse_skeleton_to_rule_proposals`, `generate_word`
- `backend/app/services/schulungsmodus_check.py`: `SchulungsmodusPausedException`, `check_schulungsmodus_active`, `raise_if_paused`
- `backend/app/services/tree_service.py`: `TreeService`
- `backend/app/services/validation_service.py`: `ValidationErrorType`, `ValidationError`, `ValidationService`
- `backend/app/services/vba/daten_export_service.py`: `export_berichtsdaten`
- `backend/app/services/vba/vba_ai_service.py`: `optimize_vba_code`
- `backend/app/services/vba/vba_analyzer.py`: `analyze_vba_code`, `extract_object_refs`
- `backend/app/services/vba/vba_compiler.py`: `validate_template`, `check_compilation_gate`, `compile_template`
- `backend/app/services/vba/vba_importer.py`: `extract_vba_from_bas`, `extract_vba_from_office_file`, `detect_host_type`
- `backend/app/services/vpai_notebook/auto_tagger.py`: `AutoTagger`, `auto_tag_page`, `apply_auto_tags`
- `backend/app/services/vpai_notebook/embeddings.py`: `NotebookEmbeddingService`, `get_notebook_embedding_service`
- `backend/app/services/vpai_notebook/importer.py`: `ImportResult`, `BaseImporter`, `ZipImporter`, `GoogleKeepImporter`, `OneNoteImporter`, `ObsidianImporter`, `ImportService`
- `backend/app/services/vpai_notebook/notebook_storage.py`: `notebook_filename_from_title`, `ensure_notebook_page_dir`, `delete_notebook_page_dir`, `sync_notebook_page_file`
- `backend/app/services/vpai_notebook/ollama.py`: `OllamaService`, `get_ollama_service`, `summarize_page`, `get_ai_tags`
- `backend/app/services/vpai_notebook/rag.py`: `SearchResult`, `RagResponse`, `SearchResponse`, `NotebookRagService`, `get_notebook_rag_service`
- `backend/app/services/vpai_notebook/search.py`: `SearchQuery`, `parse_search_query`, `parse_date_value`, `search_pages`, `create_excerpt`, `get_search_suggestions`
- `backend/app/services/vpai_notebook/vault.py`: `VaultError`, `VaultLockedError`, `VaultNotConfiguredError`, `InvalidPinError`, `VaultService`
- `backend/app/services/word_cd/cd_migrator.py`: `CdMigrationError`, `migrate_to_hessen_cd`
- `backend/app/services/word_cd/converter.py`: `ConversionError`, `convert_document`, `to_pdf`
- `backend/app/services/word_cd/cover_builder.py`: `build_cover`
- `backend/app/services/word_cd/cover_splicer.py`: `CoverSpliceError`, `splice_cover`
- `backend/app/services/word_cd/transforms.py`: `list_text_parts`, `extract_text`, `text_hash`, `collect_stats`, `transform_font_table`, `transform_styles`, `transform_document`, `transform_arial_rfonts`
- `backend/app/services/word_template_service.py`: `FontStyle`, `ParagraphStyle`, `HeadingStyle`, `TableStyle`, `ExtractedStyle`, `DocumentStyles`, `WordTemplateService`
- `backend/app/services/workspace_prompt_service.py`: `generate_task_prompt`

## Vollständiger statischer Pfadindex: flowstat

Dieser Index enthält sämtliche getrackten Python-Dateien mit API-/Services-Pfad unter `backend/app`, außerdem die getrackten gemeinsamen Recherche- und Modulkerne. Test-, Modell-, Schema- und Frontend-Dateien sind damit nicht als eigene Funktionen gezählt. Dateipfade belegen Auffindbarkeit; nicht jeder Eintrag wurde im Detail fachlich bewertet.


### backend/app/api

- `backend/app/api/dependencies.py`: `get_audit_info`
- `backend/app/api/routes/admin_cache.py`: `get_cache_statistics`, `trigger_manual_cleanup`, `delete_dataframe`
- `backend/app/api/routes/admin_plugins.py`: `list_all_plugins`, `upload_plugin`, `activate_plugin`, `deactivate_plugin`
- `backend/app/api/routes/analysis.py`: `run_analysis`
- `backend/app/api/routes/analysis_results.py`: `list_analysis_results`, `get_analysis_stats`, `get_analysis_result`, `create_analysis_result`, `update_analysis_result`, `delete_analysis_result`, `create_version`, `toggle_archive`, `toggle_favorite`, `get_versions`
- `backend/app/api/routes/auth.py`: `register_user`, `login`, `get_current_user_info`, `update_current_user`, `list_users`, `toggle_user_admin`, `toggle_user_active`
- `backend/app/api/routes/bpmn.py`: `validate_bpmn_bva`, `list_bpmn_diagrams`, `create_bpmn_diagram`, `get_bpmn_diagram`, `update_bpmn_diagram`, `delete_bpmn_diagram`, `validate_bpmn_diagram`, `validate_bpmn_xml`, `toggle_archive_bpmn_diagram`, `update_bpmn_header`, `update_bpmn_color_scheme`, `add_bpmn_comment`, `update_bpmn_comment`, `delete_bpmn_comment`, `get_bpmn_esi_requirements`, `get_bpmn_esi_analysis`
- `backend/app/api/routes/bpmn_export.py`: `get_bpmn_analysis`, `export_bpmn_excel`, `export_bpmn_pdf`
- `backend/app/api/routes/core_requirements.py`: `list_core_requirements`, `get_core_requirement`, `create_core_requirement`, `update_core_requirement`, `delete_core_requirement`, `list_assessment_criteria`, `create_assessment_criterion`, `update_assessment_criterion`, `delete_assessment_criterion`, `seed_core_requirements`
- `backend/app/api/routes/export.py`: `export_excel`, `PDFExportRequest`, `AnalysisPDFExportRequest`, `export_pdf`, `export_analysis_pdf`, `CSVExportRequest`, `export_csv`, `PowerPointExportRequest`, `WordExportRequest`, `export_powerpoint`, `export_word`, `export_analysis_powerpoint_get`, `export_analysis_word_get`
- `backend/app/api/routes/health.py`: `read_health`
- `backend/app/api/routes/jobs.py`: `create_job_endpoint`, `list_jobs_endpoint`, `get_job_endpoint`, `get_job_status_endpoint`, `update_job_endpoint`, `delete_job_endpoint`, `list_all_jobs_endpoint`, `cleanup_jobs_endpoint`
- `backend/app/api/routes/mapping.py`: `apply_mapping`
- `backend/app/api/routes/personnel_costs.py`: `seed_personnel_costs_2024_endpoint`, `list_personnel_cost_rates`, `list_available_years`, `list_available_grades`, `create_personnel_cost_rate`, `create_personnel_cost_rates_bulk`, `get_personnel_cost_rate`, `update_personnel_cost_rate`, `delete_personnel_cost_rate`
- `backend/app/api/routes/pipelines.py`: `list_pipelines`, `get_pipeline`, `create_pipeline`, `update_pipeline`, `delete_pipeline`
- `backend/app/api/routes/plugins.py`: `list_plugins`, `get_plugin_parameters`, `run_plugin`, `get_job`
- `backend/app/api/routes/project_archive.py`: `preview_export`, `export_project`, `import_project`
- `backend/app/api/routes/projects.py`: `list_projects`, `get_project`, `create_project`, `update_project`, `delete_project`
- `backend/app/api/routes/roles.py`: `list_permissions`, `create_permission`, `list_roles`, `get_role`, `create_role`, `update_role`, `delete_role`, `assign_role_to_user`, `remove_role_from_user`, `get_user_permissions_endpoint`
- `backend/app/api/routes/sampling.py`: `run_sampling_procedure`, `list_sampling_templates`, `get_sampling_template`
- `backend/app/api/routes/sampling_UPDATED.py` (Adapter/Konfiguration/Hilfsmodul; keine öffentlichen Top-Level-Definitionen)
- `backend/app/api/routes/sandbox.py`: `get_sandbox_status`, `get_job_status`, `list_all_jobs`
- `backend/app/api/routes/transform.py`: `filter_dataframe`, `join_dataframes`, `apply_feature_engineering`
- `backend/app/api/routes/upload.py`: `upload_file`

### backend/app/services

- `backend/app/services/analysis_core_service.py`: `run_grouping`, `run_stratification`, `run_age_analysis`, `run_heatmap`, `run_benford`, `run_duplicates`, `run_gap_analysis`, `run_outlier`, `run_sampling`
- `backend/app/services/audit_service.py`: `log_audit_event`, `get_client_info`, `build_change_log`
- `backend/app/services/bpmn_analyzer.py`: `TaskProperties`, `ProcessAnalysis`, `BpmnAnalyzer`, `analyze_bpmn`
- `backend/app/services/bpmn_export.py`: `BpmnExcelExporter`, `export_bpmn_to_excel`
- `backend/app/services/dataframe_service.py`: `DataFrameCacheEntry`, `cache_dataframe`, `get_dataframe`, `load_and_cache`, `apply_mapping`, `cleanup_expired_dataframes`, `get_cache_stats`, `delete_dataframe`, `cache_dataframe_persistent`, `get_dataframe_persistent`, `delete_dataframe_persistent`, `filter_dataframe`, `join_dataframes`, `apply_feature_engineering_operations`
- `backend/app/services/dataframe_storage_service.py`: `save_dataframe`, `load_dataframe`, `list_dataframes`, `delete_dataframe`, `get_storage_info`, `cleanup_expired`, `get_version_history`
- `backend/app/services/esi_analysis_service.py`: `ESIAnalysisService`
- `backend/app/services/export_service.py`: `build_excel_export`, `build_pdf_export`, `build_analysis_pdf_export`, `build_powerpoint_export`, `build_word_export`
- `backend/app/services/file_service.py`: `save_upload_file`
- `backend/app/services/job_service.py`: `create_job`, `update_job_status`, `get_job`, `list_jobs`, `cancel_job`, `cleanup_old_jobs`
- `backend/app/services/plugin_loader.py`: `PluginValidationError`, `PluginMetadata`, `LoadedPlugin`, `load_plugin_from_path`
- `backend/app/services/plugin_service.py`: `PluginConflictError`, `PluginNotFoundError`, `PluginInactiveError`, `SandboxJobNotFoundError`, `register_plugin_from_bytes`, `list_plugins`, `set_activation_state`, `get_plugin_parameters`, `run_plugin`, `get_job`
- `backend/app/services/project_archive_service.py`: `export_project_to_archive`, `import_project_from_archive`, `get_export_preview`
- `backend/app/services/sampling_service.py`: `run_materiality_assessment`, `run_mus_conservative`, `run_mus_standard`, `run_mus_stratified`, `run_mus_two_periods_combined`, `run_mus_two_periods_separate`, `run_srs_standard`, `run_srs_stratified`, `run_srs_two_periods_combined`, `run_srs_two_periods_separate`, `run_mus_stratified_two_periods_separate`, `run_srs_stratified_two_periods_separate`, `run_difference_estimation_basic`, `run_difference_estimation_ratio`, `run_difference_estimation_regression`, `run_difference_estimation_stratified`, `run_difference_estimation_two_periods`, `run_non_statistical_top_items`, `run_non_statistical_key_items`, `run_non_statistical_judgmental`, `run_non_statistical_haphazard`, `run_non_statistical_stratified_equal_probability`, `run_non_statistical_pps`, `run_non_statistical_stratified_pps`, `run_error_projection`, `run_precision_calculation`, `run_chi_square_goodness_of_fit`, `run_two_sample_t_test`, `run_normality_test`, `run_population_segmentation`
- `backend/app/services/sandbox_runner.py`: `SandboxJobStatus`, `SandboxJob`, `submit_plugin_job`, `get_job`, `list_jobs`, `is_docker_available`, `check_docker_image`, `submit_plugin_job_persistent`

## Modul- und Harvesterabdeckung

Getrackte Python-Dateien je Designer-Modul (einschließlich Tests/Modelle/Schemata; keine Funktionszahl):

| Modul | Dateien |
|---|---:|
| `document_compare` | 11 |
| `ecohesion` | 108 |
| `flowstat` | 556 |
| `lernmodule` | 19 |
| `memory` | 23 |
| `registratur` | 12 |
| `reporting` | 18 |
| `schulung` | 22 |
| `standards` | 8 |
| `vba_analyzer` | 49 |
| `vp_ai` | 273 |

Harvesterdateien unter `backend/app/modules/vp_ai/harvester/` (Basis und Scheduler eingeschlossen; nicht alle Dateien sind eigenständige Quellenadapter):

`_funding_period.py`, `acfe.py`, `audit_fraud.py`, `bafin.py`, `base.py`, `bmas.py`, `bmf.py`, `bmwk.py`, `brh.py`, `bundesrat.py`, `bundestag_dip.py`, `bva.py`, `cohesion_policy.py`, `curia.py`, `dg_empl.py`, `dg_regio.py`, `diir.py`, `eca.py`, `egesif.py`, `eu_agencies.py`, `eu_budget.py`, `eu_cohesion_2028.py`, `eu_council.py`, `eu_kommission.py`, `eu_opendata.py`, `eu_parliament.py`, `eucrim.py`, `euractiv.py`, `eurlex.py`, `eurosai.py`, `fatf.py`, `folder_watch.py`, `fraud_prevention.py`, `gesetze_im_internet.py`, `greco.py`, `hessen_foerderung.py`, `hessenrecht.py`, `hessischer_landtag.py`, `idw.py`, `ifac.py`, `iia.py`, `interreg.py`, `intosai.py`, `ipsasb.py`, `isaca.py`, `kom_guidance.py`, `kom_swd.py`, `landesrechnungshoefe.py`, `nrpp.py`, `oecd.py`, `olaf.py`, `playwright_base.py`, `rechnungshof_at.py`, `scheduler.py`, `state_aid.py`, `structural_funds_history.py`, `transparency.py`, `unodc.py`, `vvbho.py`, `wibank.py`

Vergleich gleichnamiger Rechenkerne: SHA-256 der Quelldateien wurde tatsächlich gegenübergestellt.

| Datei | Designer gegen eigenständiges FlowStat |
|---|---|
| `analysis_core_service.py` | Unterschiedlich; noch kein semantischer Gleichheitsnachweis |
| `sampling_service.py` | Unterschiedlich; noch kein semantischer Gleichheitsnachweis |
| `bpmn_analyzer.py` | Unterschiedlich; noch kein semantischer Gleichheitsnachweis |
| `esi_analysis_service.py` | Unterschiedlich; noch kein semantischer Gleichheitsnachweis |

Graphify wurde durch die übergeordnete Analyse live abgefragt: Der Knotenname `mcp_http_server.py` wurde dort einem `pdf_editor::`-Alias zugeordnet; `run_benford` war zwischen FlowStat und PDF-Editor mehrdeutig. Diese Ergebnisse sind keine bestätigte Caller-/Callee-Zuordnung dieser Revisionen. Die Consumer-Belege dieses Teilberichts stammen deshalb aus lokalen Imports, Registrierungen und gelesenen Aufrufen. Zentrale KIRA-/Graphify-Evidenz wird separat geführt.
