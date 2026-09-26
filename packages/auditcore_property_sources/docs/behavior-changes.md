# Legacyverhalten und korrigierter Vertrag

Quellen: `janpow77/wohnungsmonitor@76571bf` (sechs Portalexporter) und
`janpow77/versteigerung@e4ad7af` (`backend/app/crawler/zvg_crawler.py`),
tatsächlich ausgeführt mit Python 3.12.3, beautifulsoup4 4.12.3, httpx 0.28.1
und psycopg 3.2.3 (`tools/capture_property_sources.py`, 238 Fälle).

**Eingaben:** Keines der beiden Repositories enthält gespeicherte Portalseiten.
Die Fixtures sind deshalb **synthetisch und strukturabgeleitet**
(`tools/synthetic_pages.py`): aus den Regexen, JSON-LD-/Livewire-Formaten,
Docstrings und Kommentaren der Parser nachgebaut, alle Namen, Adressen,
Kennungen und Preise erfunden, keine Anbieternamen oder Telefonnummern. Sie
belegen das Verhalten des Originalcodes auf diesen Eingaben, nicht das heutige
Layout der Portale.

**Lebenszyklus:** `Ingest.mark_seen`, `Ingest.close_vanished` und
`Ingest.upsert` liefen unverändert gegen eine wegwerfbare PostgreSQL-16/PostGIS-
Datenbank, migriert mit den Original-Alembic-Migrationen (12 Szenarien,
7 Schritte). `zvg_lifecycle` reproduziert jeden Statusübergang.

Ergebnis: Alle 228 Funktionsfälle werden **exakt** reproduziert (JSON-gleich),
die sechs Paging-Abläufe (`hole_bestand`) liefern über die Harvest-Adapter
dieselben Datensätze, alle Lebenszyklusschritte denselben Status.

