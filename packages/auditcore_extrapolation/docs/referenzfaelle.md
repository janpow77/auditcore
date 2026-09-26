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
