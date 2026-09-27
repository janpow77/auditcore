# Formeln, Quellen und Referenzfälle

Quelle der Formeln: Europäische Kommission, *Guidance on sampling methods for
audit authorities*, EGESIF_16-0014-01 vom 20.01.2017 (im Folgenden „Leitfaden“),
und die Vorlage *RER calculation* CPRE_23-0013-01 Annex 3. Die Formeln gelten
für den Zeitraum 2021–2027 unverändert (Art. 79 VO (EU) 2021/1060); Begriffe
TER und RER nach Art. 2 Nr. 35 und 36 der Verordnung.

## Formeln

| Größe | Formel | Fundstelle | Funktion |
|---|---|---|---|
| z | Tabelle 3 (0,842 / 1,036 / 1,282 / 1,645 / 1,960) bzw. Φ⁻¹(1 − (1 − KN)/2) | 5.3 | `z_value` |
| Mittelwertschätzung | EE = N × ΣE / n | 6.1.1.3 | `mean_per_unit_error` |
| Verhältnisschätzung | EE = BV′ × ΣE / ΣBV′ᵢ | 6.1.1.3; Anhang 1, 2.3 | `ratio_error` |
| Präzision | SE = N × z × s / √n; q-Variable qᵢ = Eᵢ − (ΣE/ΣBV) × BVᵢ | 6.1.1.4 | `precision`, `ratio_q_values` |
| geschichtet | SE = N × z × s_w / √n, s_w² = Σ N_h/N × s_h² | 6.1.2.4, 6.2.2.4 | `stratified_precision` |
| Schätzerwahl | Verhältnis, wenn COV(E, BV)/VAR(BV) > ER/2 | 6.1.1.3 | `estimator_check` |
| Differenzenschätzung | CBV = BV − TER, LL = CBV − SE, Vergleich mit BV − TE | 6.2.1.5; Anhang 1, 3 | `evaluate` |
| MUS | EE = EE_e + Σ BV_hs/n_hs × Σ Eᵢ/BVᵢ | 6.3.1.4, 6.3.2.4 | `tainting_projection` |
| MUS-Präzision | SE = z × √(Σ BV_hs²/n_hs × s_rh²) | 6.3.1.5, 6.3.2.5 | `mus_precision` |
| MUS-Verhältnis | EE_s = BV′_s × Σ(E/BV)/Σ(BV′/BV), SE = z × BV_s/√n_s × s_rq | Anhang 1, 4.2 | `project` |
| Hochwertschicht | BVᵢ > BV/n, iterativ BVᵢ > BV_s/n_s | 6.3.1.3 | `split_top_stratum` |
| konservativ | SI = BV/n, BP = SI × RF(0), IAᵢ = (RF(i) − RF(i−1) − 1) × SI × Eᵢ/BVᵢ | 6.3.5 | `incremental_allowances` |
| Faktoren | Tabelle 4 (RF(0)), Anhang 3 (RF(k)) bzw. exakte Poisson-Obergrenze | 6.3.5.2, Anhang 3 | `reliability_factor`, `poisson_factor` |
| TER | EE + abgegrenzte systemische + nicht korrigierte anomale Fehler, geteilt durch BV | Anhang 1, Anhang 6 | `evaluate` |
| Obergrenze | ULE = TER + SE | 4.12; Anhang 1 | `evaluate` |
| Ergebnis | TER > TE wesentlich; ULE < TE nicht wesentlich; sonst nicht schlüssig | 4.12, 6.4.6 | `conclude` |
| Mehrere Zeiträume | EE = Σ_t EE_t; SE = √(Σ_t SE_t²), d. h. z × √(Σ_t N_t² s_t²/n_t) bzw. z × √(Σ_t Σ_h BV_hts²/n_hts × s_rhts²) | 6.1.3.3/4, 6.2.3.3/4, 6.3.3.4/5, 6.3.4.4/5, 6.4.9, 7.3; Anhang 2 | `project_periods`, `combined_precision` |
| Teilstichprobe | EE_i = BV_i × ΣE_ij/ΣBV_ij, N_i × ΣE_ij/n_i oder BV_is/n_is × ΣE_ij/BV_ij je Teilschicht, plus Vollerhebung (z. B. Lead-Partner) | 7.6.3, 6.5.3.3.1 | `project_subsample` |
| Neuberechnung Konfidenzniveau | z* = z × (TE − Gesamtfehler)/SE; KN* = 1 − 2 × (1 − Φ(z*)) | 7.7; Tabelle 1 in 3.2.1 | `recalculate_confidence` |
| Gruppen von Programmen | Gesamtauswertung über alle Schichten, je Programm über dessen Schichten; Hinweis unter 30 Beobachtungen | 7.8 | `assess_groups` |
| Merkmalsstichprobe | EDR = k/n; SE = z × √(p(1 − p)/n); ULD = EDR + SE | 7.9.3–7.9.5 | `evaluate_attributes` |
| Ausschluss (verhältnismäßige Kontrolle) | EE_s × BV_s,orig/BV_s,red (N-Verhältnis bei Mittelwertschätzung), EE_e × BV_e,orig/BV_e,red; SE ebenso | 7.10.2 | `extend_to_original`, `extension_factor` |
| Negative Einheiten | positive Grundgesamtheit (Buchwert für Stichprobe und TER), negative gesondert; netto = positiv + negativ | 4.6 | `split_population` |
| Discovery / Stop-or-go | exakte Obergrenze p_u mit P(X ≤ k \| n, p_u) = 1 − KN | 7.9.6 (Methodenwahl) | `upper_deviation_limit` |
| RER | F = A − E1 − E2, G = D × F, I = F − H, J = G − H, K = J/I; L, M bei ROUND(K; 4) > 2 % | Annex 3 | `residual_error_rate` |

