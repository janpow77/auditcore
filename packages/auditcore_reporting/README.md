# auditcore_reporting

Eigenständig installierbare, frameworkunabhängige Berichtsformatierung aus
Flowlib. Die Distribution benötigt weder `auditcore` noch openpyxl, pandas,
Webframeworks oder Datenbanktreiber zur Laufzeit.

```python
from auditcore_reporting import get_number_format

assert get_number_format("Betrag") == '#,##0.00 "EUR"'
assert get_number_format("Quote") == "0.00%"
```

`get_number_format(col_name, value=None)` liefert Excel-Formatstrings anhand
der unveränderten Flowlib-Spaltennamensheuristik. Reihenfolge der Regeln:
Beträge, Prozente, Datumswerte, Anzahlen, Stunden/Tage, ansonsten `General`.
`value` bleibt aus Kompatibilitätsgründen vorhanden und beeinflusst das
Ergebnis nicht. Ungültige nichttextuelle Spaltennamen behalten das beobachtete
Fehlerverhalten. Die Funktion konvertiert keine Werte und schreibt keine Dateien.

Die 34 Golden-Fälle stammen aus beobachteten Legacy-Aufrufen vor der Extraktion.
Quelle: `janpow77/flowlib`, Commit
`aca2dc6aad25aea0720312dbcc6da00b0bcba330`,
`python/flowlib/excel/formats.py:get_number_format` samt `_PATTERNS` und
`_DEFAULT_FORMAT`. Ursprünglicher MIT-Copyrightvermerk bleibt in `LICENSE`
erhalten; Herkunft und Quellhashes stehen in `provenance.json`.

Die gleichnamige JKB-Implementierung besitzt andere Regeln und wird nicht
still zusammengeführt. Zusätzliche Formatprofile sind nicht enthalten.
Die bisherige Plattform-API `auditcore.reporting` wird durch dieses Paket
nicht verändert; Consumer migrieren ausdrücklich mit geprüfter Versionsbindung.

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
```

Installation erfolgt aus einem geprüften Wheel bzw. einem eingerichteten
Paketindex. Ein vorhandenes Git-Repository beweist keine Veröffentlichung.
Das entsprechende Debian-Paket heißt `python3-auditcore-reporting`.
Paket-Quality-/Policy-Nachweise und reale Consumerintegration werden separat
ausgewiesen; reine Unit Tests sind keine Freigabe einer Anwendung.
