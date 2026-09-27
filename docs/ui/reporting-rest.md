# REST-Vertrag Tabellenexport und Berichtsvorlagen (`auditcore_reporting.web`, `reporting_ui/1`)

Stand 2026-09-27. Vertrag zwischen `auditcore_reporting.web` und den
Oberflächenkomponenten `<flowaudit-report-export>` (Vue `ReportExportPanel`,
React `FlowauditReportExport`) und `<flowaudit-report-templates>` (Vue
`ReportTemplates`, React `FlowauditReportTemplates`) aus `@auditcore/ui`.

## Was das Paket kann – und was nicht

`auditcore_reporting` kann drei Dinge belastbar:

1. **Formatprofile** (`flowlib-legacy-v1`, `flowlib-v2`, `plain-v1`): Excel-Zahlenformat je
   Spaltenname, charakterisiert gegen flowlib (34 Goldens); `flowlib-v2`
   berücksichtigt zusätzlich den Werttyp und formatiert Kennungen als Text.
2. **XLSX-Export** übergebener Tabellen (`render_workbook`, Extra `excel`):
   neu erzeugte Arbeitsmappe, Texte immer als Text (kein `=`-Formelrisiko),
   feste Ressourcengrenzen.
3. **Berichtsvorlagen** (`auditcore_reporting.templates`): versionierte
   Vorlagen mit Datenvertrag (JSON-Schema), bedingten Textbausteinen und
   Abschnitten, deterministisch als DOCX, PDF (Extra `pdf`) und HTML, oder
   Word-Vorlagen der Anwendung mit Platzhaltern (Extra `docx`). Mitgeliefert
   sind nur die neutralen Vorlagen `vermerk` und `pruefbericht` und die
   Gestaltung `neutral-v1`; eigene Vorlagen und Hausgestaltungen übergibt die
   Anwendung als `TemplateCatalogue`.

Für Tabellen übergibt die Anwendung ihre Daten, die Oberfläche lässt das
**Formatprofil** wählen, zeigt die **Vorschau** und liefert den **Export** als
XLSX. Für Berichte wählt sie die **Vorlage**, zeigt **Datenvertrag** und
**Textbausteine**, prüft die Daten in der **Vorschau** und erzeugt den
**Bericht**.

## Einbinden

| Extra | Paket (pip) | Debian (optional, „Suggests“) |
|---|---|---|
| `auditcore_reporting[web]` | `starlette>=0.26.1,<2` | `python3-starlette (>= 0.26.1)` |
| `auditcore_reporting[fastapi]` | `fastapi>=0.92` | `python3-fastapi (>= 0.92)` |
| `auditcore_reporting[excel]` | `openpyxl`, `defusedxml` (für `/export` und den Probelauf) | `python3-openpyxl`, `python3-defusedxml` |
| `auditcore_reporting[pdf]` | `reportlab>=3.6.12,<6` (BSD; PDF-Ausgabe der Vorlagen) | `python3-reportlab (>= 3.6.12)` |
| `auditcore_reporting[docx]` | `defusedxml` (Word-Vorlagen der Anwendung einlesen) | `python3-defusedxml (>= 0.7.1)` |

```python
from auditcore_reporting.web import create_app, create_router, routes
app = create_app("/api/reporting")                               # eigenständig (Starlette)
fastapi_app.include_router(create_router("/api/reporting"))       # FastAPI

# Eigene Vorlagen und Gestaltung der Anwendung (sonst: mitgelieferte, neutral)
from auditcore_reporting.templates import TemplateRegistry, define_template, design_from_dict
from auditcore_reporting.web import TemplateCatalogue
catalogue = TemplateCatalogue(TemplateRegistry([define_template(meine_definition)]),
                              [design_from_dict({"id": "amt-v1", "header_text": "Musteramt"})])
app = create_app("/api/reporting", templates=catalogue)
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
| GET | `/templates` | Berichtsvorlagen (neueste nicht archivierte Version), Gestaltungen, verfügbare Formate |
| GET | `/templates/{id}?version=` | Datenvertrag (JSON-Schema), Beispieldaten, Bedingungen, Textbausteine |
| POST | `/templates/{id}/preview` | Datenprüfung, HTML-Vorschau, verwendete Textbausteine |
| POST | `/templates/{id}/render` | Bericht als DOCX, PDF oder HTML (`Content-Disposition: attachment`) |

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
              {"id": "flowlib-v2", "label": "Flowlib-Formate, Kennungen als Text",
               "version": "2.0.0", "…": "…"},
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

## Berichtsvorlagen

### `GET /templates`

```json
{"contract": "reporting_ui/1",
 "templates": [{"id": "pruefbericht", "version": "1.0.0", "title": "Prüfbericht",
                "document_title": "Prüfbericht {{ aktenzeichen }}", "description": "…",
                "status": "Freigegeben", "kind": "structured", "formats": ["docx", "pdf", "html"],
                "fingerprint": "…64 Hex…", "versions": ["1.0.0"]}, "…"],
 "designs": [{"id": "neutral-v1", "version": "1.0.0", "label": "Neutral", "font_family": "Arial", "…": "…"}],
 "formats": {"docx": true, "pdf": true, "html": true}}
