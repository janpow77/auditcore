# Changelog

## 0.2.0 – unveröffentlicht

Additive Erweiterungen aus Issue #236 (Umstellung von regulierung auf
`HarvestEngine`). Vertrag bleibt `auditcore_harvest.contract/1`; alle
bisherigen Namen, Parameter und Standardwerte bleiben gültig. Ohne die neuen
Optionen ist das Laufzeitverhalten unverändert.

### Hinzugefügt
- **Vertragsfelder für Status und Fehlerart:** `ErrorKind` (`network`,
  `timeout`, `http_status`, `rate_limited`, `auth`, `parse`, `config`, `sink`,
  `checkpoint`, `cancelled`, `limit`, `unknown`). Jeder `HarvestError` trägt
  `kind` und `http_status` (Schlüsselwortparameter, Standard je Klasse bzw.
  `None`); `raise_for_status` setzt beide. `HarvestResult` hat die optionalen
  Felder `http_status` und `error_kind` des Fehlers, der den Lauf beendet hat.
- **Konfigurierbare Statusprüfung:** `StatusPolicy` (`check`, `accept`,
  `rate_limited`, `auth`, `retryable`, `retry_server_errors`) als optionales
  zweites Argument von `raise_for_status`, als `HarvestEngine.status_policy`
  und als `FetchContext.status_policy`; Adapter wenden sie mit
  `context.check(response)` an. Die Referenzadapter nutzen `context.check`.
- **Retry-After kappen:** `RetryPolicy.retry_after_cap` (Standard `None` =
  bisheriges Aufgeben über `max_retry_after`). Mit Wert wird ein zu langes
  `Retry-After` auf die Obergrenze gekürzt und erneut versucht.
- **Binärnutzlast:** `BinaryContent(data, media_type)` und
  `HarvestRecord.content` (auch `FetchContext.record(..., content=...)`).
  Der `content_hash` umfasst dann die SHA-256 der Bytes; Datensätze ohne
  Inhalt behalten Hash und `to_dict()` bytegleich. `to_dict()` nennt den
  Inhalt unter `content` (Base64 in `data_b64`, abschaltbar mit
  `include_content_data=False`); `BinaryContent.from_dict` prüft die Prüfsumme.
- **Cookies über Weiterleitungen:** `SessionTransport(inner, session)` und
  `CookieSession` folgen Weiterleitungen selbst, sammeln `Set-Cookie` aus allen
  Zwischenantworten und senden sie bei allen Folgeabrufen der Sitzung mit
  (303 und POST bei 301/302 werden GET; beim Ursprungswechsel entfallen
  `Authorization`/`Cookie` des Aufrufers; höchstens `max_redirects`).
  `Response` hat dafür `raw_headers` (wiederholte Kopfzeilen), `history`
  (Zwischenantworten) und `header_values()`.
- Beispiel `docs/examples/urllib_transport.py`: `follow_redirects=False`,
  `raw_headers`, Zeitüberschreitung als `ErrorKind.TIMEOUT`.
- **Async und Abbruch:** Modul `auditcore_harvest.aio` mit
  `AsyncHarvestEngine`, `AsyncSourceAdapter`, `AsyncFetchContext`
  (`await context.fetch(...)`), `AsyncTransport`, `AsyncSleeper`/
  `AsyncioSleeper` und `AsyncSessionTransport`. `CancelToken.cancel()` (auch
  aus einem anderen Thread) bricht eine laufende Anfrage sofort ab
  (`cancelled`); das Ablaufen von `max_duration_seconds` bricht Anfrage oder
  Wartezeit ab (`partial`, `limit_reached`); ein `task.cancel()` des
  Aufrufers bricht ab und reicht `CancelledError` weiter. Das Modul wird nicht
  aus `auditcore_harvest` importiert, damit `import auditcore_harvest` kein
  `asyncio`/`socket` lädt. `CancelToken.on_cancel()` registriert Rückrufe.
- **Mehrstufige Abläufe und Crawls:** Modul `auditcore_harvest.crawl` mit
  `CrawlTask`, Stufen-Port `Stage`/`AsyncStage`, `StageResult`, `Frontier`
  (Kandidatenliste als Cursor `auditcore_harvest.crawl/1`, dedupliziert),
  `CrawlLimits` (verworfene Kandidaten als `RecordIssue`) sowie
  `CrawlAdapter`/`AsyncCrawlAdapter`.
- **Contract-Suite:** `check_adapter`/`assert_adapter(...,
  malformed=MalformedExpectation.RAW_DOCUMENT)` prüft Rohdokument-Adapter
  darauf, dass die Bytes unverändert übernommen werden;
  `NOT_APPLICABLE` meldet `SKIPPED`. Standard `PARSER_ERROR` unverändert.

### Geändert
- `to_dict()` von Fehlern und `HarvestResult` enthält zusätzlich
  `http_status` und `error_kind` (additiv; bestehende Schlüssel unverändert).
- `ReplayTransport` meldet aufgezeichnete Zeitüberschreitungen mit
  `ErrorKind.TIMEOUT`.
- Intern: der abrufunabhängige Ablauf (Seitenprüfung, Senke, Checkpoint,
  Grenzen, Ereignisse, Laufbuchhaltung) liegt in `auditcore_harvest.flow` und
  wird vom synchronen und asynchronen Engine gemeinsam genutzt; Verhalten des
  `HarvestEngine` unverändert. `RateLimit` hat `pending()`/`mark()`.

