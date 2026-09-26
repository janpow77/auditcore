# auditcore_legal_sources

## Zweck

Quellenadapter für Rechts-, Parlaments- und Prüfquellen – Bundestag DIP, EUR-Lex/Cellar, BaFin, CURIA und Europäischer Rechnungshof – mit strikter Antwortprüfung und Normalisierung zu `LegalDocument`.

Für Wissens- und Rechercheanwendungen (auditdatabase, audit_designer VP-AI),
die Drucksachen, Rechtsakte und Prüfberichte mit stabiler Identität,
Contenthash, geparstem Publikationsdatum und Provenienz aufnehmen. Abruf,
Seitenfolge, Wiederholungen, Rate-Limits und Checkpoints übernimmt
`auditcore_harvest`; Scheduler, Datenbank und Rechte bleiben beim Consumer.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_legal_sources \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.3 im
Release v0.4.0; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-legal-sources/`):

```text
auditcore_legal_sources @ https://github.com/janpow77/auditcore/releases/download/v0.4.0/auditcore_legal_sources-0.1.3-py3-none-any.whl#sha256=87419f5ddc0a4b93b3865f1db851ccf6680043ea5b54674a4f380c4a6b861e0d
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-legal-sources
```

Extras: `[feeds]` – feedparser für die RSS-/Atom-Quellen BaFin und CURIA;
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Eine DIP-Antwortseite prüfen und normalisieren (ohne Netzwerk):

```python
from datetime import date

from auditcore_legal_sources import load_profile
from auditcore_legal_sources import dip

profile = load_profile("auditdatabase.esi", "2026.09.1")
params = dip.drucksache_query(profile, "EFRE")  # enthält keinen API-Schlüssel
assert params == {"format": "json", "num": "30", "f.titel": "EFRE"}

