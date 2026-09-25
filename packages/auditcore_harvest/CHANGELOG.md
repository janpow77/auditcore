# Changelog

## 0.1.1 – 2026-09-25

Refaktorierung ohne Verhaltensänderung; Vertrag `auditcore_harvest.contract/1`
unverändert, alle bisherigen Namen bleiben importierbar.

### Hinzugefügt
- `FetchContext.record(source, record_id, raw, normalized, locator, *, deleted=False)`:
  Datensatz mit Provenienz über den Rohwert in einem Schritt.
- `decode_json(body, message="Antwort ist kein JSON.")`: JSON-Antwortkörper
  lesen, unlesbare Körper als `ParserError` mit quellenspezifischem Text.
- `page_result(records, issues=(), next_cursor=None, *, total_hint=None)`:
  übliche Seite (abgeschlossen genau ohne Folgecursor, `PARTIAL` bei Issues).
  Die drei Hilfen fassen die in den Quellenpaketen mehrfach kopierten
  Schritte zusammen.
- `deprecated_aliases(module, {alt: (neu, objekt)})`: Modul-`__getattr__` für
  umbenannte öffentliche Namen mit `DeprecationWarning` (für Quellenpakete, deren
  Architekturtests nur `auditcore_harvest` und ausgewählte Standardmodule zulassen).
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
