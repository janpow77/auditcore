# Changelog auditcore_statistics

## 0.3.2 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung außer der Bibliothekskennung in den Ergebnissen
(„auditcore_statistics 0.3.2“). Neue Laufzeitabhängigkeit
`auditcore_common==0.1.0` (APT `python3-auditcore-common`).

- `numeric.numpy_pairwise_sum` und `numeric.numpy_round` sind dieselben
  Objekte wie in `auditcore_common.numeric` (dort bitgleich gegen die
  bisherigen Kopien und gegen NumPy geprüft); die Namen in
  `auditcore_statistics.numeric` bleiben.

## 0.3.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 184 bestehenden Tests (Replays gegen die
aufgezeichneten Ausgaben von flowstat `run_benford` und flowinvoice
`BenfordsLawAnalyzer.analyze`, Konformität, REST-Vertrag, Reproduzierbarkeit,
Architektur) laufen unverändert grün. Ein zusätzlicher Differenzlauf gegen
0.3.0 (56 695 Aufrufe mit Zufallsdaten inkl. `None`, NaN, Null, Negativwerten,
`Decimal`, Text und allen Fehlerpfaden) ergab bitgleiche Ergebnisse und
identische Fehlermeldungen.

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
- `conformity` und `web` (seit 0.3.0) erfüllen die Maßstäbe bereits und sind
  unverändert.

Einzige sichtbare Änderung ist die Versionskennung `library` in
`BenfordResult.to_dict()` („auditcore_statistics 0.3.1“); sie folgt vertraglich
`__version__` (siehe `tests/test_reproducibility.py`).

Messung mit `auditcore-codegate check --package auditcore_statistics`:

| Messung | 0.3.0 | 0.3.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 1 | 0 |
| Funktionen > 60 Zeilen | 3 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Verwendungen | 10 | 6 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die verbleibenden `Any` stehen an
öffentlichen Rückgabe-Dictionaries (`to_dict`, Legacy-Ergebnisse),
`RECOMMENDED_PARAMETERS` und dem Parameter von
`recommended_flowinvoice_benford`; eine Verengung dort würde typisierte
Consumer brechen.

## 0.3.0 – Konformitätskennzahlen und REST-Vertrag (Extra `web`)

`benford_test`, die Legacy-Adapter und ihre Ergebnisse bleiben unverändert.

- Neues Modul `auditcore_statistics.conformity`: MAD mit Bewertungsbändern,
  z-Wert je Ziffer (mit Stetigkeitskorrektur) und Zweitziffertest, abgeleitet
  aus einem `BenfordResult`. Stufen und kritische Werte nur aus dem
  ausdrücklich benannten Profil `nigrini.2012`; eine Stufe ist keine
  Feststellung.
- Neues Unterpaket `auditcore_statistics.web`: REST-Vertrag (`catalogue`,
  `analyse`; JSON-Zahlen exakt als `Decimal`), Starlette-Routen und optionaler
  FastAPI-Router. Vertrag: `docs/ui/benford-rest.md`.
- Extra `web` (`starlette>=0.26`, Debian `python3-starlette`).
