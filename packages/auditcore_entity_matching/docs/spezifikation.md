# Spezifikation auditcore_entity_matching

Stand: 26.09.2026, Paketversion 0.2.4. Charakterisierung: `tests/fixtures/legacy_observed.json`
(440 Fälle flowworkshop/audit_designer), `transliteration_observed.json` (220 Fälle),
riskanalysis- und flowinvoice-Replays (`tests/test_legacy_replay.py`,
`tests/test_transliteration_replay.py`, `tests/test_riskanalysis_payee.py`);
Abweichungen in [`behavior-changes.md`](behavior-changes.md).

## Zweck

Das Paket bildet Namen von Unternehmen und Personen auf eine **Vergleichsform**
ab, prüft Legal Entity Identifier (LEI) nach ISO 17442 und liefert
nachvollziehbare unscharfe Vergleiche. Es dient Anwendungen, die Begünstigte,
Rechnungssteller oder Listeneinträge (Sanktionen, PEP, Beihilfetransparenz)
abgleichen – bei jeder Prüfbehörde und in jedem ESI-Fonds. Die angezeigte
Schreibweise eines Namens wird nie verändert; die Vergleichsform dient nur dem
Abgleich. Jede Regel stammt aus einem benannten, versionierten Profil; es gibt
kein stilles Standardprofil.

## Verträge

| Schnittstelle | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `load_profile(id, version)` | Profilkennung und Version als Text | unveränderliches `Profile` mit `reference` (`id`, `version`, SHA-256-`fingerprint` des kanonischen Profildokuments) | liest nur Paketdaten |
| `available_profiles()` | – | Tupel aller mitgelieferten `(id, version)` | keine |
| `recommended_profile(zweck)` | `entity_normalization`, `sanctions_screening`, `pep_screening`, `payee` | das eine Profil mit diesem `recommended_for` | keine |
| `normalize(text, profil, *, drop_filler=False)` | Text oder `None`; Profil mit Normalisierung | Vergleichsform (Text) | keine; deterministisch |
| `check_lei(wert)` | beliebiger Wert | `LeiCheck(normalized, format_ok, checksum_ok)`, `valid` = beides | keine |
| `is_lei_format`, `lei_checksum_ok`, `lei_check_digits`, `extract_lei` | Text | Wahrheitswert, Prüfziffern, erstes LEI-Token | keine |
| `pair_score(links, rechts, scorer)` | zwei bereits normalisierte Namen, Scorer aus `PAIR_SCORERS` | Wert 0–100 (rapidfuzz) | Extra `fuzzy` |
| `best_match(anfrage, kandidaten, profil, *, min_score)` | normalisierte Anfrage, `Candidate(id, normalized)`, Auflösungsprofil, **ausdrückliche** Schwelle | `MatchResult` (Kandidat, auf eine Nachkommastelle gerundeter Wert, Scorer, alle Einzelwerte, Profilreferenz) oder `None` | Extra `fuzzy` |
| `classify(wert, profil, anfrage_norm=None, treffer_norm=None)` | Wert, Screening-Profil | `exact`/`high`/`medium`/`low` | Extra `fuzzy` nur mit Normformen |

Normalisierungsverfahren (je Profil genau eines): `translate_then_casefold`,
`casefold_fold_nfkd`, `casefold_nfc_fold_nfkd`, `lower_nfkd_ascii`,
`nfkd_lower_regex`; optional `compose: "NFC"` in den nutzerentschiedenen
Profilen (23.09.2026). Auswahlregel von `best_match`: je Scorer des Profils die
besten `per_scorer_limit` Treffer ab `min_score`, der höchste Einzelwert
gewinnt, bei Gleichstand der frühere Kandidat und der frühere Scorer.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | `normalize` ist deterministisch und liefert Text; `None` und `""` ergeben `""`. | `tests/test_spezifikation.py::test_i1_normalize_is_deterministic_text` |
| I2 | Die Vergleichsform ist ein Fixpunkt: erneutes Normalisieren ändert sie nicht – für alle Verfahren außer `translate_then_casefold` (Befund unten). | `test_i2_normalize_is_idempotent`, `test_i2_translate_then_casefold_is_not_idempotent_legacy` |
| I3 | Die Vergleichsform hat keine führenden, abschließenden oder doppelten Leerzeichen und keine Großbuchstaben. | `test_i3_comparison_form_has_single_spaces_and_no_upper_case` |
| I4 | Bei tokenbasierten Verfahren ist kein Token der Vergleichsform eine Rechtsform des Profils (mit `drop_filler` auch kein Füllwort). | `test_i4_legal_form_tokens_are_removed` |
| I5 | Ein 18-stelliges Präfix mit `lei_check_digits` ist ein gültiger LEI, unabhängig von Groß-/Kleinschreibung und umgebenden Leerzeichen; `extract_lei` findet ihn im Fließtext. | `test_i5_generated_check_digits_make_a_valid_lei` |
| I6 | `LeiCheck.valid` gilt genau dann, wenn Format und Prüfziffern (ISO 7064 MOD 97-10) stimmen; `is_lei_format` prüft nur das Format. | `test_i6_valid_implies_format_and_checksum` |
| I7 | `extract_lei` liefert `None` oder ein Token mit richtigen Prüfziffern; ohne Prüfziffernprüfung mindestens ein formal richtiges Token. | `test_i7_extracted_lei_has_correct_check_digits` |
| I8 | Die Klasse von `classify` ist in der Punktzahl monoton (`low` < `medium` < `high` < `exact`). | `test_i8_score_class_is_monotone` |
| I9 | `pair_score` liegt in 0–100, ein nichtleerer Name erreicht gegen sich selbst 100; `ratio`, `token_set_ratio` und `token_sort_ratio` sind symmetrisch. | `test_i9_pair_score_is_bounded_and_reflexive` |
| I10 | `best_match` liefert nur Treffer mit (gerundet) mindestens der ausdrücklichen Schwelle, nur Kandidaten aus der Liste und die Profilreferenz; eine höhere Schwelle erzeugt nie einen Treffer, den eine niedrigere nicht hatte. | `test_i10_best_match_respects_the_explicit_threshold`, `test_i10_returned_score_is_rounded_to_one_decimal` |
| I11 | Nur mitgelieferte Profile laden, jedes unter seiner eigenen Kennung und Version mit 64-stelligem Fingerabdruck; alles andere ist `ProfileError`. | `test_i11_only_packaged_profiles_load`, `test_i11_packaged_profiles_are_identified` |

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| Profil unbekannt, falsche Version, Pfadzeichen im Namen, Profildokument unvollständig, Klassengrenzen nicht aufsteigend, unbekannter Algorithmus/Scorer | `ProfileError` (Code `profile_error`) |
| Profil ohne Normalisierung an `normalize`, ohne Auswahlregeln an `best_match`, ohne Klassengrenzen an `classify` | `ProfileError` |
| Nicht-Text an `normalize` oder `pair_score` | `TypeError` „Namen sind als Text zu übergeben.“ (keine stille Umwandlung, EM-C05) |
| Unbekannter Scorer an `pair_score` | `ProfileError` |
| `rapidfuzz` fehlt | `DependencyError` (Code `missing_optional_dependency`, zugleich `ImportError`) |
| LEI-Präfix nicht 18 Zeichen `A-Z0-9` | `ValueError` |
| Anfrage ohne Token der Mindestlänge oder leere Kandidatenliste | `best_match` liefert `None` (kein Raten) |

