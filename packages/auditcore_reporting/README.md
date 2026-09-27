# auditcore_reporting

## Zweck

Charakterisierte Flowlib-Zahlenformate für Berichte (Spaltenname → Excel-Zahlenformat) mit benannten Formatprofilen, optionalem, abgesichertem XLSX-Export und versionierten Berichtsvorlagen (DOCX, PDF, HTML).

Für Anwendungen, die tabellarische Berichte als Excel-Datei ausgeben –
etwa `auditcore_dataprotection` für seine tabellarischen XLSX-Exporte – und
für Prüfberichte, Vermerke und Schreiben aus Vorlagen mit Datenvertrag und
Textbausteinen (`auditcore_reporting.templates`). Der Kern
benötigt nur die Standardbibliothek (die REST-Schicht zusätzlich
`auditcore_common`); der Renderer übernimmt ausschließlich
übergebene Daten und fragt weder HTTP, Datenbanken noch Dateisysteme ab.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_reporting[excel]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.3.0 im
Release v0.4.2; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-reporting/`):

```text
auditcore_reporting @ https://github.com/janpow77/auditcore/releases/download/v0.4.2/auditcore_reporting-0.3.0-py3-none-any.whl#sha256=b0058d75d82e5367942ebed8e1381ac994cf8874ad30afee92f511672a8069a2
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)); das Excel-Extra
entspricht den Systempaketen `python3-openpyxl` und `python3-defusedxml`:

```bash
sudo apt-get install python3-auditcore-reporting
```

Extras: `[excel]` – openpyxl (≥ 3.0.9, < 4) und defusedxml für
`render_workbook`; `[web]` – Starlette für den REST-Vertrag `reporting_ui/1`
(`auditcore_reporting.web`), `[fastapi]` – zusätzlich FastAPI-Router;
`[pdf]` – reportlab (BSD, ≥ 3.6.12, < 6) für die PDF-Ausgabe der Vorlagen
(APT `python3-reportlab`); `[docx]` – defusedxml zum Einlesen von
Word-Vorlagen der Anwendung; `[dev]` – Test- und Prüfwerkzeuge (einschließlich
pandas nur für die Charakterisierung, python-docx und pypdf nur zum Nachlesen
erzeugter Dateien in Tests).

## Schnellstart

```python
from auditcore_reporting import PROFILE_IDS, get_number_format, get_profile_format

# Flowlib-Heuristik: Betrag vor Prozent vor Datum vor Anzahl vor Stunden/Tagen
assert get_number_format("Betrag") == '#,##0.00 "EUR"'
assert get_number_format("Quote %") == "0.00%"
assert get_number_format("Datum") == "DD.MM.YYYY"
assert get_number_format("Anzahl") == "#,##0"
assert get_number_format("Name") == "General"

# Benannte Profile: plain-v1 verzichtet auf die Heuristik
assert PROFILE_IDS == ("flowlib-legacy-v1", "flowlib-v2", "plain-v1")
assert get_profile_format("plain-v1", "Betrag") == "General"

# flowlib-v2: Kennungen ohne Tausendertrenner, Kopf des Kompositums entscheidet
assert get_number_format("Postleitzahl") == "#,##0"  # Altverhalten
assert get_profile_format("flowlib-v2", "Postleitzahl") == "@"
assert get_profile_format("flowlib-v2", "Stundensatz") == '#,##0.00 "EUR"'
```

