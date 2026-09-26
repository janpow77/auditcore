# auditcore_market_indicators

## Zweck

Technische Marktindikatoren (Renditen, SMA/EMA, RSI, ATR, ADX, MACD, Volatilität, Z-Score, Breakout) auf einfachen Zahlenfolgen, mit ausdrücklich gewählten, quellengebundenen Profilen.

Für Anwendungen, die Kursreihen auswerten – zunächst krypto, aus dem die
Berechnungen charakterisiert übernommen sind. Das Paket ruft keine Daten ab und
trifft keine Portfolio- oder Handelsentscheidungen; Scores, Gewichte und
Signallogik bleiben beim Consumer.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_market_indicators \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.1 im
Release v0.4.0; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-market-indicators/`):

```text
auditcore_market_indicators @ https://github.com/janpow77/auditcore/releases/download/v0.4.0/auditcore_market_indicators-0.1.1-py3-none-any.whl#sha256=c92a5aba7a5c4692b903fe773dcdd6f3fc51293694e9bc62544a90a93cb54371
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-market-indicators
```

Extras: `[polars]` – polars ≥ 1.21 für Series-Ein- und -Ausgabe
(`auditcore_market_indicators.polars_adapter`); `[dev]` – Test- und
Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_market_indicators import (
    IndicatorInputError,
    ema,
    load_profile,
    method_reference,
    rsi,
    sma,
)

profil = load_profile("krypto.indicators_base", "2026.09.1")
schluss = [100.0, 101.5, 99.8, 102.3, 103.0, 101.2, 104.8]

mittel = sma(schluss, 3)
assert mittel[:2] == [None, None]  # Anlaufphase n−1
werte = ema(schluss, 3, profile=profil)  # Start = SMA der ersten 3 Werte
assert werte[2] == mittel[2]
staerke = rsi(schluss, 3, profile=profil)  # Wilder-Glättung, erster Wert an Index 3
assert staerke[:3] == [None, None, None] and 0 <= staerke[3] <= 100

# Laufbeschreibung zum Speichern neben den Werten
lauf = method_reference("rsi", profile=profil, n=3)
assert lauf["profile"]["id"] == "krypto.indicators_base"

try:
    sma([1.0, float("nan")], 1)
except IndicatorInputError:
    pass  # NaN wird abgewiesen; fehlende Werte als None angeben
else:
    raise AssertionError("NaN hätte abgewiesen werden müssen")
```

```pycon
>>> [round(x, 4) for x in staerke[3:]]
[70.1754, 74.8148, 46.7593, 74.9455]
```

## API-Überblick

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

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_market_indicators.__all__` (31):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `METHOD` | Konstante | – | `indicators` |
| `RECOMMENDED_PROFILE` | Konstante | Nutzerentscheidung vom 23.09.2026 („6 ja wilder, rsi“; „5. 250 kerzen“): empfohlenes Profil für den krypto-Consumer. | `profiles` |
| `AdxResult` | Datenklasse | +DI, -DI and ADX (unpacks like the original ``(plus_di, minus_di, adx)`` tuple). | `_smoothers` |
| `BreakoutResult` | Datenklasse | Breakout flag and strength; flag ``None`` where it cannot be evaluated. | `indicators` |
| `DependencyError` | Ausnahme | The optional polars extra (``auditcore_market_indicators[polars]``) is not installed. | `errors` |
| `IndicatorInputError` | Ausnahme | Input series or parameters violate the documented contract. | `errors` |
| `IndicatorProfile` | Datenklasse | Immutable profile with identity, source and fingerprint. | `profiles` |
| `MacdResult` | Datenklasse | MACD line, signal line and histogram. | `_smoothers` |
| `MarketIndicatorError` | Ausnahme | Base class; ``code`` is stable and machine readable. | `errors` |
| `ProfileError` | Ausnahme | A profile is missing, malformed or does not define the requested indicator. | `errors` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `adx` | Funktion | +DI, -DI and ADX after Wilder (1978). | `_smoothers` |
| `atr` | Funktion | Average True Range; smoothing from ``profile.atr.smoothing``. | `_smoothers` |
| `available_profiles` | Funktion | Packaged ``(id, version)`` pairs; no profile is an implicit default. | `profiles` |
| `breakout` | Funktion | Breakout: ``P_t`` above the maximum of the ``n`` previous closes and ``VF_t > threshold``. | `indicators` |
| `ema` | Funktion | Exponential moving average with ``α = 2/(n+1)``. | `_smoothers` |
| `historical_volatility` | Funktion | Annualised volatility: rolling sample std of log returns · √factor. | `indicators` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `profiles` |
| `log_returns` | Funktion | Log return ``ln(P_t / P_{t-1})``; ``None`` if the ratio is undefined or ≤ 0. | `indicators` |
| `macd` | Funktion | MACD after Appel: ``EMA_fast - EMA_slow``, signal = EMA of the MACD line. | `_smoothers` |
| `method_reference` | Funktion | Self-description of one indicator run: library, method, parameters, profile. | `indicators` |
| `normalized_range` | Funktion | ``NR_t = (max - min) / mean`` over ``n`` values; ``None`` where the mean is 0. | `indicators` |
| `profile_document` | Funktion | Canonical dictionary of a profile's rules (for result metadata). | `profiles` |
| `profile_from_dict` | Funktion | Validate a profile document; nothing is defaulted silently. | `profiles` |
| `returns` | Funktion | Discrete return ``(P_t - P_{t-k}) / P_{t-k}``; ``None`` for the first ``periods``. | `indicators` |
| `rolling_std` | Funktion | Rolling sample standard deviation (ddof = 1) over ``n`` values. | `indicators` |
| `rsi` | Funktion | Relative Strength Index ``100 - 100 / (1 + AG/AL)``. | `_smoothers` |
| `sma` | Funktion | Simple moving average over ``n`` values; windows with a gap are ``None``. | `indicators` |
| `true_range` | Funktion | ``TR_t = max(H-L, \|H-C_{t-1}\|, \|L-C_{t-1}\|)``; ``H-L`` without a previous close. | `_smoothers` |
| `volume_factor` | Funktion | ``VF_t = V_t / VMA_n(t)``; ``None`` where the moving average is 0. | `indicators` |
| `zscore` | Funktion | Rolling z-score ``(X_t - μ_n) / σ_n``; ``None`` where ``σ_n = 0``. | `indicators` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_market_indicators.errors` | Error contract of the market indicator library. |
| `auditcore_market_indicators.indicators` | Technical market indicators on plain sequences. |
| `auditcore_market_indicators.polars_adapter` | Optional polars adapter (extra ``auditcore_market_indicators[polars]``). |
| `auditcore_market_indicators.profile_data` | – |
| `auditcore_market_indicators.profiles` | Versioned, source-bound indicator profiles. |
<!-- api-overview:end -->

