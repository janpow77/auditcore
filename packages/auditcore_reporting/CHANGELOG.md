# Changelog auditcore_reporting

Rekonstruiert aus der Git-Historie.

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
