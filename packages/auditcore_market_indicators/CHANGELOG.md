# Changelog auditcore_market_indicators

Rekonstruiert aus der Git-Historie (Pull Requests #14, #23).

## 0.1.0 – 2026-09-23

- Indikatorkern aus krypto charakterisiert: Renditen, SMA/EMA, RSI, True
  Range/ATR, +DI/−DI/ADX, MACD, historische Volatilität, Volumenfaktor,
  Z-Score, Konsolidierungsmaß und Breakout mit quellengebundenen Profilen,
  polars-Adapter im Extra `[polars]`; 1 922 nachgespielte Originalaufrufe;
  Consumer krypto geplant (#14).
- Nutzerentscheidungen vom 23.09.2026 umgesetzt (#23): neues, empfohlenes
  Profil `krypto.entschieden` 2026.09.1 (`RECOMMENDED_PROFILE`) mit ATR nach
  Wilder, RSI ohne Bewegung = 50 und Mindest-Rückblick 250 Kerzen; die
  charakterisierten Profile bleiben unverändert.