payload = {
    "numFound": 2,
    "cursor": "AoE1",
    "documents": [
        {"id": 290001, "titel": "Umsetzung des EFRE in der Förderperiode 2021-2027",
         "dokumentnummer": "20/1234", "datum": "2026-03-05", "drucksachetyp": "Antwort"},
        {"id": 290002, "titel": ""},
    ],
}
documents, errors = dip.normalize_page(dip.parse_page(payload), profile)
document = documents[0]
assert document.publication_date == date(2026, 3, 5)
assert document.classification["heuristic"] is True
```

```pycon
>>> document.identity
'dip_bundestag:dip_290001'
>>> document.document_url
'https://dserver.bundestag.de/btd/20/012/2001234.pdf'
>>> [(error.location, str(error)) for error in errors]
[('documents[1].titel', 'DIP-Drucksache 290002 ohne Titel.')]
```

## API-Überblick

| Modul | Inhalt |
|---|---|
| `dip` | Bundestag DIP: Anfrageparameter, `Authorization: ApiKey`-Header, Seitenprüfung mit Cursor, Normalisierung von Drucksachen |
| `eurlex` | EUR-Lex/Cellar: SPARQL-Formular, Aktualisierungsabfrage aus Profilvorlage, Prüfung des W3C-JSON-Ergebnisformats, CELEX-Dokumenttyp, Kerndokumente |
| `feeds` | BaFin/CURIA (RSS/Atom, Extra `feeds`) und ECA-Publikationslinks aus HTML; stabile SHA-256-Identitäten |
| `normalize` | Publikationsdatum mit Genauigkeit, Förderperiode (Regeln `auditdatabase`/`designer`), Fonds, Relevanz, Dubletten |
| `adapters` | `auditcore_harvest`-Adapter `legal.dip_bundestag`, `legal.eurlex`, `legal.bafin`, `legal.curia`, `legal.eca` |
| `legacy` | verhaltensgleiche Wiedergabe beider Quellanwendungen (Unterpakete `common`, `dip`, `eurlex`, `feeds`) |

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_legal_sources.__all__` (9):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `ConfigurationError` | Ausnahme | Configuration or credentials are missing or invalid (maps to NOT_CONFIGURED). | `errors` |
| `LegalDocument` | Datenklasse | A parliamentary, legal or audit publication in normalized form. | `model` |
| `LegalSourceError` | Ausnahme | Base class of all errors raised by this package. | `errors` |
| `ParseError` | Ausnahme | A source response does not have the documented structure; never an empty success. | `errors` |
| `ProfileError` | Ausnahme | A source profile is missing, malformed or does not match its fingerprint. | `errors` |
| `SourceProfile` | Datenklasse | Immutable, explicitly selected source profile. | `profile` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `available_profiles` | Funktion | Packaged ``(id, version)`` pairs; there is no implicit default profile. | `profile` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `profile` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_legal_sources.adapters` | Source adapters for ``auditcore_harvest`` (contract version 1). |
| `auditcore_legal_sources.dip` | Bundestag DIP (Dokumentations- und Informationssystem) request and response contract. |
| `auditcore_legal_sources.errors` | Error contract; ``code`` is stable and distinguishes the error classes of the adapter guide. |
| `auditcore_legal_sources.eurlex` | EUR-Lex/Cellar SPARQL request and result contract. |
| `auditcore_legal_sources.feeds` | RSS/Atom feed entries and publication pages (BaFin, CURIA, ECA). |
| `auditcore_legal_sources.legacy` | Behavior-compatible adapters of the two characterized source applications. |
| `auditcore_legal_sources.model` | Normalized legal/audit source document with provenance. |
| `auditcore_legal_sources.normalize` | Normalization helpers: publication dates, classification rules, deduplication. |
| `auditcore_legal_sources.profile` | Versioned, source-bound profiles: keywords, endpoints, queries and core documents. |
| `auditcore_legal_sources.profiles` | – |
<!-- api-overview:end -->

## Profile und Konfiguration

`available_profiles()` liefert `auditdatabase.esi` und `audit_designer.vp_ai`
(je 2026.09.1). Beide sind aus den ausgeführten Quellanwendungen aufgezeichnet
und bewusst getrennt: unterschiedliche DIP-Suchbegriffe (27 bzw. 10),
DIP-Klassifikation nur bei auditdatabase (als `heuristic: true` markiert),
eigene EUR-Lex-Abfragen und Kerndokumente, eigene Förderperiodenregeln. Ein
Profil wird mit `load_profile(id, version)` ausdrücklich gewählt; jedes
`LegalDocument` trägt die Profilreferenz.

Zugangsdaten: der DIP-API-Schlüssel kommt ausschließlich aus dem
Credential-Provider des Consumers; ohne Schlüssel ist die Quelle
`NOT_CONFIGURED`. Inkrementelle DIP-Abrufe über `updated_since`
(`f.aktualisiert.start`) und den Cursor.

## Herkunft und Charakterisierung

Extrahiert aus `janpow77/auditdatabase@bba911e` (Harvester `base`, `dip`,
`eurlex`, `rss`) und `janpow77/audit_designer@030a71e` (VP-AI-Harvester;
Blobs in `provenance.json`). `tools/capture_legacy_harvesters.py` hat 176 Fälle
ohne Netzwerk aufgezeichnet (httpx ersetzt, SPARQL gestubbt;
`tests/fixtures/legacy_harvesters_observed.json`), die Feedquellen zusätzlich
in `tests/fixtures/legacy_feeds_observed.json`. `legacy` reproduziert beide
Anwendungen exakt; der neue Vertrag weicht nur in den dokumentierten Punkten
ab. Nicht übernommen: fest kodierter DIP-Schlüssel, Laden der Suchbegriffe aus
der Datenbank, defekte `get_vorgang`/`test_connection`, HTML-Volltextabruf.

## Bewusste Verhaltensabweichungen

Korrigiert (LS-C01 bis LS-C15), unter anderem: Publikationsdaten werden
tatsächlich geparst (im Original ergab jede Zeichenkette `None`); kein
API-Schlüssel im Code oder in der URL; defekte DIP-Einträge sind `ParseError`
statt Dokumente „Ohne Titel“; fehlgeschlagene Seiten und SPARQL-Abfragen sind
Fehler statt `success=True` mit 0 Dokumenten; Pagination über den DIP-Cursor;
prozessstabile Identitäten für Feeds; keine pauschale Klassifikation
`EFRE`/`2021-2027` für BaFin-, CURIA- und ECA-Meldungen; keine
ECA-Platzhalterberichte. Offen: DIP-Standardklassifikation
(`HUMAN_DECISION_REQUIRED`), Wirkung des Parameters `num`
(`REVIEW_REQUIRED`). Vollständig:
[docs/behavior-changes.md](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11. Pflicht: `auditcore_harvest==0.1.2` (Adaptervertrag) und
`auditcore_common==0.1.1` (Profile, Fingerprint, Linksammler; nur
Standardbibliothek). Extra `feeds`: feedparser ≥ 6.0.10 < 7. ECA-Links liest
der `html.parser` der Standardbibliothek über `auditcore_common.html_text`. Keine Abhängigkeit von httpx, Datenbanken oder der
Plattform `auditcore`.

## Sicherheit und Datenschutz

- **Geheimnisse:** Der DIP-Schlüssel wird nur als Header gesendet
  (`auth_header_value` weist leere und mehrzeilige Werte ab), nie als
  Query-Parameter; `drucksache_query` enthält ihn nicht.
- **Netzwerk:** kein eigener Abruf; Transport, Wiederholungen und Rate-Limits
  über `auditcore_harvest`. SPARQL-Abfragen entstehen nur aus festen
  Profilvorlagen mit einem `date`-Platzhalter.
- **Daten:** öffentliche Veröffentlichungen; Drucksachen können Namen von
  Abgeordneten und Urhebern enthalten (`metadata.autoren`). Die Nutzungs-
  bedingungen der Quellen (DIP, EUR-Lex-Weiterverwendung nach Beschluss
  2011/833/EU) beachtet der Consumer; das Paket enthält nur synthetische
  Fixtures.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) nur für den in diese Bibliothek extrahierten Code: Beide
Quellrepositories hatten keine Lizenz; der Rechteinhaber hat am 22.09.2026
entschieden, dass die Bibliotheken MIT sind, die Repositories nicht
(`USER_AUTHORIZED_MIT`). Quellen, Blobs und Erklärung: `NOTICE` und
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