## Bewusst korrigiert (PS-C)

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| PS-C01 | Modulglobale Zustände: `MERKMALE` (inberlinwohnen), `_PLZ_BEZIRKE` (immobilien.de), `_ZUORDNUNG` (Kleinanzeigen) werden aus Dateien neben dem Modul gelesen bzw. über Läufe hinweg angesammelt. | Zuordnungen werden ausdrücklich übergeben (`plz_bezirke`, `district_index(...)`, `attributes`). Die amtlichen Zuordnungsdateien bleiben Daten des Consumers. | Keine versteckten Dateizugriffe, keine Fremddaten im Paket, reproduzierbar. |
| PS-C02 | bienici: bei Privatanbietern (`accountType = individual`) wird `accountDisplayName` – potenziell ein Personenname – als `gesellschaft` übernommen. | **DECIDED 2026-09-23:** Standard `advertiser_names="legacy"` reproduziert das Original exakt; `"minimal"` setzt „Privatangebot“ und bleibt wählbar. | Nutzerentscheidung (siehe unten). `"minimal"` bleibt für Datenminimierung (Art. 5 Abs. 1 lit. c, Art. 25 DSGVO) verfügbar. |
| PS-C03 | inberlinwohnen normalisiert erst am Ende mit den bis dahin gelernten Merkmalen aller Seiten. | Adapter normalisiert je Seite mit den bis einschließlich dieser Seite gelernten Merkmalen (im Cursor). | Seitenweise Übergabe an die Senke; auf den Fixtures identisch. Taucht ein Merkmalsname erst auf einer späteren Seite auf, fehlt er im früheren Datensatz. |
| PS-C04 | `parse_detail` prüft das Baujahr gegen `datetime.now().year + 1`. | `reference_year` wird übergeben; der Detailadapter nimmt es aus der injizierten Uhr. | Deterministische Ergebnisse. |
| PS-C05 | `Verfahren` trägt `lat`/`lon` aus der Nominatim-Geokodierung. | `ZvgNotice` ohne Koordinaten; Geokodierung bleibt beim Consumer. | Eigener Dienst mit Nutzungsrichtlinie (Lastenheft: Self-Hosting), Geo-Domäne (`auditcore_geo`). |
| PS-C06 | Unlesbare JSON-LD-Blöcke, Livewire-Snapshots, bienici-Anzeigen ohne Kennung, Citya-Angebote ohne Adresse und ZVG-Treffer ohne Aktenzeichen werden still übergangen. | Dieselben Datensätze, zusätzlich `RecordIssue` und Seitenstatus `partial`. | Teilfehler sichtbar statt still. |
| PS-C07 | `ZvgPortal`/`main` überspringen unbekannte Gerichte mit einer Konsolenmeldung. | `ZvgListingAdapter.validate_config` weist unbekannte Gerichte ab. | Konfigurationsfehler vor dem ersten Abruf. |
| PS-C08 | Abrufe ohne Prüfung der robots.txt (Kleinanzeigen: gesperrter Pfad; ZVG: gesperrte Detail- und Anhangsseiten). | **DECIDED 2026-09-23:** Einstellung `robots_policy`. Standard `"ignore"` ruft wie das Original ohne robots.txt ab; `"respect"` liest robots.txt über den injizierten Transport und verweigert gesperrte Adressen (`access_not_permitted`, nicht wiederholbar). `file:`-Archive sind nie betroffen. | Nutzerentscheidung (siehe unten). Der robots.txt-Befund bleibt im Katalog dokumentiert; das Lastenheft versteigerung (Kap. 22.3/33) verlangt die Beachtung weiterhin – der Widerspruch ist bewusst in Kauf genommen. |
| PS-C09 | `ZvgPortal` baut vor dem Detailabruf eine Sitzung auf (`button=Termine suchen`) und ruft `showZvg` mit Referer der Trefferliste ab. | Der `ZvgDetailAdapter` tut das seit 2026-09-23 ebenso (Sitzung einmal je Lauf, im Cursor vermerkt); zuvor rief er die Detailseite direkt ab und erhielt live keine auswertbare Seite. | Beim ersten Live-Abruf nach PS-D01 gefunden; danach Live-Smoke PASS (`docs/live-smoke.json`). |
| PS-C10 | `parse_de_number` sucht die erste Zahl irgendwo im Text; das erste Muster (Tausenderpunkte) greift auch ohne Punkte und schneidet nach drei Ziffern ab: „1234,56“ → 123,0, „2015“ → 201,0, „1.5“ → 1,0; „1.234“ → 1234,0 (geraten), „ca. 120,5 m²“ → 120,5 (charakterisiert: `tests/fixtures/legacy_observed.json`). | **Ab 0.1.2 (Nutzerauftrag 25.09.2026):** Regeln des gemeinsamen Vertrags `contracts/common-cases/parse-number.json`, Modus `de`, über `auditcore_common.numbers_de`: der ganze Text ist die Zahl (Währung/Leerraum erlaubt), Dezimalkomma, Punkte nur als Tausendertrenner in Dreiergruppen, höchstens zwei Nachkommastellen; mehrdeutige Formen („1.234“, „1.5“, „1,234“, „85,555“) und Text um die Zahl ergeben `None`. Rückgabe weiter `float`. Das Original bleibt als `zvg.legacy_parse_de_number` (Replay der 238 Fälle läuft dagegen). | Korrekte Wohnflächen („Wohnfläche 1234,56 m²“ ergab 123,0 m²); Mehrdeutiges wird nicht geraten. Unverändert: „945,80“, „1.234,5“, „12.345.678,99“, „keine Angabe“. Tests: `tests/test_parse_de_number.py` (alle `de`-Fälle des Vertrags, Differenzliste alt/neu). |

## Bewusst beibehalten (PS-L)

