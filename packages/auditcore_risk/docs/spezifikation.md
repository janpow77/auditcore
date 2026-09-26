# Spezifikation auditcore_risk

Stand: 26.09.2026, Paketversion 0.3.4. Charakterisierung: riskanalysis
(173 Frames, `tests/test_replay_riskanalysis.py`), Flowstat in audit_designer und
audit-portal (112 Frames, `tests/test_replay_flowstat.py`), flowinvoice
RiskChecker, Betrugsprüfung und Kriterien der risikobasierten
Verwaltungsüberprüfung (`tests/test_replay_flowinvoice_*.py`);
Abweichungen und Entscheidungen in [`behavior-changes.md`](behavior-changes.md)
(RK-L, RK-C, K1…K12, C2, K2a), Eingabefelder in [`eingabefelder.md`](eingabefelder.md).

## Zweck

Das Paket leitet **Risikomerkmale (Red Flags)** aus ausdrücklich gewählten,
versionierten und quellengebundenen Regelprofilen ab. Jedes Merkmal trägt
Code, Begründung, Belegwerte, Interpretation und die Fundstelle der Regel in
der Quelle. Anwendungen nutzen die Merkmale, um Belege, Rechnungen oder
Mittelabrufe für Stichproben, Verwaltungsüberprüfungen (Art. 74 CPR) und
Prüfungen zu priorisieren – bei jeder Prüf-, Verwaltungs- oder
Bescheinigungsbehörde und in jedem ESI-Fonds. Ein Merkmal ist ein
Prüfhinweis, **keine Feststellung und keine Fehlerquote**; das Paket bildet
keinen profilübergreifenden Risikoscore (Entscheidung K1).

## Verträge

| Schnittstelle | Eingabe | Ausgabe |
|---|---|---|
| `load_profile(id, version)`, `available_profiles()` | ausdrücklich benanntes Regelprofil | unveränderliches `RiskProfile` (Regeln mit Code, Art, Parametern, Fundstelle; `reference` mit Fingerabdruck) |
| `evaluate(datensätze, profil, *, columns=None, reference_date=None, points=None)` | Zuordnungen Spalte → Wert; Spaltenmenge (Vorgabe: Vereinigung der Schlüssel) | `Evaluation`: je Datensatz `RecordResult` (`flags` Code → `True`/`False`/`None`, `hits`, `undetermined` mit Grund, Werte, profileigene Bewertung), datensatzweite `DatasetFinding`s, `skipped` mit Grund, `summary` im Format des Profils |
| `missing_columns(profil, spalten)` | Spaltennamen | je Regel fehlende Pflichtspalten |
| `name_similarity(regel, links, rechts)`, `identifier_missing(regel, wert)` | eine Regel der Art `name_similarity` bzw. `missing_procurement` | Ähnlichkeit 0–1 bzw. „Vergabekennung fehlt“ |
| `flatten_record(datensatz)` | verschachtelte Zuordnung | eine Ebene `eltern.kind` |
| `load_fraud_profile`, `find_duplicates`, `score_signals`, `assess_contractor`, `select_contracts` | Profile der flowinvoice-Betrugsprüfung | Dubletten, Signale mit Blockern/Warnungen und profileigenem Score, TED-Auftragnehmerstatistik |
| `auditcore_risk.frame` (Extra `pandas`), `auditcore_risk.web` (Extras `web`/`fastapi`) | DataFrame bzw. JSON-REST | dieselbe Auswertung |

Regelarten (`KINDS`) sind die wiederverwendbare Mechanik; jede fachliche
Einstellung (Schwelle, Vielfaches, Muster, Umgang mit fehlenden Spalten
`error`/`skip`/`all_false`/`undetermined`) steht als Parameter im Profil.
Jahresbezogene EU-Vergabeschwellen kommen aus `auditcore_procurement`
(Extra `procurement`), Namensabgleich aus `auditcore_entity_matching`
(Extra `fuzzy`).

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Gleiche Datensätze und gleiches Profil ergeben dieselbe Auswertung; sie trägt die Identität des Profils. | `tests/test_spezifikation.py::test_i1_evaluation_is_deterministic_and_profile_bound` |
| I2 | Jede Regel ist angewandt, übersprungen oder datensatzweit; die Treffer eines Datensatzes sind genau die Regeln mit `True` in Profilreihenfolge, `undetermined` genau die mit `None`. | `test_i2_every_rule_is_accounted_for_and_hits_match_flags` |
| I3 | Eine Regel mit `when_missing_columns = "skip"` wird genau dann übersprungen (mit Grund), wenn eine Pflichtspalte fehlt. | `test_i3_rules_are_skipped_exactly_when_columns_are_missing` |
| I4 | Jeder Treffer gehört zu einer Regel des Profils und hat Begründung und Fundstelle. | `test_i4_every_hit_is_justified` |
| I5 | Die Vergaberegel (Beispiel BL_RF08: Betrag > 25.000 ohne Vergabekennung) ist im Betrag monoton: ein höherer Betrag hebt einen Treffer nie auf. | `test_i5_procurement_flag_is_monotone_in_the_amount` |
| I6 | Die Regel „runder Betrag“ trifft positive Vielfache der Profilschrittweite und keinen Betrag einen Cent daneben. | `test_i6_round_amounts_are_multiples_of_the_profile_step` |
| I7 | Datensatzbezogene Regeln hängen nicht von anderen Datensätzen oder deren Reihenfolge ab. | `test_i7_record_rules_do_not_depend_on_other_records` |
| I8 | Fehlt der Nettobetrag (Spalte oder Wert) im Profil `riskanalysis.year_bound` 2026.09.5, sind alle Datensätze, die der Betrag entscheiden würde, unbestimmt (`None`), nie „kein Treffer“: RF02 immer, RF08 ohne Vergabekennung. | `test_i8_missing_net_amount_is_undetermined_not_clear` |
| I9 | `flatten_record` legt genau eine Ebene flach; andere Werte bleiben unter ihrem Schlüssel. | `test_i9_flatten_record_is_one_level` |
| I10 | Ohne geladenes Profil `ProfileError`; Datensätze, die keine Zuordnung sind, und nicht numerische Werte in streng gelesenen Betragsfeldern `InputError` – kein Raten. | `test_i10_invalid_input_is_an_error_not_a_guess` |
| I11 | Die Namensähnlichkeit (RF09) liegt in 0–1, ist symmetrisch und für einen hinreichend langen Namen gegen sich selbst 1. | `test_i11_name_similarity_is_bounded_symmetric_and_reflexive` |

