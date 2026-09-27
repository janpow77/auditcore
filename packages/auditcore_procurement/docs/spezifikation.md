# Spezifikation auditcore_procurement

Stand: 26.09.2026, Paketversion 0.2.4, Datensatzvertrag `auditcore_procurement.notice/1`.
Charakterisierung: tatsächlich ausgeführtes Original (`tools/capture_procurement_legacy.py`,
`tests/fixtures/procurement_legacy_observed.json`, `tests/test_legacy_replay.py`),
Schwellenwerte je Jahr (`tests/test_year_thresholds.py`, `tests/test_historic_thresholds.py`);
Abweichungen in [`behavior-changes.md`](behavior-changes.md) (P-C01…P-C12).

## Zweck

Das Paket bildet Vergabebekanntmachungen (TED, HAD) auf einen kanonischen
Datensatz ab und führt deterministische, versionierte **Vergabe-Vorprüfungen**
aus: Einordnung des geschätzten Auftragswerts in Schwellenwertstufen,
Verfahrenswahl, Pflichtdokumente, Mindestangebote und Abweichung zwischen
Vertrags- und Abrechnungswert. Es dient Prüfbehörden, Verwaltungsbehörden und
zwischengeschalteten Stellen aller ESI-Fonds bei der Vorbereitung einer
vergaberechtlichen Prüfung. Die Vorprüfung **meldet Regelergebnisse, sie
entscheidet keinen Vergabefall**.

## Verträge

| Schnittstelle | Eingabe | Ausgabe |
|---|---|---|
| `normalize_notice(notice, *, require_contractor=True)` | TED-v3-Objekt | flacher Datensatz mit Feldern aus `NOTICE_FIELDS` oder `None` (kein Objekt; ohne Auftragnehmer bei `require_contractor=True`) |
| `normalize_notices`, `parse_ted_file`, `build_ted_query` | Liste, Datei, Filter | Datensätze, Kopfzeilen/Fehler, TED-Suchausdruck mit Abdeckungskennzeichen |
| `inspect_notice(notice)` | TED-Objekt | Hinweise (`ambiguous_amount` blockierend, `unparsed_amount`, `unparsed_date`, `no_contractor`, `correction_notice`); verändert nichts |
| `validate_record(record, *, require_contractor=True)` | Datensatz | Hinweise `unknown_field`, `not_numeric`, `not_text`, `not_iso_date`, `missing_contractor` |
| `load_profile(id, version)` | ausdrücklich benanntes Profil | `PrecheckProfile` mit `reference` (Kennung, Version, Fingerabdruck) |
| `run_prechecks(profil, geschätzt, vertrag, abrechnung, leistungsart, vergabeart, stufe, dokumente, *, mode, now, reference_date, year, authority_type)` | Beträge als `Decimal` oder `None`, Dokumente mit `procurement_doc_type` | Bericht: `checks` (je Prüfung `check_id`, `status`, Meldung, Belege), `overall_status`, `timestamp`; in `strict` zusätzlich `mode` und `profile` |
| `ted_company_result`, `had_result` | HTTP-Status und Antwort | `SearchResult` mit Status `ok`, `no_hit`, `rate_limited`, `failed` |