| ID | Verhalten | Hinweis |
|---|---|---|
| PS-L01 | Getrennte Preissemantik je Quelle: immobilien.de (Mietart aus Markup), inberlinwohnen (Tafel-Gesamtmiete inkl. Heizung), Kleinanzeigen/Citya (`unklar`), bienici (`price` warm), ParuVendu (CC/HC), ZVG (Verkehrswert). | Keine Vereinheitlichung; `preisart` und Profil sagen, was der Betrag ist. |
| PS-L02 | immobilien.de `_mietart_zu` probiert vier Schreibweisen, darunter `f"{wert:,.2f}".replace(",", ".")` (für 1234,5 → „1.234.50“). | Exakt übernommen. |
| PS-L03 | ZVG `extract_market_value` erkennt Beträge nur mit nachgestelltem `€`/`EUR` oder als *Gesamtverkehrswert*; „245.000,00“ ohne Währungszeichen ergibt keinen Wert. | Beobachtet (`detail-efh`), unverändert. |
| PS-L04 | ZVG `80,000,-` gilt als 80 000 EUR (Tausenderkomma). | Wie `repair_market_values.py` begründet. |
| PS-L05 | `ZvgPortal.search_court` liest die rohe HTML-Seite und findet `&amp;`-kodierte Links nicht (liefert `[]`), zählt aber Treffer ohne Aktenzeichen mit. | Nicht übernommen als Funktion; die Bibliothek nutzt wie `main` die geparsten Links (`parse_listing_akten`, `listing_ids`). |
| PS-L06 | Lebenszyklus: Schließen nur bei `last_seen_at` **strikt** älter als die Karenz; `abgehalten` nur ohne Termin ab jetzt; Wiedererscheinen öffnet auch `abgehalten`. | Exakt als reine Funktionen. |
| PS-L07 | Kleinanzeigen-Güterfilter und Citya-Wohnraumfilter verwerfen Einträge ohne Hinweis. | Übernommen (fachlicher Filter, kein Parserfehler). |

## Entscheidungen (DECIDED, 2026-09-23, Nutzer)

Wortlaut: „1-4 bitte ignoriere die robots.txt. das klappt gerade gut“; nach der Blockade durch die Rechteprüfung ausdrücklich
bestätigt mit „A1 erlauben“ / „A1 ok“.

| ID | Entscheidung | Umsetzung |
|---|---|---|
| PS-D01 | robots.txt wird nicht erzwungen (Punkte 1 und 2 unten). | `robots_policy="ignore"` als Standard, `"respect"` wählbar; Kleinanzeigen-Suche und ZVG-Detailseiten (`showZvg`) werden wie im Original abgerufen. `showAnhang` gehört nicht zum Paket. |
| PS-D02 | bienici sendet die Browser-Kennung des Originals (Punkt 3). | `bienici.request_headers()` mit `BROWSER_USER_AGENT`, `Accept-Language` und `Referer` wie `_hole`; `user_agent=None` überlässt die Kennung dem Transport. |
| PS-D03 | Namen privater Anbieter wie im Original (Punkt 5). | `advertiser_names="legacy"` als Standard. |

Nutzungsbedingungen und Datenbankherstellerrecht (Punkt 4) bleiben
`REVIEW_REQUIRED`; die Verantwortung für den Abruf liegt beim Betreiber.

## Ursprünglich offene Punkte (vor der Entscheidung)

1. **Kleinanzeigen:** Die Suchadresse `…/berlin/[seite:N/]preis::700/c203l3331`
   ist durch `Disallow: /*/preis:*` gesperrt; der Docstring des Exporters nennt
   den Suchpfad fälschlich frei. Ohne Preissegment wäre der Pfad erlaubt, würde
   aber die Treffermenge ändern. Entscheidung: Quelle abschalten, Abruf ohne
   Preissegment mit lokaler Filterung, oder Genehmigung des Betreibers.
2. **ZVG-Portal:** versteigerung ruft Detail- (`showZvg`) und Anhangsseiten
   (`showAnhang`) ab, die robots.txt sperrt – im Widerspruch zum eigenen
   Lastenheft. Die Trefferliste ist erlaubt und genügt für den Lebenszyklus.
   Entscheidung über Detailabruf (Genehmigung, offizielle Schnittstelle, Verzicht).
3. **bienici:** Das Original sendet eine Browser-Kennung, weil das Portal die
   eigene Kennung mit 403 abgewiesen habe. Der Live-Smoke vom 2026-09-23
   erhielt mit einer ehrlichen, nicht getarnten Kennung HTTP 200. Ob
   wohnungsmonitor die Tarnung aufgibt und ob der Abruf nach den
   Nutzungsbedingungen zulässig ist, ist zu klären (REVIEW_REQUIRED).
4. **Nutzungsbedingungen** aller sieben Portale sind nicht geprüft
   (REVIEW_REQUIRED); ebenso Datenbankherstellerrecht (§§ 87a ff. UrhG).
5. **bienici-Privatanbieter:** Soll wohnungsmonitor weiterhin Namen privater
   Anbieter führen (`advertiser_names="legacy"`)?