```pycon
>>> get_profile_format("flowlib-legacy-v1", "Stunden")
'#,##0.00'
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_reporting.__all__` (10):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `get_number_format` | Funktion | DE: Excel-Zahlenformat anhand der unveränderten Flowlib-Heuristik auswählen. | `formats` |
| `PROFILE_IDS` | Konstante | – | `profiles` |
| `get_profile_format` | Funktion | Return a profile's format without modifying values or guessing locale. | `profiles` |
| `get_profile_metadata` | Funktion | Return versioned profile provenance after checking source and content hashes. | `profiles` |
| `ExcelDependencyError` | Ausnahme | The optional openpyxl adapter dependency is not installed. | `workbook` |
| `ExcelOptions` | Datenklasse | Formatting and resource controls; formulas are never accepted as cell data. | `workbook` |
| `ReportTable` | Datenklasse | A named sheet with ordered columns and caller-supplied rows, consumed once. | `workbook` |
| `WorkbookLimitError` | Ausnahme | Input or output exceeds an explicit workbook resource limit. | `workbook` |
| `WorkbookLimits` | Datenklasse | Per-export resource limits; row count excludes headers, cells include them. | `workbook` |
| `render_workbook` | Funktion | Render supplied tables as XLSX bytes without filesystem/network/application access. | `workbook` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_reporting.formats` | Excel-Zahlenformate / Excel format selection preserving Flowlib behavior. |
| `auditcore_reporting.formats_v2` | Excel number formats of profile ``flowlib-v2`` (successor of ``flowlib-legacy-v1``). |
| `auditcore_reporting.profiles` | Explicit format profiles; the original Flowlib selector remains unchanged. |
| `auditcore_reporting.templates` | Versioned report templates: data contract, text blocks, DOCX/PDF/HTML rendering. |
| `auditcore_reporting.web` | REST contract ``reporting_ui/1``: table export and report templates (``web``, ``fastapi``). |
| `auditcore_reporting.workbook` | Standard-library-only workbook contracts with an optional Excel adapter. |
<!-- api-overview:end -->

## Profile und Konfiguration

- `flowlib-legacy-v1`: unveränderte Flowlib-Spaltennamensheuristik; Betrag vor
  Prozent vor Datum vor Anzahl vor Stunden/Tagen, sonst `General`.
- `flowlib-v2`: Nachfolger von `flowlib-legacy-v1` mit denselben Formaten,
  aber Wörtern statt Teilzeichenketten (Kopf des Kompositums entscheidet),
  Kennungen wie Postleitzahl, Kontonummer, IBAN oder Steuernummer als `@`
  (Zahlen `0`) und Werttyp vor Spaltenname (Datumswerte immer als Datum).
  Regeln: [docs/spezifikation.md](docs/spezifikation.md).
- `plain-v1`: keine Heuristik, `General`. Echte Datumsobjekte behalten die
  notwendige openpyxl-Datumsdarstellung.
- `formats={"Kennung": "@"}` überschreibt einzelne Spalten ausdrücklich.

`get_profile_format(profile, column, value=None)` ändert keine Werte.
`get_profile_metadata(profile)` liefert versionierte Herkunft und geprüfte
Inhalts-/Implementierungshashes. Unbekannte Profile werden abgewiesen. Die
JKB-Variante hat andere Regeln und keine hier erteilte MIT-Quellfreigabe;
ihr Code wird weder übernommen noch still in Flowlib-Regeln gemischt.

XLSX-Export (Extra `[excel]`):

```python
from datetime import date
from pathlib import Path
from auditcore_reporting import ReportTable, render_workbook

