# auditcore_price_sources

## Zweck

Preis- und Marktdatenquellen (Bundesbank, Destatis GENESIS, EIA, Tankerkönig, Overpass, EU Oil Bulletin) als Adapter auf `auditcore_harvest`, mit Einheit, Zeitbezug und Wertstatus je Datensatz.

Für Anwendungen der Preisüberwachung und -prüfung; erster Consumer ist
`janpow77/regulierung` (`services/external_apis/`). Laufprotokoll, Registry,
Zugangsdatenverwaltung, Speicherung, Scheduler und Anwendungsrechte bleiben
beim Consumer; das Paket enthält weder Netzwerkclient noch Datenbank.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_price_sources \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.3 im
Release v0.4.2; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-price-sources/`):

```text
auditcore_price_sources @ https://github.com/janpow77/auditcore/releases/download/v0.4.2/auditcore_price_sources-0.1.3-py3-none-any.whl#sha256=f48ee1f9dd1ab3dfc283b17e40a0cfc5e76152f496a36c75acb6264796211d74
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-price-sources
```

Keine Extras außer `[dev]` (Test- und Prüfwerkzeuge).

## Schnellstart

Ein vollständiger Lauf des EIA-Adapters mit aufgezeichneter Antwort
(`ReplayTransport`) statt Netzwerk; der API-Schlüssel kommt aus dem
Credential-Provider und wird weder abgeglichen noch aufgezeichnet:

```python
from auditcore_harvest import AdapterRegistry, HarvestEngine, HarvestRequest, ReplayTransport
from auditcore_harvest.memory import (
    ClockSleeper, FixedClock, ListSink, MemoryStateStore, StaticCredentials,
)

import auditcore_price_sources as ps

BASE = "https://example.invalid/api"
answer = {"response": {"total": "2", "data": [
    {"period": "2026-09-01", "product": "EPCBRENT", "value": "71.25", "units": "$/BBL"},
    {"period": "2026-08-31", "product": "EPCBRENT", "value": None, "units": "$/BBL"},
]}}
params = {  # Anfrage, die der Adapter stellt (30-Tage-Fenster zur Engine-Uhr)
    "frequency": "daily", "data[0]": "value", "facets[product][]": "EPCBRENT",
    "start": "2026-08-02", "end": "2026-09-01", "sort[0][column]": "period",
    "sort[0][direction]": "desc", "offset": "0", "length": "5000",
}
transport = ReplayTransport(({
    "request": {"method": "GET", "url": f"{BASE}/petroleum/pri/spt/data/", "params": params},
    "response": {"status": 200, "body_json": answer},
},))

