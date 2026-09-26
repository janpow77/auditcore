# auditcore_property_sources

## Zweck

Getrennte Quellprofile für Immobiliendaten – Berliner und französische Mietportale sowie Zwangsversteigerungen des ZVG-Portals – mit Harvest-Adaptern, reinem ZVG-Lebenszyklus und Zugangskatalog.

Für die Anwendungen `wohnungsmonitor` (Mietangebote) und `versteigerung`
(Versteigerungstermine) und andere Consumer, die Portaldaten ohne
Vereinheitlichung der Preissemantik übernehmen wollen. Amtliche Zuordnungen
(PLZ → Bezirk), Geokodierung, Speicherung und Transaktionen bleiben beim
Consumer.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_property_sources \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.2 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-property-sources/`):

```text
auditcore_property_sources @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_property_sources-0.1.2-py3-none-any.whl#sha256=91059653c498aaa9c7bd14d57ad6bcb6b47f11d122320c17ec5d895515c811cb
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-property-sources
```

Extras: `[sources]` – Harvest-Adapter (`auditcore_harvest`); die Parser
brauchen nur die Standardbibliothek; `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

ZVG-Beträge lesen, verschwundene Verfahren eines Gerichts schließen und
robots.txt auswerten – alles ohne Netzwerk:

```python
from datetime import datetime, timedelta, timezone

from auditcore_property_sources import is_allowed, parse_robots, source_entry, zvg, zvg_lifecycle

assert zvg.extract_market_value("Verkehrswert: 245.000,00 €") == 245000.0
assert zvg.extract_market_value("245.000,00") is None  # ohne Währung kein Wert (PS-L03)
assert zvg.classify_type("Einfamilienhaus mit Garage") == "efh"

now = datetime(2026, 9, 25, 12, tzinfo=timezone.utc)
seen = now - timedelta(days=5)
cases = [
    zvg_lifecycle.CaseState("1 K 1/26", "terminiert", seen, dates=(now - timedelta(days=2),)),
    zvg_lifecycle.CaseState("1 K 2/26", "terminiert", seen, dates=(now + timedelta(days=10),)),
    zvg_lifecycle.CaseState("1 K 3/26", "erfasst", now - timedelta(days=1)),
]
updated, closed = zvg_lifecycle.close_vanished(cases, now, grace_days=3)

rules = parse_robots("User-agent: *\nDisallow: /showZvg\n")
assert not is_allowed(rules, "https://www.zvg-portal.de/showZvg?id=1")
assert source_entry("property.zvg")
```

```pycon
>>> [(case.file_number, case.status) for case in updated], closed
([('1 K 1/26', 'abgehalten'), ('1 K 2/26', 'aufgehoben'), ('1 K 3/26', 'erfasst')], 2)
```

Adapter (Extra `sources`) laufen über den Engine von `auditcore_harvest`:

```python no-run
from auditcore_harvest import HarvestEngine, HarvestRequest, RateLimit
from auditcore_property_sources.adapters import ZvgListingAdapter

engine = HarvestEngine(transport, credentials, state, clock, sleeper, rate_limit=RateLimit(0.7))
result = engine.run(
    ZvgListingAdapter(), HarvestRequest("property.zvg", run_id="…"), sink, config={"courts": "kern"}
)
```

## API-Überblick

| Modul | Quelle | Betrag bedeutet | Adapter |
|---|---|---|---|
| `immobilien_de` | immobilien.de (Berlin) | Miete; Mietart aus dem Markup (kalt/warm/unklar) | `ImmobilienDeAdapter(plz_bezirke)` |
| `inberlinwohnen` | landeseigene Gesellschaften (Berlin) | Kaltmiete, Gesamtmiete laut Angebotstafel | `InBerlinWohnenAdapter()` |
| `kleinanzeigen` | Kleinanzeigen (Berlin) | Anzeigenpreis, `preisart: unklar` | `KleinanzeigenAdapter(ortsteile_bezirke)` |
| `bienici` | bien'ici (Frankreich) | `price` warm, Kaltmiete = price − charges | `BieniciAdapter()` |
| `citya` | Citya (Frankreich) | ein Betrag, `preisart: unklar` | `CityaAdapter()` |
| `paruvendu` | ParuVendu (Frankreich) | CC warm, HC kalt, sonst unklar | `ParuvenduAdapter()` |
| `zvg` | ZVG-Portal | **Verkehrswert** (gerichtlich, EUR) | `ZvgListingAdapter()`, `ZvgDetailAdapter()` |

