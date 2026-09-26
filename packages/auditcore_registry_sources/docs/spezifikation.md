# Spezifikation auditcore_registry_sources

Stand: 26.09.2026, Paketversion 0.2.3. Charakterisierung: 456 Fälle der
Originale (audit_designer, flowworkshop, flowsearch, flowinvoice,
audit-portal; `tests/fixtures/legacy_observed.json`, `tests/test_replay_*.py`).
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket liest Register-, Sanktions- und PEP-Listen, ruft sie über
`auditcore_harvest` ab, gleicht Namen nach ausdrücklich gewählten Profilen
ab, prüft Firmendaten (VIES, OffeneRegister, Kammerverzeichnisse),
berechnet Eigentümerketten und KMU-Einstufungen und macht
Screening-Treffer nachvollziehbar entscheidbar. Ein Treffer ist ein
Prüfhinweis für die Prüferin oder den Prüfer, keine Feststellung; ein
Ergebnis ohne Treffer belegt keine Unbedenklichkeit.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `load_profile(id, version)`, `available_profiles()` | ausdrücklich genanntes Profil | `RegistryProfile` mit Art (`screening`, `list_catalog`, `ownership`, `sme`, `company_verification`, `match_api`), Status und Fingerprint | keine; kein Standardprofil außer `recommended_profile(zweck)` |
| `parse_targets_simple_csv(data, list_key=)` / `serialize_targets_simple_csv(rows, columns=)` | UTF-8-Bytes im OpenSanctions-Format `targets.simple.csv` bzw. Zeilen | `ParsedList` (Einträge, `RowIssue`, gelesene Zeilen, SHA-256 der Lieferung) bzw. deterministische CSV-Bytes | keine |
| `sanctions_xml.parse_xml_list` / `xml_entries` (Extra `xml`) | EU FSF 1.1, OFAC SDN, UN SC | Einträge in Listenschreibweise, alle Geburtsdaten und Länder | keine; `defusedxml` |
| `screen(name, snapshots, profile, …)` (Extra `fuzzy`) | Name, `ListSnapshot` je Liste mit Stand, Profil `screening` | `ScreeningResult` (Vertrag `…screening/1`): Status `HITS`/`NO_HITS`/`INCOMPLETE`/`NOT_SEARCHED`, `ListFinding` je Liste, Treffer mit Rohwert, Anpassungen und Indikatoren | keine |
| `bulk_screening.local_screen`, `pep_bulk_screen` | Name, Listeneinträge, flowinvoice-Profil | `BulkResult` mit Status und Datenstand | keine |
| `MatchClient`, `parse_response`, `assess_sanctions`, `assess_pep` | Anfrage, injizierter Transport, Schlüssel aus dem Credential-Provider | ausgewertete `/match`-Antwort | Netz nur über den Transport |
| `company.verify_company`, `check_vat`, `lookup_register`, `normalize_company_name`, `names_match`, `score_indicators` | Firmendaten, USt-IdNr., Transport, Profil `company_verification` | `CompanyVerification` (Indikatoren, Score, nicht ausführbare Prüfungen), `VatCheck`, `RegisterLookup` | Netz nur über den Transport |
| `ownership.traverse`, `ownership_chain`, `beneficial_owners`, `unclassified_holders`, `sme_status` | Unternehmensdaten des Aufrufers, Profil `ownership`/`sme` | Graph, Kette mit Zyklusangabe, wirtschaftlich Berechtigte, KMU-Einstufung mit offenen Punkten | keine |
| `adapters` | Listen-, Register- und Kammerquellen | Harvest-Vollbestand mit `snapshot_complete` | Netz nur über den Transport des Hosts |
| `web.ScreeningReviewService` | Prüfläufe, Entscheidungen mit Pflichtbegründung | Protokoll nach Vertrag `…screening_review/1` | Speicher des Hosts |

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Einträge, die mit `entry_to_row` und `serialize_targets_simple_csv` geschrieben werden, liest `parse_targets_simple_csv` unverändert zurück; die Prüfsumme ist der SHA-256 der Lieferung. | `test_i1_targets_csv_roundtrip` |
| I2 | Jede gelesene Zeile ist Eintrag oder `RowIssue` (`rows_seen` = Einträge + Probleme, Reihenfolge erhalten); eine Lieferung ohne verwertbare Zeile oder ohne UTF-8 ist ein `FormatError`, nie eine leere Liste. | `test_i2_every_row_is_an_entry_or_an_issue` |
| I3 | `local_screen`: jeder Treffer erreicht den Mindestwert, der exakte Name ergibt 1,0 und Methode `exact`; ohne Datenbestand lautet der Status `NOT_SEARCHED`. | `test_i3_local_screen_hits_are_at_or_above_the_minimum` |
| I4 | `screen` liefert je angefragter Liste einen Befund in Anfragereihenfolge; eine Liste ohne Bestand gilt als nicht durchsucht. Status: `HITS` bei Treffern, sonst `NOT_SEARCHED` ohne durchsuchte Liste, `INCOMPLETE` bei teilweiser Durchsuchung, `NO_HITS` nur bei vollständiger; ohne Treffer steht der Hinweis, dass keine Unbedenklichkeit belegt ist, in den Einschränkungen. | `test_i4_screening_status_reflects_the_searched_lists` |
| I5 | Zu kurze Namen und Mindestwerte außerhalb des Profilbereichs werden mit `QueryError` abgewiesen, nicht angepasst. | `test_i5_queries_outside_the_profile_are_rejected` |
| I6 | Rechtsformen werden nur als ganze Wortfolgen entfernt (`Hagen` bleibt `hagen`); die Normalisierung ist idempotent, der Namensabgleich reflexiv und symmetrisch. | `test_i6_company_names_lose_only_whole_legal_forms` |
| I7 | Der Firmenscore liegt in [0, 1] und steigt mit weiteren Indikatoren nie; „verifiziert“ genau dann, wenn kein kritischer Indikator vorliegt. | `test_i7_indicator_score_is_bounded_and_monotone` |
| I8 | `ownership_chain` terminiert für jeden Elterngraphen, enthält jeden Knoten höchstens einmal und meldet einen wiederholten Knoten als Zyklus. | `test_i8_ownership_chain_terminates_and_reports_cycles` |
| I9 | Wirtschaftlich Berechtigte (Profil `flowsearch.ubo` 2026.09.2) sind genau die natürlichen Personen mit mehr als 25 % Kapital oder Stimmrechten, absteigend nach Anteil. | `test_i9_beneficial_owners_are_persons_above_a_threshold` |
| I10 | KMU nach Anhang I AGVO (Profil `flowsearch.kmu` 2026.09.2): Klasse aus Beschäftigten und Umsatz **oder** Bilanzsumme; fehlen Beschäftigte oder beide Finanzwerte, lautet sie „Nicht bestimmbar“ (`is_sme = None`), ab 250 Beschäftigten „Großunternehmen“. | `test_i10_sme_category_never_guesses` |
| I11 | VIES: Gültigkeit wird unabhängig vom Namensraumpräfix gelesen; SOAP-Fault und Transportfehler ergeben `UNAVAILABLE`, nie `INVALID`; die USt-IdNr. wird idempotent normalisiert. | `test_i11_vies_unavailability_is_never_a_negative_answer` |

