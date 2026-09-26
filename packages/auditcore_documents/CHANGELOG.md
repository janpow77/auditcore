# Changelog – auditcore_documents

## Unreleased

- Neu: REST-Vertrag `documents_extraction/1` für die Belegerkennung
  (`auditcore_documents.web`): `ExtractionService`, `ExtractionEngines`
  (OCR-Gateway, Chandra, Tesseract, Donut als Ports der Anwendung),
  `ExtractionSettings`, `Thresholds`; Starlette `create_extraction_app`/
  `extraction_routes` (Extra `web`), FastAPI `create_extraction_router`
  (Extra `fastapi`). `GET /profile`, `POST /runs`; ohne Engine 404
  `extraction_disabled`. Keine Speicherung, keine festen Hosts. Vertrag:
  `docs/ui/extraction-rest.md`.
- Keine Verhaltensänderung. Die Prüfziffern `de_vat_check_digit` und
`at_uid_check_digit` (`pipeline.stages.donut_values`, `donut_merge`) sind jetzt
die Funktionen aus `auditcore_identifiers` (gleiche Normalform; waren die
beiden paketübergreifenden Duplikate des Code-Gates). Neue Pflichtabhängigkeit
`auditcore_identifiers==0.1.0` (APT `python3-auditcore-identifiers`, nur
Standardbibliothek). Gleichheitstest alt ↔ neu: `tests/test_identifiers_parity.py`.

## 0.3.3 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pflichtabhängigkeit `auditcore_common==0.1.1`; README nach der Vorlage (docs/bibliotheken/readme-vorlage.md).

## 0.3.2 – Mehrdeutige Beträge als Befund statt still verworfen

Im Modus `locale-aware` (`CORRECTED_PIPELINE`) setzte `normalize_fields`
mehrdeutige (`1.234`) oder ungültige Beträge auf `None`, ohne das irgendwo
festzuhalten; nur wer zusätzlich die Regel `VAL_AMOUNT_FORMAT` ausführte, sah
den Grund.

- Neu: `normalize_fields_checked(fields, amount_mode)` → `(werte, befund)` mit
  `befund[feld] = {"raw": …, "state": "ambiguous"|"invalid"}`;
  `amount_findings(fields)` liefert den Befund allein (auch von
  `VAL_AMOUNT_FORMAT` genutzt, Evidenz unverändert).
- `PostprocessStage` setzt im Modus `locale-aware` je Befund das Flag
  `AMOUNT_AMBIGUOUS_<FELD>` bzw. `AMOUNT_INVALID_<FELD>` (zusätzlich zum
  REVIEW der Regel). `LEGACY_PIPELINE` (`legacy-de`) ist unverändert und setzt
  keine solchen Flags.
- `normalize_fields` behält Signatur und Werte; die Doku nennt die Grenze
  (`None` = fehlt oder mehrdeutig).

## 0.3.1 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung. Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`).

- Profil-Fingerprints → `canonical_sha256(data, compact=False)` (Standardtrenner
  wie bisher; das Weglassen der Altvorgaben bleibt im Paket).
- `HashingService.hash_string`/`hash_json`/`hash_file` →
  `sha256_text`/`canonical_sha256(ensure_ascii=True, default=str)`/`sha256_file`;
  `compare.sha256_file`, `pipeline.donut.sha256_file`, `utc_now`, `new_id`,
  `rate`, `compact` sind dieselben Objekte aus `auditcore_common`
  (`sha256_file`, `clock.utc_now`, `ids.new_uuid`, `numeric.parse_percent_rate`,
  `text.compact_upper`); Namen bleiben.
- Audit-Details einfrieren/auftauen → `auditcore_common.frozen`; lxml über
  `optional.require_module`.
- 634 Tests grün (Replays unverändert).

## 0.3.0 – REST-Anbindung für die Synopse-Oberfläche (2026-09-25)

