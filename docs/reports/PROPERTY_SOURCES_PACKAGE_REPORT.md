# auditcore_property_sources 0.1.0 – Paketbericht

Stand 2026-09-23, Branch `feat/auditcore-property-sources` auf `origin/main` 886a53a.
Abschnitt H5 der [Repository-Abdeckung](../architecture/REPOSITORY_PACKAGE_COVERAGE.md).

## Entscheidung und Consumer

Nutzerentscheidung 2026-09-23: Das Paket wird auch ohne bereits belegten
Mehrfachnutzen gebaut – „der mehrfache Nutzen kommt noch“. Consumer sind
deshalb **geplant**, nicht umgestellt. Vorhandene Nutzungen:

- `janpow77/wohnungsmonitor@76571bf`: `wohnungsmonitor.py` (`erhebe`,
  `erhebe_frankreich`) importiert `inberlinwohnen_export`,
  `kleinanzeigen_export`, `immobilien_export`, `bienici_export`,
  `citya_export`, `paruvendu_export` sowie `details.py`.
- `janpow77/versteigerung@e4ad7af`: `backend/app/crawler/zvg_crawler.py`
  (`ZvgPortal`, `parse_detail`, `Ingest`), genutzt von
  `repair_market_values.py`, `reparse_addresses.py`, `regeocode.py` und
  `worker.py`.

Jede Quelle hat heute genau einen Consumer; Miet- und Versteigerungsdaten
teilen keine Fachsemantik. Finanzmarkt- und Immobilienadapter bleiben getrennt.

## Inhalt

| Modul | Funktion |
|---|---|
| `immobilien_de`, `inberlinwohnen`, `kleinanzeigen` | Berliner Mietportale: Seitenparser, Normalisierung ins Bestandsformat von wohnungsmonitor, eigene Preissemantik |
| `bienici`, `citya`, `paruvendu` | französische Mietportale (Elsass/Lothringen) |
| `zvg` | ZVG-Portal: Trefferliste, Detailseite, Adress-, Betrags-, Objektart- und Zeichensatzbehandlung (Verkehrswert) |
| `zvg_lifecycle` | reiner Statuslebenszyklus (`mark_seen`, `close_vanished` mit Karenz, `reappear`) |
| `robots` | robots.txt-Auswertung (Platzhalter, Anker, längste Regel) |
| `adapters` (Extra `sources`) | acht Harvest-Adapter auf `auditcore_harvest` mit robots.txt-Sperre |
| `catalog` | Herkunft, geplanter Consumer, Semantik, Zugang, Live-Status je Quelle |

Nicht extrahiert (Begründung im Katalog): wohnungsmonitor `details.py`
(personenbezogene Detaildaten) und die Anwendungslogik von
`wohnungsmonitor.py`; versteigerung Geokodierung (Nominatim, Geo-Domäne),
`Ingest`-SQL und `gutachten_ingest.py`.

## Characterization

- Quellen gegen GitHub verifiziert (HEAD = inventarisierter Commit), eigener
  Klon im Scratch-Verzeichnis, Module blobgeprüft und unverändert ausgeführt.
- Keine gespeicherten Portalseiten in den Repos: 25 **synthetische,
  strukturabgeleitete** Seiten ohne Personendaten (`tools/synthetic_pages.py`).
- `tools/capture_property_sources.py`: 238 Fälle, 0 Ausnahmen; Netzwerk durch
  eine Seitenkarte ersetzt. Lebenszyklus: Original-`Ingest` auf wegwerfbarer
  PostGIS 16 mit Original-Alembic-Migrationen, 12 Szenarien, 7 Schritte.
- Replay: 228 Funktionsfälle exakt, 6 Paging-Abläufe gleich, alle
  Lebenszyklusschritte gleich. Abweichungen nur dokumentiert (PS-C01…08,
  PS-L01…07, [behavior-changes](../../packages/auditcore_property_sources/docs/behavior-changes.md)).

## Zugang (robots.txt einmalig am 2026-09-23 gelesen)

| Quelle | Adressen des Originals | Live-Smoke (1 Seite, nur Aggregate) |
|---|---|---|
| immobilien.de | erlaubt | PASS, 24 Datensätze |
| inberlinwohnen | erlaubt | PASS, 10 Datensätze (Seitenlimit 1) |
| Kleinanzeigen | **gesperrt** (`Disallow: /*/preis:*`) | NOT_EXECUTED |
| bienici | erlaubt | PASS, 24 Datensätze, ehrliche Kennung → HTTP 200 |
| Citya | erlaubt | PASS, 17 Datensätze |
| ParuVendu | erlaubt | PASS, 30 Datensätze |
| ZVG-Portal | Trefferliste erlaubt; `showZvg`/`showAnhang` **gesperrt** | Trefferliste PASS (8), Detail NOT_EXECUTED |

Nutzungsbedingungen aller Portale: REVIEW_REQUIRED (nicht geprüft).

## Prüfungen (tatsächlich ausgeführt)

| Prüfung | Ergebnis |
|---|---|
| pytest (Python 3.12) | 289 passed: Replay 239, Adapter 24 (Contract-Suite für 7 Adapter), Lebenszyklus 9, robots 9, Katalog 3, Policy 3, Architektur 2 |
| ruff, ruff format, mypy strict, bandit | PASS |
| Plattform-pytest (nach Merge von main) | 284 passed |
| auditcore-quality strict | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; API NOT_EXECUTED (keine Baseline); 5× AC-OSS-001 geprüft (Regex-Muster, keine Kennungen); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy (verwaltung-app-framework@15f5338) | F-07, F-09, F-15, F-16 VERIFIED (T-11/14/30/37/38); offen: F-05 (Personenbezug möglich), F-07.ASSESS (Schutzbedarf UNKNOWN), SOLL-01 |
| Wheel/sdist + SBOM | Wheel SHA-256 `130f2bd6028836580bdf82d6aa042f022c98929fafd6fee1f7164b2dc18d9d90` |
| `scripts/verify_domain_packages.py --apt` (mit `auditcore_harvest`) | 28/28 PASS: hashgebundene Installation, `pip check`, Herkunft, Smoke, selektive Installation, Entfernung, Debian-Pakete, signierte APT-Quelle, Install/Upgrade/Remove im netzlosen Container |
| Consumer-Integration (Kopien, installiertes Wheel) | 8/8 PASS; versteigerung-Tests auf der umgestellten Kopie 10 passed |

## Offene Entscheidungen (HUMAN_DECISION_REQUIRED)

1. Kleinanzeigen-Suchadresse verstößt gegen robots.txt (Abschalten, Abruf ohne
   Preissegment mit lokaler Filterung, oder Genehmigung).
2. versteigerung ruft robots-gesperrte Detail-/Anhangsseiten ab (Widerspruch zum
   eigenen Lastenheft).
3. bienici-Browserkennung und Nutzungsbedingungen aller Portale (REVIEW_REQUIRED).
4. Namen privater bienici-Anbieter: `minimal` (Standard) oder `legacy`.
5. Der Harvest-Katalog `auditcore_harvest/catalogs/sources.json` führt
   immobilien.de noch nicht; maßgeblich für Zugangsbefunde ist der Paketkatalog.
   Eine Ergänzung dort braucht eine neue auditcore_harvest-Version.