```

`kind`: `structured` (Blöcke; DOCX, PDF, HTML) oder `docx` (Word-Vorlage; nur
DOCX). `formats` nennt, was der Server rendern kann (`pdf` nur mit Extra `pdf`).

### `GET /templates/{id}`

Zusätzlich zu den Listenfeldern: `schema` (Datenvertrag, Teilmenge von JSON
Schema 2020-12: `type`, `properties`, `required`, `additionalProperties`,
`items`, `enum`, `const`, Grenzen, `minLength`/`maxLength`,
`minItems`/`maxItems`, `format` `date`/`date-time`), `sample`
(synthetische Beispieldaten), `conditions` (benannte Bedingungen) und
`text_blocks` (`id`, `title`, `text`, `required`, `legal_basis`,
`condition`). `?version=` wählt eine ältere Version; unbekannt → 404.

### Anfrage (`/templates/{id}/preview`, `/templates/{id}/render`)

```json
{"data": {"pruefbehoerde": "Musterprüfbehörde", "aktenzeichen": "PB-2026-0042", "…": "…"},
 "version": "1.0.0", "design": "neutral-v1", "format": "pdf", "filename": "Prüfbericht"}
```

`data` ist Pflicht und wird gegen den Datenvertrag geprüft; `version` und
`design` sind optional (neueste Version, erste Gestaltung). `format` (nur
`render`) muss eines der `formats` der Vorlage sein. `filename` wie beim
Export, die Endung folgt dem Format; Standard ist die Vorlagenkennung.

### `POST /templates/{id}/preview`

```json
{"contract": "reporting_ui/1",
 "template": {"id": "pruefbericht", "version": "1.0.0", "fingerprint": "…"},
 "valid": true, "issues": [], "html": "<!DOCTYPE html>…",
 "text_blocks": ["rechtsgrundlage", "verwaltungsueberpruefung", "mit_feststellungen"],
 "data_sha256": "…"}
```

Ungültige Daten sind hier kein Fehler: `valid` ist `false`, `html` `null` und
`issues` nennt jede Fundstelle (`{"path": "$.berichtsdatum", "message": "muss
ein ISO-Datum (JJJJ-MM-TT) sein"}`, höchstens 50). Die HTML-Seite enthält
keine Skripte und keine externen Quellen (eigene Content-Security-Policy); die
Oberfläche zeigt sie in einem iframe mit `sandbox=""`. Bei Word-Vorlagen
besteht die Vorschau aus den Absatztexten des gefüllten Dokuments.

### `POST /templates/{id}/render`

Antwort `200` mit dem Medientyp des Formats, `Content-Disposition:
attachment` und den Herkunftskopfzeilen `X-Template-Id`,
`X-Template-Version`, `X-Template-Fingerprint` und `X-Data-SHA256` (SHA-256
der kanonischen Daten). Gleiche Vorlage, Daten und Gestaltung ergeben
bytegleiche Dateien; die Anwendung legt diese Angaben in ihrem Nachweis ab.

## Fehler

`{"error": {"code": "…", "message": "…"}}`:
400 `invalid_json` (auch `NaN`/`Infinity`), 413 `too_large` (Anfrage über
16 MiB, mehr als 32 Blätter, Grenzen der Bibliothek), 422 `invalid_input`
(Vertrag, deutsche Meldung mit Feldpfad), 422 `unknown_profile`,
422 `workbook_rejected` (Prüfung der Bibliothek, z. B. ungültiger Blattname
oder Ganzzahl mit mehr als 15 Stellen – Meldung der Bibliothek im Wortlaut),
501 `excel_unavailable` (Extra `excel` fehlt).

Berichtsvorlagen: 404 `unknown_template`, 422 `unknown_design`,
422 `invalid_data` (nur `render`; zusätzlich `"issues": [{"path", "message"}]`),
422 `template_rejected` (Vorlage lässt sich nicht anwenden), 413 `too_large`
(Grenzen der Auflösung: 20 000 Bausteine, 5 Mio. Zeichen, 10 000 Einträge je
Schleife), 501 `pdf_unavailable` bzw. `docx_unavailable` (Extra fehlt).

## Oberfläche

Tabellenexport:

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

Berichtsvorlagen: `ReportTemplates` / `FlowauditReportTemplates` mit
`createReportTemplatesRestPort({ baseUrl: '/api/reporting' })`, Eigenschaften
`port`, `data`, `filename`, `locale`, Ereignisse `template-select`,
`preview-completed`, `report-rendered`, `error`
([reporttemplates.md](reporttemplates.md)).