## Profile und Konfiguration

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

Mit dem Extra `[polars]` stehen dieselben Funktionen für Series bereit:

```python
import polars as pl
from auditcore_market_indicators import load_profile
from auditcore_market_indicators import polars_adapter as mi

profil = load_profile("krypto.indicators_base", "2026.09.1")
plus_di, minus_di, adx = mi.adx(high, low, close, 14, profile=profil)
```

Gleiche Funktionen, Serien-Namen (`tr`, `plus_di`, `breakout_flag` …) und
Datentypen wie `krypto/backend/app/services/indicators/base.py`.

Serien-Namen (`tr`, `plus_di`, `breakout_flag` …) und Datentypen wie
`krypto/backend/app/services/indicators/base.py`.

## Herkunft und Charakterisierung

Neuimplementierung aus charakterisierten Quellen in `janpow77/krypto@34d6017`
(`services/indicators/base.py` sowie einzelne Funktionen aus
`scoring/rsi_macd.py`, `scoring/confluence.py`, `regime/hmm.py`,
`scoring/ma_crossover.py`). `tools/capture_krypto_indicators.py` führt die
Originale tatsächlich aus (31 synthetische Reihen, 1 922 Aufrufe, davon 343 mit
Ausnahme; Python 3.12.3, polars 1.44.2, NumPy 2.5.3);
`tests/test_legacy_replay.py` spielt jeden Aufruf nach. Renditen, EMA, RSI, ADX
und MACD sind bitgenau, Fensterstatistiken relativ ≤ 1·10⁻¹⁰. Consumer krypto
ist geplant ([Umstellung](docs/consumer-migration.md)).

## Bewusste Verhaltensabweichungen

MI-C01–C09, als Profil beibehaltene Varianten MI-L01–L06 und Befunde für krypto
(MI-K01–K04): [docs/behavior-changes.md](docs/behavior-changes.md).
Kurzfassung: `NaN`/`inf` in Eingaben sind ein `IndicatorInputError`,
undefinierte Werte `None` statt `NaN`/`±inf`, nicht auswertbarer Breakout
`None` statt `False`, Fensterstatistiken mit `math.fsum` statt
versionsabhängiger polars-Summen, klarere Parameterfehler. Die
Nutzerentscheidungen vom 23.09.2026 (ATR nach Wilder, RSI ohne Bewegung = 50,
Rückblick 250 Kerzen) stecken im empfohlenen Profil `krypto.entschieden`; die
charakterisierten Profile bleiben unverändert.

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional
`polars>=1.21` über `[polars]`. NumPy ist keine Abhängigkeit.

## Sicherheit und Datenschutz

Reine Berechnung auf übergebenen Zahlenfolgen: kein Netzwerk, keine Dateien
außer den mitgelieferten Profil-JSON-Dateien, keine personenbezogenen Daten.
Eigene Profile (`profile_from_dict`) werden gegen dasselbe Schema geprüft und
erhalten einen eigenen Fingerabdruck. Die Werte sind keine Anlage- oder
Handelsempfehlung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`), Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliothek; das private Quellrepository krypto wird nicht umlizenziert.
Quellen, Blobs und Entscheidungen: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
