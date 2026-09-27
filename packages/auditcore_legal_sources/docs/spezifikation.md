# Spezifikation auditcore_legal_sources

Stand: 26.09.2026, Paketversion 0.1.5. Charakterisierung: 176 Replay-Fälle
beider Quellanwendungen (`tests/fixtures/legacy_harvesters_observed.json`,
`tests/test_legacy_replay.py`) und 12 Feedfälle
(`tests/fixtures/legacy_feeds_observed.json`, `tests/test_feeds.py`).
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket prüft Antworten von Rechts-, Parlaments- und Prüfquellen (Bundestag
DIP, EUR-Lex/Cellar, BaFin, CURIA, Europäischer Rechnungshof) und
normalisiert sie zu `LegalDocument` mit stabiler Identität, Contenthash,
geparstem Publikationsdatum und Profilreferenz. Es dient Wissens- und
Rechercheanwendungen jeder Prüfbehörde; Abruf, Seitenfolge, Wiederholungen,
Rate-Limits und Checkpoints übernimmt `auditcore_harvest`, Speicherung und
Zeitplanung bleiben bei der Anwendung.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `load_profile(id, version)` | ausdrücklich genannte Profilkennung und Version | unveränderliches `SourceProfile` mit Fingerprint (SHA-256 des kanonischen Profil-JSON) | liest nur Paketdaten; kein Standardprofil |
| `normalize.parse_publication_date(value)` | `date`/`datetime` oder Text `JJJJ-MM-TT[T…]`, `JJJJ-MM`, `TT.MM.JJJJ`, `JJJJ` | `(date, "day"\|"month"\|"year")` oder `(None, None)` | keine |
| `normalize.funding_period_auditdatabase(text)` / `funding_period_designer(text, publication_date)` | Text, beim Designer zusätzlich Publikationsdatum | Förderperiode oder `None` | keine; zwei getrennte, benannte Regeln |
| `normalize.detect_fund`, `is_relevant`, `deduplicate` | Text bzw. Dokumente | Fonds, Wahrheitswert, (behaltene Dokumente, verworfene Identitäten) | keine |
| `dip.auth_header_value(key)` | API-Schlüssel des Credential-Providers | Headerwert `ApiKey …` | keine |
| `dip.drucksache_query(profile, keyword, cursor=, updated_since=)` | Profil, Suchbegriff, Cursor, `date` | Query-Parameter ohne Zugangsdaten | keine |
| `dip.parse_page(payload)` / `normalize_page(page, profile)` | JSON-Antwort `{"numFound","cursor","documents"}` | `DipPage`; (Dokumente, `ParseError` je defektem Eintrag) | keine |
| `eurlex.sparql_form`, `update_query(profile, since)` | Abfragetext bzw. Profil und `date` | Formularfelder bzw. Abfrage aus fester Profilvorlage | keine |
| `eurlex.parse_results`, `merge_rows`, `normalize_row` | W3C-SPARQL-JSON bzw. Zeilen | Zeilen, zusammengeführte Zeilen, `LegalDocument` | keine |
| `feeds.parse_feed(text)` (Extra `feeds`) | RSS/Atom | feedparser-Einträge | keine |
| `feeds.normalize_entry(entry, profile, key, feed)`, `normalize_entries`, `select_relevant`, `publication_links` | Feedeintrag bzw. HTML-Übersichtsseite | `LegalDocument` | keine |
| `adapters` | Harvest-Adapter `legal.dip_bundestag`, `legal.eurlex`, `legal.bafin`, `legal.curia`, `legal.eca` | Datensätze nach Adaptervertrag 1 von `auditcore_harvest` | Netz nur über den Transport des Hosts |

