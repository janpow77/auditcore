# Spezifikation auditcore_statistics

Stand: 26.09.2026, Paketversion 0.3.4. Charakterisierung: flowstat
`run_benford` (32 Fälle, `tests/test_legacy_replay.py`) und flowinvoice
`BenfordsLawAnalyzer` (65 Fälle, `tests/test_legacy_flowinvoice.py`),
Einzelheiten in `docs/behavior-changes.md`. Eigenschaftstests:
`tests/test_spezifikation.py`.

## Zweck

Beschreibende Prüfstatistik für Prüfbehörden und Prüfanwendungen: Benford-Test
der ersten Ziffer und der ersten zwei Ziffern mit Chi-Quadrat-Statistik und
p-Wert, dazu Konformitätsmaße (MAD-Band, z-Test je Ziffer, Zweitziffertest)
nach ausdrücklich benannten, quellengebundenen Profilen. Die Ergebnisse sind
Statistiken, keine Feststellungen: Das Paket markiert keine Datensätze und
wählt keine Schwellen still.

## Verträge

| Funktion/Klasse | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `benford_test(values, *, digits, short_values=None, significance_level=None)` | Folge aus `int`, `float`, `Decimal`, `None`/NaN (fehlend); `digits` 1 oder 2; bei `digits=2` Pflichtangabe `short_values` = `"exclude"` oder `"pad"`; optional α ∈ (0, 1) | `BenfordResult` (Methode `auditcore_statistics.benford/1`) mit Zeilen je Ziffer(ngruppe), Ausschlusszählern `missing`, `zero`, `short_excluded`, Zähler `negative_absolute`, χ², Freiheitsgraden, p-Wert, `deviates_at_level` | keine, deterministisch |
| `expected_share(d)` | Ziffer bzw. Zifferngruppe d ≥ 1 | log10(1 + 1/d) | keine |
| `chi2_survival(x, dof)` | Statistik, Freiheitsgrade ≥ 1 | P(X ≥ x) der Chi-Quadrat-Verteilung | keine |
| `conformity.assess(result, test, profile_id)` | Ergebnis von `benford_test`; `test` = `first` (digits=1), `first_two` oder `second` (digits=2); Profil ausdrücklich (derzeit `nigrini.2012`) | `Conformity` mit MAD, MAD-Stufe und -Bezeichnung, z je Ziffer, auffälligen Ziffern, χ² und p-Wert | keine |
| `recommended_flowinvoice_benford(values)` | Beträge | `benford_test(values, digits=1, significance_level=0.05)` | keine |
| `legacy_run_benford`, `legacy_flowinvoice_benford` | wie die Quellen | exakte Altergebnisse | keine |
| REST `auditcore_statistics.web` (Extra `web`) | JSON-Objekt, Obergrenze 1 000 000 Werte, 64 MiB | JSON-Ergebnis bzw. `{"error": {"code", "message"}}` | keine |

Ziffernbildung: signifikante Ziffern aus der exakten Dezimaldarstellung
(`repr` für `float`, sonst `str`, dann `Decimal.normalize`); negative Werte
zählen mit ihrem Betrag, Null wird ausgeschlossen und gezählt. Summen laufen in
NumPy-Paarweisenreihenfolge (bitgleich zu den Quellen).

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Die Benford-Erwartungswerte summieren über 1..9 und über 10..99 zu 1 und fallen streng mit der Ziffer. | `test_i1_erwartete_anteile_summieren_zu_eins` |
| I2 | Jeder Eingabewert ist entweder analysiert oder als fehlend, null bzw. kurz ausgeschlossen ausgewiesen (Summe = Eingabelänge); beobachtete Anzahlen summieren zur Zahl der analysierten Werte, Anteile zu 1; negative Werte werden gezählt. | `test_i2_jeder_wert_ist_gezaehlt_oder_als_ausschluss_ausgewiesen` |
| I3 | Das Ergebnis hängt nicht von der Reihenfolge der Werte ab. | `test_i3_reihenfolge_der_werte_ist_ohne_einfluss` |
| I4 | Vorzeichen, Skalierung mit Zehnerpotenzen und Datentyp (int, float, Decimal) desselben Werts ändern die Ziffernzeilen nicht. | `test_i4_vorzeichen_skala_und_datentyp_sind_ohne_einfluss` |
| I5 | χ² ≥ 0, p ∈ [0, 1], Freiheitsgrade 8 bzw. 89; `chi2_survival` fällt monoton mit der Statistik. | `test_i5_statistik_nichtnegativ_p_wert_im_einheitsintervall`, `test_i5_p_wert_faellt_mit_der_statistik` |
| I6 | Ohne ausdrückliches Signifikanzniveau gibt es keine Aussage (`deviates_at_level` = `None`); mit Niveau gilt genau p < α. | `test_i6_aussage_nur_mit_ausdruecklichem_niveau` |
| I7 | Konformität: MAD ≥ 0 und liegt im gemeldeten Band des Profils; auffällige Ziffern sind genau die mit z > z_krit; der Zweitziffertest hat 10 Zeilen, deren Erwartungsanteile zu 1 summieren. | `test_i7_konformitaet_mad_band_und_z_test_konsistent` |
| I8 | Werte mit nur einer signifikanten Ziffer werden im Zwei-Ziffern-Test nur nach ausdrücklicher Regel behandelt: ohne `short_values` Fehler, `pad` zählt d als 10·d, `exclude` weist sie als kurz aus. | `test_i8_einstellige_werte_im_zweiziffertest_nur_mit_ausdruecklicher_regel` |
| I9 | Wahrheitswerte, Texte und unendliche Werte werden abgewiesen, nie still umgedeutet. | `test_i9_nicht_numerisches_wird_abgewiesen_nicht_umgedeutet` |

