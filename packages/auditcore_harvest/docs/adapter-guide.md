# Adapteranleitung für `auditcore_harvest`

Vertragsversion: **`auditcore_harvest.contract/1`** (`auditcore_harvest.CONTRACT_VERSION`),
Paketversion 0.1.1. Diese Schnittstelle ist stabil. Inkompatible Änderungen
erscheinen nur als eigener Commit `feat(harvest)!: …` und werden unten unter
„Änderungen“ eingetragen; kompatible Ergänzungen behalten Version 1.

Ein Quellenadapter übersetzt genau **eine Seite** einer Quelle in Datensätze.
Seitenfolge, Wiederholungen, Rate-Limit, Zeitgrenzen, Abbruch, Dubletten,
Übergabe an die Senke und Checkpoints übernimmt der gemeinsame
`HarvestEngine`. Adapter schlafen nicht, wiederholen nicht, speichern nicht
und kennen weder Datenbank noch Mandant noch Scheduler.

Das vollständige, ausführbare Beispiel steht in
[`examples/eigener_adapter.py`](examples/eigener_adapter.py) und läuft ohne
Netz gegen eine aufgezeichnete Fixture (`python docs/examples/eigener_adapter.py`).
Die Referenzadapter `JsonApiAdapter` und `FeedAdapter` stehen in
`auditcore_harvest.reference`. XML-Quellen parsen nur über defusedxml
(`auditcore_common.safe_xml.parse_xml`, Extra `xml`), nie über
`xml.etree.ElementTree.fromstring`; `FeedAdapter` zeigt das Muster.

## 1. Quelle deklarieren

```python
Source(
    source_id="familie.quelle",  # stabil, klein, mit Punkt
    title="…",
    family="funding",
    adapter_version="1.0.0",  # Code des Adapters
    profile_version="2026.09.1",  # Quellprofil: Felder, Filter, Regeln
    data_format="application/json",
    auth=AuthKind.API_KEY,  # NONE | API_KEY | BASIC | TOKEN | UNKNOWN
    capabilities=Capabilities(
        pagination=True, incremental=None, full_snapshot=True, deletions=False
    ),
    snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
    filters=("land", "jahr"),
)
```

Unbekannte Fähigkeiten bleiben `None` bzw. `SnapshotSemantics.UNKNOWN`; nichts
wird geraten. `snapshot_semantics` beschreibt, was ein vollständiger Lauf für
den Bestand des Consumers bedeutet:

| Wert | Bedeutung für den Consumer |
|---|---|
| `INCREMENTAL_UPSERT` | Neue/geänderte Datensätze übernehmen; der letzte Cursor ist die Hochwassermarke des nächsten Laufs. |
| `FULL_SNAPSHOT_REPLACE` | Nur bei `result.snapshot_complete is True` darf der Consumer seinen eigenen Ersetzungs-/Löschschritt ausführen. |
| `APPEND_ONLY` | Datensätze werden nur hinzugefügt; kein Löschen. |
| `UNKNOWN` | Kein Löschen, keine Vollständigkeitsaussage. |

Der Kern löscht nie. Quellspezifische Verfahren wie `smart`, `full-refresh`,
`force` oder `snapshot` bleiben eigene, benannte Profile und werden nicht zu
einer gewöhnlichen Parseroption zusammengefasst.

## 2. Konfiguration prüfen und genau eine Seite abrufen

- `validate_config(config)` wirft `ConfigError` und fragt die Quelle nicht an.
  Die Konfiguration enthält **keine Geheimnisse**.
- Zugangsdaten holt der Adapter über `context.secret(source_id, name)` vom
  `CredentialProvider` des Consumers; fehlen sie, entsteht `AuthError`.
- `fetch_page(context, cursor)` nutzt ausschließlich `context.transport` mit
  `timeout=context.timeout` und liefert ein `PageResult`:
  Datensätze, `next_cursor` und `complete`. Eine nicht abgeschlossene Seite
  ohne neuen Cursor, ein Cursor ohne Fortschritt oder Datensätze einer
  anderen Quelle sind Parserfehler und werden nie als Ende gewertet.
