# Rechenkerne mit `@accelerate` und `to_buffer` schreiben

Diese Anleitung richtet sich an Entwickler, die in einem auditcore-Paket eine
rechenintensive Schleife über viele Zeilen (Buchungen, Belege, Vorhaben)
beschleunigen wollen. Sie beschreibt das Muster, die Determinismusregeln und
die Prüfungen, die jeder neue Kernel bestehen muss.

## Das Muster in drei Teilen

Ein Rechenkern besteht immer aus drei Teilen:

1. **Hilfsfunktionen** mit `@jitable`: kleine, reine Funktionen auf Skalaren
   (z. B. Rundung, Datumsumrechnung). Sie bleiben gewöhnliche
   Python-Funktionen und werden in kompilierte Kernel eingebettet.
2. **Kernel** mit `@accelerate`: eine Schleife über C-zusammenhängende
   NumPy-Arrays fester Datentypen, die ihr Ergebnis in ein vorher angelegtes
   Ausgabe-Array schreibt (oder einen Skalar zurückgibt).
3. **Öffentliche Funktion** ohne Dekorator: Sie nimmt Listen, Arrays oder
   pandas-/polars-Serien entgegen, wandelt sie mit `to_buffer`,
   `to_cents_buffer` oder `to_days` um, prüft Wertebereiche, legt die
   Ausgabe an, ruft den Kernel und gibt typisierte Ergebnisse zurück.

```python
import numpy as np
import numpy.typing as npt

from auditcore_compute import accelerate, jitable, prange, to_buffer


@jitable
def clamp(value: int, limit: int) -> int:
    return limit if value > limit else value


@accelerate(parallel=True)  # nur elementweise: jede Zeile unabhängig
def clamp_kernel(values: npt.NDArray[np.int64], limit: int, out: npt.NDArray[np.int64]) -> None:
    for i in prange(values.shape[0]):
        out[i] = clamp(values[i], limit)


def clamp_cents(values: object, limit_cents: int) -> npt.NDArray[np.int64]:
    data = to_buffer(values, np.int64)  # fehlende Werte lösen ValueError aus
    out = np.zeros(data.shape, dtype=np.int64)
    clamp_kernel(data, limit_cents, out)
    return out
```

Ohne Numba (Extra `[jit]` nicht installiert), mit
`AUDITCORE_COMPUTE_DISABLE_JIT=1` oder wenn Numba den Kernel nicht übersetzen
kann, läuft **dieselbe** Funktion als reines Python. Das wird einmal über
`logging` (Logger `auditcore_compute`, Stufe WARNING) gemeldet und ist über
`engine_info(clamp_kernel)` bzw. `engine_report()` abfragbar. Konsumenten
schreiben `engine_report()` (als `as_dict()`) in ihre Provenienz.

## Determinismusregeln (verbindlich)

Prüfergebnisse müssen bitgleich reproduzierbar sein – zwischen Läufen,
Rechnern, Thread-Zahlen und zwischen kompiliertem und Python-Pfad.

1. **Kein `fastmath`.** `accelerate(fastmath=...)` mit einem wahren Wert wirft
   `ValueError`. `fastmath` erlaubt Umordnung und FMA-Zusammenfassung von
   Gleitkomma-Operationen; das Ergebnis hinge dann vom Compiler ab.
2. **`parallel=True` nur elementweise.** Eine `prange`-Schleife darf nur
   Ausgabezellen `out[i]` beschreiben. Keine Summen, Mittelwerte, Zähler oder
   Maxima über `prange` – Numba würde sie als parallele Reduktion in
   wechselnder Reihenfolge ausführen. `tests/test_architecture.py` prüft das
   (kein `x += …` auf einer einfachen Variablen in parallelen Kerneln).
3. **Reduktionen sequenziell und kompensiert.** Gleitkomma-Summen laufen in
   Eingabereihenfolge mit Neumaier-Kompensation (`stats.deterministic_sum`,
   intern `_compensated_sum`).
4. **Geld nur in ganzen Cent (`int64`).** Beträge kommen über `to_cents` bzw.
   `to_cents_buffer` (aus `Decimal`, `str`, `int` als Euro, `float` über
   `Decimal(str(x))`, Rundung `ROUND_HALF_UP`; float64-Arrays und -Serien
   wandelt `to_cents_buffer` vektorisiert und bitgleich dazu um, nur Werte nahe
   einem halben Cent über `Decimal`). Quoten sind exakte Brüche
   (`finance.rate`), Zinssätze ganze Basispunkte. Kein `float64` für Geld.
