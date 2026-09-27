# Spezifikation auditcore_property_sources

Stand: 26.09.2026, Paketversion 0.1.3. Charakterisierung: 238 Fälle aus den
ausgeführten Originalen (`tests/fixtures/legacy_observed.json`,
`tests/test_legacy_replay.py`, Lebenszyklus gegen eine PostgreSQL-Datenbank
mit den Original-Migrationen in `tests/test_lifecycle.py`).
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket liest Immobilienangebote und Versteigerungstermine aus getrennten
Quellprofilen – Berliner und französische Mietportale sowie das ZVG-Portal der
Justiz – und übergibt sie mit Herkunft an `auditcore_harvest`. Jede Quelle
behält ihre eigene Preissemantik (kalt, warm, unklar, Verkehrswert); das Paket
vereinheitlicht sie nicht. Dazu kommen ein datenbankfreier Lebenszyklus für
ZVG-Verfahren, eine robots.txt-Auswertung und ein Zugangskatalog.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| Portalmodule `immobilien_de`, `inberlinwohnen`, `kleinanzeigen`, `bienici`, `citya`, `paruvendu` | Seiteninhalt (HTML, JSON-LD, JSON) und ausdrücklich übergebene Zuordnungen (`plz_bezirke`, `ortsteile_bezirke`, `attributes`) | Datensätze im Bestandsformat des Consumers mit `preisart` | keine |
| `bienici.normalise(ad, advertiser_names=)` | Anzeige aus `realEstateAds.json`; `"legacy"` (Standard) oder `"minimal"` | Datensatz; Kaltmiete = Warmmiete − Nebenkosten, wenn nicht angegeben | keine |
| `zvg.parse_listing_akten`, `listing_ids`, `parse_detail(html, notice, reference_year=)` | Trefferliste bzw. Detailseite, Bezugsjahr ausdrücklich | Aktenzeichen, Kennungen, `ZvgNotice` mit Verkehrswert in EUR | keine; keine Geokodierung |
| `zvg.parse_de_number(text)` | Zahltext | `float` nach dem gemeinsamen Vertrag `parse-number`, Modus `de` (`auditcore_common.numbers_de`), sonst `None` | keine |
| `zvg.resolve_courts(arg)` | `kern`, `he`, `all` oder Kommaliste von Gerichtskennungen | Liste in Eingabereihenfolge | keine |
| `zvg_lifecycle.mark_seen`, `close_vanished`, `reappear`, `closing_status`, `status_for_date` | `CaseState`-Werte mit zeitzonenbehafteten Zeitpunkten, `now`, Karenztage | neue `CaseState`-Werte, Zahl geschlossener Fälle | keine; Speicherung und Transaktionen beim Consumer |
| `robots.parse_robots(text, token)`, `is_allowed(rules, url)`, `require_allowed` | robots.txt-Text, Kennung, Adresse | Regelgruppe, Wahrheitswert bzw. `AccessNotPermitted` | keine; robots.txt wird über den Transport des Adapters geholt |
| `catalog()`, `source_entry(id)` | – bzw. Quellkennung | tiefe Kopie des versionierten Zugangskatalogs | keine |
| `adapters` (Extra `sources`) | Einstellungen `courts`, `robots_policy`, `advertiser_names`, Zuordnungen | Harvest-Datensätze, `RecordIssue` und Seitenstatus `partial` bei Teilfehlern | Netz nur über den injizierten Transport; Uhr injiziert |

Statusmodell ZVG: `erfasst` und `terminiert` sind offen, `abgehalten` und
`aufgehoben` geschlossen.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Eine deutsche Zahl (Tausenderpunkte in Dreiergruppen, Dezimalkomma, höchstens zwei Nachkommastellen, optional `€`/`EUR`) wird exakt gelesen – außer einer Ganzzahl mit genau einer Tausendergruppe (I2). | `test_i1_german_number_roundtrip` |
| I2 | Mehrdeutige Formen (`12.345`, `1,234`) und Text um die Zahl (`ca. 120,5 m²`) ergeben `None`; es wird nicht geraten. | `test_i2_ambiguous_or_embedded_numbers_give_none` |
| I3 | Portalbeträge mit Tausenderpunkten, `,-` und Währung ergeben den Betrag in EUR. | `test_i3_money_amounts_roundtrip` |
| I4 | `mark_seen` setzt `last_seen_at = now` genau bei den gelisteten Aktenzeichen und lässt alles andere unverändert; eine leere Liste ändert nichts. | `test_i4_mark_seen_only_touches_listed_cases` |
| I5 | `close_vanished` schließt genau die offenen, nicht gelöschten Fälle, deren `last_seen_at` strikt vor `now − Karenz` liegt (`abgehalten` nur ohne künftigen Termin), setzt `closed_at = now`, zählt richtig und ist idempotent. | `test_i5_close_vanished_closes_exactly_the_stale_open_cases` |
| I6 | `reappear` öffnet jeden Fall wieder: `terminiert` genau bei Termin ab `now`, sonst `erfasst`; `closed_at` leer, Termine ersetzt. | `test_i6_reappear_reopens` |
| I7 | Unbekannte Status, zeitzonenlose Zeitpunkte und negative Karenz werden abgewiesen, nicht ausgelegt. | `test_i7_case_state_rejects_unknown_status_and_naive_times` |
| I8 | robots.txt: einfache Regeln sind Präfixe, die längste passende Regel gewinnt, bei gleicher Länge `Allow`; ohne passende Regel und bei leerem `Disallow` ist alles erlaubt; die Cursorform (`to_list`/`from_list`) ist verlustfrei. | `test_i8_robots_prefix_rules` |
| I9 | bien'ici: `"minimal"` gibt für Privatanbieter nie den Anzeigenamen weiter; `"legacy"` ist der Standard und übernimmt ihn; die Kaltmiete wird als Warmmiete − Nebenkosten abgeleitet, wenn sie fehlt. | `test_i9_bienici_private_names_and_rents` |
| I10 | bien'ici-Zeitstempel werden `TT.MM.JJJJ`; `1970-01-01` und fehlende Werte bedeuten „unbekannt“. | `test_i10_bienici_dates` |
| I11 | Die Gerichtsauswahl ist ausdrücklich: benannte Gruppen (`kern` ⊆ `all`) oder eine Kommaliste in Eingabereihenfolge. | `test_i11_court_selection` |