- `request.filters`, `request.since` und `request.page_size` sind Wünsche des
  Consumers; der Adapter übernimmt nur Filter, die er deklariert.

## 3. Datensätze mit stabiler ID, Rohwert, Normalisierung und Provenienz

```python
HarvestRecord(
    source_id=...,
    record_id="stabile-quellen-id",
    raw=item,
    normalized={...},
    provenance=context.provenance(self.source, locator, item),
    deleted=False,
)
```

Kürzer und gleichwertig (seit 0.1.1):

```python
record = context.record(self.source, "stabile-quellen-id", item, {...}, locator)
payload = decode_json(response.body, "Antwort ist kein JSON.")  # sonst ParserError
return page_result(records, issues, next_cursor, total_hint=total)
```

`page_result` setzt `complete` genau dann, wenn kein `next_cursor` folgt, und
den Status `PARTIAL`, sobald ein `RecordIssue` vorliegt.

`content_hash` wird aus `normalized` und `deleted` berechnet; unveränderte
Inhalte sind dadurch als Dublette erkennbar. Nicht übersetzbare Einträge
gehören als `RecordIssue` in `PageResult.issues` (Status `PARTIAL`), nicht
stillschweigend weg. Eine unlesbare Antwort ist `ParserError`, **kein leeres
erfolgreiches Ergebnis**; ein wohlgeformter leerer Bestand ist dagegen ein
gültiges leeres `PageResult(complete=True)`.

## 4. Fehler unterscheidbar machen

`raise_for_status(response)` bildet HTTP-Status ab: 429 → `RateLimitError`
mit `retry_after` aus `Retry-After`; 401/403 → `AuthError`; 408/5xx →
`TransportError` (wiederholbar); sonstige Nicht-2xx → `TransportError`
(nicht wiederholbar). Weitere Klassen: `ConfigError`, `ParserError`,
`SinkError`, `CheckpointConflict`, `Cancelled`, `LimitReached`. Jede trägt
`code`, `retryable`, `retry_after` und `detail` (`to_dict()`). Der
`RetryPolicy` wiederholt nur wiederholbare Fehler, begrenzt die Versuche,
nutzt Backoff mit injizierbarer Zufallsquelle und bricht bei einem
`Retry-After` über `max_retry_after` ab. Fachliche, irreversible
Entscheidungen trifft kein allgemeiner Retry-Handler.

## 5. Registrieren, aufrufen, Senke und Checkpoints

Den Netzwerktransport stellt der Consumer bereit (Protokoll `Transport`,
z. B. ein httpx-Client oder das Standardbibliotheks-Beispiel
[`examples/urllib_transport.py`](examples/urllib_transport.py)); der Kern
selbst enthält bewusst keinen Netzwerkclient.

```python
registry = AdapterRegistry()
registry.register("familie.quelle", MeinAdapter)  # explizit, keine Plugin-Magie
engine = HarvestEngine(
    transport,
    credentials,
    state_store,
    clock,
    sleeper,
    retry=RetryPolicy(),
    rate_limit=RateLimit(1.0),
)
result = engine.run(
    registry.create("familie.quelle"),
    HarvestRequest("familie.quelle", run_id="…", max_pages=50),
    sink,
    config=config,
    cancel=cancel_token,
)
```

- **Senke** (`Sink.deliver`) muss jeden übergebenen Datensatz als `accepted`
  oder `duplicate` bestätigen und je `(source_id, record_id, content_hash)`
  idempotent sein. Speicherfehler als Ausnahme melden.
- **Checkpoint** (`StateStore.save(checkpoint, expected)`, Compare-and-Set)
  wird erst **nach** der Bestätigung der Senke fortgeschrieben. Nach einem
  Absturz zwischen Bestätigung und Checkpoint wird die Seite erneut geliefert:
  Zustellung *mindestens einmal*, keine Exactly-once-Zusage.