5. **Wertebereiche prüfen, bevor der Kernel läuft.** `int64` läuft in Numba
   still über. Die öffentliche Funktion begrenzt deshalb die Eingaben
   (Beträge bis 10 Mrd. € je Zeile, Nenner bis 10⁶, Daten 1900–2199) und der
   Kernel nutzt überlauffreie Hilfen wie `mul_div_round`.
6. **Gleiche Semantik in beiden Pfaden.** Nur Operationen verwenden, die in
   Python und Numba gleich definiert sind: Ganzzahl-`//` und `%` (beide
   abrunden), IEEE-Gleitkomma, `abs`, `min`, `max`, `np.sort` auf endlichen
   Werten. Keine Zufallszahlen, keine Zeitstempel, keine Ausgabe im Kernel.
7. **Fehlende Werte nie still als 0.** `to_buffer(..., nulls="raise")` (Standard)
   wirft; `nulls="mask"` liefert Werte **und** Maske, die der Kernel
   ausdrücklich auswertet (Beispiel: `validation.reconcile`).

## `to_buffer` im Detail

`to_buffer(values, dtype, *, nulls="raise")` mit `dtype` aus `np.int64`,
`np.float64`, `np.bool_`:

| Eingabe | Verhalten |
|---|---|
| passendes, C-zusammenhängendes `ndarray` | wird unverändert zurückgegeben (keine Kopie) |
| anderes `ndarray` | genau eine Kopie, nur verlustfreie Umwandlung (`np.can_cast(..., "safe")`) |
| `pandas.Series`/`polars.Series` ohne Lücken | `to_numpy()`, bei numerischen Serien ohne Kopie |
| Serie mit `NA`/`null`/NaN | `ValueError` oder `MaskedBuffer(values, missing)` |
| Liste, Tupel, Generator | Typprüfung je Element (kein `1.5` in `int64`, kein `bool` als Zahl) |
| Zeichenkette, Skalar, 2-D-Array | `TypeError` bzw. `ValueError` |

pandas und polars werden nicht importiert, sondern über `to_numpy`, `isna`
bzw. `is_null` angesprochen (duck typing).

## Cache und Container

`@accelerate(cache=True)` (Standard) legt den Maschinencode im Numba-Cache ab.
Der Schlüssel enthält zusätzlich einen Hash aller Module des Pakets
(`SOURCE_FINGERPRINT`): Numba selbst prüft nur die Datei des Kernels und würde
nach einer Änderung an einer `@jitable`-Hilfe in einem anderen Modul sonst
veralteten Code laden. Ist kein Cache-Verzeichnis beschreibbar (read-only
Container, Debian-Paket unter `/usr/lib`), wird ohne Cache kompiliert; der
Grund steht in `engine_info(...).reason`. Mit `NUMBA_CACHE_DIR` lässt sich ein
beschreibbares Verzeichnis vorgeben.

## Pflichtprüfungen für einen neuen Kernel

- Reine Python-Referenz im Testcode (andere Mittel als der Kernel, z. B.
  `Fraction`, `datetime`, sortierte Listen) und Abgleich mit Hypothesis:
  Cent-Beträge exakt, Statistik innerhalb weniger ULP bzw. der Fehlerschranke
  des Verfahrens.
- Bitgleichheit: Ergebnis mit Engine und unter `use_python()` byteweise
  vergleichen (`tests/conftest.py`: `both_paths`, `bits`). Die
  Autouse-Fixture führt jeden Test zusätzlich im Python-Pfad aus.
- Grenzfälle: leere Arrays, negative Beträge, NaN/fehlende Werte, Schaltjahre,
  Monatsenden.
- 100 % Zeilenabdeckung, `mypy --strict`, `ruff`, Komplexität ≤ 10 je Funktion.

## Messen statt versprechen

Ob ein Kernel schneller ist als NumPy-Vektorisierung, hängt von der Operation
ab. `tools/benchmark.py` misst Quoten- und Plausibilitätsprüfung auf 500.000
Zeilen; die Ergebnisse stehen in [benchmark.md](benchmark.md). Es gibt keine
Zusage linearer Skalierung über Kerne.