## Nachgerechnete Beispiele

| Beispiel | Ergebnis Leitfaden | Test | Abweichung |
|---|---|---|---|
| 6.1.1.6 SRS | EE₁ 566.703, EE₂ 548.058, SE₁ 514.169, SE₂ 512.134 | `test_srs_standard_6_1_1_6`, `test_srs_example_from_units` | EE aus den gedruckten Summen 566.680 bzw. 548.036 (< 0,01 %): Der Leitfaden rechnet mit ungerundeten Tabellenwerten. |
| 6.1.2.6 SRS geschichtet | EE₁ 4.519.900, EE₂ 4.389.095, SE₁ 3.695.304, SE₂ 3.733.563 | `test_srs_stratified_6_1_2_6` | Standardabweichungen auf ganze Euro gedruckt (≤ 0,1 %). **Druckfehler:** SE₂ zeigt √59 im Nenner, das Ergebnis gehört zu √121. |
| 6.2.1.6 Differenzenschätzung | EE 51.096.780, SE 52.597.044, CBV 4.148.785.244, LL 4.096.188.200 | `test_difference_estimation_6_2_1_6` | keine |
| 6.3.1.7 MUS | SI 49.464.419, EE 61.829.809, SE 60.831.129, ULE 122.660.937 | `test_mus_standard_6_3_1_7`, `test_mus_standard_example_from_units` | keine |
| 6.3.2.7 MUS geschichtet | EE 65.016.597, SE 22.958.216, ULE 87.974.813 | `test_mus_stratified_6_3_2_7` | keine |
| 6.3.5.7 MUS konservativ | n 136, SI 30.881.485, EE 41.102.934, BP 71.336.231, ULE 126.869.926 | `test_mus_conservative_6_3_5_7` | Die Zuschlagstabelle ist nur in Auszügen gedruckt; geprüft sind die Zeilen 12–16 und SE = BP + IA. |
| 6.3.5.5 Zuschlag | 0,58 × 0,25 × 200.000 = 29.000 | `test_mus_conservative_first_allowance_example_6_3_5_5` | Der Text nimmt RF(0) = 2,31 aus Tabelle 4, das Rechenbeispiel 6.3.5.7 RF(0) = 2,30 aus Anhang 3. Die Bibliothek folgt dem Rechenbeispiel (Zuschläge aus Anhang 3, Basispräzision aus Tabelle 4). |
| 6.4.7 nicht-statistisch PPS | EE 145.439, TE 440.625 | `test_nonstatistical_pps_6_4_7`, `test_nonstatistical_pps_example_from_units` | Der Leitfaden druckt BV_s einmal als 9.619.623 statt 9.619.263; das Ergebnis gehört zu 9.619.263. |
| Annex 3 A, B, C.1, C.2, Negative units | Zellwerte der Vorlage | `tests/test_reference_rer.py` | keine (Dezimalarithmetik) |

