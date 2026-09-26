# Changelog – auditcore_legal_sources

## 0.1.5 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_common==0.2.0`, `auditcore_harvest==0.1.3`.

## 0.1.4 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pflichtabhängigkeiten `auditcore_common==0.1.1` und `auditcore_harvest==0.1.2`; README-Installationshinweis auf v0.4.0.

## 0.1.3 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung. Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`).

- `fingerprint` → `hashing.canonical_sha256`; `available_profiles`/
  `load_profile` → `auditcore_common.profiles` (`invalid_name="invalid_or_hidden"`,
  ohne Typprüfung wie bisher).
- Linksammler der ECA-Seite → `html_text.anchor_links`; HTML-Erkennung →
  `has_html_marker(text, ("<a", "<html"), window=None)`.
- Meldungen und Ergebnisse unverändert.

## 0.1.2 – Harvest-Hilfen, Typen

Refaktorierung ohne Verhaltensänderung; benötigt `auditcore_harvest==0.1.1`.

- Die Adapter nutzen die gemeinsamen Hilfen von `auditcore_harvest` 0.1.1:
  `decode_json` (gleiche Fehlertexte „DIP: …“/„EUR-Lex: …“), `page_result`
  und `FetchContext.record`. Die eigenen Kopien `_json` und `_page` in
  `_adapter_support` entfallen (privat), `_record` ist ein Einzeiler.
- Roh-JSON-Grenzen (Profile, DIP-Items, Feedeinträge, Legacy-Eingaben und
  -Ausgaben) sind mit dem Vertragsalias `auditcore_harvest.JSON` statt
  `typing.Any` annotiert (typgleich); `legacy_parse_date` nimmt `object`.
  Cursor als `auditcore_harvest.Cursor`.
- Messung (Code-Qualitäts-Gate): `Any` 50 → 0 (JSON-Alias), McCabe > 10 0,
  Funktionen > 60 Zeilen 0, Module > 400 Zeilen 0, mypy --strict sauber.
  Verbleibend: `legacy.designer_dip_vorgang` (Spiegel von
  `_parse_vorgang`, DIP-Ressource „vorgang“) als fachlicher Name belassen.

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

- `legacy` ist ein Unterpaket nach Quelle: `legacy.common` (Datumsparser,
  Erkennungsregeln, Dokumentform), `legacy.dip`, `legacy.eurlex`,
  `legacy.feeds`. Alle bisherigen Namen bleiben unter
  `auditcore_legal_sources.legacy` importierbar.
- `legacy_dip_normalize` in kurze Hilfsfunktionen zerlegt (PDF-URL,
  Förderperiode, Fonds); die Ausnahmebehandlung der Quelle bleibt gleich.
- `funding_period_designer` liest seine Regeln aus deklarativen Tabellen
  in unveränderter Reihenfolge.
- Gemeinsame Adapterhilfen (Profilwahl, JSON, Datensätze, Seiten) liegen in
  `_adapter_support`; `adapters` enthält nur noch die Adapterklassen.
- Typen: Konfigurationen als `Mapping[str, object]`, Antwortkörper als
  `object` mit Strukturprüfung; `Any` bleibt nur an Roh-JSON-Grenzen.
- Keine Umbenennung öffentlicher Namen, keine Aliase nötig.

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 1 | 0 |
| Module > 400 Zeilen | 2 | 0 |
| `Any`-Vorkommen | 69 | 59 |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 244 / 96,7 % | 254 / 96,9 % |
