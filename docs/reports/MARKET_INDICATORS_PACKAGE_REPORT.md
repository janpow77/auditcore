# Paketbericht auditcore_market_indicators 0.1.0

Stand 23.09.2026, Branch `feat/auditcore-market-indicators` auf `main@886a53a`.
Ergebnisstatus: Bibliothek gebaut und geprüft; **Consumer geplant**, keine
Umstellung in krypto vorgenommen (Release v0.3.0 folgt zentral).

## Entscheidung und Consumer

H5 der [Repository-Abdeckung](../architecture/REPOSITORY_PACKAGE_COVERAGE.md)
nennt den Polars-Indikatorkern von krypto als prüfbaren Kandidaten. Ein
repositoryübergreifender Mehrfachnutzen ist nicht belegt: kiraclaw
`server/market_client.py` ruft CoinGecko-Kurse und Sparklines ab, rechnet aber
keine Indikatoren; die gleitenden Mittel in Flowstat (`chart_service.py`,
`min_periods=1`) und Designer (`period_metrics.py`) haben eine andere Fachsemantik.
Innerhalb von krypto rechnen sechs Module dieselben Indikatoren mit
abweichenden Varianten (vier EMA-, zwei RSI-, zwei SMA- und zwei
Volatilitätsimplementierungen).

**Nutzerentscheidung vom 23.09.2026:** Das Paket wird trotzdem gebaut – „der
mehrfache Nutzen kommt noch“. Der Consumer-Status lautet deshalb **geplant**.
Vorhandener Consumer: `janpow77/krypto` mit `services/indicators/base.py` und
`pipeline.py`, `scoring/rsi_macd.py`, `scoring/confluence.py`,
`scoring/adx_trend.py`, `scoring/ma_crossover.py`, `regime/hmm.py`.

## Umfang

Öffentliche API (nur Standardbibliothek): `returns`, `log_returns`, `sma`,
`rolling_std`, `ema`, `rsi`, `true_range`, `atr`, `adx`, `macd`,
`historical_volatility`, `volume_factor`, `zscore`, `normalized_range`,
`breakout`, `method_reference`; Profile über `load_profile`,
`available_profiles`, `profile_from_dict`. Optionaler Adapter
`polars_adapter` (Extra `polars`, `polars>=1.21`) mit identischen Serien-Namen und
Datentypen wie krypto `base.py`. Datenabruf, Scores, Gewichte, HMM-Modell sowie
Portfolio- und Handelslogik bleiben in krypto.

Vier versionierte Profile (2026.09.1) binden die Varianten an ihre Quellen:
`krypto.indicators_base`, `krypto.scoring_rsi_macd`, `krypto.scoring_confluence`,
`krypto.regime_hmm`. Glättung (Wilder/EMA/SMA für RSI, SMA/Wilder/EMA für ATR),
EMA-Start (SMA/erster Wert), Lückenbehandlung und Summationsreihenfolge sind
ausdrücklich Profilbestandteil; es gibt kein Standardprofil.

## Quellen und Rechte

`janpow77/krypto@34d601726227f913548a118e144de5519eee0f3f` (GitHub-HEAD
verifiziert): `indicators/base.py` 1bad05fa, `scoring/rsi_macd.py` a3e8960b,
`scoring/confluence.py` 52af074e, `regime/hmm.py` 2ae11f35,
`scoring/ma_crossover.py` 1266032a. Repository privat, ohne Lizenz. MIT gemäß
Nutzerentscheidung vom 22.09.2026 („die Bibliotheken sollen MIT sein, die
anderen Repos nicht“) für den extrahierten Bibliothekscode; keine
Umlizenzierung von krypto, Datenrechte der Marktdatendienste getrennt.
Alle Testreihen sind synthetisch.

## Characterization

