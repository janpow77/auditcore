# Abgrenzung und Umsetzung des Lastenhefts

`auditcore_compute` ergänzt die bestehenden Fachpakete um eine
Rechen-Engine und um Fachroutinen, die es dort noch nicht gibt. Es doppelt
keine vorhandenen Verfahren.

## Was bewusst nicht enthalten ist

| Thema | Zuständiges Paket | Grund |
|---|---|---|
| Stichprobenumfang, MUS-Ziehung, Schichtung | `auditcore_sampling` | bereits in reinem Python implementiert und charakterisiert |
| Hochrechnung, Präzision, TER, RER | `auditcore_extrapolation` | bereits nach EGESIF_16-0014-01 und CPRE_23-0013-01 Annex 3 implementiert |
| Benford-Analyse, Chi-Quadrat | `auditcore_statistics` | bereits vorhanden |
| GPU/CUDA | – | ausgeschlossen (Entscheidung zum Lastenheft) |

Wenn eines dieser Pakete später Beschleunigung braucht, nutzt es
`auditcore_compute.accelerate` für seine eigenen Kernel (siehe
[anleitung.md](anleitung.md)); die Fachlogik bleibt in seinem Paket.

## Umsetzung der Anforderungen

| Anforderung | Umsetzung | Abweichung oder Einschränkung |
|---|---|---|
| hardwarenah kompilierter Rechenkern (Numba/LLVM) | `@accelerate` → `numba.njit` beim ersten Aufruf | Numba ist optional (Extra `[jit]`) |
| Dekorator `@accelerate` | `accelerate(func, *, parallel=False, cache=True)` | `fastmath` ist verboten (`ValueError`), weil Ergebnisse bitgleich sein müssen |
| Konverter `to_buffer` | `to_buffer(values, dtype, *, nulls=…)`, dazu `to_cents_buffer`, `to_days` | `dtype` als NumPy-Typ (`np.int64`, `np.float64`, `np.bool_`) |
| Rückfall ohne Compiler | identische Python-Funktion; einmalige Warnung über `logging`; `engine_info`, `engine_report`; `AUDITCORE_COMPUTE_DISABLE_JIT=1` | – |
| Zinsroutinen | tagesgenaue Zinsen, act/360, act/365, act/act (ISDA), 30E/360, 30E/360 (ISDA, „deutsche Methode“), stückweise Sätze aus einer Satztabelle | Sätze nur in ganzen Basispunkten (zwei Nachkommastellen in Prozent), Daten 1900–2199, Beträge bis 10 Mrd. € je Zeile |
| Quotenroutinen | Kürzung, Kofinanzierung, Eigenanteil in Cent, exakte Schwellenwertprüfung | Quote als exakter Bruch mit Nenner ≤ 10⁶ |
| Plausibilitätsroutinen | Soll-/Ist-Abgleich, feste Schwelle, MAD, IQR, Doppelförderung | Schwellen, Toleranzen und Faktoren sind Eingaben |
| Faktor ≥ 15 gegenüber CPython auf 500.000 Zeilen | gemessen mit `tools/benchmark.py`, siehe [benchmark.md](benchmark.md) | ehrliche Messung inklusive Vergleich mit NumPy und Einzelthread |
| Linux x86_64 und macOS ARM64 | Linux x86_64 lokal geprüft (Python 3.12 mit Numba, Python 3.11 mit NumPy 1.24 ohne Numba) | macOS ARM64 wurde nicht gemessen (keine Hardware im Lauf); Numba bietet Wheels für macOS ARM64 an |
| `nogil`/lineare Skalierung | – | wird nicht zugesagt; elementweise Kernel laufen mit `parallel=True`, gemessen statt versprochen |

## Zinsmethoden

Die Bezeichnungen folgen den ISDA 2006 Definitions, Abschnitt 4.16:

- `act/360`, `act/365`: tatsächliche Tage durch 360 bzw. 365.
- `act/act-isda`: Tage in Schaltjahren durch 366, übrige durch 365.
- `30e/360` (4.16(g)): Tag 31 wird zu 30, Februar unverändert.
- `30e/360-isda` (4.16(h), häufig „deutsche Methode“): der letzte Tag eines
  Monats wird zu 30, außer das Zinsende ist der letzte Februartag.

Gezählt wird `[Beginn, Ende)`: der Beginn zählt mit, das Ende nicht. Bei
Satzwechseln wird jeder Abschnitt nach der Methode gezählt; gerundet wird
einmal am Ende je Zeile (kaufmännisch, ab 0,5 Cent vom Nullpunkt weg).

Die Satztabelle ist Eingabe. Für § 49a Abs. 3 VwVfG (fünf Prozentpunkte über
dem Basiszinssatz) wird die Basiszins-Tabelle mit `rate_table(...)` angelegt
und mit `.plus_points(5)` erhöht; das Paket enthält keine Basiszinssätze.
Ob und ab wann ein Erstattungsanspruch zu verzinsen ist, entscheidet die
Behörde, nicht die Bibliothek.
