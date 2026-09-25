# Changelog auditcore_price_sources

Aus der Git-Historie rekonstruiert (`git log -- packages/auditcore_price_sources`).

## 0.1.0 – 2026-09-23

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