Alle Funktionen außer den Adaptern sind rein und deterministisch.
`LegalDocument.identity` ist `"<source_id>:<external_id>"`,
`content_hash` der SHA-256 von `content`, sonst `abstract`, sonst `title`
(quellkompatible Definition).

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Jede unterstützte Schreibweise eines Kalenderdatums wird mit ihrer Genauigkeit zurückgelesen (ISO-Tag und -Zeitpunkt → `day`, `TT.MM.JJJJ` → `day`, `JJJJ-MM` → Monatserster/`month`, `JJJJ` → 1. Januar/`year`). | `test_i1_publication_date_roundtrip` |
| I2 | Alle anderen Eingaben ergeben `(None, None)`; ungültige Kalenderdaten (30. Februar) werden nicht „repariert“. Datum und Genauigkeit sind nur gemeinsam gesetzt. | `test_i2_publication_date_never_guesses` |
| I3 | Identität ist `source_id:external_id`; der Contenthash folgt der Reihenfolge Inhalt → Zusammenfassung → Titel; `to_dict()` ist JSON-tauglich. | `test_i3_identity_and_content_hash` |
| I4 | `deduplicate` behält je Identität genau das erste Dokument in Eingabereihenfolge, zählt jedes verworfene und ist idempotent. | `test_i4_deduplicate_first_occurrence_wins` |
| I5 | Jeder DIP-Eintrag wird entweder Dokument (mit nicht leerem Titel, `dip_<id>`, Profilreferenz) oder `ParseError` mit Fundort `documents[i]`; nichts geht verloren. Die Klassifikation trägt `heuristic: true` genau beim Profil mit Regel `auditdatabase.dip`. | `test_i5_dip_items_are_documents_or_located_errors` |
| I6 | Der DIP-Schlüssel steht nur im Header; leere und mehrzeilige Schlüssel werden abgewiesen; die Query-Parameter enthalten nie Zugangsdaten. | `test_i6_dip_credentials_never_in_the_query` |
| I7 | Feed-Identitäten sind `<quelle>_<SHA-256(id oder link)[:16]>`, unabhängig von Titel und Text; ohne `id` und `link` gibt es keine Identität (`ParseError`). | `test_i7_feed_identity_depends_only_on_id_or_link`, `test_i7_entry_without_id_and_link_is_rejected` |
| I8 | Die Förderperiodenregeln liefern nur bekannte Perioden; die Jahresregel des Designers ordnet ein Jahr der jüngsten Periode zu, die nicht später beginnt, vor 1994 keiner. | `test_i8_funding_period_rules_are_closed` |
| I9 | `merge_rows`: Kerndokumente zuerst, jede CELEX-Nummer genau einmal, Zeilen ohne CELEX entfallen, keine CELEX kommt hinzu. | `test_i9_eurlex_core_documents_first_celex_unique` |
| I10 | `update_query` setzt genau das ISO-Datum in den einzigen Platzhalter der Profilvorlage; Text statt Datum und Profile ohne Vorlage werden abgewiesen. | `test_i10_update_query_inserts_exactly_the_date`, Befund LS-S1: `test_i10_update_query_rejects_datetimes` (xfail) |
| I11 | Der CELEX-Dokumenttyp ist für jeden Text definiert und stammt aus der festen Liste Unbekannt, Verordnung, Richtlinie, Beschluss, Guidance, Rechtsprechung, Sonstiges. | `test_i11_celex_type_is_total` |
| I12 | Relevanz ist ein Teilstring-Abgleich ohne Groß-/Kleinschreibung gegen ausdrücklich übergebene Suchbegriffe; ohne Begriffe ist nichts relevant. | `test_i12_relevance_is_case_insensitive_substring` |

## Fehlerfälle

| Fall | Ergebnis |
|---|---|
| Profil unbekannt, Name mit Pfadtrenner oder führendem Punkt, Schema- oder Feldfehler, Seitengröße außerhalb 1…100, Vorlage ohne genau einen `{since}` | `ProfileError` |
| DIP-Schlüssel leer/mehrzeilig, Suchbegriff leer, Suchbegriffe außerhalb des Profils, fehlende Feedquelle, fremder Feedname, fehlende Aktualisierungsvorlage, Startdatum kein `date` | `ConfigurationError` (Code `NOT_CONFIGURED` im Adapter) |
| DIP-Antwort kein Objekt oder ohne Dokumentliste; Eintrag ohne ID/Titel | `ParseError` (Seite bzw. je Eintrag mit Fundort) |
| SPARQL-Antwort ohne `results.bindings`, Binding kein Objekt, Wert ohne `value`; EUR-Lex-Zeile ohne CELEX | `ParseError` |
| Feed nicht lesbar (bozo ohne Einträge), Eintrag ohne Titel oder ohne `id`/`link` | `ParseError` |
| Nicht auswertbares Datum | `publication_date = None`, Rohwert bleibt in `raw_date` |

