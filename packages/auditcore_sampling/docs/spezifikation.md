# Spezifikation auditcore_sampling

Stand: 27.09.2026, Paketversion 0.2.3 (mit Unreleased). Charakterisierung:
8 883 am Original (`janpow77/flowstat@d665ac2`, `janpow77/audit-portal@d8eefa4`)
beobachtete Fälle in `tests/fixtures/sampling_legacy_observed.json.gz`
(`tools/capture_sampling_legacy.py`, Replay `tests/test_legacy_replay.py`) und
240 Ziehungen von flowinvoice (`fb2d18568d2e`) in
`tests/fixtures/intermediate_body_observed.json.gz`
(`tests/test_intermediate_body_parity.py`). Abweichungen:
`docs/behavior-changes.md`; Umfang nach Leitfaden: `docs/leitfaden-umfang.md`.
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket bestimmt Stichprobenumfänge und zieht Stichproben nachvollziehbar
und mit Seed reproduzierbar – für Prüfbehörden aller ESI-Fonds (Vorhabenprüfung
nach Art. 79 VO (EU) 2021/1060) und für Stellen, die Verwaltungsüberprüfungen
(Art. 74) stichprobenweise durchführen. Es enthält drei getrennte Teile mit
eigenem Status: charakterisierte Methoden der Quellanwendungen, den
Stichprobenumfang nach dem KOM-Leitfaden EGESIF_16-0014-01 („nach Leitfaden“)
und die Belegziehung einer Zwischengeschalteten Stelle als versioniertes
Profil.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `mus_size(method, *, population_value, materiality, expected_error_rate, confidence_level)` | benannte MUS-Methode aus `METHODS`, Beträge in Euro, Anteile in [0, 1) | `SizePlan` (Methode, Umfang, Intervall, Eingaben, Hinweise) | keine; deterministisch |
| `recommended_mus_size(…)` | wie oben ohne Methode | Plan mit `portal.mus_poisson` (Entscheidung 23.09.2026) | – |
| `srs_size(method, *, population_size, confidence_level, margin_of_error, expected_proportion)` | benannte SRS-Methode, N ≥ 1, e ∈ (0, 1), p ∈ [0, 1] | `SizePlan`, n ≤ N | – |
| `systematic_mus(values, *, sample_size, interval, start, variant)` | Beträge in Reihenfolge, Variante `portal` oder `flowstat` | `MusSelection` (Treffer, Positionen, Ausschlüsse) | – |
| `draw_start(rng, interval)`, `simple_random(rng, population, size)` | ausdrücklicher `random.Random` | Startwert bzw. Auswahl ohne Zurücklegen | nur der übergebene Generator |
| `stratified_allocation(n, strata, method)` | Gesamtumfang, Schichtgrößen, `proportional`/`equal` | Umfang je Schicht, höchstens N_h | – |
| `guidance.equal_probability_size`, `guidance.stratified_equal_probability_size` | Methode `guidance.srs`/`guidance.difference`, N, BV, σ_e bzw. Schichten, Konfidenzniveau, Faktorprofil, erwartete Fehlerquote, Wesentlichkeit ≤ 2 % | `GuidancePlan` mit Herleitung und Fundstelle je Schritt, Status `GUIDANCE_EGESIF_16_0014_01` | – |
| `guidance.mus_standard_size`, `guidance.mus_stratified_size`, `guidance.mus_conservative_size` | BV, σ_r bzw. Schichten, Konfidenzniveau, Faktorprofil, Fehlerquote | `GuidancePlan` (bei MUS Standard mit `book_values` auch Hochwertschicht) | – |
| `guidance.nonstatistical_minimum(rule, *, population_size, book_value, assurance_level)` | Regelprofil `cpr_2021_art79_2` oder `cpr_2013_art127_1` | Mindestumfang, Mindestabdeckung, Tabelle-6-Bänder | – |
| `guidance.high_value_split(book_values, n)` | Buchwerte > 0, n ≥ 1 | `HighValueSplit` (Hochwertschicht, SI, n_s) | – |
| `guidance.error_sd`, `guidance.error_rate_sd` | Vorstichprobe | Standardabweichung (Divisor n − 1) | – |
| `intermediate_body.value_share_draw(amounts, errors, order, profile)` | Beträge ≥ 0, Fehlerbeträge, Ziehreihenfolge, Profil `zs.value_share_escalation` | `ValueShareDraw` (Positionen, Stufen, Leiter) | – |
| `intermediate_body.draw_order`, `derived_seed`, `quality_sample` | Generator bzw. Seed und Schlüssel | Permutation, Seed je Mittelabruf, jeder k-te Kandidat | – |
| `web` (Extra) | JSON | Verträge `sampling-rest.md` und `auditcore_sampling.guidance/1` | keine Speicherung |

