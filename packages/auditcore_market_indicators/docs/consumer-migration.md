# Umstellung von krypto auf auditcore_market_indicators

Status: **Consumer geplant** – Nutzerentscheidung vom 23.09.2026: das Paket wird
auch ohne bereits belegten repositoryübergreifenden Mehrfachnutzen gebaut,
„der mehrfache Nutzen kommt noch“. Vorhandener Consumer ist `janpow77/krypto`;
dort ist noch nichts umgestellt (die Requirements-Umstellung folgt nach dem
zentralen Release v0.3.0).

## Betroffene Stellen (krypto@34d6017)

| Datei | Symbol | Profil |
|---|---|---|
| `backend/app/services/indicators/base.py` | alle zwölf Funktionen | `krypto.indicators_base` (polars-Adapter) |
| `backend/app/services/indicators/pipeline.py` | `vma_20 = vol.rolling_mean(…, min_samples=20)` → `sma(vol, 20)` | – |
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
3. `pipeline_version` der Indikator-Pipeline erhöhen (z. B. `v1.1.0`): Fenster
   werden jetzt korrekt gerundet summiert (Abweichung ≤ 1·10⁻¹⁰ relativ), so dass
   neu berechnete Zeilen als eigene Fassung gespeichert werden. Bestehende Zeilen
   bleiben unverändert (Idempotenzregel §10.6).
4. Tests: `pytest` im Verzeichnis `backend`.

## Tatsächlich geprüft (lokal, Kopie, keine Produktionsdatenbank, kein Push)

- Kopie von `krypto@34d6017`, eigene venv (Python 3.12.3, `pip install -e
  'backend[dev]'`), Wheel `auditcore_market_indicators-0.1.0-py3-none-any.whl[polars]`
  installiert.
- Vorher: `pytest tests` → **1345 passed** (nicht als Integration markierte Tests).
- Nach `migrate_krypto.py`: `pytest tests` → **1345 passed**; die Indikator-,
  Scoring- (RSI/MACD, Confluence, ADX-Trend, MA-Crossover) und Regime-Tests
  (92) laufen gegen die installierte Bibliothek.
- `ruff check app`: dieselben 63 Altbefunde wie vor der Umstellung, kein neuer.

Offene fachliche Entscheidungen vor der Umstellung: MI-K03 (Rückblick/Einschwingen)
und MI-K04 (ATR-Glättung, RSI bei flachem Markt), siehe
[behavior-changes.md](behavior-changes.md).