Kein Fehler wird in ein leeres Erfolgsergebnis verwandelt.

## Abgrenzung

- Kein eigener Netzabruf, keine Wiederholungen, kein Scheduler, keine
  Datenbank: das leisten `auditcore_harvest` und die Anwendung.
- Keine Zugangsdatenverwaltung: der DIP-Schlüssel kommt aus dem
  Credential-Provider des Hosts.
- Kein HTML-Volltextabruf, keine Vorgangsabfrage (`get_vorgang`) und keine
  Verbindungsprüfung wie in den Quellanwendungen.
- Keine fachliche Bewertung: Fonds- und Periodenregeln sind benannte
  Quellregeln, die DIP-Klassifikation ist als Heuristik gekennzeichnet.
- Profile verschiedener Anwendungen werden nicht zusammengeführt.

## Bewusste Abweichungen vom Altverhalten

Vollständige Liste LS-C01 bis LS-C15 in
[behavior-changes.md](behavior-changes.md). Die Altfassungen bleiben im
Modul `legacy` verhaltensgleich erhalten (Replay), sind aber nicht für neue
Aufrufer gedacht:

| Altverhalten | Gewollt | Legacy-Variante | Nachweis |
|---|---|---|---|
| Jede Datumszeichenkette ergibt `None` (Zuschnittfehler, LS-C01) | Datum wird geparst (I1, I2) | `legacy.legacy_parse_date` | Replay, `test_i1_…` |
| Fehlgeschlagene DIP-Suchen melden Erfolg mit 0 Dokumenten (LS-C05), defekte Einträge werden „Ohne Titel“ (LS-C03) | Fehler je Seite/Eintrag (I5) | `legacy.legacy_dip_harvest`, `legacy.legacy_dip_normalize` | Replay, `test_i5_…` |
| API-Schlüssel als Query-Parameter (LS-C02) | nur Header (I6) | `legacy.legacy_dip_query` | `test_i6_…` |
| Feed-Identität aus prozessabhängigem `hash()` (LS-C10), pauschal `EFRE`/`2021-2027` (LS-C14), CURIA-Rückfall auf allgemeine Einträge (LS-C15) | SHA-256-Identität (I7), keine erfundene Klassifikation, expliziter Filter (I12) | `legacy.legacy_bafin_entry`, `legacy.legacy_curia_entry` | `tests/test_feeds.py`, `test_i7_…` |
| ECA-Platzhalterberichte bei nicht lesbarer Seite (LS-C13) | keine Ersatzinhalte | `legacy.legacy_eca_core_reports` | `tests/test_feeds.py` |
| Aktualisierungsabfrage per f-String aus `datetime` (LS-C09) | nur `date`, feste Vorlage (I10) | `legacy.legacy_update_query` | Replay, `test_i10_…` |

**Befund LS-S1 (offen):** `eurlex.update_query` prüft `isinstance(since,
date)`; da `datetime` eine Unterklasse von `date` ist, wird ein Zeitpunkt
angenommen und als `"2024-01-02T03:04:00"^^xsd:date` in die Abfrage gesetzt –
ein ungültiges `xsd:date`-Literal, entgegen LS-C09 („nur `date`-Objekte“).
Festgehalten als `xfail(strict=True)` in
`test_i10_update_query_rejects_datetimes`; die Korrektur (Ablehnung oder
`as_date`) ist eine Verhaltensänderung und bleibt einer eigenen Änderung
vorbehalten.
