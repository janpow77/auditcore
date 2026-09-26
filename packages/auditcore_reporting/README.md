# auditcore_reporting

## Zweck

Charakterisierte Flowlib-Zahlenformate für Berichte (Spaltenname → Excel-Zahlenformat) mit benannten Formatprofilen und optionalem, abgesichertem XLSX-Export.

Für Anwendungen, die tabellarische Berichte als Excel-Datei ausgeben –
etwa `auditcore_dataprotection` für seine tabellarischen XLSX-Exporte. Der Kern
benötigt nur die Standardbibliothek; der Renderer übernimmt ausschließlich
übergebene Daten und fragt weder HTTP, Datenbanken noch Dateisysteme ab.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_reporting[excel]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.2 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-reporting/`):

```text
auditcore_reporting @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_reporting-0.2.2-py3-none-any.whl#sha256=417f78ca06b8458860699a88728e15118a855a41d8999fc58b87aadab9ce4ba8
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)); das Excel-Extra
entspricht den Systempaketen `python3-openpyxl` und `python3-defusedxml`:

```bash
sudo apt-get install python3-auditcore-reporting
```

Extras: `[excel]` – openpyxl (≥ 3.0.9, < 4) und defusedxml für
`render_workbook`; `[dev]` – Test- und Prüfwerkzeuge (einschließlich pandas nur
für die Charakterisierung).

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
assert PROFILE_IDS == ("flowlib-legacy-v1", "plain-v1")
assert get_profile_format("plain-v1", "Betrag") == "General"
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
| `auditcore_reporting.profiles` | Explicit format profiles; the original Flowlib selector remains unchanged. |
| `auditcore_reporting.workbook` | Standard-library-only workbook contracts with an optional Excel adapter. |
<!-- api-overview:end -->

## Profile und Konfiguration

- `flowlib-legacy-v1`: unveränderte Flowlib-Spaltennamensheuristik; Betrag vor
  Prozent vor Datum vor Anzahl vor Stunden/Tagen, sonst `General`.
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

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional
`openpyxl>=3.0.9,<4` und `defusedxml>=0.7.1` über `[excel]`; ohne Extra meldet
`render_workbook` `ExcelDependencyError`, Formatfunktionen und Datenmodelle
bleiben nutzbar. pandas ist keine Laufzeitabhängigkeit.

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

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`); Original-MIT und Copyright von flowlib bleiben in `LICENSE`
und `NOTICE` erhalten. Quelle, Hashes und Charakterisierung:
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