Dazu `zvg_lifecycle` (`mark_seen`, `close_vanished`, `reappear`), `robots`
(robots.txt-Auswertung) und `catalog()`/`source_entry()` (Zugangskatalog).

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_property_sources.__all__` (9):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `AccessNotPermitted` | Ausnahme | robots.txt of the portal disallows the requested path (never retried). | `errors` |
| `DependencyError` | Ausnahme | The optional harvest extra (``auditcore_property_sources[sources]``) is missing. | `errors` |
| `PropertySourceError` | Ausnahme | Base class; ``code`` is stable and machine readable. | `errors` |
| `RobotsRules` | Datenklasse | Rules of one group: ``(allow, pattern)`` in file order. | `robots` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `catalog` | Funktion | Deep copy of the whole catalog document. | `catalog` |
| `is_allowed` | Funktion | Whether ``url`` (absolute or path) may be fetched under ``rules``. | `robots` |
| `parse_robots` | Funktion | Rules of the group for ``token`` (case-insensitive), else of ``*``. | `robots` |
| `source_entry` | Funktion | Catalog entry of one source profile (``KeyError`` if unknown). | `catalog` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_property_sources.adapters` | Harvest adapters (extra ``auditcore_property_sources[sources]``) on ``auditcore_harvest``. |
| `auditcore_property_sources.bienici` | bienici.com: French rental ads from the portal's JSON search (realEstateAds.json). |
| `auditcore_property_sources.catalog` | Versioned source catalog: origin, planned consumer, semantics and access status. |
| `auditcore_property_sources.citya` | citya.com: rental offers of the property manager Citya (schema.org OfferCatalog). |
| `auditcore_property_sources.errors` | Error contract of the property source library. |
| `auditcore_property_sources.immobilien_de` | immobilien.de: Berlin rental offers from schema.org JSON-LD. |
| `auditcore_property_sources.inberlinwohnen` | inberlinwohnen.de: offers of Berlin's state-owned housing companies (Livewire snapshots). |
| `auditcore_property_sources.kleinanzeigen` | Kleinanzeigen: Berlin rental ads from the result list (private and commercial offerers). |
| `auditcore_property_sources.paruvendu` | paruvendu.fr: French rental ads (private and agency) from result cards. |
| `auditcore_property_sources.robots` | robots.txt evaluation (RFC 9309 with the common ``*``/``$`` wildcards). |
| `auditcore_property_sources.zvg` | ZVG-Portal (Justizportal der Länder): notices of forced auctions. |
| `auditcore_property_sources.zvg_lifecycle` | Status lifecycle of ZVG notices as pure, database-free functions. |
<!-- api-overview:end -->

## Profile und Konfiguration

Jedes Modul ist ein eigenes Quellprofil (wohnungsmonitor-Profile „berlin“ und
„frankreich“, versteigerung für ZVG) und behält die Normalisierung und die
Feldnamen seines Originals. Zuordnungen übergibt der Consumer ausdrücklich
(`plz_bezirke`, `ortsteile_bezirke`, `attributes`).

Adaptereinstellungen: `courts` (`"kern"`, `"he"`, `"all"` oder eine Liste von
Gerichtskennungen; unbekannte Gerichte werden vor dem ersten Abruf
abgewiesen), `robots_policy` (`"ignore"` Standard wie das Original,
`"respect"` verweigert gesperrte Adressen mit `access_not_permitted`),
`advertiser_names` bei bien'ici (`"legacy"` Standard, `"minimal"` setzt
„Privatangebot“), `user_agent` bei bien'ici (Browser-Kennung des Originals,
`None` überlässt sie dem Transport). `snapshot_semantics =
FULL_SNAPSHOT_REPLACE`: Ausscheiden und Schließen nur nach
`result.snapshot_complete`.

## Herkunft und Charakterisierung

