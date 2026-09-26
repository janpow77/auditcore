# Stichprobenumfang nach dem KOM-Leitfaden (`auditcore_sampling.guidance`)

Status aller Methoden dieses Moduls: `GUIDANCE_EGESIF_16_0014_01` („nach
Leitfaden“). Sie stehen getrennt neben den charakterisierten Altmethoden aus
flowstat und audit-portal (`auditcore_sampling.sizes`, `legacy`) und ändern
deren Verhalten nicht.

Quelle: Europäische Kommission, *Guidance on sampling methods for audit
authorities*, EGESIF_16-0014-01 vom 20.01.2017 („Leitfaden“); die Formeln
gelten unverändert für 2021–2027 (Art. 79 VO (EU) 2021/1060). Jede Funktion
nennt die Fundstelle im Docstring und in jedem Schritt der Herleitung
(`GuidancePlan.steps`).

## Paketort

Das Modul liegt in `auditcore_sampling`, nicht in `auditcore_extrapolation`:

- Die Aufteilung ist dort bereits festgelegt: Die Hochrechnung verweist für
  Umfang und Auswahl ausdrücklich auf `auditcore_sampling`
  (`auditcore_extrapolation/docs/abgrenzung.md`).
- `auditcore_extrapolation` hängt (nur für Tests) schon von
  `auditcore_sampling` ab. Läge die Planung in der Hochrechnung und
  bräuchte `sampling` die Faktoren von dort, entstünde ein Zyklus.
- Die Planung braucht nur z (Tabelle 3), RF (Tabelle 4) und EF (Tabelle 5).
  Die ersten beiden stehen in beiden Paketen; ihre Gleichheit und die gleiche
  Abtrennung der Hochwertschicht prüft der Konsistenztest
  `auditcore_extrapolation/tests/test_planning_consistency.py` – der einzige
  Ort, an dem beide Pakete installiert sind.

## Formeln

| Methode (`method`) | Formel | Fundstelle | Funktion |
|---|---|---|---|
| `guidance.srs` | n = (N × z × σ_e / (TE − AE))² | 6.1.1.2 | `equal_probability_size` |
| `guidance.srs_stratified` | σ_w² = Σ N_h/N × σ_eh², n wie oben, n_h = N_h/N × n, Vollerhebungsschichten n_h = N_h | 6.1.2.2 | `stratified_equal_probability_size` |
| `guidance.difference` | wie `srs` | 6.2.1.2 | `equal_probability_size` |
| `guidance.difference_stratified` | wie `srs_stratified` | 6.2.2.2 | `stratified_equal_probability_size` |
| `guidance.mus_standard` | n = (z × BV × σ_r / (TE − AE))², Hochwertschicht BVᵢ > BV/n, iterativ BVᵢ > BV_s/n_s | 6.3.1.2, 6.3.1.3 | `mus_standard_size`, `high_value_split` |
| `guidance.mus_stratified` | σ_rw² = Σ BV_h/BV × σ_rh², n_h = BV_h/BV × n, Schwellenwert BV_h/n_h | 6.3.2.2, 6.3.2.3 | `mus_stratified_size` |
| `guidance.mus_conservative` | n = BV × RF / (TE − AE × EF), SI = BV/n; EF nur bei AE > 0 | 6.3.5.2, 6.3.5.3 | `mus_conservative_size` |
| `guidance.nonstatistical` | Mindestumfang je Regelprofil (unten) | 6.4.3 | `nonstatistical_minimum` |
| σ_e aus Vorstichprobe | √(Σ (Eᵢ − Ē)² / (n_p − 1)) | 6.1.1.2 | `error_sd` |
| σ_r aus MUS-Vorstichprobe | rᵢ = Eᵢ/BVᵢ, über BV/n: Eᵢ/(BV/n) | 6.3.1.2, Fußnote 27 | `error_rates`, `error_rate_sd` |
| Endlichkeitskorrektur (wahlweise) | n′ = n / (1 + n/N) | Fußnote 25 | `finite_population_correction=True` |

Gemeinsam: TE = Wesentlichkeit × BV (höchstens 2 %, niedriger zulässig),
AE = erwartete Fehlerquote × BV (kleiner als die Wesentlichkeit), der Umfang
wird aufgerundet. Proportionale Aufteilungen runden nach dem größten Rest
(die Summe bleibt n). Hinweise statt stiller Korrekturen: unter 30 Einheiten
(Fußnote 37), Umfang über 10 % von N ohne Endlichkeitskorrektur, mindestens
3 Einheiten je Schicht (6.1.2.2, wird angewandt und gemeldet).