`tools/capture_krypto_indicators.py` führt die Originale tatsächlich aus
(Python 3.12.3, polars 1.44.2, NumPy 2.5.3; Blobprüfung, AST-Extraktion ohne
App-Importe): **31 Reihen, 1922 Aufrufe, 343 aufgezeichnete Ausnahmen**; ein
zweiter Lauf ist inhaltsgleich. Schleifenbasierte Originale werden bitgenau
reproduziert (Neumaier-Summe wie `sum()` ab Python 3.12, NumPy-Paarweisesumme),
Fensterstatistiken auf ≤ 1·10⁻¹⁰ relativ (gemessen ≤ 8,5·10⁻¹²). Das Original
selbst weicht zwischen polars 1.21.0 und 1.44.2 bis 7,9·10⁻¹⁰ relativ und
semantisch ab; mit polars 1.12.0 und 1.20.0 bricht es mit `TypeError`
(`min_samples`) ab, obwohl krypto `polars>=1.12` zulässt.
Korrekturen MI-C01…C09, beibehaltene Profile MI-L01…L06 und Consumer-Befunde
MI-K01…K04: [behavior-changes.md](../../packages/auditcore_market_indicators/docs/behavior-changes.md).

## Tests und Gates (tatsächlich ausgeführt, Python 3.12.3)

| Prüfung | Ergebnis |
|---|---|
| Paket-pytest | **2088 passed**: Replay 1925, polars-Adapter 104, Indikatoren 34, Profile 21, Architektur 3, Reproduzierbarkeit 1 |
| ruff, ruff format, mypy strict, bandit | PASS |
| Plattform-pytest / ruff / mypy | 281 passed / PASS / PASS; `auditcore-quality`, `-consolidate`, `-refactor`, `-deploy --help` PASS |
| `tests/test_release_preparation.py` mit neuem `EXPECTED_SOURCES`-Eintrag | 24 passed |
| auditcore-quality strict (Framework `verwaltung-app-framework@15f5338`) | PASS: Syntax, Lint, Typen, bandit, pip-audit, Tests, API-Vergleich, Supply Chain; Policy PASS ohne blockierende Anforderung, SOLL-01 Hinweis |
| Policy-Nachweis `tools/policy_proof.py` | F-09, F-15, F-17 VERIFIED (T-31, T-38, F-15-methods PASS), an Quellstand, Kontext und Framework-Commit gebunden |
| Graphify (`auditcore-consolidate graphify`) | PASS, 157 Knoten, 430 Kanten |
| GitHub-CI | siehe Pull Request |

## Installation

`scripts/verify_domain_packages.py … --apt` mit installierter Plattform-Wheel:
alle 21 Prüfungen PASS – Build mit SBOM (CycloneDX 1.6), hashgebundene
Requirements-Installation, `pip check`, Importherkunft, Smoke aus dem
installierten Wheel, selektive Installation und Entfernung, zwei Debian-Revisionen,
signierte APT-Quelle, Installation, Upgrade 0.1.0-1 → 0.1.0-2 und Entfernung im
netzlosen bookworm-Container (System-Python 3.11). Wheel-SHA256
`dd2e128f97ac1a25e6e45f86f3b8fa919688622a95c401542a59f54e8ed75af6`.
Zusätzlich `installed_polars_smoke.py` nach `pip install '…whl[polars]'` PASS.
Das Debian-Paket enthält den Kern; für den polars-Adapter gibt es in bookworm
kein `python3-polars`, er ist daher nur über pip nutzbar (kein Suggests-Eintrag).

## Consumer-Integration krypto (Kopie, nicht gepusht)

Kopie von `krypto@34d6017`, eigene venv mit `pip install -e 'backend[dev]'` und
installiertem Wheel. `tools/migrate_krypto.py` stellt sechs Stellen um (siehe
[consumer-migration.md](../../packages/auditcore_market_indicators/docs/consumer-migration.md)).
`pytest tests` in `backend`: **1345 passed vorher, 1345 passed nachher**; die 92
Indikator-, Scoring- und Regime-Tests laufen gegen die installierte Bibliothek.
`ruff check app`: dieselben 63 Altbefunde, kein neuer. Keine Datenbank, kein Push.

## Offene Punkte

1. **HUMAN_DECISION_REQUIRED MI-K03:** 60-Kerzen-Rückblick der Pipeline macht
   EMA(50) und RSI(14) startabhängig; gespeichert bleibt der erste Wert.
2. **HUMAN_DECISION_REQUIRED MI-K04:** ATR als SMA (Docstring sagt Wilder) und
   RSI 100 gegenüber 50 bei flachem Markt fachlich bestätigen.
3. Umstellung in krypto: nach Release v0.3.0 Requirements binden,
   `polars>=1.21`, `pipeline_version` erhöhen – **MIGRATION_BLOCKED** bis zur
   Veröffentlichung.
4. Weitere Consumer: geplant laut Nutzerentscheidung, derzeit keiner belegt.