Aus dem Commit `3d27fd6` (#74) rekonstruiert; bestehende Module unverändert.

- Neues Unterpaket `auditcore_documents.web` für `<flowaudit-synopsis>`:
  `SynopsisService` (Uploads prüfen, vergleichen, Zeilenauswahl und Grund,
  Ausgabe als JSON/Markdown/DOCX/PDF), Ablage-Port `ComparisonStore` mit
  `InMemoryComparisonStore`, Starlette-App `create_app` (Extra `web`) und
  FastAPI-Router `create_router` (Extra `fastapi`).
- Eigentümer je Anfrage über `identify`, fremde Vergleiche ergeben 404;
  strenge Feld- und Größenprüfung.
- Vertrag `docs/ui/synopsis-rest.md`, Paritätsinventur gegen audit_designer,
  ecohesion und regulierung in `docs/ui/synopsis-paritaet.md`;
  Debian-Suggests in `packaging/library-extras.json`.

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

- `pipeline.watchdog` ist ein Unterpaket nach Prüfgruppen: `model`
  (Befunde, Stufen, Schwellen), `values` (Werteumwandlung),
  `document_checks` (C-01 bis C-06, A-07) und `portfolio_checks`
  (C-07 bis C-10, B-12, C-12/C-13). `ExtractionQualityWatchdog`,
  `validate_extraction_quality` und alle Modelle bleiben unter
  `auditcore_documents.pipeline.watchdog` importierbar.
- `pipeline.context`: Grundlage (`model_base`) und Profileinstellungen
  (`settings_models`) ausgelagert; alle Namen bleiben über `context` erreichbar.
- `stages.ocr`: Ports, Antwortmodelle und Normalisierung in `ocr_results`;
  Ergebnisse sind als `OcrOutput` (TypedDict) typisiert, der Chandra-Dienst
  als `ChandraService`-Protocol.
- `stages.donut_merge`: Normalisierung und Textabgleich in `donut_values`,
  Kandidaten und Pflichtprüfungen in `donut_checks` (typisiert über `Parsed`
  statt `Any`); `plausibility` und `merge` in kleine Prüf- und
  Entscheidungsfunktionen zerlegt, Meldungsreihenfolge unverändert.
- `stages.validation`: Regelbasis (`validation_base`), Einzelregeln
  (`validation_rules`) und Betrugsregel (`fraud_rule`) getrennt; `validation`
  re-exportiert alle Namen.
- `PipelineOrchestrator.run`, `apply_commands` (Handler-Tabelle je
  Befehlsart), `checklist_items`, `dumps_compact`, `sanitise_settings` und
  `_sanitise_layout` (deklarative Bereinigungstabellen in unveränderter
  Reihenfolge) in kurze Funktionen zerlegt; ebenso `compare_files`,
  `build_rows`, `article_law_result`, `build_pipeline`,
  `FraudDetectionRule.evaluate` und der Gateway-Pfad der OCR-Stufe
  (keine Funktion über 60 Zeilen).
- DOCX-Synopse: Seite, Kopf-/Fußzeile, Titelblock, Gliederung, Tabelle,
  Zeilen und Anhänge als eigene Schritte, Zell-/Formatbausteine und
  `DocxStyle` in `docx_parts`; PDF-Synopse über einen Absatzbaukasten.
- Private deutsche Hilfsnamen vereinheitlicht (z. B. `_zeile_zusammenhalten`
  → `docx_parts.keep_row_together`). Keine Umbenennung öffentlicher Namen,
  keine Aliase nötig.

Belegt durch die unveränderten Charakterisierungs-, Replay- und Originaltests
sowie Differenzvergleiche gegen 0.2.0: 48 DOCX- und 40 PDF-Ausgaben
(reportlab `invariant`) bytegleich; Zufallsvergleiche für
`apply_commands` (3 000), Donut-`merge` (4 000), Watchdog (1 500),
Einstellungen (3 000) und `dumps_compact` (3 000) ergebnisgleich.

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 11 | 0 |
| Module > 400 Zeilen | 6 | 0 |
| `Any`-Vorkommen (`grep -wo`) | 221 | 209 |
| Funktionen > 60 Zeilen (Code-Gate) | 16 | 0 |
| Code-Gate `any_usages` / `mypy_strict_errors` / `non_english_identifiers` | 196 / 1 / 1 | 182 / 0 / 0 |
| mypy --strict (Paketkonfiguration) | sauber | sauber |
| Tests / Abdeckung | 581 (+3 übersprungen) / 94 % | 591 (+3 übersprungen) / 95 % |

Verbleibende `Any` stehen an Grenzen ohne Typinformation: python-docx-,
lxml-, reportlab- und torch-Objekte (keine Stubs) sowie öffentliche
JSON-Felder (`PipelineArtifacts`, `ComparisonResult.metadata`,
`SynopsisReport`).

## 0.2.0 – Donut-Port und `DONUT_PIPELINE` (2026-09-24)

Aus dem Commit `0704ace` (#47) rekonstruiert.

- `DonutPort` mit `HttpDonut` (vision-service bzw. FlowAgent über den
  `post`-Port), `FakeDonut` und `LocalDonut` (Extra `donut`, nur lokales
  Verzeichnis mit SHA-256-Prüfung vor dem Laden).
- `OcrBackend.DONUT` mit Tesseract-Abgleich, `DonutFieldMergeStage` und die
  Regeln `VAL_DONUT_PLAUSIBILITY`/`VAL_DONUT_DISAGREEMENT`: Donut-Werte nur
  nach Summen-, IBAN-, USt-IdNr.-, Steuersatz- und Datumsprüfung sowie
  Konfidenz oder Textbestätigung, sonst `REVIEW_NEEDED`.
- `LEGACY_PIPELINE` und `CORRECTED_PIPELINE` bitgenau (Fingerabdrücke und
  30 Replays).

## 0.1.x – Dokumentvergleich, Synopse und Dokumentpipeline (2026-09-23)

Aus den Commits `d779a44` (#18), `afb218a` (#26) und `e5a4eea` (#32)
rekonstruiert.

- Dokumentvergleich und Gesetzessynopse aus `audit_designer@030a71e0` mit
  DOCX- und PDF-Synopse, charakterisiert gegen das ausgeführte Original.
- Kern der flowinvoice-Dokumentpipeline (`fb2d185`) als
  `auditcore_documents.pipeline`; OCR, Persistenz und Betrugsprüfung als
  Ports; Replay 30/30 exakt.
- Entscheidungen D1–D8: `CORRECTED` (2026.09.2) empfohlenes Vergleichsprofil,
  `CORRECTED_PIPELINE` 2026.09.2 empfohlenes Pipelineprofil, Portierung des
  Extraktions-Watchdogs mit echten Umlauten; `LEGACY`, `LEGACY_DIFFLIB` und
  `LEGACY_PIPELINE` bleiben bitgenau.