## Fehlerfälle

| Fall | Ergebnis |
|---|---|
| Profil unbekannt, unvollständig oder falscher Art | `ProfileError` |
| Name leer oder zu kurz, Mindestwert außerhalb des Bereichs, unbekannter Eintragstyp, Trefferlimit < 1, USt-IdNr. ohne Ländercode | `QueryError` |
| Lieferung nicht UTF-8, Pflichtspalten fehlen, keine verwertbare Zeile, CSV/XML nicht lesbar | `FormatError` bzw. `ParserError` |
| Zeile ohne Kennung oder Namen | `RowIssue` (im Harvest-Lauf `RecordIssue`, Lauf `partial`) |
| Optionales Extra fehlt (`fuzzy`, `xml`, `html`) | `DependencyError` |
| VIES-Fault, Serverfehler, Transportfehler; Registerabfrage scheitert | `UNAVAILABLE` und Eintrag in `unavailable` – nie „ungültig“ oder „nicht im Register“ |
| `/match` ohne gültigen Schlüssel, Rate-Limit, Transport- oder Formfehler | `AuthError`, `RateLimitError`, `TransportError`, `ParserError` – nie `found: False` |
| Kein Datenbestand für eine Liste | `ListFinding.searched = False`, Status `INCOMPLETE` oder `NOT_SEARCHED` |

