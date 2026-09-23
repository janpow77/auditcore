# Umstellung von krypto auf auditcore_market_indicators

Status: **Consumer geplant** – Nutzerentscheidung vom 23.09.2026: das Paket wird
auch ohne bereits belegten repositoryübergreifenden Mehrfachnutzen gebaut,
„der mehrfache Nutzen kommt noch“. Vorhandener Consumer ist `janpow77/krypto`;
dort ist noch nichts umgestellt (die Requirements-Umstellung folgt nach dem
zentralen Release v0.3.0).

## Betroffene Stellen (krypto@34d6017)

| Datei | Symbol | Profil |
|---|---|---|
| `backend/app/services/indicators/base.py` | alle zwölf Funktionen | `krypto.entschieden` = `RECOMMENDED_PROFILE` (polars-Adapter) |
| `backend/app/services/indicators/pipeline.py` | `vma_20 = vol.rolling_mean(…, min_samples=20)` → `sma(vol, 20)`; `lookback: int = 60` → `250` | `min_lookback` |
| `backend/app/services/pipelines/hourly.py`, `four_hour.py`, `daily.py` | `lookback=60` / `60` / `90` → `lookback=250` | `min_lookback` |
| `backend/app/services/scoring/rsi_macd.py` | `compute_rsi`, `_ema` (damit `compute_macd`) | `krypto.scoring_rsi_macd` |
| `backend/app/services/scoring/confluence.py` | `_ema_numpy` | `krypto.scoring_confluence` |
| `backend/app/services/regime/hmm.py` | `_ema`, `_annualized_vol` | `krypto.regime_hmm`, `rolling_std` |
| `backend/app/services/scoring/ma_crossover.py` | `_rolling_mean` | `sma` |
| `backend/app/services/scoring/adx_trend.py` | nutzt `base.adx` – keine Änderung | – |

Öffentliche Namen, Signaturen, Serien-Namen und Rückgabetypen bleiben
erhalten. `tools/migrate_krypto.py` führt genau diese Änderungen auf einer
**Kopie** aus (prüft vorher die Git-Blobs, schreibt nichts in ein Repository):

```bash
python tools/migrate_krypto.py <kopie-von-krypto> --ruff <krypto-venv>/bin/ruff
```

## Schritte

1. `backend/pyproject.toml`: `polars>=1.12` → `polars>=1.21` (MI-K01) und
   `auditcore_market_indicators[polars]==0.1.0` ergänzen (nach Veröffentlichung
   von v0.3.0; bis dahin Wheel aus dem Release-Artefakt).
2. `tools/migrate_krypto.py` anwenden oder die Tabelle oben von Hand umsetzen.
3. Entscheidungen vom 23.09.2026 übernehmen: `base.py` rechnet mit dem Profil
   `krypto.entschieden` (ATR nach Wilder, RSI 50 bei flachem Markt; „6 ja
   wilder, rsi“), Rückblick der Pipeline von 60 (täglich 90) auf 250 Kerzen
   („5. 250 kerzen“). Die Scoring-/Regime-Module behalten ihre charakterisierten
   Profile (`rsi_macd` liefert bei flachem Markt bereits 50).
4. `pipeline_version` der Indikator-Pipeline erhöhen (z. B. `v2.0.0`): ATR und
   flacher RSI ändern sich fachlich, EMA/RSI durch den längeren Rückblick, die
   Fenster werden korrekt gerundet summiert. Neu berechnete Zeilen werden als
   eigene Fassung gespeichert, bestehende bleiben unverändert (Idempotenzregel §10.6).
5. Tests: `pytest` im Verzeichnis `backend`.

## Tatsächlich geprüft (lokal, Kopie, keine Produktionsdatenbank, kein Push)

- Kopie von `krypto@34d6017`, eigene venv (Python 3.12.3, `pip install -e
  'backend[dev]'`), Wheel `auditcore_market_indicators-0.1.0-py3-none-any.whl[polars]`
  installiert.
- Vorher: `pytest tests` → **1345 passed** (nicht als Integration markierte Tests).
- Nach `migrate_krypto.py` (Profil `krypto.entschieden`, Rückblick 250):
  `pytest tests` → **1345 passed**; die Indikator-,
  Scoring- (RSI/MACD, Confluence, ADX-Trend, MA-Crossover) und Regime-Tests
  (92) laufen gegen die installierte Bibliothek.
- `ruff check app`: dieselben 63 Altbefunde wie vor der Umstellung, kein neuer.

MI-K03 (Rückblick) und MI-K04 (ATR-Glättung, RSI bei flachem Markt) sind seit
dem 23.09.2026 entschieden, siehe [behavior-changes.md](behavior-changes.md).
