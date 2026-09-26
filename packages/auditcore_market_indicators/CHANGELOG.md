# Changelog auditcore_market_indicators

Rekonstruiert aus der Git-Historie (Pull Requests #14, #23, #59).

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. README-Installationshinweis auf v0.4.0.

## 0.1.1 – 2026-09-25 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle bestehenden Tests (bitgenauer Replay gegen die
aufgezeichneten krypto-Ausgaben, Profile, polars-Adapter, Reproduzierbarkeit,
Architektur) laufen unverändert grün. Ein zusätzlicher Differenzlauf gegen
0.1.0 (22 500 Indikatoraufrufe über alle mitgelieferten Profile mit Lücken,
NaN, Nullen und ungültigen Fenstern sowie 20 000 zufällig verfälschte
Profildokumente) ergab identische Ergebnisse und Fehlermeldungen.

- `indicators` nach Verantwortung geschnitten: Reiheneingaben, Fenster und
  Summierung in `_series`, die profilabhängigen Glättungen (EMA, RSI, ATR, ADX,
  MACD, True Range) in `_smoothers`; `indicators` behält die einfachen
  Kennzahlen und gibt alle bisherigen Namen weiter aus.
- `profile_from_dict` in Kopfprüfung, je Abschnitt eine Regel und Aufwärmphase
  zerlegt; Prüfreihenfolge und Meldungen unverändert.
- Typen: interne Profilprüfungen nehmen `Mapping[str, object]` statt
  `Mapping[str, Any]`.
- Neue Tests `tests/test_structure.py` (19 Fälle): alte Importpfade und der
  Vorrang der Profilfehler; sie liefen auch gegen 0.1.0 grün.
- Sichtbar ändert sich nur die Versionskennung `library` in den
  Methodenangaben („auditcore_market_indicators 0.1.1“).

Messung mit `auditcore-codegate check --package auditcore_market_indicators`:

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 2 | 0 |
| Module > 400 Zeilen | 1 | 0 |
| `Any`-Verwendungen | 8 | 4 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die verbleibenden `Any` stehen an
öffentlichen Signaturen (`IndicatorProfile.source`, `profile_from_dict`,
`profile_document`) und am polars-Adapter.

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