content = render_workbook(
    [
        ReportTable(
            "Übersicht",
            ["Betrag", "Quote", "Datum", "Text"],
            [[123.45, 0.25, date(2024, 1, 2), "=1+1"]],
        )
    ]
)
Path("bericht.xlsx").write_bytes(content)  # Dateiziel legt der Consumer fest
```

`ReportTable(name, columns, rows, start_row=1, profile="flowlib-legacy-v1",
formats={})` definiert ein Blatt. Zeilen sind Sequenzen in Spaltenreihenfolge
oder Mappings mit exakt passenden Schlüsseln; Iteratoren werden einmal
konsumiert. Mehrere Tabellen erzeugen mehrere Blätter. Doppelte Blattnamen
(auch bei anderer Großschreibung), fehlende/zusätzliche Zellen und doppelte
Spalten werden abgewiesen.

Erlaubte Werte: `None`, `str`, `bool`, `int`, endliche `float`, `date` und
zeitzonenfreie `datetime`. NaN wird wie im Original zu einer leeren Zelle.
Zeitzonen müssen vom Consumer bewusst umgerechnet werden. Unendliche Werte,
ungültige XML-Zeichen, zu lange Texte und Ganzzahlen mit mehr als 15 Stellen
werden abgewiesen; lange Kennungen ausdrücklich als Text übergeben. Es gibt
keine stille Kürzung und keine automatische Zahlen-/Datumserkennung in Texten.

`ExcelOptions` steuert Zebra-Streifen, Rahmen, Kopfzeilenfixierung, Autofilter,
Spaltenbreiten und `WorkbookLimits`. Defaults: 100.000 Datenzeilen je Blatt,
256 Spalten, 32 Blätter, insgesamt 500.000 geschriebene Zellen, 5 Millionen
Textzeichen und 32 MiB fertige XLSX-Datei. Die XLSX-Grenzen von 1.048.576 Zeilen,
16.384 Spalten und 32.767 UTF-16-Einheiten je Textzelle gelten zusätzlich.
Eigene Limits können explizit gesetzt werden; Überschreitungen führen zu
`WorkbookLimitError`. Ungültige Eingaben führen zu `ValueError`/`TypeError`.
Ohne Extra meldet der Renderer `ExcelDependencyError`; Formatfunktionen und
Datenmodelle bleiben nutzbar.

Die Datei ist ein neu erzeugter Datenexport. Vorlagen, Charts, Makros und
Formeln aus existierenden Arbeitsmappen werden nicht importiert. Für native
Excel-Darstellung, Formelberechnung oder PDF-Ausgabe wird kein Test behauptet.

## Berichtsvorlagen

`auditcore_reporting.templates` (Kern: Standardbibliothek und
`auditcore_common`). Eine Vorlage ist eine JSON-Definition mit Kennung,
Version (MAJOR.MINOR.PATCH), Status (`Entwurf`, `Freigegeben`, `Archiviert`),
Datenvertrag als JSON-Schema-Teilmenge, benannten Bedingungen, Textbausteinen
(Text mit Platzhaltern, Bedingung, Pflichtkennzeichen, Rechtsgrundlage) und
einem Rumpf aus Blöcken (`heading`, `paragraph`, `textblock`, `list`,
`table`, `fields`, `pagebreak`, `section` mit `if` und `for`) – oder einer
Word-Datei (DOCX/DOTX) mit `{{ … }}`-Platzhaltern und `{%p … %}`/`{%tr … %}`-
Steuer-Tags. `define_template` prüft beim Anlegen jeden Platzhalter,
jede Bedingung und jede Schleife gegen den Datenvertrag, Pflichtbausteine
und die Beispieldaten; der Fingerabdruck (SHA-256) deckt Definition und
Word-Datei ab, eine registrierte Version ist unveränderlich
(`TemplateRegistry`).

Platzhalter sind Datenpfade mit festen Filtern (`text`, `zahl`, `ganzzahl`,
`eur`, `prozent`, `datum`, `ja_nein`; deutsche Schreibweise), Bedingungen
JSON-Operatoren (`filled`, `empty`, `equals`, `not_equals`, `in`, `greater`,
`less`, `at_least`, `at_most`, `all`, `any`, `not`) – keine Ausdruckssprache,
kein `eval`. `render(template, data, "docx" | "pdf" | "html", design)` prüft
die Daten (`TemplateDataError` mit allen Fundstellen) und liefert die Datei
mit Vorlagenkennung, -version, Fingerabdruck, Datenhash und verwendeten
Textbausteinen. Ausgabe deterministisch: gleiche Eingaben, gleiche Bytes
(feste ZIP-Zeitstempel, reportlab `invariant`). DOCX und HTML entstehen ohne
Fremdpakete; PDF braucht `[pdf]`. Die Gestaltung ist ein austauschbares
`DesignProfile` (Schrift, Farben, Ränder, Kopf- und Fußzeile); mitgeliefert
ist nur `neutral-v1`. Logos und Briefköpfe gehören in die Word-Vorlage der
Anwendung. Mitgelieferte neutrale Vorlagen: `vermerk` und `pruefbericht`
(ESI-Fonds, Art. 74/77 VO (EU) 2021/1060).

```python
from auditcore_reporting.templates import builtin_registry, render

report = builtin_registry().get("pruefbericht")
result = render(report, report.sample, "docx")
assert result.content[:2] == b"PK" and result.template_version == "1.0.0"
assert render(report, report.sample, "docx").content == result.content
assert "mit_feststellungen" in result.text_blocks
```

Spezifikation der Vorlagen: Invarianten I14–I18 in
[docs/spezifikation.md](docs/spezifikation.md).

## REST-Vertrag und Oberfläche

`auditcore_reporting.web` (Extras `web`/`fastapi`, Export zusätzlich `excel`)
stellt `GET /profiles`, `POST /preview` und `POST /export` bereit, für die
Berichtsvorlagen `GET /templates`, `GET /templates/{id}`,
`POST /templates/{id}/preview` und `POST /templates/{id}/render`
(Vertrag `reporting_ui/1`, [docs/ui/reporting-rest.md](../../docs/ui/reporting-rest.md);
eigene Vorlagen und Gestaltungen über `TemplateCatalogue`).
Die Oberflächen dazu sind `<flowaudit-report-export>` und
`<flowaudit-report-templates>` aus `@auditcore/ui` (React:
`FlowauditReportExport`, `FlowauditReportTemplates`). Formatregeln, Export und
Rendering laufen ausschließlich in dieser Bibliothek.

```python
from auditcore_reporting.web import catalogue, preview