Faktorprofile wie in `auditcore_extrapolation`: `kom_2017_tables` (Werte wie
gedruckt, nur deren Konfidenzniveaus) und `exact` (z = Φ⁻¹(1 − (1 − KN)/2),
RF = −ln(1 − KN)); den Expansionsfaktor gibt es nur als Tabelle 5.

## Nicht-statistische Mindestumfänge

| Regel (`rule`) | Inhalt | Quelle |
|---|---|---|
| `cpr_2021_art79_2` | nur bei weniger als 300 Stichprobeneinheiten; mindestens 10 % der Einheiten des Geschäftsjahres, zufällig | Art. 79 Abs. 2 VO (EU) 2021/1060 |
| `cpr_2013_art127_1` | mindestens 5 % der Vorhaben und 10 % der Ausgaben; dazu Tabelle 6 nach Bewertung der Systemprüfung (`works_well`, `works`, `works_partially`, `does_not_work`) | Art. 127 Abs. 1 VO (EU) Nr. 1303/2013; Leitfaden 6.4.3 |

Das Ergebnis ist ein Mindestwert; den Umfang legt die Prüfbehörde nach
pflichtgemäßem Ermessen fest (6.4.3). Über 150 Einheiten empfiehlt der
Leitfaden, vorab den Rat der Kommission einzuholen (6.4.1).

## Referenzfälle (nachgerechnet, `tests/test_guidance_reference.py`)

| Beispiel | Leitfaden | Bibliothek | Abweichung |
|---|---|---|---|
| 6.1.1.6 SRS | n ≈ 53 | 53 (52,39) | keine |
| 6.1.2.6 SRS geschichtet | σ_w² 24.737.134, n ≈ 121 + 5 = 126, 90 / 31 / 5 | σ_w² 24.711.404, 126, 90 / 31 / 5 | **Unstimmigkeit:** N₁ + N₂ = 4.807, gerechnet wird mit N = 4.802. **Druckfehler:** √24.734,134 in der Formel für n. Ergebnis gleich. |
| 6.2.1.6 Differenzenschätzung | n ≈ 101 | 101 (100,07) | keine |
| 6.2.2.6 Differenzenschätzung geschichtet | σ_w² 32.092.103.451, n ≈ 51, 16 / 35 / 5 | gleich (50,75) | **Druckfehler:** z = 0,845 in der Formel (mit 0,845 wären es 52); geprüft werden später 60, weil die Vorstichprobe (20) in Schicht 1 größer ist als der Anteil 16. |
| 6.3.1.7 MUS | n ≈ 77, Schwellenwert 54.593.922, SI 49.464.419 | 77 (76,37), 54.543.922, 49.464.419 | **Druckfehler:** Schwellenwert; BV/77 = 54.543.922. |
| 6.3.1.7 Fehlerquoten | 0,0491 und 0,0371 (Eᵢ/(BV/50)) | gleich | keine |
| 6.3.2.7 MUS geschichtet | σ_rw² 0,004425, n ≈ 148, 89 / 59 | 148, 88 / 60 | **Rundung:** n₁ = 88,33 wird im Leitfaden aufgerundet, in 6.1.2.6 (90,26) abgerundet; die Bibliothek rundet einheitlich nach dem größten Rest. |
| 6.3.5.7 MUS konservativ | n ≈ 136, SI 30.881.485 | 136 (135,88), 30.881.485 | keine |

## Konsistenz Planung → Stichprobe → Hochrechnung

`auditcore_extrapolation/tests/test_planning_consistency.py` (Hypothesis):
Umfang planen, mit `simple_random` bzw. `systematic_mus` ziehen, mit
`auditcore_extrapolation.assess` hochrechnen.

- Gleiche Wahrscheinlichkeit und MUS-Standard: Zeigt die Stichprobe genau die
  geplante Standardabweichung, ist SE = (TE − AE) × √(n_roh / n) ≤ TE − AE;
  ohne Fehler ist SE = 0 und das Ergebnis „nicht wesentlich“.
- MUS konservativ: Ohne Fehler ist die Obergrenze BP = BV × RF / n
  = (TE − AE × EF) × n_roh / n ≤ TE. Ist n_roh ganzzahlig, gilt ULE = TE und
  der Leitfaden (4.12) wertet „nicht schlüssig“.
- Tabellen 3 und 4 sind in beiden Paketen gleich; `high_value_split` und
  `auditcore_extrapolation.split_top_stratum` trennen dieselben Einheiten ab.

Nicht enthalten: Zwei-Perioden-Verfahren (6.1.3, 6.2.3, 6.3.3, 6.3.4) und
mehrstufige Stichproben (6.5).
