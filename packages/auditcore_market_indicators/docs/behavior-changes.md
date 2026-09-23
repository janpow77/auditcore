# Legacyverhalten und korrigierter Vertrag: Marktindikatoren

Quelle: `janpow77/krypto@34d601726227f913548a118e144de5519eee0f3f` (GitHub-HEAD
am 23.09.2026 verifiziert). Tatsächlich ausgeführt mit Python 3.12.3,
polars 1.44.2 und NumPy 2.5.3 über `tools/capture_krypto_indicators.py`:
`indicators/base.py` unverändert als Modul, aus `scoring/rsi_macd.py`,
`scoring/confluence.py`, `regime/hmm.py` und `scoring/ma_crossover.py` nur die
benannten Funktionen (AST, Git-Blob geprüft). 31 synthetische Reihen, 1922
Aufrufe, davon 343 mit aufgezeichneter Ausnahme. Die Aufzeichnung ist
reproduzierbar (erneuter Lauf inhaltsgleich).

## Reproduktion

| Klasse | Funktionen | Ergebnis |
|---|---|---|
| Bitgenau | `returns`, `log_returns`, `ema`, `rsi`, `adx`, `compute_rsi`, `_ema` (rsi_macd, confluence, hmm), `compute_macd` | alle aufgezeichneten Werte identisch |
| Fensterstatistiken | `sma`, `atr`, `historical_volatility`, `volume_factor`, `zscore`, `normalized_range`, Breakout-Stärke, `_annualized_vol`, `_rolling_mean` | relativ ≤ 1·10⁻¹⁰ (gemessen ≤ 8,5·10⁻¹²), siehe MI-C04 |
| Parameterfehler | alle | gleicher Fehlertext, `ValueError` |

## Bewusst korrigiert

| ID | Original | Vertrag | Begründung |
|---|---|---|---|
| MI-C01 | `NaN`/`inf` in den Eingaben wird weitergerechnet (EMA ab der Stelle dauerhaft `NaN`). | `IndicatorInputError`; fehlende Werte sind `None`. | Datenfehler werden sichtbar statt still fortgeschrieben. |
| MI-C02 | Division durch 0 und `log(inf)` liefern `NaN`/`±inf`. | `None`. | krypto speichert über `_decimal()` ohnehin `None`; gespeicherte Werte ändern sich dadurch nicht. |
| MI-C03 | Breakout-Flag `False`, auch wenn die Regel nicht auswertbar ist. | `None` (Stärke ebenfalls `None`). | Fehlende Angaben werden nicht zu einer negativen Aussage. `bool(None)` in der Pipeline bleibt `False`. |
| MI-C04 | Fensterstatistiken über polars (Kahan-Summe, Welford-Varianz, versionsabhängig) bzw. NumPy-`cumsum`. | Fenster mit `math.fsum` (korrekt gerundet), Standardabweichung zweistufig. | Das Original schwankt selbst: polars 1.21.0 gegenüber 1.44.2 bis 7,9·10⁻¹⁰ relativ und semantisch (Nullvolumen: `NaN` gegenüber `0.0`, Z-Score `NaN` gegenüber `inf`, Breakout bei `NaN`). |
| MI-C05 | `rsi_macd._ema`: Lücke im ersten Fenster ergibt `NaN`-Start, danach Neustart mit einem Einzelwert. | Start am Ende des ersten lückenlosen Fensters. | Der Einzelwert-Neustart ist im Original als „sollte nie passieren“ kommentiert. |
| MI-C06 | `confluence`/`hmm`/`ma_crossover`: eine `NaN`-Lücke macht alle Folgewerte `NaN`. | Profile `confluence`/`hmm`: Lücke → `IndicatorInputError`; führende fehlende Werte sind Anlaufphase. SMA: nur betroffene Fenster `None`. | Keine stille Weitergabe beschädigter Werte. |
| MI-C07 | `hmm._ema([])` → `IndexError`. | `[]`. | Leere Reihe ist ein gültiger Randfall. |
| MI-C08 | `volume_factor` prüft `n` nicht; `annualization_factor` 0 → Nullen, negativ → `math domain error`. | `n ≥ 1`, Faktor endlich und > 0. | Eindeutige Parameterfehler. |
| MI-C09 | `n` als `float`/`bool` führt zu uneinheitlichen Fehlern. | `n` muss eine ganze Zahl sein. | Klarer Fehlervertrag. |

## Als Profil beibehalten (kein stilles Vereinheitlichen)

| ID | Verhalten | Profil |
|---|---|---|
| MI-L01 | ATR = einfacher gleitender Mittelwert der True Range, obwohl der Moduldocstring von `base.py` Wilder nennt. | `krypto.indicators_base`: `atr.smoothing = sma` |
| MI-L02 | RSI ohne jede Bewegung: `base.py` → 100, `rsi_macd.py` → 50. | `rsi.flat_value` 100 bzw. 50 |
| MI-L03 | RSI/ADX zählen eine Bewegung zu oder von einem fehlenden Wert als „keine Bewegung“. | `rsi.gaps`/`adx.gaps = zero_move` |
| MI-L04 | True Range ohne Vorschlusskurs = Hoch − Tief (auch nach einer Lücke). | alle |
| MI-L05 | EMA-Start: `base`/`confluence`/`rsi_macd` mit SMA (Neumaier- bzw. NumPy-Summe), `hmm` mit dem ersten Wert. | `ema.seed`, `summation` |
| MI-L06 | ADX überspringt undefinierte DX (Summe TR = 0); fehlt ein DX im ersten Fenster, bleibt der ADX leer. | alle |

## Befunde für krypto (Consumer)

- **MI-K01:** `base.py` nutzt `min_samples` (polars ≥ 1.21), `backend/pyproject.toml`
  erlaubt `polars>=1.12`. Mit polars 1.12.0 und 1.20.0 tatsächlich
  `TypeError: … unexpected keyword argument 'min_samples'`. Die Umstellung
  hebt die Untergrenze auf `polars>=1.21`.
- **MI-K02:** Gespeicherte Indikatorwerte hängen von der installierten
  polars-Version ab (siehe MI-C04); krypto pinnt polars nicht.
- **MI-K03 – HUMAN_DECISION_REQUIRED:** Die Pipeline lädt `lookback=60` Kerzen.
  EMA(50) startet an Index 49 mit einem SMA und hat nur 11 rekursive Schritte;
  RSI(14) nach Wilder ist ebenfalls startabhängig. Wegen der Idempotenzregel
  bleibt der zuerst berechnete Wert je Zeitstempel gespeichert, obwohl ein
  späterer Lauf mit anderem Fensterbeginn einen anderen Wert ergäbe
  (`tests/test_indicators.py::test_ema_value_depends_on_the_warm_up_window`).
  Zu entscheiden: längerer Rückblick oder Speichern erst nach Einschwingen.
- **MI-K04 – HUMAN_DECISION_REQUIRED:** ATR als SMA (MI-L01) und RSI-Wert bei
  flachem Markt (100 gegenüber 50, MI-L02) sind fachlich zu bestätigen. Die
  Bibliothek bildet beide Varianten ab und entscheidet nicht.

Nicht übernommen: Datenabruf (`adapters`, `ingestion`), Score-Abbildungen
(`map_rsi_to_score`, `map_macd_to_score`), Gewichte, HMM-Modell und
Handels-/Portfolio-Logik.
