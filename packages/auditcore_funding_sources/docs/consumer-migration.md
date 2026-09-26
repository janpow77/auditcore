# Consumer-Migration flowworkshop

| Angabe | Wert |
|---|---|
| Repository | `janpow77/flowworkshop` |
| Ausgangsstand | `a05bb2143bd96d5e981f9462f05b965e1658be36` |
| Branch / Worktree | `feat/auditcore-funding-sources` in `~/Projekte/flowworkshop-wt-funding` |
| Commit | `9f5b6ec` (lokal, nicht gepusht) |
| Installierte Wheels | `auditcore_funding_sources-0.1.0` (sha256 `6a65c819…cd13`), `auditcore_harvest-0.1.0` (sha256 `b98aea3c…2dd2`) per `pip install --target` in ein Scratch-Verzeichnis, eingebunden über `PYTHONPATH`; die Anwendungsumgebung bleibt unverändert. Das spätere Wheel `061607ca…1404` (README-Formatierung in den Metadaten) enthält byte-gleichen Paketcode |

## Umfang

`services/state_aid_service.py`: `parse_amount`, `parse_date`,
`_strip_accents`, `normalize_company_name`, `detect_sa_reference`,
`_LEGAL_SUFFIXES`, `_FILLER_WORDS`.

`services/beneficiary_harvester.py`: `_normalize_for_hash`,
`compute_record_hash`, `_normalize_company_name_simple`,
`_detect_canonical_columns`, `parse_xlsx_or_csv` (XLSX/CSV über
`workshop.parse_file`, PDF über den anwendungseigenen Leser und
`workshop.map_rows`), `_stringify`, `_stringify_plz`, `_coerce_float`,
`validate_beneficiary_rows`, `filtere_nach_fonds` sowie die Konstanten
`_HASH_FIELDS`, `NAMENLOS_*`, `_CANONICAL_ALIASES`, `_FONDS_SPALTEN`.

`run_beneficiary_harvest` (Datenbankzugriff, Modi) bleibt in der Anwendung.

## Nachweise

Tests der Anwendung (`test_beneficiary_harvester`, `test_state_aid_normalize`,
`test_state_aid_nuts3`, `test_state_aid_search_quality`,
`test_audit_report_polish_v3`), Datenbank-URL auf `127.0.0.1:1`:

| Stand | passed | failed | skipped |
|---|---|---|---|
| vorher (a05bb21) | 104 | 7 | 15 |
| nachher (9f5b6ec) | 104 | 7 | 15 |

Die Mengen der fehlgeschlagenen und übersprungenen Tests sind identisch. Die
sieben Fehlschläge und 15 Übersprünge hängen an Containerpfaden (`/app/data`:
NUTS-Dateien, Alias-Liste), pymupdf und der Datenbank, nicht an der Migration.
Die beiden direkt betroffenen Dateien allein: 48 passed, 3 skipped.

`tools/capture_legacy.py flowworkshop … --migrated --modes-database …` gegen
den migrierten Stand (Wegwerf-PostgreSQL `postgres:16` auf `127.0.0.1:55440`,
danach gestoppt): 315 Fälle; Konstanten einschließlich der elf Harvest-Läufe
identisch; 313 Fälle identisch; zwei Fälle abweichend, beide
`semikolon_titelzeilen.csv` (vorher `ParserError`, nachher gelesen, FS-W04).

## Offen

- Die Pins in `requirements.txt` setzen einen Paketindex oder eine
  APT-Quelle mit beiden Paketen voraus; bis dahin baut das Docker-Image
  nicht (**MIGRATION_BLOCKED** für das Deployment, nicht für den Code).
- `typing="text"` und `header_detection="strict"` sind nicht aktiviert
  (FS-W02, FS-W03, FS-W08): Umstellung ändert Feldwerte bzw. Hashes,
  **HUMAN_DECISION_REQUIRED**.