## Fehlerfälle

| Fall | Ergebnis |
|---|---|
| Unbekannter Status, zeitzonenloser Zeitpunkt in `CaseState`, negative oder nicht ganzzahlige Karenz | `ValueError` bzw. Fehler von `auditcore_common.clock.require_aware` |
| Unbekannte Gerichte, `robots_policy` außer `ignore`/`respect`, `advertiser_names` außer `minimal`/`legacy` | Konfigurationsfehler des Adapters vor dem ersten Abruf (PS-C07) |
| Adresse durch robots.txt gesperrt bei `robots_policy="respect"` | `AccessNotPermitted` (Code `access_not_permitted`, nicht wiederholbar) |
| Extra `sources` fehlt | `DependencyError` |
| Unlesbare JSON-LD-Blöcke, Livewire-Snapshots, Anzeigen ohne Kennung, Angebote ohne Adresse, ZVG-Treffer ohne Aktenzeichen | dieselben Datensätze wie im Original, zusätzlich `RecordIssue` und Seitenstatus `partial` (PS-C06) |
| Nicht lesbare oder mehrdeutige Zahl, Betrag ohne Währungszeichen im Verkehrswertblock | `None` (PS-C10, PS-L03) |
| Unbekannte Quelle im Katalog | `KeyError` |

## Abgrenzung

- Keine Vereinheitlichung der Preissemantik; `preisart` und Profil sagen, was
  ein Betrag ist (PS-L01).
- Keine amtlichen Zuordnungen (PLZ → Bezirk), keine Geokodierung (Geodomäne:
  `auditcore_geo`), keine Speicherung, keine Transaktionen, kein Scheduler.
- Kein Abruf von ZVG-Anhängen (`showAnhang`).
- Keine rechtliche Bewertung der Nutzungsbedingungen der Portale
  (REVIEW_REQUIRED, beim Betreiber).

## Bewusste Abweichungen vom Altverhalten

Vollständige Liste PS-C01 bis PS-C10 und PS-L01 bis PS-L07 in
[behavior-changes.md](behavior-changes.md).

| Altverhalten | Gewollt | Legacy-Variante | Nachweis |
|---|---|---|---|
| `parse_de_number` nimmt die erste Zahl irgendwo im Text und schneidet ohne Tausenderpunkte nach drei Ziffern ab („1234,56“ → 123,0; PS-C10) | Vertrag `parse-number`, Modus `de` (I1, I2) | `zvg.legacy_parse_de_number` – nur für Replay und Migration, nicht für neue Aufrufer | `tests/test_parse_de_number.py`, Replay |
| bien'ici übernimmt bei Privatanbietern den Anzeigenamen als `gesellschaft` (PS-C02) | `"minimal"` setzt „Privatangebot“ (Datenminimierung) | `advertiser_names="legacy"` – Standard nach Nutzerentscheidung PS-D03 vom 23.09.2026 | `test_i9_…` |
| Abruf ohne robots.txt-Prüfung (PS-C08) | `"respect"` verweigert gesperrte Adressen | `robots_policy="ignore"` – Standard nach Nutzerentscheidung PS-D01 | `tests/test_robots.py`, `test_i8_…` |
| Modulglobale Zuordnungen aus Dateien (PS-C01), Baujahrprüfung gegen die Systemuhr (PS-C04), Koordinaten aus Nominatim (PS-C05) | ausdrücklich übergebene Zuordnungen, Bezugsjahr, keine Koordinaten | – | Replay |
| Stilles Überspringen defekter Einträge (PS-C06) | zusätzlich `RecordIssue` | – | `tests/test_adapters.py` |

Keine offenen Befunde aus den Eigenschaftstests.
