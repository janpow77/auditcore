# auditcore_reporting 0.2.1

Frameworkunabhängige Berichtsformatierung und optionaler echter XLSX-Export.
Der Kern benötigt ausschließlich die Standardbibliothek. Version 0.1.0 bleibt
unverändert; `get_number_format(col_name, value=None)` behält seinen bisherigen
Vertrag und alle 34 beobachteten Flowlib-Fälle.

```bash
python -m pip install 'auditcore_reporting[excel]==0.2.1'
# Debian: Kernpaket python3-auditcore-reporting, Excel-Extra über python3-openpyxl python3-defusedxml
```

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

Der Renderer übernimmt ausschließlich übergebene Daten. Er fragt weder HTTP,
Datenbanken noch Dateisysteme ab, lädt keine vorhandenen Arbeitsmappen und
liefert vollständige XLSX-Bytes. Er erstellt keine Makros, externen Links oder
aktiven Formeln. Alle Texte – auch Spaltenüberschriften, `=...` und `#REF!` –
werden ausdrücklich als XML-String gespeichert, ohne ihren Inhalt durch
vorangestellte Apostrophe zu verändern.

## Datenvertrag und Grenzen

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

## Formatprofile und Kompatibilität

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

## Herkunft, Sicherheit und Prüfung

Wiederverwendung aus `janpow77/flowlib` am Commit
`aca2dc6aad25aea0720312dbcc6da00b0bcba330`; Original-MIT und Copyright bleiben
in `LICENSE`/`NOTICE` erhalten. Fünf echte Workbook-Characterization-Fälle
wurden **vor** der Anpassung mit den per SHA256 geprüften Originalmodulen
ausgeführt. Normale Zellwerte, Formate, Stile und Breiten bleiben erhalten.
Die beobachtete aktive Originalformel `=1+1` wird im neuen Datenexport bewusst
zu Text; dies ist ein expliziter Sicherheitstest, keine heimliche Gleichsetzung.

```bash
python -m pip install -e '.[dev,excel]'
pytest
ruff check .
mypy src
python -I tests/installed_smoke.py        # nach Installation des Core-Wheels
python -I tests/installed_excel_smoke.py  # installiertes Wheel mit Excel-Extra
```

`tools/capture_flowlib_excel.py ORIGINAL_EXCEL_DIR OUTPUT_JSON` wiederholt
Originalbeobachtungen und prüft zuerst die Quellhashes; pandas wird nur für
diese Dev-Charakterisierung verwendet. pandas ist keine Laufzeitabhängigkeit.
Die XLSX-Stringbehandlung folgt dem [openpyxl-Zellmodell](https://openpyxl.pages.heptapod.net/openpyxl/_modules/openpyxl/cell/cell.html).

Die Kontextdatei beschreibt Bibliotheks-Selfchecks mit synthetischen Daten.
Berechtigungen, Personenbezug und Freigaben tatsächlicher Consumer bleiben
separat zu beurteilen. Die Profilhistorie und Releaseregeln stehen in
[docs/profiles.md](docs/profiles.md).

The Excel extra also includes defusedxml for the bounded, internally generated
styles XML. Font properties are reordered without changing their values to match
the [Open XML SDK Font schema](https://github.com/dotnet/Open-XML-SDK/blob/main/generated/DocumentFormat.OpenXml/DocumentFormat.OpenXml.Generator/DocumentFormat.OpenXml.Generator.OpenXmlGenerator/schemas_openxmlformats_org_spreadsheetml_2006_main.g.cs).
This corrects two reproduced schema errors from openpyxl output. Package and
Microsoft365 SDK schema validation are distinct from native Excel execution;
no native Excel opening test is claimed.