Extrahiert aus `janpow77/wohnungsmonitor@76571bf` (sechs Portalexporter) und
`janpow77/versteigerung@e4ad7af` (`backend/app/crawler/zvg_crawler.py`).
`tools/capture_property_sources.py` hat 238 Fälle am Original ausgeführt
(`tests/fixtures/legacy_observed.json`); die Eingaben sind synthetisch und
strukturabgeleitet, ohne Personendaten, und belegen das Verhalten des
Originalcodes, nicht das heutige Portallayout. Der Lebenszyklus lief mit der
Original-SQL gegen eine wegwerfbare PostgreSQL/PostGIS-Datenbank. Alle 228
Funktionsfälle werden **exakt** reproduziert, die sechs Paging-Abläufe liefern
über die Adapter dieselben Datensätze. Live-Prüfung je Portal eine
Ergebnisseite: [docs/live-smoke.json](docs/live-smoke.json). Umstellung der
Consumer: [docs/consumer-migration.md](docs/consumer-migration.md).

## Bewusste Verhaltensabweichungen

Korrigiert (PS-C01 bis PS-C10): keine modulglobalen Zustände und versteckten
Dateizugriffe, Zuordnungen werden übergeben; das Baujahr wird gegen ein
übergebenes `reference_year` geprüft; ZVG-Meldungen ohne Koordinaten
(Geokodierung beim Consumer); still übergangene Einträge erzeugen
`RecordIssue` und Seitenstatus `partial`; unbekannte Gerichte sind
Konfigurationsfehler; `zvg.parse_de_number` liest deutsche Zahlen ab 0.1.2
nach dem gemeinsamen Vertrag `parse-number` (Modus `de`, über
`auditcore_common.numbers_de`): „1234,56“ ergibt 1234,56 statt 123,0,
Mehrdeutiges („1.234“, „1.5“) ergibt `None`; das Original bleibt als
`zvg.legacy_parse_de_number`. Beibehalten (PS-L01 bis PS-L07) unter anderem die
getrennte Preissemantik und die ZVG-Betragsregeln. Entschieden am 23.09.2026
(PS-D01 bis PS-D03): robots.txt wird standardmäßig nicht erzwungen, bien'ici
sendet die Kopfzeilen des Originals, Anbieternamen wie im Original.
Vollständig: [docs/behavior-changes.md](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11, Parser nur Standardbibliothek und `auditcore_common==0.2.0`
(Zahleneingabe `numbers_de`, ab 0.1.2 einzige Pflichtabhängigkeit);
Extra `sources`: `auditcore_harvest==0.1.3` (das im Release v0.3.0
veröffentlichte Wheel 0.1.0 verlangt noch 0.1.0). Kein beautifulsoup4, kein
HTTP-Client, keine Datenbank.

## Sicherheit und Datenschutz

- **Personenbezug:** Anzeigen können Namen privater Anbieter enthalten; mit
  `advertiser_names="legacy"` (Standard nach Entscheidung PS-D03) werden sie
  wie im Original übernommen, `"minimal"` dient der Datenminimierung
  (Art. 5 Abs. 1 lit. c, Art. 25 DSGVO).
- **Zugang:** Kleinanzeigen-Suche und ZVG-Detailseiten sind laut robots.txt
  gesperrt und werden nach Nutzerentscheidung trotzdem abgerufen;
  `robots_policy="respect"` ist wählbar. Nutzungsbedingungen aller Portale sind
  `REVIEW_REQUIRED` (`catalog()`); Portalinhalte gehören nicht zum Paket.
- **Netzwerk:** Transport, User-Agent, Sitzung und Rate-Limit injiziert der
  Consumer über `auditcore_harvest`; `file:`-Archive sind von robots.txt nie
  betroffen.
- Fixtures sind synthetisch, alle Namen, Adressen und Preise erfunden.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) für den nach auditcore extrahierten Bibliothekscode:
Entscheidung des Rechteinhabers vom 22.09.2026 (`USER_AUTHORIZED_MIT`); die
Quellrepositories werden nicht umlizenziert, Portalinhalte und -daten sind
nicht erfasst. Quellen, Blobs und Erklärung: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
