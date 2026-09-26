# Spezifikation auditcore_price_analysis

Stand: 26.09.2026, Paketversion 0.1.3, Vertrag `auditcore_price_analysis.contract/1`.
Charakterisierung: 274 tatsächlich ausgeführte Fälle von regulierung
(`tests/fixtures/regulierung_calculator_observed.json`, `tests/test_legacy_replay.py`,
`tests/test_contract_vs_legacy.py`); Abweichungen in
[`behavior-changes.md`](behavior-changes.md) (PA-L01…L17, PA-C01, Entscheidungen PA-H01…H04).

## Zweck

Das Paket berechnet Jahreskosten regulierter Tarife (Nahwärme, Wasser mit
Staffeln) exakt in Dezimalzahlen, wählt für einen Stichtag deterministisch den
maßgeblichen Tarif und liefert Vergleichsregeln (prozentuale Abweichung,
Ampel, Gruppenkennzahlen). Es dient Preisaufsicht und Preisprüfung, die
Tarife verschiedener Anbieter nachvollziehbar vergleichen. Alle Regeln stammen
aus ausdrücklich gewählten, versionierten Profilen; die Bibliothek gibt nie
einen Preis frei und greift nicht auf das Netz zu.

## Verträge

| Schnittstelle | Eingabe | Ausgabe |
|---|---|---|
| `load_calculation_profile(id, version)`, `load_comparison_profile(id, version)`, `load_recommended_*` | Profilkennung, Version | unveränderliches Profil mit `reference` |
| `parse_decimal(wert, *, field)` | `int`, `Decimal`, endliches `float`, Zahltext mit Punkt oder in deutscher Schreibweise | exakte `Decimal` |
| `Rounding(places, mode).apply(x)` | Schritt > 0, Modus `ROUND_HALF_UP`/`HALF_EVEN`/`DOWN`/`UP` | einmal gerundeter Wert |
| `Tariff.from_mapping(daten, profil, …)` | Preisbestandteile des Profils (fehlend = `None`, `0` = nicht erhoben), Staffel, Gültigkeit, Freigabestatus | `Tariff` |
| `tiered_amount(stufen, menge, *, open_last)` | sortierte Stufen, Menge ≥ 0 | Betrag, Stufennutzung, „über letzter Grenze“ |
| `calculate(tarif, profil, *, consumption, stichtag)` | jede Verbrauchsgröße des Profils ausdrücklich, Stichtag als Kalendertag | `CalculationResult`: Zeilen mit Status (`angegeben`, `fehlt`, `gestaffelt`, `nicht_anwendbar`), exakte und gerundete Summe, Untergrenzen-Kennzeichen, Vergleichbarkeit mit Gründen, Mischpreis, Fix-/Variabelanteil, Hinweise |
| `select_tariff(kandidaten, *, stichtag, profile, q3=None)` | Tarife, Stichtag, Vergleichsprofil, Zählergröße | `Selection`: Tarif oder `None`, `datenstatus` (`ok`, `nicht_verfuegbar_fuer_q3`, `kein_tarif`), Mehrdeutigkeit, ausgeschlossene Zeilen mit Grund |
| `delta_pct(wert, referenz, profil)` | Zahlen | `(wert − referenz) / referenz × 100`, gerundet, oder `None` |
| `traffic_light(wert, median, profil)` | Zahlen | `gruen`/`gelb`/`rot` oder `None` |
| `group_statistics(werte, profil)` | Zahlen ohne `None` | Anzahl, Median, Mittelwert, Standardabweichung (Grundgesamtheit oder Stichprobe laut Profil), Minimum, Maximum |

Alle Funktionen sind rein und deterministisch.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | `Decimal`, `int` und einfacher Punkttext behalten ihren exakten Wert. | `tests/test_spezifikation.py::test_i1_numbers_are_read_exactly` |
| I2 | Deutsche Schreibweise („1.234,56“, „1234,56 €“) wird exakt gelesen; drei Nachkommastellen nach einem einzelnen Komma werden nicht geraten. | `test_i2_german_notation_is_read_and_ambiguity_rejected` |
| I3 | Fehlt ein Wert, ist er nie 0: `None` → `missing_value`; Wahrheitswerte, nicht endliche Werte und Exponenten → `invalid_number`. | `test_i3_missing_is_never_zero` |
| I4 | Eine Rundungsregel verschiebt einen Wert um höchstens einen halben Schritt und ist idempotent. | `test_i4_rounding_is_idempotent_and_within_half_a_step` |
| I5 | Mit offener letzter Stufe wird jede Mengeneinheit genau einmal abgerechnet, der Betrag ist die exakte Summe Menge × Preis je Stufe und steigt mit der Menge nie ab; ohne offene letzte Stufe ist Menge über der letzten Grenze ein Fehler. | `test_i5_tiers_bill_every_unit_once_and_monotonically` |
| I6 | Die Summe ist die exakte Summe der Zeilenbeträge, die gerundete Summe genau einmal gerundet; jeder fehlende Bestandteil macht die Summe zur Untergrenze und wird benannt; vergleichbar genau dann, wenn kein Grund vorliegt; nicht freigegebene Tarife sind nie vergleichbar; ohne Verbrauch kein Mischpreis. | `test_i6_total_is_the_exact_sum_and_missing_is_a_lower_bound` |
| I7 | Ohne positive Referenz keine Abweichung; sonst folgt ihr Vorzeichen `wert − referenz`. | `test_i7_deviation_has_the_sign_of_the_difference` |
| I8 | Die Ampel ist im Wert monoton (höherer Wert nie mildere Farbe); ohne positiven Median keine Ampel. | `test_i8_traffic_light_is_monotone` |
| I9 | Gruppenkennzahlen: Minimum ≤ Median, Mittelwert ≤ Maximum, Standardabweichung ≥ 0, unabhängig von der Reihenfolge; leere Gruppe → `None`. | `test_i9_group_statistics_are_ordered_and_order_free` |
| I10 | Die Tarifauswahl ist unabhängig von der Eingabereihenfolge und wählt nur Tarife, die am Stichtag gelten und (laut Profil) freigegeben sind. | `test_i10_selection_is_deterministic_and_only_picks_eligible` |
| I11 | `legacy_parse_decimal` stimmt bei Punkttext mit `parse_decimal` überein und lehnt jedes Komma ab. | `test_i11_legacy_reader_rejects_every_comma` |
| I12 | Fix- und Variabelanteil werden getrennt gerundet; ihre Summe weicht von 100 höchstens um einen Rundungsschritt ab; ohne Kosten sind beide `None`. | `test_i12_fixed_and_variable_share_differ_from_100_by_at_most_one_step`, `test_i12_shares_can_add_up_to_100_1` |

