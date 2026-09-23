# auditcore_price_sources

Preis- und Marktdatenquellen als Adapter auf dem gemeinsamen Harvest-Kern
`auditcore_harvest` (Vertrag `auditcore_harvest.contract/1`). Laufzeit:
Standardbibliothek und `auditcore_harvest==0.1.0`; kein Netzwerkclient, keine
Datenbank, kein Scheduler. Erster Consumer: `janpow77/regulierung`
(`services/external_apis/`, Admin-API `api/admin/external_apis.py`).

```bash
pip install auditcore_price_sources==0.1.0
```

| Quelle | Adapter | Zugang | Einheit | Zeitbezug |
|---|---|---|---|---|
| `price.bundesbank` | `BundesbankSeriesAdapter` | keiner | aus der Reihe (z. B. USD je 1 EUR) | Tag |
| `price.destatis_genesis` | `DestatisTabellenAdapter` | `username` + Geheimnis `token` | je Tabelle (`value_unit`) | Zeitangaben der Tabelle |
| `price.eia_brent` | `EiaSpotPriceAdapter` | Geheimnis `api_key` | aus `units` (USD/Barrel) | Handelstag |
| `price.eu_oil_bulletin` | `PageSnapshotAdapter` | keiner | – (nur Seiten-Snapshot) | Abrufzeitpunkt |
| `price.overpass_fuel_stations` | `OverpassFuelStationAdapter` | keiner | – (Stammdaten, WGS84) | OSM-Datenstand |
| `price.tankerkoenig` | `TankerkoenigListAdapter` | Geheimnis `api_key` | EUR/Liter | Abrufzeitpunkt, **kein** Änderungszeitpunkt |

```python
from auditcore_harvest import AdapterRegistry, HarvestEngine, HarvestRequest
import auditcore_price_sources as ps

registry = AdapterRegistry()
ps.register(registry)
engine = HarvestEngine(
    transport=mein_transport,
    credentials=meine_geheimnisse,
    state=mein_zustand,
    clock=uhr,
    sleeper=warten,
)
ergebnis = engine.run(
    registry.create("price.bundesbank"),
    HarvestRequest("price.bundesbank", run_id="lauf-1"),
    meine_senke,
    config={"url": "https://api.statistiken.bundesbank.de/rest"},
)
ps.legacy_status(ergebnis)  # "erfolg" | "teilweise" | "fehler"
```

Jeder Datensatz nennt Einheit (mit Herkunft `quelle`/`profil`/`unbekannt`),
Zeitbezug (Art und Wert) und Wertstatus: ein fehlender Quellwert ist
`wert: null` mit `status: fehlwert`, nie 0. Unlesbare Einträge werden als
Hinweis gemeldet und machen den Lauf `partial`, statt still zu verschwinden.
`RecordingTransport` hält Quellen-Snapshots (Rohantwort, SHA-256, ohne
Geheimnisparameter) für Archiv und Paket-Hash. Brücken für die bestehende
Speicherung: `legacy_exchange_rate_rows`, `legacy_commodity_rows`,
`legacy_station_fields`, `check_list_response`, `legacy_status`, `error_text`.

- Quellenkatalog mit Herkunft, Consumer, Konfiguration, Einheit, Zeitbezug,
  Datenrechten (`REVIEW_REQUIRED`) und Live-Prüfstatus:
  `src/auditcore_price_sources/catalog.json`.
- Beobachtetes Originalverhalten und Abweichungen PS-C01 bis PS-C13, offene
  Entscheidungen PS-H01/PS-H02: [docs/behavior-changes.md](docs/behavior-changes.md).
- Umstellung von regulierung: [docs/consumer-migration.md](docs/consumer-migration.md).
- Eigene Adapter: Anleitung und Contract-Suite in `auditcore_harvest`
  (`docs/adapter-guide.md`, `auditcore_harvest.testing.assert_adapter`); alle
  Adapter dieses Pakets bestehen die Suite.

Laufprotokoll, Registry, Zugangsdatenverwaltung, ORM-Speicherung, Scheduler
und Anwendungsrechte bleiben beim Consumer. MTS-K (Push-Eingang) und die
vertraglich nicht angebundenen Verbraucher-Informationsdienste haben keinen
Abrufvertrag und sind nicht enthalten. Herkunft und Lizenz: `NOTICE`,
`provenance.json` (MIT, Freigabe des Rechteinhabers vom 22.09.2026; Daten der
Dienste nicht erfasst). Debian-Paket: `python3-auditcore-price-sources`.
