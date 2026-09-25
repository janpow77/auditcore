# Changelog auditcore_market_indicators

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

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