## Fehlerfälle

`PriceAnalysisError` (Unterklasse von `ValueError`) mit stabilem `code`:

| Code | Anlass |
|---|---|
| `missing_value` | Pflichtwert oder Verbrauchsgröße fehlt (`None`), Staffelstufe ohne Preis |
| `invalid_number` | Wahrheitswert, falscher Typ, Exponent, nicht endlich, unlesbarer Text |
| `ambiguous_number` | deutsche Schreibweise mehrdeutig (z. B. „1,234“) |
| `negative` | negativer Preis oder Verbrauch |
| `invalid_date` | Stichtag kein Kalendertag `JJJJ-MM-TT` (auch `datetime`) |
| `unknown_component`, `unknown_consumption` | Preis- oder Verbrauchsschlüssel, die das Profil nicht kennt |
| `invalid_tiers` | unbekannte Staffelform, Grenze ≤ 0, doppelte Grenze, offene Stufe vor der letzten |
| `beyond_last_tier` | Verbrauch über der letzten Grenze bei Profil ohne `open_last` |
| `profile_mismatch`, `mixed_kinds` | Tarifart passt nicht zum Profil; Kandidaten verschiedener Arten |
| `ProfileError` | Profil unbekannt oder fehlerhaft, Rundungsschritt ≤ 0, unbekannter Rundungsmodus |

Kein Fehler, sondern `None`: Abweichung und Ampel ohne positive Referenz,
Mischpreis bei Verbrauch 0, Anteile bei Kosten 0, Kennzahlen einer leeren Gruppe.

## Abgrenzung

- Freigabe (Vier-Augen-Prinzip), Speicherung und Abruf der Preisdaten bleiben
  in der Anwendung; die Bibliothek liest nur den erfassten Freigabestatus.
- Die Ampel ist ein algorithmisches Signal ohne Rechtsfolge.
- Welche Ergebnisse zu einer Vergleichsgruppe gehören, entscheidet der Aufrufer.
- Standardverbräuche (`standard_consumption`) sind benannte Profilwerte, keine
  stillen Vorgaben: `calculate` verlangt jede Verbrauchsgröße ausdrücklich.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten (regulierung) | Gewollter Vertrag | Legacy-Variante | Nachweis |
|---|---|---|---|
| Fehlender Verbrauch oder Preisbestandteil zählt still als 0 (PA-L01/L02/L03) | `missing_value` bzw. Untergrenze mit `missing_optional` | `legacy.calculate_nahwaerme`, `legacy.calculate_wasser` | I3, I6 |
| Gleitkomma und Banker's Rounding in Abweichung, Ampel, Kennzahlen (PA-L11…L13) | exakte Dezimalrechnung, `ROUND_HALF_UP`, `None` ohne Referenz | `legacy.calculate_delta`, `legacy.determine_compliance`, `legacy.calculate_cluster_statistics` | I7–I9 |
| Q3-Toleranz im Gleitkomma, `valid_to` unbeachtet (PA-L17, PA-H04) | exakter Vergleich `< 0,01`; `valid_to` beachtet (Profil 2026.09.2) | `legacy.waehle_preis_deterministisch`, `legacy.waehle_wasser_preis`, Profil `regulierung.hpp.vergleich` 2026.09.1 | I10 |
| Nur Punkttext, jedes Komma abgelehnt (bis 0.1.1, PA-C01) | deutsche Schreibweise lesen, Mehrdeutiges ablehnen | `legacy_parse_decimal` | I2, I11 |
| Rechner-Vorgaben 150 m³ bzw. Profilstände vor den Entscheidungen | empfohlene Profile 2026.09.2 | Profile `regulierung.hpp.nahwaerme` 2026.09.1, `regulierung.hpp.wasser` 2026.09.1 | Replays |

Legacy-Funktionen und -Profile reproduzieren das Original bitgenau für die
Umstellung bestehender Aufrufer; neue Aufrufer nutzen den Vertrag oben.

**Befund aus den Eigenschaftstests (26.09.2026, dokumentiert, Code unverändert):**
Fix- und Variabelanteil werden je für sich mit `ROUND_HALF_UP` auf 0,1 gerundet.
Liegen beide genau auf der Hälfte (33,35 % / 66,65 %), ergibt die Summe
100,1 % (Beispiel in I12). Das entspricht der Regel „jede Zeile einzeln
runden“ (PA-L10); wer eine Summe von genau 100 braucht, bildet den zweiten
Anteil als `100 − Fixanteil`.