## Abgrenzung

- Keine Datenbank, kein Scheduler, keine Auslistungsentscheidung, keine
  Zugangsdatenverwaltung: das bleibt bei der Anwendung (REG-C16).
- Keine rechtliche Würdigung: UBO- und KMU-Ergebnisse tragen die offenen
  Entscheidungen des Profils; ein Treffer ist ein Prüfhinweis.
- Keine phonetischen Verfahren; Namensvergleich nur nach den
  Normalisierungsprofilen von `auditcore_entity_matching`.
- Listenstand wird nie erfunden: er kommt aus der Lieferung oder vom Aufrufer
  (`as_of`).

## Bewusste Abweichungen vom Altverhalten

Vollständige Liste REG-C01 bis REG-C18 und die Entscheidungen R1 bis R10 in
[behavior-changes.md](behavior-changes.md). Die Originale bleiben im Modul
`legacy` verhaltensgleich (Replay), sind aber nicht für neue Aufrufer
gedacht; frühere Profilstände bleiben ladbar.

| Altverhalten | Gewollt | Legacy-Variante | Nachweis |
|---|---|---|---|
| VIES-Antwort mit `ns2:`-Präfix gilt immer als ungültig; Fault = ungültig (REG-C07, REG-C08) | präfixunabhängig, Fault/Ausfall = `UNAVAILABLE` (I11) | `legacy.flowinvoice_validate_vat` | Replay, `test_i11_…` |
| Rechtsformen als Teilzeichenkette entfernt (`Hagen Metall AG` → `hen metall`, REG-C10) | ganze Wortfolgen (I6) | `legacy.flowinvoice_normalize_company_name` | Replay, `test_i6_…` |
| Registerfehler = „nicht im Register“, SQL-Text aus dem Namen (REG-C09) | gebundene Parameter, `UNAVAILABLE` getrennt von `NOT_FOUND` | `legacy.flowinvoice_register_company` | Replay |
| `check_entity` gegen den nicht mehr erreichbaren Dienst sanctions.network, erfundene Listenstände (REG-C14) | nicht übernommen | Profil `flowinvoice.sanctions_network` (Status `LEGACY_ONLY`), `legacy.flowinvoice_sanctions_network` | Replay |
| Geburtsjahr wird 1. Januar, nur erste Werte (REG-C04) | Schreibweise und alle Werte behalten | `parse_xml_list(..., dates="legacy")` | `tests/test_replay_formats.py` |
| Listen ohne Bestand still übersprungen (REG-C01) | Befund je Liste, `INCOMPLETE`/`NOT_SEARCHED` (I4) | – | `test_i4_…` |
| Endlosschleife bei Selbstverweis (REG-C12) | Abbruch mit `cycle` (I8) | – | `test_i8_…` |
| UBO-Stimmrechtsschwelle 50 %, KMU ohne Bilanzalternative (Profilstand 2026.09.1) | § 3 Abs. 2 GwG 25 % mit mittelbaren Anteilen, Anhang I AGVO (R4, R5; I9, I10) | Profile `flowsearch.ubo` und `flowsearch.kmu` in Version 2026.09.1 | `tests/test_ownership_and_bulk.py` |

Keine offenen Befunde aus den Eigenschaftstests.