assert [p["id"] for p in catalogue()["profiles"]] == ["flowlib-legacy-v1", "flowlib-v2", "plain-v1"]
table = {"name": "Liste", "columns": ["Betrag"], "rows": [[12.5]]}
result = preview({"profile": "flowlib-legacy-v1", "tables": [table]})
assert result["tables"][0]["columns"][0]["format"] == '#,##0.00 "EUR"'
```

## Herkunft und Charakterisierung

Wiederverwendung aus `janpow77/flowlib` am Commit `aca2dc6a`
(`python/flowlib/excel/formats.py`, `report.py`, `styles.py`, per SHA-256
geprüft). `get_number_format(col_name, value=None)` behält seinen Vertrag und
alle 34 beobachteten Flowlib-Fälle (`tests/fixtures/flowlib-number-format-golden.json`)
– **legacy-exakt**. Für den Workbook-Export 0.2.0 wurden fünf echte
Workbook-Fälle **vor** der Anpassung mit den Originalmodulen ausgeführt
(`tests/fixtures/flowlib-workbook-golden.json`, `tools/capture_flowlib_excel.py`);
normale Zellwerte, Formate, Stile und Breiten bleiben erhalten. Die
JKB-Variante (`auswertungjkb.get_number_format`) hat andere Regeln und keine
MIT-Quellfreigabe; sie wird weder übernommen noch in die Flowlib-Regeln
gemischt. Prüfnachweis: [docs/excel-validation.md](docs/excel-validation.md),
Profilhistorie und Releaseregeln: [docs/profiles.md](docs/profiles.md).

## Bewusste Verhaltensabweichungen

Keine eigene `docs/behavior-changes.md`; die Formatregeln sind unverändert.
Bewusst anders als das Original ist nur der Export: die beobachtete aktive
Formel `=1+1` wird zu Text (Schutz vor Formel-Injektion), Tabellen werden als
einfache Daten statt pandas-DataFrames übergeben, Formen, Typen, Textlängen und
Größen werden geprüft, und die Reihenfolge der Schrifteigenschaften in der
erzeugten `styles.xml` folgt dem Open-XML-SDK-Schema (zwei reproduzierte
Schemafehler der openpyxl-Ausgabe; Werte unverändert).

## Abhängigkeiten

Python ≥ 3.11 und `auditcore_common==0.2.0` (selbst nur Standardbibliothek;
rahmenwerkfreier Teil der REST-Schicht für `web`, APT
`python3-auditcore-common`), sonst nur die Standardbibliothek. Optional
`openpyxl>=3.0.9,<4` und `defusedxml>=0.7.1` über `[excel]`; ohne Extra meldet
`render_workbook` `ExcelDependencyError`, Formatfunktionen und Datenmodelle
bleiben nutzbar. pandas ist keine Laufzeitabhängigkeit. Berichtsvorlagen:
DOCX und HTML ohne Fremdpakete; `reportlab>=3.6.12,<6` (BSD-Lizenz) über
`[pdf]`, sonst `RenderDependencyError`; `defusedxml>=0.7.1` über `[docx]` für
Word-Vorlagen. Kein LibreOffice, kein Jinja, kein python-docx zur Laufzeit.

## Sicherheit und Datenschutz

Der Renderer erzeugt eine neue Arbeitsmappe aus übergebenen Daten: keine
Makros, keine externen Links, keine aktiven Formeln; vorhandene Arbeitsmappen,
Vorlagen und Charts werden nicht geladen. Alle Texte – auch
Spaltenüberschriften, `=...` und `#REF!` – werden als XML-String gespeichert,
ohne sie durch vorangestellte Apostrophe zu verändern. Grenzen
(`WorkbookLimits`) verhindern übergroße Dateien; die intern erzeugte
`styles.xml` wird mit defusedxml gelesen. Die Datei wird nicht geschrieben –
das Dateiziel legt der Consumer fest. Personenbezug und Berechtigungen der
exportierten Daten beurteilt die Anwendung. Ein Öffnungs- oder Layouttest in
nativem Microsoft Excel wird nicht behauptet.

Berichtsvorlagen: Word-Vorlagen werden vor jeder Verarbeitung geprüft und
abgewiesen, wenn sie Makros (VBA, makrofähige Inhaltstypen), ActiveX,
OLE-Objekte, `altChunk`/Teildokumente, angehängte Dokumentvorlagen, externe
Quellen außer Hyperlinks, nachladende Felder (`INCLUDETEXT`, `DDE`, `LINK` …),
DTDs, unsichere Eintragsnamen, Verschlüsselung oder ZIP-Bomben enthalten; jede
XML-Datei wird über `auditcore_common.safe_xml` (defusedxml, DTD verboten)
gelesen. Datenwerte werden nur eingesetzt, nie als Platzhalter oder Markup
ausgewertet; HTML ist maskiert, ohne Skripte und externe Quellen und mit
eigener Content-Security-Policy. Grenzen (`ResolveLimits`, `DocxLimits`)
verhindern übergroße Dokumente. Erzeugte Dateien enthalten keine Makros.
Die Beispieldaten sind synthetisch; Personenbezug der Berichtsdaten beurteilt
die Anwendung. Ein Öffnungstest in nativem Microsoft Word wird nicht
behauptet (geprüft mit python-docx und LibreOffice).

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`); Original-MIT und Copyright von flowlib bleiben in `LICENSE`
und `NOTICE` erhalten. Quelle, Hashes und Charakterisierung:
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
