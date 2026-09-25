# Changelog auditcore_statistics

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 160 bestehenden Tests (Replays gegen die
aufgezeichneten Ausgaben von flowstat `run_benford` und flowinvoice
`BenfordsLawAnalyzer.analyze`, Reproduzierbarkeit, Architektur) laufen
unverändert grün. Ein zusätzlicher Differenzlauf gegen 0.2.0 (56 695 Aufrufe mit
Zufallsdaten inkl. `None`, NaN, Null, Negativwerten, `Decimal`, Text und allen
Fehlerpfaden) ergab bitgleiche Ergebnisse und identische Fehlermeldungen.

- `benford_test`: Klassifizierung der Werte (`_classify` mit `_Tally`) und
  χ²-Summe (`_chi2_statistic`) als eigene Schritte.
- `legacy_run_benford`: positive Werte, Ziffernbildung, Tabellenzeile und
  SciPy-Summenprüfung als eigene Schritte; Reihenfolge der Fehler und der
  Rundungspfade (NumPy- bzw. Python-`round`) unverändert.
- `legacy_flowinvoice_benford`: kleine Stichprobe, χ²/z-Test und
  Interpretationstext als eigene Schritte.
- Typen: `legacy_run_benford(digit=…)` von `Any` auf `object`,
  `recommended_flowinvoice_benford` liefert annotiert `BenfordResult` statt
  `Any`; interne Zeilen als `dict[str, object]`.

Einzige sichtbare Änderung ist die Versionskennung `library` in
`BenfordResult.to_dict()` („auditcore_statistics 0.2.1“); sie folgt vertraglich
`__version__` (siehe `tests/test_reproducibility.py`).

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 1 | 0 |
| Funktionen > 60 Zeilen | 3 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Vorkommen | 11 | 8 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die verbleibenden `Any` stehen an
öffentlichen Rückgabe-Dictionaries (`to_dict`, Legacy-Ergebnisse),
`RECOMMENDED_PARAMETERS` und dem Parameter von
`recommended_flowinvoice_benford`; eine Verengung dort würde typisierte
Consumer brechen.
