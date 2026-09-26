# REST-Vertrag Tabellenexport (`auditcore_reporting.web`, `reporting_ui/1`)

Stand 2026-09-26. Vertrag zwischen `auditcore_reporting.web` und der
Oberflächenkomponente `<flowaudit-report-export>` aus `@auditcore/ui` (Vue
`ReportExportPanel`, React `FlowauditReportExport`).

## Was das Paket kann – und was nicht

`auditcore_reporting` hat **keine Berichtsvorlagen** (keine Dokumentvorlagen,
Textbausteine, Diagramme oder PDF-Ausgabe). Es kann zwei Dinge belastbar:

1. **Formatprofile** (`flowlib-legacy-v1`, `plain-v1`): Excel-Zahlenformat je
   Spaltenname, charakterisiert gegen flowlib (34 Goldens).
2. **XLSX-Export** übergebener Tabellen (`render_workbook`, Extra `excel`):
   neu erzeugte Arbeitsmappe, Texte immer als Text (kein `=`-Formelrisiko),
   feste Ressourcengrenzen.

Der Vertrag bildet genau das ab: Die Anwendung übergibt ihre Tabellen, die
Oberfläche lässt das **Formatprofil** wählen (das ist hier die „Vorlage“),
zeigt die **Vorschau** (Format je Spalte, erste Zeilen, Probelauf des Exports)
und liefert den **Export** als XLSX. Berichtsvorlagen im engeren Sinn wären
eine neue Bibliotheksfunktion, kein Oberflächenthema.

## Einbinden

| Extra | Paket (pip) | Debian (optional, „Suggests“) |
|---|---|---|
| `auditcore_reporting[web]` | `starlette>=0.26.1,<2` | `python3-starlette (>= 0.26.1)` |
| `auditcore_reporting[fastapi]` | `fastapi>=0.92` | `python3-fastapi (>= 0.92)` |
| `auditcore_reporting[excel]` | `openpyxl`, `defusedxml` (für `/export` und den Probelauf) | `python3-openpyxl`, `python3-defusedxml` |

```python
from auditcore_reporting.web import create_app, create_router, routes
app = create_app("/api/reporting")                               # eigenständig (Starlette)
fastapi_app.include_router(create_router("/api/reporting"))       # FastAPI
```

`catalogue`, `preview` und `export` sind ohne Web-Framework aufrufbar.
Authentisierung, Berechtigung auf die exportierten Daten, CORS und
Ratenbegrenzung sind Sache der Anwendung.

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/profiles` | Formatprofile, Spaltentypen, Grenzen, `excel_available` |
| POST | `/preview` | Format je Spalte, erste 20 Zeilen, Probelauf (Größe) |
| POST | `/export` | XLSX-Datei (`Content-Disposition: attachment`) |

### Anfrage (`/preview`, `/export`)

```json
{"profile": "flowlib-legacy-v1",
 "filename": "Vorhabenliste",
 "tables": [{"name": "Vorhaben",
             "columns": ["Vorhaben", "Betrag", "Datum", "Kennung"],
             "rows": [["V-001", 1234.5, "2026-01-31", "000123"]],
             "types": {"Datum": "date", "Kennung": "text"},
             "formats": {"Kennung": "@"}}]}
```

- `profile` ist Pflicht (keine stille Voreinstellung); die Oberfläche wählt das
  erste Profil sichtbar vor.
- `rows`: Listen in Spaltenreihenfolge, gleiche Länge wie `columns`.
- `types` (optional je Spalte): `json` (Standard, JSON-Typ wie gesendet),
  `text`, `number`, `boolean`, `date`, `datetime`. `date`/`datetime` erwarten
  ISO-Text (`2026-01-31`, `2026-01-31T10:00:00`, ohne Zeitzone). Es gibt keine
  Erkennung von Zahlen oder Daten in Texten.
- `formats` (optional): ausdrückliches Excel-Format je Spalte (z. B. `@` für
  Kennungen mit führenden Nullen).
- `filename` (optional): nur Buchstaben, Ziffern, Leerzeichen, `._-()`;
  anderes wird zu `_`, `.xlsx` wird angehängt; Standard `bericht.xlsx`.

### `GET /profiles`

```json
{"contract": "reporting_ui/1", "library": "auditcore_reporting 0.3.0", "excel_available": true,
 "profiles": [{"id": "flowlib-legacy-v1", "label": "Flowlib-Formate nach Spaltennamen",
               "description": "…", "version": "1.0.0", "status": "Draft",
               "source": "janpow77/flowlib@aca2dc6a…"},
              {"id": "plain-v1", "label": "Ohne Formatregeln", "…": "…"}],
 "column_types": ["json", "text", "number", "boolean", "date", "datetime"],
 "limits": {"max_rows_per_sheet": 100000, "max_columns": 256, "max_sheets": 32,
            "max_cells": 500000, "max_text_characters": 5000000,
            "max_output_bytes": 33554432, "max_body_bytes": 16777216, "sample_rows": 20}}
```

Version, Status und Herkunft stammen aus `get_profile_metadata` (mit
geprüften Implementierungs-Fingerabdrücken).

### `POST /preview`

```json
{"contract": "reporting_ui/1", "profile": "flowlib-legacy-v1",
 "tables": [{"name": "Vorhaben", "rows": 1,
             "columns": [{"name": "Betrag", "type": "json", "format": "#,##0.00 \"EUR\"", "source": "profile"},
                         {"name": "Kennung", "type": "text", "format": "@", "source": "override"}],
             "sample": [["V-001", 1234.5, "2026-01-31", "000123"]]}],
 "workbook": {"bytes": 6843, "filename": "Vorhabenliste.xlsx"}}
```

`format` ist genau das Format, das `render_workbook` setzt
(`formats` vor `get_profile_format`). `workbook` ist das Ergebnis eines
vollständigen Probelaufs des Exports (alle Grenzen und Prüfungen der
Bibliothek); ohne Extra `excel` ist es `null`. Bei `General` behalten echte
Datumswerte die Datumsdarstellung von openpyxl.

### `POST /export`

Antwort `200` mit
`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` und
`Content-Disposition: attachment; filename="…"; filename*=UTF-8''…`.

## Fehler

`{"error": {"code": "…", "message": "…"}}`:
400 `invalid_json` (auch `NaN`/`Infinity`), 413 `too_large` (Anfrage über
16 MiB, mehr als 32 Blätter, Grenzen der Bibliothek), 422 `invalid_input`
(Vertrag, deutsche Meldung mit Feldpfad), 422 `unknown_profile`,
422 `workbook_rejected` (Prüfung der Bibliothek, z. B. ungültiger Blattname
oder Ganzzahl mit mehr als 15 Stellen – Meldung der Bibliothek im Wortlaut),
501 `excel_unavailable` (Extra `excel` fehlt).

## Oberfläche

```ts
import { ReportExportPanel, createReportingRestPort } from '@auditcore/ui'   // Vue
import { FlowauditReportExport } from '@auditcore/ui-react'                   // React
const port = createReportingRestPort({ baseUrl: '/api/reporting' })
```

Eigenschaften: `port`, `tables`, `filename`, `locale`. Ereignisse:
`preview-completed` (Vorschau), `export-completed` (`DownloadFile`), `error`
(React: `onPreviewCompleted`, `onExportCompleted`, `onError`). Die Datei wird
im Browser angeboten (`saveFile`). Ändern sich Profil, Dateiname oder
Tabellen nach einer Vorschau, wird sie als veraltet markiert.