## Abgrenzung

- Datenbank, SQL-Vorfilter (ILIKE, Trigramm, Limit), Konfidenzklassen der
  Anwendung und Geburtsdatums-/Länderregeln bleiben in der Anwendung bzw. in
  `auditcore_registry_sources`.
- Schwellen und Mindestlängen der Red-Flag-Regel RF09 gehören zum Regelprofil
  von `auditcore_risk`.
- Das Paket entscheidet nicht, ob zwei Namen dieselbe Person oder dasselbe
  Unternehmen bezeichnen; es liefert Vergleichsform, Werte und Belege für die
  Entscheidung eines Menschen.
- Kein Profil wird für einen Aufrufer stillschweigend gewählt;
  `recommended_profile` ist eine ausdrücklich abgerufene Empfehlung.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten | Gewollter Vertrag | Legacy-Variante | Nachweis |
|---|---|---|---|
| LEI gilt bei richtigem Format als gültig, auch mit falschen Prüfziffern (EM-C01) | `check_lei(...).valid` verlangt Prüfziffern | `legacy.flowworkshop_is_valid_lei` | `test_legacy_replay.py`, I6 |
| Erstes formal passendes Token als LEI (EM-C02) | `extract_lei` überspringt Tokens mit falschen Prüfziffern | `legacy.flowworkshop_extract_lei_from_text` (`require_checksum=False`) | I7 |
| `Müller → muller` im Sanktionsabgleich | empfohlen: Umschrift `mueller` (Profile 2026.09.2/2026.09.3) | Profile `flowworkshop.sanctions` 2026.09.1 und `audit_designer.sanctions` 2026.09.1 (`legacy.flowworkshop_normalize_name`, `legacy.designer_normalisiere_name`) | Replays |
| flowinvoice-PEP: alles außer `a-z0-9` wird Trenner (`Straße → stra e`) | empfohlen: `flowinvoice.pep` 2026.09.2 | Profil `flowinvoice.pep` 2026.09.1 (`legacy.flowinvoice_pep_normalize_name`) | Replays |
| riskanalysis: NFKD vor dem Zeichenmuster zerlegt Umlaute (`Müller → mu ller`, EM-L01) | empfohlen: `riskanalysis.payee` 2026.09.2 (`Müller → mueller`) | Profil `riskanalysis.payee` 2026.09.1 | `test_riskanalysis_payee.py` |
| Eingaben wurden mit `str()` umgewandelt (`NaN → "nan"`, EM-C05) | nur Text, sonst `TypeError` | keine (Aufrufer wandelt um) | Fehlerfälle |

Die Legacy-Profile und `legacy.*`-Funktionen sind zur bitgenauen Reproduktion
bestehender Ergebnisse da, nicht für neue Aufrufer.

**Befunde aus den Eigenschaftstests (26.09.2026, dokumentiert, Code unverändert):**

1. *`translate_then_casefold` ist nicht idempotent* (Profile
   `flowworkshop.state_aid` 2026.09.1 und 2026.09.2): Die Zeichentabelle wirkt
   vor der Kleinschreibung, großgeschriebene Akzentbuchstaben ohne
   Tabelleneintrag bleiben stehen (`É → é`); ein zweiter Durchlauf ergibt
   `e`. Wer bereits normalisierte Werte erneut normalisiert, erhält andere
   Vergleichsformen. Charakterisiertes Quellverhalten (EM-C03), deshalb nicht
   korrigiert; eine Korrektur wäre eine neue Profilversion.
2. *Gerundeter Trefferwert:* `best_match` rundet den Wert auf eine
   Nachkommastelle (Quellverhalten). Er kann dadurch bis zu 0,05 unter einer
   ungerundeten Schwelle liegen (Schwelle 90,909…, Rückgabe 90,9). Wer den
   Wert erneut gegen die Schwelle prüft, vergleicht mit der gerundeten Schwelle.