registry = AdapterRegistry()
ps.register(registry)
clock = FixedClock()  # 01.09.2026 08:00 UTC
engine = HarvestEngine(
    transport=transport,
    credentials=StaticCredentials({("price.eia_brent", "api_key"): "schlüssel"}),
    state=MemoryStateStore(), clock=clock, sleeper=ClockSleeper(clock),
)
sink = ListSink()
result = engine.run(
    registry.create("price.eia_brent"),
    HarvestRequest("price.eia_brent", run_id="lauf-1"), sink, config={"url": BASE},
)
assert ps.legacy_status(result) == "erfolg"
values = {r.record_id: r.normalized for r in sink.records.values()}
assert values["EPCBRENT@2026-08-31"]["status"] == "fehlwert"  # nie 0
```

```pycon
>>> brent = values["EPCBRENT@2026-09-01"]
>>> brent["wert"], brent["einheit"]["text"], brent["einheit"]["herkunft"], brent["zeitbezug"]
('71.25', 'USD/Barrel', 'quelle', {'art': 'handelstag', 'wert': '2026-09-01'})
```

## API-Überblick

| Quelle | Adapter | Zugang | Einheit | Zeitbezug |
|---|---|---|---|---|
| `price.bundesbank` | `BundesbankSeriesAdapter` | keiner | aus der Reihe (z. B. USD je 1 EUR) | Tag |
| `price.destatis_genesis` | `DestatisTabellenAdapter` | `username` + Geheimnis `token` | je Tabelle (`value_unit`) | Zeitangaben der Tabelle |
| `price.eia_brent` | `EiaSpotPriceAdapter` | Geheimnis `api_key` | aus `units` (USD/Barrel) | Handelstag |
| `price.eu_oil_bulletin` | `PageSnapshotAdapter` | keiner | – (nur Seiten-Snapshot) | Abrufzeitpunkt |
| `price.overpass_fuel_stations` | `OverpassFuelStationAdapter` | keiner | – (Stammdaten, WGS84) | OSM-Datenstand |
| `price.tankerkoenig` | `TankerkoenigListAdapter` | Geheimnis `api_key` | EUR/Liter | Abrufzeitpunkt, **kein** Änderungszeitpunkt |

`RecordingTransport` hält Quellen-Snapshots (Rohantwort, SHA-256, ohne
Geheimnisparameter). Brücken für die bestehende Speicherung:
`legacy_exchange_rate_rows`, `legacy_commodity_rows`, `legacy_station_fields`,
`check_list_response`, `legacy_status`, `error_text`.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_price_sources.__all__` (28):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `CONTRACT_VERSION` | Konstante | – | `(Paketstamm)` |
| `FACTORIES` | Konstante | – | `(Paketstamm)` |
| `MISSING` | Konstante | – | `observation` |
| `OBSERVATION_SCHEMA` | Konstante | – | `observation` |
| `PRESENT` | Konstante | – | `observation` |
| `STATION_SCHEMA` | Konstante | – | `observation` |
| `BundesbankSeriesAdapter` | Klasse | ``price.bundesbank``: one Bundesbank series, last *N* daily observations (one page). | `bundesbank` |
| `DestatisTabellenAdapter` | Klasse | One page per GENESIS table; raw data kept byte-exact. | `destatis` |
| `EiaSpotPriceAdapter` | Klasse | ``price.eia_brent``: EIA v2 daily spot prices of one product with offset paging. | `eia` |
| `OverpassFuelStationAdapter` | Klasse | ``price.overpass_fuel_stations``: all ``amenity=fuel`` nodes/ways of one ISO area. | `overpass` |
| `PageSnapshotAdapter` | Klasse | ``price.eu_oil_bulletin``: snapshot of the publication page (no price extraction). | `pages` |
| `RecordingTransport` | Datenklasse | Wraps a transport and records bounded snapshots of all responses. | `snapshots` |
| `SourceSnapshot` | Datenklasse | One response as received: request identity without secrets, status, bytes, digest. | `snapshots` |
| `TankerkoenigListAdapter` | Klasse | ``price.tankerkoenig``: stations and current prices around one point (one page). | `tankerkoenig` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `canonical_json_bytes` | Funktion | ``json.dumps(payload, sort_keys=True)`` of a JSON body (regulierung's package bytes). | `snapshots` |
| `check_list_response` | Funktion | Health semantics of the original: HTTP 200 and ``ok: true``, else the reason. | `tankerkoenig` |
| `error_text` | Funktion | Error and issue messages of the run, joined and bounded; ``None`` if there were none. | `runs` |
| `exact` | Funktion | Exact decimal from a JSON number or plain text; ``None``/``""``/``False`` → ``None``. | `observation` |
| `fuel_query` | Funktion | Overpass-QL of the original (for ``DE-HE`` byte-identical to regulierung). | `overpass` |
| `legacy_commodity_rows` | Funktion | Rows as regulierung's ``Rohstoffpreis`` (present values only, legacy constants). | `eia` |
| `legacy_exchange_rate_rows` | Funktion | Rows as regulierung's ``Wechselkurs`` (only present values; missing ones are skipped). | `bundesbank` |
| `legacy_station_fields` | Funktion | Row values exactly as regulierung stored a new ``Tankstelle`` (``None`` = skipped). | `overpass` |
| `legacy_status` | Funktion | ``erfolg`` (complete), ``teilweise`` (partial) or ``fehler`` (failed/cancelled). | `runs` |
| `package_sha256` | Funktion | Digest of a response as regulierung logs it (canonical JSON or raw bytes). | `snapshots` |
| `parse_ffcsv` | Funktion | Parse GENESIS ffcsv (semicolon separated, German decimal comma, BOM tolerated). | `destatis` |
| `parse_sdmx_json` | Funktion | Parse an SDMX-JSON data message; structural problems raise ``ParserError``. | `bundesbank` |
| `register` | Funktion | Register all adapters of this package explicitly. | `(Paketstamm)` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_price_sources.bundesbank` | Deutsche Bundesbank time series (SDMX-JSON), e.g. the ECB reference rate USD per EUR. |
| `auditcore_price_sources.destatis` | Destatis GENESIS-Online table files (ffcsv), default: fuel price tables. |
| `auditcore_price_sources.eia` | U.S. EIA API v2 spot prices (default: Brent, product ``EPCBRENT``, daily). |
| `auditcore_price_sources.observation` | Normalized record shapes with explicit unit, time reference and value status. |
| `auditcore_price_sources.overpass` | Overpass API (OpenStreetMap): fuel stations of one area as master data. |
| `auditcore_price_sources.pages` | Publication pages as source snapshots (default: EU Weekly Oil Bulletin). |
| `auditcore_price_sources.runs` | Bridge from a harvest run to regulierung's run protocol (``erfolg``/``teilweise``/``fehler``). |
| `auditcore_price_sources.snapshots` | Source snapshots: a transport decorator that keeps every response body with its hash. |
| `auditcore_price_sources.tankerkoenig` | Tankerkönig ``list.php`` (consumer information service under § 6 MTSKraftV). |
<!-- api-overview:end -->

## Profile und Konfiguration

Jeder Adapter liest seine Konfiguration aus dem Harvest-Aufruf (`config`):
Basis-URL (`url`), bei Destatis `username`, bei EIA etwa `page_size` und
`window_days`, bei Tankerkönig `lat`, `lng`, `rad`. Geheimnisse (`api_key`,
`token`) liefert ausschließlich der Credential-Provider. Das Destatis-Paging-
Profil 2026.09.1 und die Adapterversionen stehen im Quellenkatalog
`src/auditcore_price_sources/catalog.json` mit Herkunft, Consumer,
Konfiguration, Einheit, Zeitbezug, Datenrechten und Live-Prüfstatus.
Empfohlene Consumer-Konfiguration: 2 Versuche, `Retry-After` höchstens 30 s.

## Herkunft und Charakterisierung

Aus den ausgeführten Connectoren von `janpow77/regulierung@853676d`
(`backend/app/services/external_apis/`, Blobs in `provenance.json`).
`tools/capture_regulierung_connectors.py` hat 30 Szenarien mit synthetischen
Antworten aufgezeichnet (`tests/fixtures/regulierung_connectors_observed.json`).
Der Destatis-Adapter wurde aus regulierung verschoben (lief dort bereits auf
`auditcore_harvest`); die übrigen Adapter sind **Neuimplementierungen** der
charakterisierten Anfrage- und Parserverträge. Anfragen (Pfade, Parameter,
Overpass-QL bytegleich) sind übernommen; alle Adapter bestehen die
Contract-Suite `auditcore_harvest.testing.assert_adapter`. Umstellung von
regulierung: [docs/consumer-migration.md](docs/consumer-migration.md).

## Bewusste Verhaltensabweichungen

PS-C01 bis PS-C13, unter anderem: fehlende Quellwerte sind Datensätze mit
`wert: null`, `status: fehlwert` statt still übersprungen; unlesbare Einträge,
leere Antworten und Overpass-`remark` machen den Lauf `partial` (Consumer:
`teilweise`); EIA liest alle Seiten und die Einheit aus `units`; begrenzte
Wiederholung über den Kern; Fehlertexte ohne Antwortinhalt. Entschieden am
23.09.2026: PS-H01 `teilweise` bei Hinweisen, PS-H02 Tankerkönig wird nicht
gespeichert. Vollständig: [docs/behavior-changes.md](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11, `auditcore_harvest==0.1.3` und `auditcore_common==0.2.0`
(kanonisches JSON der Paketbytes; APT `python3-auditcore-common`); sonst nur die
Standardbibliothek. Das im Release v0.3.0 veröffentlichte Wheel 0.1.0 verlangt
noch `auditcore_harvest==0.1.0` (siehe CHANGELOG). Keine Abhängigkeit von
HTTP-Clients, Datenbanken oder der Plattform `auditcore`.

## Sicherheit und Datenschutz

- **Netzwerk:** kein eigener Abruf; der Consumer injiziert Transport und
  Credential-Provider, Rate-Limits und Wiederholungen regelt
  `auditcore_harvest`.
- **Geheimnisse:** API-Schlüssel und Token nur aus dem Credential-Provider;
  Snapshots und Replays enthalten keine Geheimnisparameter.
- **Personenbezug:** keiner beabsichtigt; Tankstellen-Stammdaten können
  Betreibernamen enthalten.
- **Zweckbindung Tankerkönig:** Preise sind Hinweise (`zweck: vorpruefung`,
  `beweismittel: false`, § 7 MTSKraftV) und werden nach PS-H02 nicht
  gespeichert.
- **Datenrechte** aller Dienste sind dokumentiert, aber nicht rechtlich geprüft
  (`REVIEW_REQUIRED`, Katalogfeld `licence_access`); Overpass-Daten unter ODbL.
  MTS-K (Push) und die Verbraucher-Informationsdienste haben keinen
  Abrufvertrag und sind nicht enthalten.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) für den Code; Freigabe des Rechteinhabers vom 22.09.2026 für
die nach auditcore extrahierten Bibliotheken (`USER_AUTHORIZED_MIT`), die
Daten der Dienste sind davon nicht erfasst. Quellen, Blobs und Erklärung:
`NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
