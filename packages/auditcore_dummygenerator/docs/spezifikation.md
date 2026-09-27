# Spezifikation auditcore_dummygenerator

Stand: 26.09.2026, Paketversion 0.1.3. Charakterisierung: 58 am Original
beobachtete Fälle (`tests/fixtures/legacy_observed.json`, Aufzeichnung mit
`tools/capture_legacy.py`), technische Altdefekte der Parallelverarbeitung in
`tests/fixtures/legacy_technical_defects.json`. Eigenschaftstests:
`tests/test_spezifikation.py`.

## Zweck

Das Paket erzeugt reproduzierbare synthetische Testdaten – einzelne Felder
(Namen, Anschriften, Kennungen, Beträge, Datumswerte, Texte) und ganze Zeilen
nach einer Feldliste. Es dient Anwendungen und Bibliotheken, die Testfälle für
Prüfsoftware brauchen (etwa `auditcore_invoicegenerator` oder
Testdatengeneratoren für Beleglisten), und erzeugt ausdrücklich keine echten
oder gültigen Stammdaten. HTTP, Dateiexporte, Oberfläche und Rechte bleiben bei
der Anwendung.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `TestDataGenerator(seed=None, *, base_date=None, max_workers=None, use_joblib=None)` | Seed (`int` oder `None`), Bezugsdatum für `date_after` ohne Referenzfeld, Obergrenze der Worker (≥ 1), Backendwahl | Generatorinstanz mit eigener `random.Random`-Quelle | keine; der globale Zufallszustand bleibt unberührt |
| `generate_first_name`, `generate_last_name`, `generate_street`, `generate_city`, `generate_postal_code`, `generate_phone` | Länderwert | Wert aus dem AT-Katalog bei `"AT"`, sonst aus dem DE-Katalog; `generate_city` liefert `(Stadt, PLZ)` | ein bis mehrere Zufallsziehungen |
| `generate_iban`, `generate_bic`, `generate_ustid` | Länderwert | Zeichenketten in IBAN-, BIC- bzw. USt-IdNr.-Form (AT oder DE) | – |
| `generate_date_range(start, end)` | ISO-Daten `JJJJ-MM-TT` | ISO-Datum im geschlossenen Bereich | – |
| `generate_date_after(ref, min_days, max_days)` | ISO-Datum und ganzzahliger Versatzbereich | ISO-Datum `ref + Versatz` | – |
| `generate_amount(min, max, decimals=2)` | Zahlbereich, Nachkommastellen | `float`, gerundet mit Pythons `round` | – |
| `generate_number(min, max)`, `generate_boolean()`, `generate_weighted_choice(items)`, `generate_invoice_no(pattern)`, `generate_company()`, `generate_purpose_text(min, max)` | wie benannt | Wert des jeweiligen Typs | – |
| `generate_field(type, params, country, row)` | Feldtyp, Parameter, Land, bisher erzeugte Zeilenwerte (Referenzfelder) | Feldwert; unbekannter Typ → `""` | – |
| `apply_deviation(row, scenario, rate)` | Zeile, Szenario `NONE`, `FOERDERFAEHIG_GT_GEZAHLT`, `BEZAHLT_VOR_RECHNUNG`, `NEGATIVE_AMOUNTS`, Rate 0…1 | dieselbe, ggf. veränderte Zeile | verändert `row` an Ort und Stelle |
| `generate_rows(request)` | Anfrage `{"rows", "countries", "fields", "deviation", "beleglisteOptions"}` | Liste von Zeilen (Dictionaries) | ab 1 000 Zeilen Prozesspool (`spawn`) oder joblib, sonst keine |
| `list_profiles()`, `profile_reference(id)` | – bzw. Profilkennung | Profil-Metadaten mit Version, Status `DRAFT`, Inhalts- und Implementierungshash | liest die mitgelieferte `profiles.json` |

Determinismus: Eine frische Instanz mit gleichem Seed, gleichem Bezugsdatum und
gleicher Anfrage erzeugt dieselbe Ausgabe; wiederholte Aufrufe derselben
Instanz setzen die Zufallsfolge fort. Der Parallelweg zerlegt die Anfrage in
geordnete Batches mit den Seeds `seed + i · 1000`; seine Ausgabe unterscheidet
sich von der sequenziellen.

