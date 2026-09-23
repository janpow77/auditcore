# Legacyverhalten und korrigierter Vertrag: Benford

Quelle: `janpow77/flowstat@d665ac2`, `backend/app/services/analysis_core_service.py:run_benford`,
tatsächlich ausgeführt mit numpy 1.26.2, pandas 2.1.3, scipy 1.11.4
(`tools/capture_flowstat_benford.py`, 32 Fälle, 40 Chi-Quadrat-Referenzen).
`legacy_run_benford` reproduziert alle 29 datenbezogenen Fälle exakt ohne
NumPy/SciPy (Summen in NumPy-Paarweisenreihenfolge, NumPy-Rundung,
p-Wert relativ ≤ 3·10⁻¹³). Parameter- und Spaltenprüfung bleiben beim Consumer.

| ID | Original | `benford_test` | Begründung |
|---|---|---|---|
| ST-C01 | Zwei-Ziffern-Test bricht ab (SciPy-Summenfehler), sobald ein Wert nur eine signifikante Ziffer hat – bei Ganzzahldaten fast immer. | `short_values` muss ausdrücklich `exclude` oder `pad` sein; ausgeschlossene Werte werden gezählt. | Ergebnis statt Absturz; Konvention ist eine fachliche Wahl. |
| ST-C02 | Ziffern hängen vom pandas-Datentyp ab: 5 → „5“, 5.0 → „50“. | Ziffern aus der exakten Dezimaldarstellung, unabhängig vom Typ. | Gleicher Wert, gleiches Ergebnis. |
| ST-C03 | Wissenschaftliche Notation (1e-05) bricht den Zwei-Ziffern-Test ab. | Exakte signifikante Ziffern (Decimal). | Korrekte Ziffernbildung. |
| ST-C04 | Booleans brechen ab; Texte werden still zu NaN (`"4,5"` fällt weg). | Booleans, Texte und Unendlich werden abgewiesen. | Keine stille Umdeutung. |
| ST-C05 | Fehlende, Null- und negative Werte verschwinden ohne Ausweis. | Anzahlen `missing`, `zero`, `negative_absolute`, `short` im Ergebnis. | Nachvollziehbarkeit. |
| ST-C06 | `significant = p < 0.05` fest eingebaut. | Aussage nur mit ausdrücklichem `significance_level`. | Keine automatisch gewählten Schwellen, keine Befunde. |

## Ergänzung 0.2.0: `legacy_flowinvoice_benford`

Quelle `flowinvoice@fb2d185 backend/app/services/fraud_detection/benfords_law.py`
(Blob `77bf2b1`, in audit-portal identisch), ausgeführt mit
`tools/capture_flowinvoice_benford.py`: 65 Fälle, alle exakt reproduziert.
Methodisch **nicht** gleich `benford_test` (gerundete Erwartungswerte 0,301 …
0,046, fester kritischer Wert 15,507 statt p-Wert, p-Wert als Stufenfunktion,
Mindestumfang 50, z-Test je Ziffer mit 2,576, stille Ausschlüsse, Texte wie
`"12.5"` zählen). Deshalb eigenes, benanntes Legacyprofil; keine Angleichung.

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| ST-C07 | `±inf` führt zu einer Endlosschleife. | `ValueError`. | Kein hängender Aufruf. |

HUMAN_DECISION_REQUIRED: Ob die Betrugsprüfung in flowinvoice/audit-portal auf
`benford_test` (exakte Erwartungswerte, echter p-Wert, ausdrückliches α)
umgestellt wird; das ändert Ergebnisse (Grenzfall χ² zwischen 15,507 und 15,51:
„anomal“ bei ausgewiesenem p = 0,08).

Nicht übernommen: die abweichende Implementierung in `audit-portal`
(`audit_tests_service.benford_test`); sie wäre ein eigenes, getrennt zu
charakterisierendes Profil. HUMAN_DECISION_REQUIRED: Konvention für
einstellige Werte im Zwei-Ziffern-Test (`exclude` nach verbreiteter Praxis
oder `pad`).
