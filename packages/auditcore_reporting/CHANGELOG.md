# Changelog auditcore_reporting

Rekonstruiert aus der Git-Historie (0.2.1: Pull Request #68).

## Unreleased

- Neues Modul `auditcore_reporting.web` (Extras `web`, `fastapi`): REST-Vertrag
  `reporting_ui/1` für Formatprofile, Vorschau und XLSX-Export übergebener
  Tabellen (`docs/ui/reporting-rest.md`). Formatregeln, Profile und
  `render_workbook` unverändert; Fingerabdrücke gültig.

## 0.2.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. README-Installationshinweis auf v0.4.0.

## 0.2.1 – 2026-09-25 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 88 bestehenden Tests (Flowlib-Goldens für
Zahlenformate und Arbeitsmappen, Profil-Fingerprints, Ressourcengrenzen) laufen
unverändert grün. Die Profile `flowlib-legacy-v1` und `plain-v1` sind
bytegleich; `formats.py`, `profiles.py` und `profile-registry.json` wurden
nicht berührt, damit die Implementierungs-Fingerprints gültig bleiben.

- `_excel._table_columns` in Einzelprüfungen zerlegt (Blattname, Spalten,
  Startzeile, Formate); Reihenfolge, Ausnahmetypen und Meldungen bleiben gleich.
- `_excel._body` in Zellformat, Zellschreiben und Blattabschluss
  (Spaltenbreiten, Fixierung, Autofilter) zerlegt.
- Neue Charakterisierungstests `tests/test_validation_messages.py` (19 Fälle)
  halten jeden Prüfzweig mit Typ, Meldung und Vorrang fest; sie liefen vor der
  Zerlegung gegen den unveränderten Code grün.

Messung mit `auditcore-codegate check --package auditcore_reporting`:

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 0 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Verwendungen | 4 | 4 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die `Any` stehen ausschließlich
in `formats.py` und `profiles.py`; beide Dateien sind per SHA-256 im
Profilregister verankert. Eine Verengung auf `object` würde die Fingerprints und
damit die Profilmetadaten ändern und ist deshalb bewusst unterblieben.

## 0.2.0 – 2026-09-22

- Optionaler, validierter XLSX-Export (`render_workbook`, `ReportTable`,
  `ExcelOptions`, `WorkbookLimits`) im Extra `[excel]` (openpyxl, defusedxml);
  fünf Workbook-Fälle am Flowlib-Original charakterisiert; Texte als
  XML-String gegen Formel-Injektion; Schriftreihenfolge in `styles.xml` nach
  Open-XML-SDK-Schema (Commit `05c0d24`).
- Benannte Formatprofile `flowlib-legacy-v1` und `plain-v1` mit
  `get_profile_format` und `get_profile_metadata`.
- `get_number_format` und die 34 beobachteten Fälle unverändert.

## 0.1.0 – 2026-09-22

- Eigenständig installierbare MIT-Bibliothek mit den charakterisierten
  Flowlib-Zahlenformaten `get_number_format` (34 Fälle, Commit `c4cc9e7`).
- Anwendbarkeitskontext für die Paketquelle ergänzt (Commit `ae737e2`).