### Kapitel 6 (zwei Zeiträume, ETC) und Kapitel 7

| Beispiel | Ergebnis Leitfaden | Test | Abweichung |
|---|---|---|---|
| 6.1.3.6 SRS, zwei Halbjahre | EE₁ 43.421.670, EE₂ 51.252.484, SE₁ 41.980.051, SE₂ 36.325.544, ULE₂ 87.578.028 | `test_srs_two_periods_6_1_3_6` | **Druckfehler:** Der Zähler von r₂ steht als 51.252.451 statt 51.252.484. |
| 6.2.3.6 Differenzenschätzung, zwei Halbjahre | EE 78.677.283, CBV 6.362.049.907, SE 82.444.754, LL 6.279.605.153 | `test_difference_two_periods_6_2_3_6` | **Druckfehler:** Die EE-Formel nennt n = 142 und 68, gerechnet ist mit 73 und 47; die SE-Formel nennt s_e2 = 78.849, das Ergebnis gehört zu 78.489 (Tabelle). |
| 6.3.3.7 MUS, zwei Halbjahre | EE 99.336.400, SE 64.499.188, ULE 163.835.589 | `test_mus_two_periods_6_3_3_7` | keine |
| 6.3.4.7 MUS geschichtet, zwei Halbjahre | EE 513.036, SE 1.062.778, ULE 1.575.814 | `test_mus_two_periods_stratified_6_3_4_7` | **Druckfehler:** Die Präzision setzt für Programm 1/1. Halbjahr die Summe der Quoten 0,0823 statt s_r = 0,0868 ein; richtig SE 1.083.499 (Ergebnis bleibt „nicht wesentlich“). |
| 7.3.2.2 MUS, vergrößerte erste Stichprobe | EE 47.973.814, SE 27.323.507, ULE 75.297.320 | `test_mus_two_periods_enlarged_first_sample_7_3_2_2` | keine |
| 6.4.9.1 nicht-statistisch, gleiche Wahrscheinlichkeit | EE 649.247,94, TE 1.206.170 | `test_nonstatistical_two_periods_equal_probability_6_4_9_1` | BV_s2 steht einmal als 33.621.524 statt 33.621.525 (< 1 €). |
| 6.4.9.2 nicht-statistisch, PPS | EE 864.435, TE 1.326.170 | `test_nonstatistical_two_periods_pps_6_4_9_2` | keine |
| 6.5.3.3.2 ETC: Lead-Partner + Partner-Stichprobe | Vorhabenfehler 5.390 / 20.327 / 554 / 6.067, EE 357.622 | `test_etc_lead_partner_and_partner_sample_6_5_3_3_2` | Die Vorhabenkennung 65 kommt zweimal vor (im Test 65a/65b). Das Beispiel rundet die Vorhabenfehler auf ganze Euro (Σ 32.338 statt 32.337,4); EE daher 357.616 statt 357.622. |
| 7.6.5 zweistufig (MUS + Zahlungsanträge) | Fehler der Top-Vorhaben 46.532.007, EE 97.678.216, 2,33 % | `test_two_stage_sampling_7_6_5` | keine |
| 7.7 Konfidenzniveau neu berechnen | z* 1,419, 84,4 % | `test_recalculated_confidence_level_7_7` | keine |
| 7.8.2 Gruppe von Programmen | EE 2.681.139; je Programm SE 442.105/456.204, EE 2.507.452/173.687 | `test_group_of_programmes_7_8_2` | **Druckfehler:** Zeile P für Programm 1 zeigt 2,90 %, (M + L)/(A + B) = 3,01 %; n₃ = N₃ steht als 5 statt 8. |
| 7.9.5 Merkmalsstichprobe | ULD 0,023 bei 3 Abweichungen in 150 (95 %) | `test_attribute_sampling_7_9_5` | **Formelfehler:** 7.9.4 druckt SE = z × p(1 − p)/√n ohne Wurzel über p(1 − p), das Beispiel rechnet so. Die Normalapproximation der Binomialverteilung ist z × √(p(1 − p)/n); die Bibliothek rechnet so (ULD 0,0424). |

