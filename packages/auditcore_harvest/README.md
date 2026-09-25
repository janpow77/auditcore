# auditcore_harvest

## Zweck

Gemeinsamer, frameworkunabhängiger Kern für Datenharvester: Quellenvertrag, Abruf mit Pagination, Zeitgrenzen, Rate-Limits und begrenzten Wiederholungen, Dubletten, idempotente Übergabe an eine Senke und Checkpoints.

Für die Quellenpakete (`auditcore_funding_sources`, `auditcore_legal_sources`,
`auditcore_price_sources`, `auditcore_registry_sources`, `auditcore_geo[geocoder]` …),
die ihre Adapter auf diesem Vertrag implementieren, und für Anwendungen, die
diese Adapter ausführen. Der Kern installiert keine Quellenadapter; Scheduler,
Datenbank, Mandanten, Anwendungsrechte und Zugangsdatenverwaltung bleiben beim
Consumer.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_harvest \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.0 im
Release v0.3.2; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-harvest/`):

```text
auditcore_harvest @ https://github.com/janpow77/auditcore/releases/download/v0.3.2/auditcore_harvest-0.1.0-py3-none-any.whl#sha256=bc6cf59f65826171d81666a28331a609395e2f3cba8ba47f9321d454b378d880
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-harvest
```

Extras: nur `[dev]` (Test- und Prüfwerkzeuge). Die Kommandozeile
`auditcore-harvest catalog` prüft den Quellenkatalog, `auditcore-harvest replay`
führt einen Adapter gegen aufgezeichnete Fixtures aus.

## Schnellstart

Ein Lauf des Referenzadapters `JsonApiAdapter` über zwei Seiten, beantwortet
von einem `ReplayTransport` statt aus dem Netz:

```python
from auditcore_harvest import (
    AuthKind, Capabilities, HarvestEngine, HarvestRequest, ReplayTransport,
    SnapshotSemantics, Source,
)
from auditcore_harvest.memory import (
    ClockSleeper, FixedClock, ListSink, MemoryStateStore, StaticCredentials,
)
from auditcore_harvest.reference import JsonApiAdapter

