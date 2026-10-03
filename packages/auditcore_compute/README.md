# auditcore_compute

## Zweck

Deterministische Rechenkerne für Prüfdaten: optionale Numba-Kompilierung, NumPy-Rückfall für elementweise Prüfungen, centgenaue Quoten und Zinsen, Plausibilitätsprüfungen und kompensierte Statistik.

Der ursprüngliche Python-Pfad bleibt als unabhängige Vergleichsausführung verfügbar.

Für Anwendungen der FlowAudit-Familie und auditcore-Pakete, die große
Buchungs- oder Belegtabellen prüfen (Kürzungs- und Kofinanzierungsquoten,
Zinsen auf Rückforderungen, Soll-/Ist-Abgleich, Ausreißer, Doppelförderung)
und die eigene Schleifen mit `@accelerate` beschleunigen wollen. Nicht
enthalten sind Stichprobenziehung (`auditcore_sampling`) und Hochrechnung,
TER und RER (`auditcore_extrapolation`); die Abgrenzung steht in
[docs/abgrenzung.md](docs/abgrenzung.md).

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt);
`auditcore_compute` ist noch nicht veröffentlicht, die Befehle gelten ab dem
ersten Release, das 0.1.0 enthält. Die Drittpakete NumPy (Pflicht) und Numba
(Extra `[jit]`) liegen nicht im auditcore-Index und werden vorher aus der
üblichen Quelle installiert; danach nur `--index-url`, damit kein
gleichnamiges fremdes Paket nachgeladen wird:

```bash
python -m pip install 'numpy>=1.24' 'numba>=0.59'
python -m pip install 'auditcore_compute[jit]==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256`
stehen nach der Veröffentlichung im Index unter
`https://janpow77.github.io/auditcore/simple/auditcore-compute/`):

```text
auditcore_compute @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_compute-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)); das Paket hängt von
`python3-numpy` ab, Numba ist in Debian nicht vorgesehen (NumPy-/Python-Pfad):

```bash
sudo apt-get install python3-auditcore-compute
```

Extras: `[jit]` – Kompilierung mit Numba (`numba>=0.59`); `[dev]` – Test- und
Prüfwerkzeuge (pytest, Hypothesis, Numba, pandas, polars, ruff, mypy).

## Schnellstart

Kofinanzierung und Zinsen in ganzen Cent, Abgleich und Doppelförderung auf
synthetischen Buchungen:

```python
import datetime as dt

from auditcore_compute import engine_report, to_cents_buffer
from auditcore_compute.finance import check_quota, cofinancing, interest_cents, rate_table
from auditcore_compute.validation import double_funding, reconcile

eligible = to_cents_buffer(["1000.00", "333.33", "0.05"])
split = cofinancing(eligible, "0.4")  # 40 % Förderung, Rest Eigenanteil
assert split.share.tolist() == [40000, 13333, 2]
assert (split.share + split.rest).tolist() == eligible.tolist()
assert check_quota(split.share, eligible, maximum="0.4").status.tolist() == [0, 0, 0]

# Satztabelle ist Eingabe (synthetischer Basiszins), plus 5 Prozentpunkte
table = rate_table([(dt.date(2023, 1, 1), "1.62"), (dt.date(2023, 7, 1), "3.12")]).plus_points(5)
interest = interest_cents(10_000_000, dt.date(2023, 3, 1), dt.date(2023, 9, 1), table, "act/360")
assert interest == 364_189  # 122 Tage zu 6,62 % und 62 Tage zu 8,12 % auf 100.000 €

