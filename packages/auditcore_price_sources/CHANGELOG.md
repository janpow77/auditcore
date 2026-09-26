# Changelog auditcore_price_sources

## 0.1.1 – 2026-09-25

Refaktorierung ohne Verhaltensänderung; Datensätze, Issues, Cursor, Fehlertexte
und Quellbelege unverändert. Benötigt `auditcore_harvest==0.1.1`.

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
| Nicht-englische Bezeichner | 1 | 1 (`DestatisTabellenAdapter`, s. u.) |
| `Any`-Verwendungen | 31 | 2 |
| mypy --strict | 0 | 0 |

### Offen
- `DestatisTabellenAdapter` behält seinen Namen: eine Umbenennung braucht einen
  Alias mit `DeprecationWarning`, der Architekturtest des Pakets lässt das
  Modul `warnings` aber nicht zu. Umbenennung, sobald ein gemeinsamer
  Alias-Helfer (`auditcore_common`) verfügbar ist.

## 0.1.0 – 2026-09-23

(Abschnitt aus der Git-Historie rekonstruiert.)

Erste Fassung (#19): Preis- und Marktdatenadapter auf `auditcore_harvest`
(Vertrag `auditcore_harvest.contract/1`) aus den charakterisierten Connectoren
von `janpow77/regulierung@853676d`.

- Adapter `price.bundesbank` (SDMX-JSON), `price.destatis_genesis` (ffcsv,
  aus regulierung verschoben), `price.eia_brent` (API v2), `price.eu_oil_bulletin`
  (Seiten-Snapshot), `price.overpass_fuel_stations`, `price.tankerkoenig`.
- Jeder Datensatz mit Einheit, Zeitbezug und Wertstatus (`fehlwert` statt 0);
  `RecordingTransport` für Quellen-Snapshots; Brücken für die bisherige
  Speicherung (`legacy_exchange_rate_rows`, `legacy_commodity_rows`,
  `legacy_station_fields`, `check_list_response`, `legacy_status`, `error_text`).
- Quellenkatalog `catalog.json`, Abweichungen PS-C01 bis PS-C13
  (`docs/behavior-changes.md`), Consumer-Umstellung (`docs/consumer-migration.md`).

### Nachträge ohne Versionsänderung

- 2026-09-23 (#28): Nutzerentscheidungen PS-H01 (`teilweise` bei Hinweisen) und
  PS-H02 (Tankerkönig nicht speichern) umgesetzt; Katalogfeld `storage` je Quelle.
- 2026-09-25 (#73): Pin auf `auditcore_harvest==0.1.1` angehoben. Das im Release
  v0.3.0 veröffentlichte Wheel 0.1.0 verlangt noch `auditcore_harvest==0.1.0`.
