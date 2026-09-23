# auditcore_market_indicators

Technische Marktindikatoren – Renditen, SMA/EMA, RSI, True Range/ATR,
+DI/−DI/ADX, MACD, historische Volatilität, Volumenfaktor, Z-Score,
Konsolidierungsmaß und Breakout – auf einfachen Zahlenfolgen. Die Berechnung
nutzt nur die Standardbibliothek; `polars` ist ein optionales Extra für
Series-Ein- und -Ausgabe. Das Paket ruft keine Daten ab und trifft keine
Portfolio- oder Handelsentscheidungen.

```python
from auditcore_market_indicators import ema, load_profile, rsi, sma

profil = load_profile("krypto.indicators_base", "2026.09.1")
schluss = [100.0, 101.5, 99.8, 102.3, 103.0, 101.2, 104.8]

sma(schluss, 3)  # [None, None, 100.43…, …]
ema(schluss, 3, profile=profil)  # Start = SMA der ersten 3 Werte
rsi(schluss, 3, profile=profil)  # Wilder-Glättung, erster Wert an Index 3
```

## Vertrag

- Eingaben: Folgen aus `float`/`int` oder `None` (fehlender Wert). `NaN`,
  `±inf` und Booleans werden mit `IndicatorInputError` abgewiesen.
- Ausgaben: Listen gleicher Länge. Positionen ohne ausreichende Historie und
  mathematisch undefinierte Werte (Division durch 0, Logarithmus ≤ 0) sind
  `None` – nie `NaN` oder unendlich.
- Parameterfehler behalten die Texte des Originals (`"n muss > 0 sein"`);
  `IndicatorInputError` ist ein `ValueError`.
- Anlaufphase (erster Wert): SMA/EMA/Z-Score `n−1`, RSI `n`, ATR `n−1`,
  DI `n`, ADX `2n`, historische Volatilität `n`, MACD `slow−1`, Signal
  `slow+signal−2`. Rekursive Werte hängen vom Startpunkt der Reihe ab.
- `method_reference(indikator, profile=…, **parameter)` beschreibt einen Lauf
  (Bibliothek, Methode, Parameter, Profil-Fingerabdruck) zum Speichern neben
  den Werten.

## Profile statt stiller Varianten

EMA, RSI, ATR, ADX und MACD verlangen ein ausdrücklich gewähltes Profil. Die
vier mitgelieferten Profile reproduzieren je ein Quellmodul aus
`janpow77/krypto@34d6017`:

| Profil | Quelle | EMA-Start / Lücken | RSI-Glättung / flacher Markt | ATR | Startsummen |
|---|---|---|---|---|---|
| `krypto.indicators_base` | `services/indicators/base.py` | SMA / überspringen | Wilder / 100 | SMA der TR | Neumaier (`sum()` ab Python 3.12) |
| `krypto.scoring_rsi_macd` | `services/scoring/rsi_macd.py` | SMA / halten | Wilder / 50 | – | NumPy paarweise |
| `krypto.scoring_confluence` | `services/scoring/confluence.py` | SMA / Fehler | – | – | NumPy paarweise |
| `krypto.regime_hmm` | `services/regime/hmm.py` | erster Wert / Fehler | – | – | – |
| `krypto.entschieden` (**empfohlen**, `RECOMMENDED_PROFILE`) | Nutzerentscheidung 23.09.2026 auf Basis `indicators_base` | SMA / überspringen | Wilder / 50 | Wilder | Neumaier; Rückblick ≥ 250 |

Die ersten vier Profile reproduzieren die Quellen bitgenau und bleiben dafür
unverändert. `krypto.entschieden` setzt die Nutzerentscheidung vom 23.09.2026
um („5. 250 kerzen. 6 ja wilder, rsi“) und nennt mit `min_lookback = 250` den
empfohlenen Mindest-Rückblick.

Die Glättungsvariante ist Teil des Profils (`rsi.smoothing`: `wilder`, `ema`,
`sma`; `atr.smoothing`: `sma`, `wilder`, `ema`). Eigene Profile entstehen mit
`profile_from_dict` nach demselben Schema und erhalten einen eigenen
Fingerabdruck; nichts wird still ergänzt.

## polars-Adapter

```python
import polars as pl
from auditcore_market_indicators import load_profile
from auditcore_market_indicators import polars_adapter as mi

profil = load_profile("krypto.indicators_base", "2026.09.1")
plus_di, minus_di, adx = mi.adx(high, low, close, 14, profile=profil)
```

Gleiche Funktionen, Serien-Namen (`tr`, `plus_di`, `breakout_flag` …) und
Datentypen wie `krypto/backend/app/services/indicators/base.py`.
Installation: `pip install 'auditcore_market_indicators[polars]'`.

## Nachweise

- Characterization: `tools/capture_krypto_indicators.py` führt die Originale
  tatsächlich aus (31 synthetische Reihen, 1922 Aufrufe, polars 1.44.2,
  NumPy 2.5.3); `tests/test_legacy_replay.py` spielt jeden Aufruf nach.
- Abweichungen und offene Entscheidungen: [docs/behavior-changes.md](docs/behavior-changes.md).
- Umstellung von krypto: [docs/consumer-migration.md](docs/consumer-migration.md).
- Herkunft und MIT-Freigabe: `NOTICE`, `provenance.json`. Debian:
  `python3-auditcore-market-indicators`.
