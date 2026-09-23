# Umstellung von regulierung auf auditcore_price_sources

Status: **getestete Integrationsvariante, noch nicht umgestellt.** Die
Requirements werden erst mit dem zentralen Release v0.3.0 geändert. Patch:
`docs/migrations/regulierung-price.patch` (Basis `janpow77/regulierung@853676d2`).

## Consumer-Stellen

| Datei | Symbol | Umstellung |
|---|---|---|
| `services/external_apis/harvest_kern.py` | neu `fuehre_aus`, `LokaleUhr`, `Warten`, `Zugang` | ein begrenzter Kernlauf mit `RecordingTransport` (Snapshots), 2 Versuche, Retry-After ≤ 30 s; `HttpxTransport`, `LaufSenke`, `LaufZustand` bleiben |
| `services/external_apis/bundesbank.py` | `BundesbankConnector.harvest` | `BundesbankSeriesAdapter` + `legacy_exchange_rate_rows`; Speicherung/Dedupe `Wechselkurs` bleibt |
| `services/external_apis/eia_brent.py` | `EiaBrentConnector.harvest` | `EiaSpotPriceAdapter` + `legacy_commodity_rows`; Speicherung `Rohstoffpreis` bleibt |
| `services/external_apis/overpass.py` | `OverpassConnector.harvest`, `HESSEN_TANKSTELLEN_QUERY` | `OverpassFuelStationAdapter` + `legacy_station_fields`; `Tankstelle`-Anlage bleibt |
| `services/external_apis/eu_oil_bulletin.py` | `EuOilBulletinConnector.harvest` | `PageSnapshotAdapter` |
| `services/external_apis/tankerkoenig.py` | `health_check` | `check_list_response`; `harvest()` bleibt deaktiviert (ADR-005) |
| `services/external_apis/destatis_genesis.py` | `DestatisTabellenAdapter`, `KRAFTSTOFF_TABELLEN`, `QUELLE` | aus `auditcore_price_sources.destatis` importiert (verschoben) |
| `services/external_apis/base.py`, `mtsk.py`, `vid_secondary.py`, `handelsregister.py`, `geoportal_hessen.py`, `api/admin/external_apis.py` | – | unverändert; `CONNECTORS`/`connector.run()`, Laufprotokoll, Registry und Geheimnisse bleiben in der Anwendung |

## Nachweis (lokal, isoliert)

- `tools/capture_regulierung_connectors.py --migrated` gegen den migrierten
  Stand, dieselben 30 Szenarien wie für das Original:
  `tests/fixtures/regulierung_migrated_observed.json`.
  **Gespeicherte Fachzeilen in allen 30 Szenarien identisch**; Health-Checks,
  MTS-K, Destatis und der EU-Snapshot vollständig identisch. Abweichungen nur
  bei fehlerhaften Antworten (Status `teilweise`, Zähler, Fehlertexte;
  PS-C02 bis PS-C11) – festgeschrieben in `tests/test_consumer_migration.py`.
- regulierung-Tests (Destatis-Kern, Registry, Rechner, Cluster) und 3 neue
  Bindungstests grün; Gesamtsuite siehe Bericht.
- Live (2026-09-23, je eine Anfrage): Bundesbank, EIA, Tankerkönig,
  EU-Seite, Overpass PASS; Destatis NOT_CONFIGURED (Kennung fehlt).

## Umstellung (nach Release v0.3.0)

1. `backend/requirements.txt`:

   ```text
   auditcore_price_sources @ https://github.com/janpow77/auditcore/releases/download/v0.3.0/auditcore_price_sources-0.1.0-py3-none-any.whl#sha256=<aus Release>
   ```
   (`auditcore_harvest==0.1.0` ist bereits gebunden.)
2. Patch anwenden (Teil `external_apis`).
3. Fachliche Abnahme PS-H01 (Anzeige `teilweise`).
