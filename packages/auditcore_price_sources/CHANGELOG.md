# Changelog

## 0.1.1 – 2026-09-25

Refaktorierung ohne Verhaltensänderung; Datensätze, Issues, Cursor, Fehlertexte
und Quellbelege unverändert. Benötigt `auditcore_harvest==0.1.1`.

### Umbenannt (mit Alias)
- `DestatisTabellenAdapter` → `DestatisTableAdapter` (englische Bezeichner).
  Der alte Name bleibt aus `auditcore_price_sources` und
  `auditcore_price_sources.destatis` importierbar und warnt mit
  `DeprecationWarning`. Der Katalog nennt den neuen Klassennamen
  (Katalogversion 0.1.1); Konstanten `KRAFTSTOFF_TABELLEN` und `QUELLE` bleiben.

### Geändert (intern)
- `parse_sdmx_json` in Hilfsfunktionen je Reihe/Beobachtung/Einheit zerlegt
  (McCabe 13 → ≤ 10).
- `fetch_page` von EIA, Tankerkönig und Overpass in Seiten- und
  Datensatzschritte zerlegt (je > 60 Zeilen → ≤ 60).
- Wiederkehrende Schritte über die neuen Hilfen von `auditcore_harvest` 0.1.1:
  `FetchContext.record`, `decode_json` (gleiche Fehlertexte), `page_result`.
- Typen: Konfigurationen/Cursor/JSON-Nutzlasten über `auditcore_harvest.JSON`
  bzw. `Cursor`, Nicht-JSON-Werte `object`. `Any` bleibt nur in den
  Rückgabetypen der Bestandsbrücken `legacy_exchange_rate_rows` und
  `legacy_commodity_rows` (Zeilen mit `date`/`Decimal` für die ORM-Schicht des
  Consumers).

### Messung (Code-Qualitäts-Gate)
| Kennzahl | 0.1.0 | 0.1.1 |
|---|---|---|
| McCabe > 10 | 1 | 0 |
| Funktionen > 60 Zeilen | 4 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| Nicht-englische Bezeichner | 1 | 0 |
| `Any`-Verwendungen | 31 | 2 |
| mypy --strict | 0 | 0 |
