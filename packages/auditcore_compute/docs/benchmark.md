# Messung: Quoten- und Plausibilitätsprüfung auf 500.000 Zeilen

Gemessen mit `tools/benchmark.py` (Seed 20261003, 500.000 synthetische
Buchungszeilen, beste von fünf Wiederholungen) am 03.10.2026 auf einem
Linux-Rechner (x86_64, 20 logische Kerne), Python 3.12.3, NumPy 2.5.3,
Numba 0.68.0. Alle Varianten liefern identische Ergebnisse; das Skript bricht
sonst ab.

- **Quote:** Förderbetrag je Zeile (Betrag × Fördersatz, kaufmännisch auf
  Cent gerundet, fünf verschiedene Sätze) und exakte Prüfung gegen einen
  synthetischen Höchstsatz von 75 %.
- **Plausibilität:** Soll-/Ist-Differenz mit Toleranz 1 € und Statuscode,
  dazu feste Betragsschwelle.
- **c)** ruft die Kernel direkt mit fertigen Puffern auf; **c')** die
  öffentlichen Funktionen mit Eingabeprüfung (eine Quote für alle Zeilen).

## Standard-Threads (elementweise Kernel parallel)

| Variante | Quote [ms] | Plausibilität [ms] | Faktor ggü. CPython | Faktor ggü. NumPy |
|---|---:|---:|---:|---:|
| a) CPython-Schleife | 95.2 | 43.5 | 1.0 | 0.11 |
| b) NumPy vektorisiert | 11.6 | 3.1 | 9.4 | 1.00 |
| c) JIT-Kernel | 1.7 | 0.6 | 60.0 | 6.39 |
| c') öffentliche API (JIT, Eingabeprüfung, eine Quote) | 2.9 | 1.6 | 30.9 | 3.29 |
| d) Kernel als reines Python (Rückfall) | 960.8 | 176.9 | 0.1 | 0.01 |
| Erstaufruf JIT ohne Cache (Kompilierung) | 1660 (beide zusammen) | – | – | – |

## Ein Thread (`NUMBA_NUM_THREADS=1`)

| Variante | Quote [ms] | Plausibilität [ms] | Faktor ggü. CPython | Faktor ggü. NumPy |
|---|---:|---:|---:|---:|
| a) CPython-Schleife | 93.3 | 45.6 | 1.0 | 0.08 |
| b) NumPy vektorisiert | 8.1 | 3.3 | 12.2 | 1.00 |
| c) JIT-Kernel | 6.9 | 1.6 | 16.4 | 1.34 |
| c') öffentliche API (JIT, Eingabeprüfung, eine Quote) | 6.2 | 2.6 | 15.8 | 1.29 |
| d) Kernel als reines Python (Rückfall) | 962.6 | 178.0 | 0.1 | 0.01 |
| Erstaufruf JIT aus dem Cache | 175 (beide zusammen) | – | – | – |

## Umwandlung in Cent und Faktorisierung (500.000 Werte)

Gleicher Lauf, Seed 20261003: Beträge mit zwei Nachkommastellen, davon 1 %
mit einem zusätzlichen halben Cent (diese gehen über `Decimal`); Schlüssel als
ganze Zahlen mit etwa 250.000 verschiedenen Werten. Das Skript prüft vorher,
dass beide Wege dasselbe Ergebnis liefern. Die Umwandlung braucht kein Numba;
die Zeiten mit `NUMBA_NUM_THREADS=1` sind gleich.

| Umwandlung | Zeit [ms] |
|---|---:|
| `to_cents` je Wert (`Decimal`) | 525.5 |
| `to_cents_buffer` vektorisiert (float64-Array) | 13.9 |
| `factorize` über eine Liste (Elementpfad) | 134.0 |
| `factorize` vektorisiert (int64-Array) | 97.2 |

- `to_cents_buffer` ist für float64-Arrays und -Serien etwa 38-mal schneller
  als die Umwandlung je Wert und bitgleich zu `to_cents`: Kandidat ist
  `rint(x·100)`; Werte, deren Hundertfaches näher als eine großzügige
  Fehlerschranke (6400·ulp(x) + 4·ulp(x·100)) an einem halben Cent liegt, und
  Beträge ab 10¹¹ € rechnet die Funktion über `Decimal(str(x))` nach.
- `factorize` gewinnt vektorisiert nur das 1,4-Fache, weil `np.unique`
  sortiert. Texte bleiben deshalb im Elementpfad (ein Sortieren von
  Zeichenketten war in der Messung langsamer als das Hashen).

## Bewertung

- Die Anforderung „Faktor ≥ 15 gegenüber reinem CPython“ ist auf diesem
  Rechner erfüllt: 60 (parallel) bzw. 16,4 (ein Thread) für die Kernel, 30,9
  bzw. 15,8 über die öffentliche API. Mit einem Thread liegt der Faktor knapp
  über der Grenze; auf langsameren Rechnern kann er darunter liegen.
- Gegenüber gut vektorisiertem NumPy ist der Gewinn klein: mit einem Thread
  das 1,3-Fache, parallel das 3- bis 6-Fache. Der Faktor 15 gegenüber NumPy
  wird **nicht** erreicht und wird auch nicht zugesagt.
- Der Rückfallpfad (Kernel als reines Python auf NumPy-Arrays) ist etwa
  achtmal langsamer als eine schlichte CPython-Schleife über Listen, weil
  jeder Elementzugriff ein NumPy-Skalar erzeugt. Er dient der Korrektheit und
  dem Gegenprüfen, nicht dem Tempo; ohne Numba ist für große Tabellen
  NumPy-Vektorisierung der schnellere Weg.
- Die erste Kompilierung kostet etwa 1,7 s für zwei Kernel; aus dem Cache
  sind es unter 0,2 s. In schreibgeschützten Containern ohne Cache fällt die
  Kompilierung bei jedem Prozessstart an.
- Parallelität skaliert nicht linear; gemessen wurde nur dieser Rechner.
  macOS ARM64 wurde nicht gemessen.

Erneut messen:

```bash
python tools/benchmark.py                      # Standard-Threads
NUMBA_NUM_THREADS=1 python tools/benchmark.py  # ein Thread
AUDITCORE_COMPUTE_DISABLE_JIT=1 python tools/benchmark.py  # nur Python-Pfad
```