Profile: 27 Feld-, Abweichungs- und Katalogprofile in `profiles.json`, Version
0.1.0, Status Draft; der Implementierungshash bindet sie an die Bytes von
`generator.py` (Regeln: `docs/profile-versioning.md`).

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Frische Instanz, gleicher Seed, gleiches Bezugsdatum und gleiche Anfrage ergeben dieselben Zeilen. | `test_i1_same_seed_and_reference_date_give_same_rows` |
| I2 | `generate_rows` liefert genau `rows` Zeilen; jede Zeile enthält genau die Feldnamen der Anfrage in deren Reihenfolge. | `test_i2_row_count_and_field_order` |
| I3 | Beträge (`generate_amount`) und Zahlen (`generate_number`) liegen im geschlossenen Intervall der Parameter; Beträge haben höchstens `decimals` Nachkommastellen. | `test_i3_amounts_and_numbers_stay_in_range` |
| I4 | Ein Auto-Increment-Feld zählt je Zeile von `start` um `step` weiter. | `test_i4_auto_increment_counts_from_start_by_step` |
| I5 | IBAN: `DE` + 2 + 18 Ziffern bzw. `AT` + 2 + 16 Ziffern; BIC: 4 Buchstaben, Ländercode, 5 Zeichen `A–Z0–9`; USt-IdNr.: `DE` + 9 bzw. `ATU` + 8 Ziffern. Jeder Länderwert außer `AT` gilt als DE. Eine Prüfziffernrichtigkeit wird **nicht** zugesagt. | `test_i5_identifiers_have_the_documented_shape` |
| I6 | `generate_date_range` liegt im geschlossenen Bereich; `generate_date_after` liegt `min_days…max_days` Tage nach dem Referenzdatum. | `test_i6_dates_stay_in_their_ranges` |
| I7 | `generate_city` liefert ein zusammengehöriges Stadt-/PLZ-Paar aus dem Katalog des Landes. | `test_i7_city_and_postal_code_come_from_the_country_catalog` |
| I8 | Abweichungen entstehen nur auf Verlangen: Rate 0 oder Szenario `NONE` lassen die Zeile gleich; `NEGATIVE_AMOUNTS` mit Rate 1 macht jeden Betragswert ≤ 0 und lässt andere Felder unverändert. | `test_i8_deviation_only_as_requested` |
| I9 | Die Parallelbatches decken die Zeilen 0…`rows`−1 lückenlos und überschneidungsfrei ab, ihre Größen unterscheiden sich um höchstens 1, die Seeds sind `seed + i · 1000`. | `test_i9_parallel_batches_cover_all_rows_once` |
| I10 | `profile_reference` nennt für jedes Profil dieselbe Version und denselben Inhaltshash wie das geprüfte Register; Profilkennungen sind eindeutig. | `test_i10_profile_references_match_the_registry` |

## Fehlerfälle

| Eingabe | Ergebnis |
|---|---|
| `max_workers < 1`, `n_workers < 1`, Umgebungsvariable `MAX_WORKERS < 1` | `ValueError` |
| `use_joblib=True` ohne Extra `[parallel]` | `ImportError` |
| ungültiges oder vertauschtes Datum in `generate_date_range`, vertauschte Grenzen in `generate_number` | `ValueError` (aus der Standardbibliothek) |
| Worker scheitert oder liefert weniger Zeilen | `BatchGenerationError` mit Ursache; es gibt kein Teilergebnis |
| veränderte `profiles.json` (Inhalts- oder Implementierungshash passt nicht), doppelte Kennung | `ValueError` |
| unbekannte Profilkennung in `profile_reference` | `KeyError` |
| unbekannter Feldtyp | kein Fehler: Wert `""` (Altverhalten, siehe unten) |

## Abgrenzung

- Keine gültigen Kennungen: Wer prüfziffernrichtige IBAN, USt-IdNr. oder
  Steuernummern braucht, nutzt `auditcore_identifiers` zur Prüfung oder eigene
  Testvektoren.
- Keine echten Personen- oder Firmendaten; Kataloge sind fest und synthetisch,
  zufällige Übereinstimmungen mit realen Personen sind möglich.
- Keine Rechnungen als Ganzes (dafür `auditcore_invoicegenerator`), keine
  Dateiformate (CSV, XML, Excel) und keine HTTP-Schnittstelle – das bleibt bei
  der Anwendung.
- Keine fachliche Prüfung der Anfrage über Schlüsselzugriffe hinaus.

## Bewusste Abweichungen vom Altverhalten

Die Datenerzeugung ist legacy-exakt; abgewichen wird nur in der technischen
Parallelverarbeitung (`tests/fixtures/legacy_technical_defects.json`).

| Altverhalten | Gewolltes Verhalten | Nachweis |
|---|---|---|
| Worker rief den Parallel-Dispatcher erneut auf | Worker erzeugen ihren Batch sequenziell | `tests/test_generator.py` |
| Worker veränderten verschachtelte Auto-Increment-Parameter der Anfrage | Worker arbeiten auf einer tiefen Kopie | `tests/test_generator.py` |
| Backendfehler ergaben still eine leere oder unvollständige Liste | `BatchGenerationError` | `tests/test_generator.py` |
| Prozesspool mit `fork` | `spawn` | `tests/test_generator.py` |
| Workergrenzen < 1 wurden hingenommen | `ValueError` | `tests/test_generator.py` |

Beibehaltene Altfehler (Legacy-Varianten, nicht für neue fachliche Annahmen
gedacht):

| Legacy-Variante | Verhalten | Empfehlung |
|---|---|---|
| `TestDataGenerator.generate_postal_code` | zieht die PLZ unabhängig von einer zuvor gezogenen Stadt; Stadt und PLZ einer Zeile passen daher meist nicht zusammen | für zusammengehörige Anschriften `generate_city` verwenden (I7) |
| `TestDataGenerator.generate_amount` | binäre `float`-Werte mit Pythons `round` (Banker's Rounding auf Binärdarstellung), keine Dezimalarithmetik | für exakte Beträge in Tests auf `Decimal` umrechnen |
| `TestDataGenerator.apply_deviation` | verändert die übergebene Zeile an Ort und Stelle und gibt sie zurück | bei Bedarf vorher kopieren |
| `TestDataGenerator.generate_field` | unbekannte Feldtypen liefern `""` statt eines Fehlers; `date_after` ohne Referenzfeld und ohne `base_date` nutzt das lokale Tagesdatum | Feldtypen in der Anwendung prüfen, `base_date` immer setzen |