check = reconcile([100, 200], [100, 201], tolerance_cents=1)
assert check.status.tolist() == [0, 1]  # 0 = gleich, 1 = innerhalb der Toleranz
dip = double_funding(["RE-7", "RE-7", "RE-8"], [500, 500, 500], ["V-1", "V-2", "V-1"])
assert dip.flagged.tolist() == [True, True, False]
assert {info.mode for info in engine_report()} <= {"jit", "python"}
```

Fehlende Werte werden nie still zu 0:

```pycon
>>> reconcile([1, None], [1, 2])
Traceback (most recent call last):
...
ValueError: Fehlender Wert an Position 1; nulls='mask' wählen oder bereinigen.
```

Eigene Kernel mit `@accelerate` und `to_buffer`: [docs/anleitung.md](docs/anleitung.md).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_compute.__all__` (15):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `DISABLE_ENV` | Konstante | – | `_engine` |
| `EngineInfo` | Datenklasse | Execution path of one kernel, for logs and provenance records. | `_engine` |
| `Kernel` | Klasse | A function compiled on first use, with the original kept as ``py_func``. | `_engine` |
| `MaskedBuffer` | Datenklasse | Values with an explicit missing-value mask (masked positions hold 0). | `_buffers` |
| `accelerate` | Funktion | Compile a kernel with Numba when available, else run it as Python. | `_engine` |
| `engine_info` | Funktion | Execution path (``"jit"``, ``"numpy"`` or ``"python"``) of an accelerated kernel. | `_engine` |
| `engine_report` | Funktion | Execution paths of all kernels defined so far (for provenance records). | `_engine` |
| `from_cents` | Funktion | Integer cents back to a Decimal euro amount with two places. | `_buffers` |
| `jitable` | Funktion | Mark a helper callable from kernels; it stays a plain Python function. | `_engine` |
| `prange` | Wert | ``numba.prange`` for element-wise loops; plain ``range`` without Numba. | `_engine` |
| `to_buffer` | Funktion | Convert values into a C-contiguous NumPy buffer of ``dtype`` (nulls raise). | `_buffers` |
| `to_cents` | Funktion | Euro amount as integer cents, commercially rounded (ROUND_HALF_UP). | `_buffers` |
| `to_cents_buffer` | Funktion | Euro amounts (sequence or series) as an int64 cent buffer; missing values raise. | `_buffers` |
| `to_days` | Funktion | Dates (``date`` objects or ``datetime64``) as int64 days since 1970-01-01. | `_buffers` |
| `use_python` | Funktion | Run every kernel as plain Python inside the block (e.g. for a cross-check). | `_engine` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_compute.finance` | Money in exact integer cents: interest on repayment claims and quotas. |
| `auditcore_compute.stats` | Deterministic summation and weighted moments on float64 buffers. |
| `auditcore_compute.validation` | Plausibility checks on booking rows: target/actual, outliers, double funding. |
<!-- api-overview:end -->

## Profile und Konfiguration

Keine benannten Profile. Laufzeitschalter:

- `AUDITCORE_COMPUTE_DISABLE_JIT=1` schaltet Numba aus (vor dem Import
  setzen). Elementweise Quoten-, Abgleich- und Schwellenprüfungen verwenden
  dann NumPy, andere Kerne ihre Python-Referenz. `use_python()` erzwingt
  innerhalb seines Blocks weiterhin die ursprüngliche Python-Ausführung.
  `engine_info`/`engine_report` unterscheiden `jit`, `numpy` und `python`.
- `NUMBA_CACHE_DIR` legt das Cache-Verzeichnis fest; ist keines beschreibbar,
  wird ohne Cache kompiliert. `NUMBA_NUM_THREADS` begrenzt die Threads der
  elementweisen Kernel (Ergebnisse bleiben gleich).
- Kleine Quoten-/Abgleichläufe verwenden serielles JIT, größere paralleles
  JIT. Einfache Schwellenmasken verwenden unter 250.000 Werten direkt NumPy,
  ohne einen Compiler zu initialisieren. Diese technischen Grenzen sind
  Startwerte aus lokalen Messungen; sie ersetzen keine Lastmessung der App.
  `accelerate` erlaubt mit `min_parallel_size` und `min_jit_size` eigene
  Grenzen anhand der Größe des ersten positionalen Array-Arguments;
  `min_jit_size` erfordert einen signaturgleichen NumPy-`fallback`.
  Serielle und parallele Kompilierungen erhalten unterschiedliche Cache-Schlüssel.
- Wiederholte Quoten werden in einem typgetrennten Cache mit höchstens
  1.024 Einträgen aufbereitet. Dokument- oder Mandantendaten werden dort nicht gehalten.
- Die Anwendung budgetiert Worker, Numba- und gegebenenfalls BLAS-Threads
  gemeinsam. JIT-Aufwärmen erfolgt bei Prozessen mit `fork` im Kindprozess.
  Weitere Entscheidungen und Messgrenzen: [Performance-Review](../../docs/performance/compute-review-2026-10-03.md).
- Zinsmethoden: `act/360`, `act/365`, `act/act-isda`, `30e/360`,
  `30e/360-isda`. Zinssätze, Schwellen, Toleranzen und Ausreißerfaktoren sind
  immer Eingaben des Aufrufers.

## Herkunft und Charakterisierung

Neuimplementierung in auditcore ohne Quellrepository (`provenance.json`:
`NEW_IMPLEMENTATION`). Jede Kernfunktion hat eine unabhängige reine
Python-Referenz in `tests/_reference.py` (`Fraction`, `datetime`, sortierte
Listen); Hypothesis vergleicht Beträge centgenau und Statistik innerhalb der
Fehlerschranke. Jeder Test läuft mit Engine und im Python-Pfad; die
Ergebnisse beider Pfade werden byteweise verglichen. Messungen:
[docs/benchmark.md](docs/benchmark.md).

## Bewusste Verhaltensabweichungen

Keine: es gibt keinen Vorgänger. Abweichungen vom Lastenheft (optionales
Numba, kein `fastmath`, Sätze in ganzen Basispunkten, keine Zusage linearer
Skalierung, macOS ARM64 nicht gemessen) stehen in
[docs/abgrenzung.md](docs/abgrenzung.md).

## Abhängigkeiten

- Pflicht: `numpy>=1.24`, Python `>=3.11`.
- Optional: `[jit]` – `numba>=0.59`; `[dev]` – Test- und Prüfwerkzeuge.
- pandas und polars sind keine Abhängigkeit: Serien werden über `to_numpy`,
  `isna`/`is_null` angesprochen. Keine GPU-/CUDA-Abhängigkeit.

## Sicherheit und Datenschutz

Rechnet nur im Speicher; kein Netzwerkzugriff, keine Geheimnisse, keine
personenbezogenen Daten im Paket. Geschrieben wird nur Numbas Maschinencode-
Cache (abschaltbar über `cache=False` bzw. bei schreibgeschütztem
Verzeichnis automatisch aus). Eingaben werden auf Typ, fehlende Werte und
Wertebereiche geprüft, bevor ein Kernel läuft. Ergebnisse sind Rechenwerte,
keine Feststellungen oder Entscheidungen.

## Lizenz und Herkunftsnachweis

MIT, siehe [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE); Herkunft und
Freigabe des Rechteinhabers (USER_AUTHORIZED_MIT, 22.09.2026) in
[`provenance.json`](provenance.json).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