### Abhängige Pakete
Neue exakte Pins `auditcore_harvest==0.2.0` mit Patch-Versionen ohne
Verhaltensänderung: `auditcore_funding_sources` 0.1.7, `auditcore_geo` 0.3.3,
`auditcore_legal_sources` 0.1.7, `auditcore_price_sources` 0.1.5,
`auditcore_procurement` 0.2.6, `auditcore_property_sources` 0.1.5,
`auditcore_registry_sources` 0.2.5; weitergereicht `auditcore_bpmn` 0.1.4
(Pin `auditcore_legal_sources==0.1.7`) und `auditcore_risk` 0.4.1
(Pin `auditcore_procurement==0.2.6`).

## 0.1.4 – 2026-10-03

Gemeinsamer Release v0.6.0 mit aktuellem Paketstand, Dokumentation und
exakt gebundenen internen Abhängigkeiten.

## 0.1.3 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_common==0.2.0`.

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.1

Sicherheit: `FeedAdapter` parst RSS/Atom nur noch über `defusedxml`
(`auditcore_common.safe_xml.parse_xml` mit `forbid_dtd=True`) statt über
`xml.etree.ElementTree.fromstring`. Die Vorprüfung auf DOCTYPE/ENTITY bleibt.
Ohne das neue Extra `xml` (`defusedxml>=0.7.1`, Debian: python3-defusedxml)
meldet der Feed-Adapter einen `ConfigError`, es gibt keinen Rückfall auf den
Standardparser. `JsonApiAdapter` braucht das Extra nicht.

- Neue Pflichtabhängigkeit `auditcore_common==0.1.1` (APT
  `python3-auditcore-common`).
- `canonical_hash` rechnet über `auditcore_common.hashing.canonical_sha256`;
  Hashwerte unverändert (Test gegen die bisherige Formel).
- README nach der Vorlage.

## 0.1.1 – 2026-09-25

Refaktorierung ohne Verhaltensänderung; Vertrag `auditcore_harvest.contract/1`
unverändert, alle bisherigen Namen bleiben importierbar.

### Hinzugefügt
- `FetchContext.record(source, record_id, raw, normalized, locator, *, deleted=False)`:
  Datensatz mit Provenienz über den Rohwert in einem Schritt.
- `decode_json(body, message="Antwort ist kein JSON.")`: JSON-Antwortkörper
  lesen, unlesbare Körper als `ParserError` mit quellenspezifischem Text
  (Gegenstück zu `raise_for_status` im Fehlervertrag des Abrufs).
- `page_result(records, issues=(), next_cursor=None, *, total_hint=None)`:
  übliche Seite (abgeschlossen genau ohne Folgecursor, `PARTIAL` bei Issues).
  Die drei Hilfen fassen die in den Quellenpaketen mehrfach kopierten
  Abrufschritte zusammen. Allgemeine Hilfen (JSON-Sicherung, Hashing, XML,
  HTML-Links, Profile) gehören nicht hierher, sondern nach `auditcore_common`.
- `JSON` und `Cursor` (Typaliase des Vertrags) sind aus `auditcore_harvest`
  importierbar.

### Geändert (nur intern bzw. Typen)
- `check_adapter`: die zehn Vertragsfälle sind Methoden einer internen
  Suite-Klasse statt verschachtelter Funktionen (Reihenfolge, Texte und
  Ergebnisse unverändert). `assert_adapter` nennt seine Schlüsselwortparameter
  explizit statt `**kwargs`.
- `HarvestEngine.run`: Seitenschleife nach `_pages` ausgelagert.
- `RetryPolicy`, `RateLimit`, `CancelToken` liegen in `policies`; sie bleiben
  aus `auditcore_harvest` und `auditcore_harvest.engine` importierbar.
- `JsonApiAdapter.fetch_page` und `FeedAdapter.fetch_page` in kleine
  Hilfsfunktionen zerlegt.
- Typen: `SourceAdapter.fetch_page` liefert `PageResult`, `require` den
  geprüften Typ (`type[T] -> T`), `cli._factory` eine Adapterfabrik.
  JSON-Nutzlasten laufen über den dokumentierten Alias `JSON`; `Any` bleibt
  nur dort (Alias) und in `**kwargs` der Testtransporte.

### Messung (Code-Qualitäts-Gate)
| Kennzahl | 0.1.0 | 0.1.1 |
|---|---|---|
| McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 3 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Verwendungen | 45 | 3 |
| mypy --strict | 0 | 0 |

## 0.1.0 – 2026-09-22

Erstausgabe mit Vertrag `auditcore_harvest.contract/1`: `HarvestEngine`,
Ports, Referenzadapter (JSON-API, RSS/Atom), Contract-Suite
`auditcore_harvest.testing`, Adapteranleitung und versionierter
Quellenkatalog (35 belegte Quellen). Characterization der Bestandsharvester
aus auditdatabase, audit_designer und regulierung
(`tests/fixtures/legacy_harvest_observed.json`). Netzwerktransporte
(`UrllibTransport`) sind nicht Teil des Kerns, sondern Beispiel in
`docs/examples/urllib_transport.py`.