- **Wiederanlauf**: `HarvestRequest(resume=True)` setzt am letzten bestätigten
  Cursor fort. Ein Checkpoint einer anderen `profile_version` wird nicht
  verwendet (Lauf `failed`, Grund im Ergebnis).
- **Abbruch**: `CancelToken.cancel()` wirkt zwischen Seiten und Versuchen;
  Ergebnis `cancelled`, bestätigte Seiten bleiben bestätigt.
- **Ergebnis** `HarvestResult`: `complete`, `partial`, `failed` oder
  `cancelled` mit Seiten, erhaltenen/übergebenen Datensätzen, Dubletten,
  Hinweisen, strukturierten Fehlern, Checkpoint vorher/nachher,
  `source_exhausted` und `snapshot_complete`. Zähler werden nie aus einer
  leeren Liste abgeleitet.
- **Ereignisse** (`EventSink`) sind begrenzt und enthalten weder Konfiguration
  noch Header noch Zugangsdaten.

## 6. Contract-Tests gegen den eigenen Adapter

```python
from auditcore_harvest.testing import assert_adapter
from auditcore_harvest.transport import ReplayTransport


def test_mein_adapter_erfuellt_den_vertrag():
    assert_adapter(
        MeinAdapter,
        config={...},
        transport_factory=lambda: ReplayTransport.from_file(FIXTURE),
        credentials={("familie.quelle", "api_key"): "fixture"},
        min_records=3,
    )
```

Die Suite führt über den echten Engine aus: Deklaration, Konfiguration,
vollständiger Replay über alle Seiten, Determinismus (gleiche IDs/Hashes),
idempotente Wiederholung, Wiederanlauf nach Senkenfehler ohne Datenverlust,
begrenzte Wiederholung und Wiederanlauf nach Netzwerkfehler, unlesbare
Antwort als `parser_error`, fehlende Zugangsdaten als `auth_error` und
geheimnisfreie Ergebnisse/Ereignisse. Fixtures sind aufgezeichnete
Originalantworten im Format
`{"exchanges": [{"request": {"method", "url", "params"}, "response": {"status", "headers", "body_json"|"body_text"|"body_b64"}}]}`.
Geheimnisparameter (`apikey`, `token`, …) werden beim Abgleich ignoriert und
gehören nie in eine Fixture.

## Quellenkatalog

`auditcore_harvest.catalog` validiert den versionierten Katalog
(`auditcore_harvest.catalog/1`, Datei `catalogs/sources.json`). Pro Quelle:
Herkunft (Repository, Commit, Pfad, Symbole), Consumer, Zielpaket, Profil,
Authentifizierung, Lizenz-/Zugangsprüfung, Konfigurationsschema ohne
Geheimnisse, Fixtures, Implementierungsstatus (`SUPPORTED`, `PLANNED`,
`LEGACY_ONLY`) und tatsächlicher Live-Test (`PASS`, `FAIL`, `NOT_EXECUTED`,
`NOT_CONFIGURED`). `auditcore-harvest catalog` prüft und fasst zusammen.

## Änderungen

- 0.1.0 / Vertrag 1: Erstfassung (Commit 0ff8d99).
- 0.1.1 / Vertrag 1 (kompatibel): Hilfen `FetchContext.record`,
  `decode_json` und `page_result` für die wiederkehrenden Schritte der
  Quellenpakete; `SourceAdapter.fetch_page` ist als `-> PageResult` typisiert,
  `require` gibt den geprüften Typ zurück. Laufzeitverhalten unverändert.
- **Inkompatibel seit c5a5e45:** `auditcore_harvest.UrllibTransport` und
  `auditcore_harvest.transport.UrllibTransport` entfallen, weil ein
  Netzwerkclient im Kern gegen AC-ARCH-002 verstößt. Adapter sind nicht
  betroffen (sie nutzen nur `context.transport`). Consumer injizieren ihren
  Transport; Standardbibliotheks-Vorlage: `docs/examples/urllib_transport.py`.
  Alle übrigen Namen und Semantiken von Vertrag 1 bleiben unverändert.