Status der Prüfungen: `PASS`, `WARNING`, `FAIL`, `NOT_CHECKED`,
`REVIEW_REQUIRED` (nur `strict`). Modi: `legacy` (Quellverhalten) und
`strict` (korrigierter Vertrag). In `strict` wählt das Profil
`procurement.hvtg` (Schema 2) den EU-Schwellenwert des Geltungszeitraums über
`reference_date` (Datum der Maßnahme bzw. Bekanntmachung) oder `year`; der
Schwellenwert gilt ab Erreichen (§ 106 Abs. 1 Satz 1 GWB, Art. 4 RL 2014/24/EU),
für Liefer- und Dienstleistungen getrennt nach zentralen und sonstigen
Auftraggebern. Nationale Stufen (`BELOW_1K`, `BELOW_25K`) sind Regeln der
Anwendungen mit Status `REVIEW_REQUIRED`, keine Normwerte.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | `normalize_notice` ist deterministisch, liefert für Nicht-Objekte `None` und nur Felder aus `NOTICE_FIELDS`; mit `require_contractor` immer einen Auftragnehmer. | `tests/test_spezifikation.py::test_i1_normalized_records_use_only_contract_fields` |
| I2 | `require_contractor=True` liefert denselben Datensatz wie `False` oder `None`, nie einen anderen. | `test_i2_contractor_filter_only_drops_records` |
| I3 | Normalisierte Datensätze bestehen die Typ- und Datumsprüfung von `validate_record` (Beträge sind Zahlen, Datumsangaben ISO, keine unbekannten Felder). | `test_i3_normalized_records_pass_the_record_check_on_types_and_dates` |
| I4 | Beträge in deutscher Schreibweise („1.234,56“) werden als blockierend mehrdeutig gemeldet; `inspect_notice` verändert die Bekanntmachung nicht. | `test_i4_german_amounts_are_reported_not_altered` |
| I5 | Aus mehreren Beträgen wird der größte übernommen (Quellregel). | `test_i5_amount_lists_yield_the_largest_amount` |
| I6 | `strict`: Erreicht oder überschreitet der Wert den EU-Schwellenwert des Zeitraums, ist die Stufe die oberhalb der EU-Schwelle, sonst nie. | `test_i6_eu_threshold_applies_when_reached` |
| I7 | `strict`: Ohne Stichtag oder ohne belegten Zeitraum lautet das Ergebnis `REVIEW_REQUIRED`, nie ein Rückgriff auf einen anderen Zeitraum. | `test_i7_no_period_means_review_not_fallback` |
| I8 | Der Gesamtstatus ist der schlechteste Einzelstatus (`FAIL` > `REVIEW_REQUIRED` > `WARNING` > `PASS`); gleiche Eingabe mit gleichem `now` ergibt denselben Bericht; `strict` nennt das Profil, `legacy` kennt kein `REVIEW_REQUIRED`. | `test_i8_overall_status_is_the_worst_and_runs_are_reproducible` |
| I9 | Pflichtdokumente: `PASS` genau dann, wenn jede geforderte Art mindestens so oft vorliegt wie gefordert. | `test_i9_required_documents_count_multiplicity` |
| I10 | Mindestangebote: `PASS` bei genügend Angeboten, `FAIL` ohne Angebot, sonst `WARNING`. | `test_i10_minimum_bids` |
| I11 | Eine größere Abweichung vom Vertragswert ergibt nie einen milderen Status; Vertragswert 0 → `WARNING`. | `test_i11_value_deviation_is_monotone` |
| I12 | `strict` prüft die Verfahrenswahl für eine im Profil unbekannte Stufe nicht (`NOT_CHECKED`); `legacy` meldet dafür `PASS` (P-C01). | `test_i12_unknown_tier_is_not_checked_in_strict_mode` |

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| Unbekannter Modus | `ValueError` |
| `authority_type` nicht `central`/`sub_central`/`None` | `ValueError` |
| Profil unbekannt oder fehlerhaft | `ProfileError` |
| Stichtag außerhalb aller Zeiträume, Profil ohne Jahrestabelle, Wert zwischen den Schwellen zentraler und sonstiger Auftraggeber ohne `authority_type` | `REVIEW_REQUIRED` mit Begründung (kein Fehler, kein Raten) |
| Vertrags- oder Abrechnungswert fehlt (nur einer) | `strict`: `NOT_CHECKED`; `legacy`: Prüfung entfällt |
| TED-/HAD-Antwort mit HTTP-Fehler, kein JSON, Parserfehler | `SearchResult` `failed` bzw. `rate_limited` mit Fehlertext statt leerer Trefferliste |

## Abgrenzung

- Die Vorprüfung ersetzt keine vergaberechtliche Würdigung; Status sind
  Hinweise für die prüfende Person.
- Nationale Wertgrenzen, Verfahrensbezeichnungen und Pflichtdokumente stammen
  aus dem Regelwerk der Anwendungen und sind je Land bzw. Behörde
  festzulegen; das Paket kennzeichnet sie als `REVIEW_REQUIRED`.
- Online-Abruf, Speicherung, Zeitplanung und Zugangsdaten liegen bei
  `auditcore_harvest` und der Anwendung (`sources`-Extra nur als Adapter).
- Berichtigungs- und Änderungsbekanntmachungen werden gemeldet, aber nicht mit
  der Ursprungsfassung verknüpft.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten | Gewollter Vertrag (`strict`) | Legacy-Variante | Nachweis |
|---|---|---|---|
| Unbekannte Stufe ergibt `PASS` (P-C01), Teilstring-Zuordnung von Verfahren und Pflichtdokumenten (P-C03) | `NOT_CHECKED`; exakte Bezeichnung | `mode="legacy"` | I12, Replays |
| Wert 0 gilt als „nicht angegeben“ (P-C02), fehlender Einzelwert still übergangen (P-C04) | 0 ist ein Wert; `NOT_CHECKED` mit Hinweis | `mode="legacy"` | I8 |
| Schwellen als Konstanten ohne Zeitbezug, `<=` an der EU-Schwelle, ein Wert für alle Auftraggeber (P-C05, P-C10…P-C12) | Profil je Geltungszeitraum mit Fundstelle, ab Erreichen, zentrale/sonstige Auftraggeber | Profil `procurement.hvtg-legacy` 2026.09.1 | I6, I7 |
| Textbeträge verlieren jedes Komma (`"1.234,56"` → 1,23456, P-C06) | Wert unverändert (Kompatibilität), aber blockierender Hinweis `ambiguous_amount` | `ted_values.extract_amount` | I4 |
| Nur Zuschlagsbekanntmachungen mit Auftragnehmer (P-C07) | ausdrückliche Abdeckung, `require_contractor=False` behält alle | `require_contractor=True` (Standard) | I2 |
| HTTP- und Parserfehler ergeben leere Trefferlisten (P-C08) | Status `failed`/`rate_limited` | – (korrigiert) | `test_sources.py` |

Die Legacy-Varianten bleiben für die bitgenaue Reproduktion bestehender
Ergebnisse; neue Aufrufer verwenden `mode="strict"` mit dem aktuellen Profil
(`CURRENT_PROFILE`).

**Befund aus den Eigenschaftstests (26.09.2026):** keiner. Anmerkung: Die
Wertabweichung rechnet wie das Original in Gleitkomma und rundet die Anzeige auf
eine Nachkommastelle; die Monotonie (I11) gilt trotzdem.