## Fehlerfälle

`StatisticsInputError` (`ValueError`) mit deutscher Meldung:

- `digits` nicht 1 oder 2; `short_values` fehlt bei `digits=2` oder ist bei
  `digits=1` angegeben; Signifikanzniveau nicht in (0, 1);
- Wert ist Wahrheitswert, Text oder anderer Nicht-Zahlentyp; `±inf` bzw.
  nicht endliches `Decimal`;
- kein auswertbarer Wert (alles fehlend, null oder kurz ausgeschlossen);
- unbekanntes Bewertungsprofil oder unbekannter Test; Test passt nicht zu
  `digits` des Ergebnisses.

`chi2_survival` weist Freiheitsgrade < 1 mit `ValueError` ab. Die
Legacy-Varianten werfen die Meldungen der Quellen (`ValueError`), außer bei
`±inf`, das in flowinvoice endlos lief.

## Abgrenzung

- Keine Einstufung von Datensätzen als verdächtig und keine Feststellungen;
  die fachliche Würdigung liegt bei der Prüferin bzw. dem Prüfer.
- Keine Stichprobenziehung und keine Hochrechnung (`auditcore_sampling`,
  `auditcore_extrapolation`).
- Kein Einlesen von Tabellen und keine Spaltenauswahl; die Anwendung übergibt
  Zahlenfolgen.
- Keine Methode aus audit-portal (`audit_tests_service.benford_test`); sie
  wäre ein eigenes, getrennt zu charakterisierendes Profil.

## Bewusste Abweichungen vom Altverhalten

Einzelheiten: `docs/behavior-changes.md` (ST-C01 bis ST-C07). Die
Legacy-Varianten reproduzieren die Quellen exakt und sind nicht für neue
Aufrufer gedacht.

| Altverhalten | Gewolltes Verhalten | Legacy-Variante | Nachweis |
|---|---|---|---|
| Zwei-Ziffern-Test bricht bei einstelligen Werten ab (ST-C01) | `short_values` ausdrücklich, kurze Werte gezählt | `legacy_run_benford` | I8 |
| Ziffern hängen vom pandas-Datentyp ab, wissenschaftliche Notation bricht ab (ST-C02/03) | exakte Dezimalziffern | `legacy_run_benford` (`dtype`) | I4 |
| Wahrheitswerte brechen ab, Texte werden still zu NaN (ST-C04) | Abweisung | `legacy_run_benford` | I9 |
| Ausschlüsse ohne Ausweis (ST-C05) | Zähler im Ergebnis | `legacy_run_benford` | I2 |
| `significant = p < 0.05` fest (ST-C06) | Aussage nur mit ausdrücklichem Niveau | `legacy_run_benford` | I6 |
| flowinvoice: gerundete Erwartungswerte, fester kritischer Wert 15,507, p-Wert als Stufenfunktion, Mindestumfang 50, Texte zählen | `recommended_flowinvoice_benford` = `benford_test` mit α = 0,05 (Entscheidung K10) | `legacy_flowinvoice_benford` | `test_legacy_flowinvoice.py` |
| flowinvoice: `±inf` Endlosschleife (ST-C07) | `ValueError` | – (auch die Legacy-Variante bricht ab) | `test_legacy_flowinvoice.py` |

Offen (HUMAN_DECISION_REQUIRED aus `docs/behavior-changes.md`): welche
Konvention (`exclude` oder `pad`) Anwendungen für einstellige Werte im
Zwei-Ziffern-Test verwenden; das Paket verlangt deshalb die ausdrückliche
Angabe.