| 7.10.3.1 b PPS, Ersetzen einer Einheit der Hochwertschicht | EE 50.020.779 | `test_pps_replacement_of_a_high_value_unit_7_10_3_1_b` | keine |
| 7.10.3.2 MUS, Ausschluss | EE 50.225.817, SE 53.015.513, ULE 103.241.330 | `test_mus_exclusion_7_10_3_2` | keine |
| 7.10.3.3 MUS konservativ, Ausschluss | EE 41.192.637, SE 85.998.313 | `test_conservative_exclusion_7_10_3_3` | nur Faktor nachgerechnet (Zuschläge nicht gedruckt) |
| 7.10.3.4 SRS, Ausschluss | Mittelwert: EE 30.317.560,43, SE 15.316.501,38, ULE 45.634.061,81; Verhältnis: EE 33.142.008,96 | `test_srs_mean_per_unit_exclusion_7_10_3_4`, `test_srs_ratio_exclusion_7_10_3_4` | **Druckfehler (Planung, nicht nachgerechnet):** Der Text nennt für σ_e vier Werte aus „3 früheren Stichproben“ (97.654 doppelt), die Formel mittelt drei (34.973, 97.654, 43.564 → 58.730). Die Präzision der Verhältnisschätzung ist nicht beziffert (s_q fehlt); geprüft ist die Erweiterung SE_red × 1,0011. |
| 4.6 negative Einheiten | X/Y/Z: positiv 120.000, netto 115.000; Variante 3: 24.300 positiv, 4.300 negativ | `test_negative_units_example_4_6` | keine |
| 7.9.6 Discovery/Stop-or-go | Tabellenwerte der Merkmalsstichprobe (5 %, 95 %): n = 59/93/124 für 0/1/2 Abweichungen | `test_exact_upper_limit_matches_the_attribute_sampling_table` | Der Leitfaden druckt keine Werte; Vergleich mit den üblichen Tabellen der Fachliteratur. |

Einige Beispiele lassen sich nicht aus Einzeleinheiten nachbauen: Bei nicht
negativen Fehlern gilt s ≤ ΣE/√n, die gedruckten Standardabweichungen in
6.1.3.6 (1. Halbjahr: 69.815 bei ΣE 199.185, n = 49) und 6.3.3.7
(2. Halbjahr: 0,29 bei Σ Quoten 1,1875, n = 96) liegen darüber. Diese
Beispiele werden mit den gedruckten Summen nachgerechnet; die Summe über
Zeiträume prüfen die Eigenschaftstests (`tests/test_properties_chapter7.py`,
u. a. „zwei Zeiträume MUS = MUS geschichtet nach Zeitraum“).

Die Stichprobenumfänge der Beispiele (erste und zweite Periode, Teilstichproben)
sind Planung und gehören zu `auditcore_sampling`; ihre Druckfehler (z. B. in
6.2.3.6 σ_e2 = 107.369 statt 87.369, in 6.3.4.7 n_12s = 14 und 18
nebeneinander) sind hier nicht nachgerechnet.

Nicht als Referenzfall genutzt: 6.2.2.6 (stratifizierte Differenzenschätzung)
enthält widersprüchliche Angaben (Stichprobe 16 statt 20 in Schicht 1,
EE 38.438.139 und 39.908.283 nebeneinander, z = 0,845 statt 0,842).

## Tabellenwerte

Alle 510 Faktoren aus Anhang 3 liegen höchstens 0,005 neben der exakten
Poisson-Obergrenze (`test_appendix3_equals_exact_poisson_limits_rounded`).
Tabelle 4 rundet RF(0) teilweise auf (90 %: 2,31 statt 2,3026; 70 %: 1,21;
50 %: 0,70), Anhang 3 kaufmännisch (2,30; 1,20; 0,69). Für 0,50/0,80/0,90/0,95/0,99
stimmt Tabelle 4 mit den Faktoren von `auditcore_sampling` (`portal.mus_poisson`)
überein (`test_basic_factors_agree_with_auditcore_sampling`).