URL = "https://api.example.invalid/v1/items"
transport = ReplayTransport((
    {"request": {"url": URL, "params": {"size": "2"}},
     "response": {"status": 200,
                  "body_json": {"items": [{"id": "E1"}, {"id": "E2"}], "next": "t2"}}},
    {"request": {"url": URL, "params": {"size": "2", "cursor": "t2"}},
     "response": {"status": 200, "body_json": {"items": [{"id": "E3"}], "next": None}}},
))
adapter = JsonApiAdapter(Source(
    source_id="beispiel.register", title="Beispielregister (synthetisch)",
    family="beispiel", adapter_version="1.0.0", profile_version="2026.09.1",
    data_format="application/json", auth=AuthKind.NONE,
    capabilities=Capabilities(
        pagination=True, incremental=False, full_snapshot=True, deletions=False
    ),
    snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
))
clock = FixedClock()
engine = HarvestEngine(
    transport=transport, credentials=StaticCredentials({}), state=MemoryStateStore(),
    clock=clock, sleeper=ClockSleeper(clock),
)
sink = ListSink()
result = engine.run(
    adapter, HarvestRequest("beispiel.register", run_id="lauf-1"), sink,
    config={"url": URL, "page_size": 2},
)
assert result.pages == 2 and result.records_delivered == 3
```

```pycon
>>> result.status.value, result.snapshot_complete
('complete', True)
>>> sorted(record_id for _, record_id in sink.records)
['E1', 'E2', 'E3']
```

Eigener Adapter Schritt für Schritt: [docs/adapter-guide.md](docs/adapter-guide.md),
ausführbar in `docs/examples/eigener_adapter.py`.

## API-Überblick

- Vertrag `auditcore_harvest.contract/1`: `Source`, `HarvestRequest`,
  `HarvestRecord`, `PageResult`, `Checkpoint`, `HarvestResult`, strukturierte
  Fehler (`auth`, `config`, `rate_limited`, `transport`, `parser`, `sink`, …).
- Ports: `Transport`, `CredentialProvider`, `StateStore`, `Sink`, `Clock`,
  `Sleeper`, `EventSink`. Mitgelieferte Transporte: `FileTransport`,
  `ReplayTransport`; Netzwerktransporte injiziert der Consumer (Beispiel ohne
  Zusatzpakete: `docs/examples/urllib_transport.py`).
- `auditcore_harvest.testing`: wiederverwendbare Contract-Suite für Adapter
  (`check_adapter`, `assert_adapter`).
- `auditcore_harvest.reference`: ausführbare Referenzadapter (JSON-API,
  RSS/Atom).

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_harvest.__all__` (50):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `CONTRACT_VERSION` | Konstante | – | `model` |
| `JSON` | Konstante | JSON payload at the source boundary. This is the one deliberate ``Any`` of the contract: raw source documents are only known to be JSON-compatible, and adapters narrow them with `` … | `model` |
| `AdapterRegistry` | Klasse | Explicit registration; no import-time discovery or plugin magic. | `adapter` |
| `AuthError` | Ausnahme | Credentials missing, rejected or expired (never retried automatically). | `errors` |
| `AuthKind` | Aufzählung | Credential need of a source; secrets come from the credential provider. | `model` |
| `Cancelled` | Ausnahme | The run was cancelled cooperatively between pages. | `errors` |
| `CancelToken` | Datenklasse | Cooperative cancellation checked between pages and attempts. | `policies` |
| `Capabilities` | Datenklasse | Declared adapter capabilities; ``None`` means explicitly unknown. | `model` |
| `Checkpoint` | Datenklasse | Confirmed progress of a source; advanced only after the sink confirmed. | `model` |
| `CheckpointConflict` | Ausnahme | The stored checkpoint changed concurrently (compare-and-set failed). | `errors` |
| `Clock` | Protokoll | Time source for timestamps, deadlines and rate limiting. | `ports` |
| `ConfigError` | Ausnahme | Invalid or missing adapter configuration (never retried). | `errors` |
| `CredentialProvider` | Protokoll | Supplies secrets by source and name; the core never stores or logs them. | `ports` |
| `Cursor` | Typalias | – | `model` |
| `EventSink` | Protokoll | Receives bounded, secret-free run events. | `ports` |
| `FetchContext` | Datenklasse | Everything an adapter may use for one page. | `adapter` |
| `FileTransport` | Klasse | Reads ``file:`` locators confined to one root directory. | `transport` |
| `HarvestEngine` | Datenklasse | Runs any :class:`SourceAdapter` through the common flow. | `engine` |
| `HarvestError` | Ausnahme | Base error with a stable machine-readable ``code``. | `errors` |
| `HarvestRecord` | Datenklasse | One source record: stable id, raw and normalized payload, provenance. | `model` |
| `HarvestRequest` | Datenklasse | What the consumer asks for; limits bound every run. | `model` |
| `HarvestResult` | Datenklasse | Structured run result; counts are never inferred from an empty list. | `model` |
| `LimitReached` | Ausnahme | A configured run limit (pages, records, duration) stopped the run. | `errors` |
| `PageResult` | Datenklasse | One bounded page: records, next cursor and an explicit completion flag. | `model` |
| `PageStatus` | Aufzählung | Result of one page fetch as seen by the adapter. | `model` |
| `ParserError` | Ausnahme | The response could not be interpreted; never presented as an empty result. | `errors` |
| `Provenance` | Datenklasse | Origin of one record. | `model` |
| `RateLimit` | Datenklasse | Minimum interval between two requests of a run. | `policies` |
| `RateLimitError` | Ausnahme | Source signalled rate limiting; ``retry_after`` in seconds if known. | `errors` |
| `RecordIssue` | Datenklasse | A single source item that could not be parsed; never dropped silently. | `model` |
| `ReplayTransport` | Datenklasse | Serves recorded responses; unmatched requests are errors, not empty data. | `transport` |
| `Response` | Datenklasse | Transport-neutral response. | `ports` |
| `RetryPolicy` | Datenklasse | Bounded exponential backoff with jitter; honours ``Retry-After`` up to a cap. | `policies` |
| `RunStatus` | Aufzählung | Overall outcome of a run. | `model` |
| `Sink` | Protokoll | Receives records; must be idempotent per ``(source_id, record_id, content_hash)``. | `ports` |
| `SinkError` | Ausnahme | The sink did not confirm the batch; the checkpoint is not advanced. | `errors` |
| `SinkReceipt` | Datenklasse | What the sink confirmed; unknown keys in the receipt are a sink error. | `model` |
| `Sleeper` | Protokoll | Waiting is injectable so tests and schedulers stay deterministic. | `ports` |
| `SnapshotSemantics` | Aufzählung | What a complete run means for the consumer's stored inventory. | `model` |
| `Source` | Datenklasse | Identity and declared behavior of one source profile. | `model` |
| `SourceAdapter` | Protokoll | Contract every source adapter implements (contract version 1). | `adapter` |
| `StateStore` | Protokoll | Persists checkpoints with compare-and-set semantics. | `ports` |
| `Transport` | Protokoll | Performs exactly one request; retries and paging belong to the engine. | `ports` |
| `TransportError` | Ausnahme | Network, timeout or server error; retryable unless stated otherwise. | `errors` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `canonical_hash` | Funktion | SHA-256 over canonical JSON; the stable content hash of a record. | `model` |
| `decode_json` | Funktion | Parse a JSON response body; undecodable bodies are a :class:`ParserError`. | `transport` |
| `page_result` | Funktion | The usual page of an adapter: complete exactly when there is no next cursor. | `model` |
| `raise_for_status` | Funktion | Map HTTP status codes to structured errors; 2xx is returned unchanged. | `transport` |
| `require` | Funktion | Small helper for ``validate_config``: required key of a given type. | `adapter` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_harvest.adapter` | Adapter interface: one source profile, one bounded page per call. |
| `auditcore_harvest.catalog` | Versioned source catalogue (``auditcore_harvest.catalog/1``). |
| `auditcore_harvest.catalogs` | – |
| `auditcore_harvest.cli` | ``auditcore-harvest``: validate the source catalogue and replay adapters on fixtures. |
| `auditcore_harvest.engine` | The harvest flow shared by all adapters. |
| `auditcore_harvest.errors` | Structured harvest errors; the engine decides retries from ``retryable``/``retry_after``. |
| `auditcore_harvest.memory` | Reference implementations of the ports for tests, replays and simple consumers. |
| `auditcore_harvest.model` | Versioned data contracts of the harvest core (``auditcore_harvest.contract/1``). |
| `auditcore_harvest.policies` | Run policies of the engine: bounded retry, request pacing and cooperative cancellation. |
| `auditcore_harvest.ports` | Ports the consumer (or a test) provides: transport, credentials, state, sink, time, events. |
| `auditcore_harvest.reference` | Executable reference adapters used by the adapter guide and the contract tests. |
| `auditcore_harvest.testing` | Reusable adapter contract suite (contract version 1). |
| `auditcore_harvest.transport` | Transports shipped with the core: confined local files and fixture replay. |
<!-- api-overview:end -->

## Profile und Konfiguration

`HarvestEngine` nimmt `retry` (`RetryPolicy`: `max_attempts=3`,
`base_delay=1.0`, `max_delay=60.0`, `jitter=0.1`, `max_retry_after=300.0`),
`rate_limit` (`RateLimit`, `min_interval_seconds=0.0`), `request_timeout=30.0`
Sekunden, eine `EventSink` und einen seeded Zufallsgenerator entgegen.
Adapter deklarieren `adapter_version`, `profile_version`, Filter,
Authentifizierung und Fähigkeiten in `Source`; die Konfiguration je Lauf prüft
`validate_config`, ohne die Quelle anzufragen. Geheimnisse liefert nur der
`CredentialProvider`.

Der versionierte Quellenkatalog (`auditcore_harvest.catalog/1`,
`catalogs/sources.json`) nennt belegte Quellen mit Herkunft, Zielpaket,
Implementierungsstatus (`SUPPORTED`, `PLANNED`, `LEGACY_ONLY`) und
tatsächlichem Live-Test; ein Eintrag bedeutet weder „implementiert“ noch
„live getestet“.

## Herkunft und Charakterisierung

Neuimplementierung gegen charakterisierte Verträge. Das Bestandsverhalten der
Harvester aus `janpow77/auditdatabase` (`bba911e9`), `janpow77/audit_designer`
(`030a71e0`) und `janpow77/regulierung` (`a5d48ea4`) wurde mit
`tools/capture_legacy_harvest.py` tatsächlich ausgeführt (46 Fälle,
14 Szenarien, Netz nur über `httpx.MockTransport`; Fixture
`tests/fixtures/legacy_harvest_observed.json`). Gleiche Namen im Bestand
(`HarvestResult`, `BaseHarvester`) haben nachweislich unterschiedliche
Semantik; der Kern übernimmt daher kein Verhalten wörtlich, sondern legt
einen gemeinsamen Vertrag fest.

## Bewusste Verhaltensabweichungen

Gegenüber dem Bestand (Details HC-01 bis HC-10 in
[docs/behavior-changes.md](docs/behavior-changes.md)): HTTP 429 und 5xx sind
strukturierte Fehler statt `success=True` mit leerem Ergebnis; Seitenfolge mit
Cursor statt Abschneiden auf `limit`; Wiederholung mit Backoff und
`Retry-After`-Obergrenze; 404/Timeout ergeben Fehler statt leeren Inhalts;
Checkpoint erst nach Bestätigung der Senke (Zustellung *mindestens einmal*,
keine Exactly-once-Zusage). Der Kern löscht nie; `snapshot_complete` sagt,
wann ein Consumer seine eigene Ersetzungsregel anwenden darf. Offen
(menschliche Entscheidung): vollständige Pagination bei Quellen mit harter
Ergebnisbegrenzung wie der DIP-Schlagwortsuche.

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Die Plattform
`auditcore` ist keine Abhängigkeit; HTTP-Clients (`httpx`, `requests`) bringt
der Consumer über seinen `Transport` mit. Der Kern ist synchron; asynchrone
Consumer rufen ihn über `asyncio.to_thread` auf.

## Sicherheit und Datenschutz

Netzwerkzugriffe erfolgen nur über den injizierten `Transport`. Geheimnisse
kommen aus dem `CredentialProvider`, erscheinen nicht in Datensätzen,
Lokatoren oder Ereignissen, und `ReplayTransport` zeichnet Schlüsselparameter
(`apikey`, `token`, `password` …) nicht auf. Der Feed-Referenzadapter nimmt
keine DTDs an. Welche personenbezogenen Daten eine Quelle liefert und wie
lange sie gespeichert werden, entscheidet der Consumer; die Datenrechte der
Dienste sind von der Paketlizenz nicht erfasst.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliothek (`USER_AUTHORIZED_MIT`); die Quellrepositories und die Datenrechte
der Dienste sind davon nicht erfasst. Quellen mit Git-Blobs:
`provenance.json`; Zuschreibung: `NOTICE`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
