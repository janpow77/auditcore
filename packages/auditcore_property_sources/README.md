# auditcore_property_sources

Getrennte Quellprofile für Immobiliendaten – Mietportale aus `wohnungsmonitor`
und Zwangsversteigerungsbekanntmachungen aus `versteigerung` – mit
Harvest-Adaptern auf `auditcore_harvest`, einem reinen ZVG-Lebenszyklus und
einem Zugangskatalog (robots.txt, Nutzungsbedingungen, Live-Status).

Die Parser nutzen nur die Standardbibliothek. Die Adapter liegen im Extra
`sources` (`auditcore_harvest==0.1.0`). Debian: `python3-auditcore-property-sources`.

## Quellprofile (keine Vereinheitlichung)

| Modul | Quelle | Betrag bedeutet | Adapter |
|---|---|---|---|
| `immobilien_de` | immobilien.de (Berlin) | Miete; Mietart aus dem Markup (kalt/warm/unklar) | `ImmobilienDeAdapter(plz_bezirke)` |
| `inberlinwohnen` | landeseigene Gesellschaften (Berlin) | Kaltmiete, Gesamtmiete laut Angebotstafel | `InBerlinWohnenAdapter()` |
| `kleinanzeigen` | Kleinanzeigen (Berlin) | Anzeigenpreis, `preisart: unklar` | `KleinanzeigenAdapter(ortsteile_bezirke)` |
| `bienici` | bien'ici (Frankreich) | `price` warm, Kaltmiete = price − charges | `BieniciAdapter()` |
| `citya` | Citya (Frankreich) | ein Betrag, `preisart: unklar` | `CityaAdapter()` |
| `paruvendu` | ParuVendu (Frankreich) | CC warm, HC kalt, sonst unklar | `ParuvenduAdapter()` |
| `zvg` | ZVG-Portal | **Verkehrswert** (gerichtlich, EUR) | `ZvgListingAdapter()`, `ZvgDetailAdapter()` |

Ein gemeinsamer HTTP-Transport beweist keine gleiche Fachsemantik; jedes
Modul behält die Normalisierung seines Originals (Feldnamen des jeweiligen
Consumer-Bestands). Die amtlichen Zuordnungen (PLZ → Bezirk, Ortsteil →
Bezirk) übergibt der Consumer.

```python
from auditcore_property_sources import immobilien_de, zvg, zvg_lifecycle

listings, unreadable = immobilien_de.parse_page(html)
angebot = immobilien_de.normalise(listings["41000001"], plz_bezirke)

notice = zvg.parse_detail(html, zvg.ZvgNotice("880001", "he", "M1201"), reference_year=2026)
cases, closed = zvg_lifecycle.close_vanished(cases, now, grace_days=3)
```

## Adapter (Extra `sources`)

```python
from auditcore_harvest import HarvestEngine, HarvestRequest, RateLimit
from auditcore_property_sources.adapters import ZvgListingAdapter

engine = HarvestEngine(transport, credentials, state, clock, sleeper, rate_limit=RateLimit(0.7))
result = engine.run(
    ZvgListingAdapter(), HarvestRequest("property.zvg", run_id="…"), sink, config={"courts": "kern"}
)
```

- Ein Aufruf von `fetch_page` = eine Ergebnisseite; Paging- und Abbruchregeln
  entsprechen den Original-`hole_bestand`-Funktionen. Timeouts, begrenzte
  Wiederholungen, Rate-Limit, Checkpoints und Teilfehler übernimmt der Engine.
- Transport (User-Agent, Cookies/Sitzung) injiziert der Consumer. Ausnahme
  bienici: Der Adapter sendet wie das Original die Browser-Kennung und die
  Kopfzeilen von `_hole` (`user_agent=None` überlässt die Kennung dem Transport).
- **robots.txt** (Einstellung `robots_policy`, Nutzerentscheidung 2026-09-23):
  Standard `"ignore"` ruft wie die Originale ohne robots.txt ab. Mit `"respect"`
  wird robots.txt vor der ersten http(s)-Anfrage gelesen; gesperrte Adressen
  enden dann mit `access_not_permitted` (nicht wiederholbar). `file:`-Adressen
  (Archiv über `FileTransport`) sind nie betroffen.
- Alle Adapter erfüllen die Contract-Suite `auditcore_harvest.testing.assert_adapter`.
- `snapshot_semantics = FULL_SNAPSHOT_REPLACE`: Ausscheiden/Schließen nur nach
  `result.snapshot_complete` (wohnungsmonitor LA-06; ZVG-Lebenszyklus je Gericht).

## Zugang und Rechte

`catalog()` nennt je Quelle Herkunft (Commit/Blob), geplanten Consumer,
Semantik, robots.txt-Befund (Schnappschuss 2026-09-23), Nutzungsbedingungen
(`REVIEW_REQUIRED`) und Live-Status (`docs/live-smoke.json`: je Portal eine
Ergebnisseite, nur Aggregate). Kleinanzeigen (Suchadresse des Originals) und
ZVG-Detailseiten sind per robots.txt gesperrt und werden nach Nutzerentscheidung
trotzdem abgerufen – siehe [docs/behavior-changes.md](docs/behavior-changes.md)
(PS-D01–D03).
Consumer-Umstellung: [docs/consumer-migration.md](docs/consumer-migration.md).
Herkunft und MIT-Freigabe: `NOTICE`, `provenance.json`.