## Fehlerfälle

| Fehler (Code) | Anlass |
|---|---|
| `ProfileError` (`profile_error`) | Profil unbekannt, fehlerhaft oder nicht ausdrücklich übergeben; unbekannte Regelart; `name_similarity`/`identifier_missing` mit Regel der falschen Art |
| `InputError` (`input_error`, zugleich `ValueError`) | Datensatz keine Zuordnung, Spaltenname kein Text, Pflichtspalte fehlt bei `when_missing_columns = "error"`, Text/Wahrheitswert/Liste in Betragsfeldern (RK-C01), TED-Legitimität außerhalb 0–1 (K8) |
| `DependencyError` (`missing_optional_dependency`, zugleich `ImportError`) | Namensabgleich ohne Extra `fuzzy`, DataFrame-Adapter ohne `pandas`, Jahresschwellen ohne `procurement` (RK-C03: kein stiller Rückfall auf andere Algorithmen) |

Kein Fehler, sondern `None` mit Grund: fehlender belegter Schwellenzeitraum
oder fehlendes Datum bei jahresbezogenen Schwellen (RK-C04), fehlender
Nettobetrag im Profil 2026.09.5 (K2a).

## Abgrenzung

- Keine Feststellung, keine Fehlerquote (weder TER noch RER), keine
  Stichprobenziehung; die Merkmale priorisieren nur.
- Kein gemeinsamer Score über Profile; Bewertungen (`assessment`) gibt es nur
  innerhalb eines Profils, das sie selbst definiert.
- Datenaufbereitung (Vorhistorie, Kalibrierung von Gewichten, Pseudonymisierung)
  bleibt in der Anwendung (RK-C11).
- Welches Profil gilt, entscheidet die Anwendung; Profile mit Status
  `CANDIDATE_HUMAN_DECISION_REQUIRED` sind nicht freigegeben.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten | Gewollter Vertrag | Legacy-Variante | Nachweis |
|---|---|---|---|
| Red Flags von riskanalysis mit allen Eigenheiten (RK-L03: RF12 über Gruppen hinweg, `Müller → mu ller` in RF09, Nettoschwellen auf Bruttobeträge) | `riskanalysis.year_bound` 2026.09.2 ff. (netto, `same_group`, `mueller`-Umschrift, Jahresschwellen) | Profil `riskanalysis.legacy` b5c523bf7eaa | RK-L01 |
| Flowstat-Belegliste: BL_RF08 nur leere Werte, BL_RF09 Teilzeichenketten | unverändert (keine korrigierte Fassung beauftragt) | Profil `audit_designer.flowstat_belegliste` 1254591156d3 | RK-L02, I5–I7 |
| RiskChecker-Score = Summe der Gewichte / 5 (RK-L04) | nur als profileigene Bewertung; Splitting an EU-Schwelle des Jahres (K9) | Profil `flowinvoice.risk_checker` fb2d18568d2e | Replays |
| WIBANK-Punkte aus Code-Konstanten statt Profildatei (RK-L08) | Profil nach Profildatei V1.21 (K11) | Profil `flowinvoice.rbvk_wibank` fb2d18568d2e | Replays |
| Ex-ante-Gewichte zur Laufzeit kalibriert (RK-L09) | kalibrierte Punkte ausdrücklich über `points` | Profile `flowinvoice.exante_basis`, `flowinvoice.exante_heuristik` | Replays |
| Betrugsprüfung: Warnungen vor Dublettenentfernung, Legitimität als Wörterbuch (RK-C08/C09) | `flowinvoice.fraud_signals` 2026.09.2 (`after_dedup`, 0–1) | Profile `flowinvoice.fraud_signals` fb2d18568d2e, `flowinvoice.ted_contractor` fb2d18568d2e, `flowinvoice.duplicates` fb2d18568d2e | Replays |
| Nicht numerische Beträge: `TypeError`, Wahrheitswerte als 1/0; fehlende Spalten `KeyError` oder still übersprungen; stiller Rückfall auf `difflib` (RK-C01…C03) | `InputError`, übersprungene Regeln mit Grund, `DependencyError` | – (korrigiert) | I3, I10 |

Die Legacy-Profile reproduzieren die Quellanwendungen bitgenau und dienen der
Umstellung bestehender Aufrufer; neue Aufrufer wählen ein freigegebenes
(`APPROVED`) Profil.

**Befund aus den Eigenschaftstests (26.09.2026):** keiner. Präzisiert wurde
I8: Im Profil 2026.09.5 ist RF08 bei fehlendem Nettobetrag nur ohne
Vergabekennung unbestimmt; mit Kennung ist der Betrag nicht entscheidend und
das Ergebnis „kein Merkmal“ – so wie in K2a beschlossen.