Faktorprofile der Planung: `kom_2017_tables` (Tabellen 3, 4, 5 wie
gedruckt) und `exact`; nie still gewählt.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | MUS-Umfang (`portal.mus_poisson`): n ≥ 1 bei V > 0, n × J = V, n wächst nicht fallend mit dem Konfidenzniveau. | `test_i1_mus_size_covers_the_population_and_grows_with_confidence` |
| I2 | SRS-Umfang: 0 ≤ n ≤ N; eine größere Fehlertoleranz ergibt keinen größeren Umfang. | `test_i2_srs_size_stays_within_population_and_falls_with_tolerance` |
| I3 | Variante `portal`: Positionen eindeutig und positiv, alle Null-, Fehl- und Negativwerte ausgewiesen, jede Einheit über dem Intervall ausgewählt. | `test_i3_portal_selection_takes_positive_units_once_and_all_certainty_items` |
| I4 | Zufallsauswahl: gleicher Seed → gleiche Auswahl, ohne Zurücklegen, im verlangten Umfang. | `test_i4_random_selection_is_reproducible_and_without_replacement` |
| I5 | Aufteilung: n_h ≤ N_h; proportional Σ n_h ≥ min(n, N). | `test_i5_allocation_respects_strata_and_reaches_the_total` |
| I6 | Umfang nach Leitfaden erreicht die geplante Präzision: N z σ / √n ≤ TE − AE, außer der Umfang ist auf N begrenzt; die Endlichkeitskorrektur vergrößert nie. | `test_i6_guidance_size_reaches_the_planned_precision` |
| I7 | Aufteilung nach größtem Rest: Σ n_h = n, Abweichung vom exakten Anteil < 1. | `test_i7_largest_remainder_is_exact_and_fair` |
| I8 | Konservatives MUS: BV × RF / n ≤ TE − AE × EF. | `test_i8_conservative_basic_precision_stays_within_the_margin` |
| I9 | Hochwertschicht: keine Einheit der Stichprobenschicht über SI, n_s = n − n_e ≥ 1. | `test_i9_high_value_split_leaves_no_unit_above_the_interval` |
| I10 | Belegziehung der Zwischengeschalteten Stelle: Positionen eindeutig, Stufen aufsteigend, Zielanteil erreicht (sofern nicht alle Belege gezogen), ohne Fehler nur Stufe 1. | `test_i10_value_share_draw_reaches_the_share_and_escalates_only_on_errors` |

Konsistenz mit der Hochrechnung (Planung → Stichprobe → Hochrechnung) prüft
`auditcore_extrapolation/tests/test_planning_consistency.py`.

## Fehlerfälle

Alle Ablehnungen sind `SamplingInputError` (Unterklasse von `ValueError`) mit
deutscher Meldung; es gibt keine stillen Ersatzwerte.

| Eingabe | Ergebnis |
|---|---|
| unbekannte Methode, unbekanntes Faktorprofil, Regelprofil oder Verfahren | Fehler mit Liste der zulässigen Kennungen |
| Konfidenzniveau nicht in der Tabelle der Methode bzw. des Profils | Fehler „kein Ersatzwert“ |
| Wesentlichkeit ≤ 0 oder über 2 %, erwartete Fehlerquote ≥ Wesentlichkeit, TE − AE × EF ≤ 0 | Fehler mit Fundstelle |
| nicht endliche Zahlen, Wahrheitswerte als Zahl, N < 1, Standardabweichung ≤ 0 | Fehler |
| nicht-statistisch nach `cpr_2021_art79_2` mit N ≥ 300 | Fehler „statistisch planen“ |
| Ziehreihenfolge ohne jede Position genau einmal, negative Beträge | Fehler |
| Grundgesamtheit ohne Wert (MUS) | Umfang 0 mit Hinweis |
| Umfang ≥ N (SRS nach Leitfaden) | Vollerhebung mit Hinweis |
| Unterschreitungen von Faustregeln (30 Einheiten, 3 je Schicht) | Hinweis bzw. angewandte Mindestzahl mit Hinweis |

## Abgrenzung

- Hochrechnung, Präzision der Auswertung, TER und RER:
  `auditcore_extrapolation`.
- Zwei-Perioden-Verfahren und mehrstufige Stichproben sind nicht enthalten.
- Die Risikoeinstufung, die bei der Zwischengeschalteten Stelle über „keine
  Prüfung / Teilprüfung / Vollprüfung“ entscheidet, liefert die Anwendung.
- Das Paket zieht keinen Zufall aus globalem Zustand; NumPy-Generatoren
  bleiben beim Consumer.
- Die Methoden geben die Formeln des Leitfadens wieder; die Wahl des
  Verfahrens und die Festlegung des Umfangs nach pflichtgemäßem Ermessen
  bleiben bei der Prüfbehörde.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten | Gewolltes Verhalten | Legacy-Variante | Nachweis |
|---|---|---|---|
| flowstat-MUS-Formel ergibt bei üblicher Wesentlichkeit n = 1 | `portal.mus_poisson` maßgeblich; neue Planung nach Leitfaden (`guidance.*`) | `flowstat.mus_z_attribute` (SUPERSEDED), `legacy.flowstat_mus_size`, `legacy.portal_mus_size_legacy` | SA-C01, `tests/test_legacy_replay.py` |
| unbekanntes Konfidenzniveau still als 95 % | Fehler | `legacy.flowstat_srs_size`, `legacy.portal_srs_size` | SA-C02 |
| Zufall aus globalem NumPy-Zustand | ausdrücklicher Generator | – | SA-C04, I4 |
| flowstat: negative Werte in der kumulierten Summe, Mehrfachtreffer | Variante `portal` | `systematic_mus` mit `variant="flowstat"` | SA-C05, I3 |
| flowinvoice: Belegziehung fest im Prüfplan verdrahtet | versioniertes Profil `zs.value_share_escalation` mit Parametern; Verhalten unverändert (240/240 Ziehungen gleich) | – | `tests/test_intermediate_body_parity.py` |

Die Legacy-Varianten sind nur für Nachvollzug und Migration gedacht, nicht
für neue Aufrufer.
