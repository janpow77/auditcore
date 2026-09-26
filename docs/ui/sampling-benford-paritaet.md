# Paritätsinventur Stichprobe und Benford

Stand 25.09.2026. Vorbilder: FlowStat im audit_designer (`origin/main` @ `2c726f3c`),
ECOHESION-Lab `sampling.py` im audit_designer, riskanalysis (`main`). Ziel: gemeinsame
Komponenten `<flowaudit-sampling>` und `<flowaudit-benford>` in `@auditcore/ui` auf Basis von
`auditcore_sampling.web` und `auditcore_statistics.web`.

Legende: **übernommen** = gleiche Fachlogik über die Bibliothek; **ergänzt** = neu gegenüber
den Vorbildern; **abweichend** = bewusst anders (Begründung); **offen** = nicht umgesetzt.

## Stichprobe

| Funktion | Vorbild | Gemeinsame Komponente | Stand |
|---|---|---|---|
| MUS-Umfang mit Poisson-Faktoren (0,50–0,99) | FlowStat `_calculate_mus_sample_size`, audit-portal | Profil `portal.mus_poisson`, als empfohlen markiert | übernommen |
| MUS-Umfang z-Attributformel | flowstat `@d665ac2` | Profil `flowstat.mus_z_attribute`, Status „abgelöst“ mit Warnung | übernommen (nur Nachvollzug) |
| SRS-Umfang mit Endlichkeitskorrektur | FlowStat `_calculate_srs_sample_size` | Profile `flowstat.srs_normal`, `portal.srs_normal` | übernommen |
| Unbekanntes Konfidenzniveau | FlowStat fällt still auf z = 1,96 zurück | Auswahl nur der im Profil definierten Niveaus, sonst 422 | abweichend (keine stille Ersetzung) |
| Herleitung des Umfangs | FlowStat zeigt nur n und Intervall; Wizard nutzt eine grobe Heuristik (Faktoren 1,0/0,85/1,4 …) | Schrittweise Herleitung mit Formel und eingesetzten Werten | ergänzt; Heuristik entfällt |
| Wesentlichkeit in % des Volumens (Wizard) | FlowStat-Wizard | Eingabe als Betrag in EUR | abweichend (Profilparameter der Bibliothek) |
| Systematische MUS-Auswahl, Start `uniform(0, J)` | FlowStat `_mus_systematic_select` | `systematic_mus`, Varianten `portal` und `flowstat` wählbar | übernommen |
| Negative/leere Werte abtrennen | FlowStat `_split_positive_for_mus` | Variante `portal`: getrennt ausgewiesen (Kennungen) | übernommen |
| Mehrfachtreffer großer Positionen | FlowStat mehrfach gezogen | Einmal gelistet, Spalte „Treffer“ | übernommen (Darstellung) |
| Seed | FlowStat: Pflicht, fest 42 im Wizard, kein Eingabefeld | Seed-Feld sichtbar; ohne Eingabe vom Server erzeugt und angezeigt; Neu-Ziehen mit gleichem Seed reproduziert | ergänzt |
| Eingabe-Fingerabdruck | ECOHESION `_fingerprints` | `items_sha256` in Antwort und JSON-Export | übernommen |
| Schichtung proportional/gleich | FlowStat `run_srs_stratified`, `run_mus_stratified` | Allokationstabelle je Schicht, Auswahl je Schicht | übernommen |
| Neyman-Allokation | nur ECOHESION-Lab | – | offen (keine charakterisierte Bibliotheksmethode) |
| Schichtbildung `equal_width`/`equal_frequency` | FlowStat-Node | Schicht kommt aus der Datenspalte | offen |
| Zwei Perioden (kombiniert/getrennt) | FlowStat `run_mus_two_periods_*` | – | offen |
| Nicht-statistische Verfahren (Top-/Key-Items, PPS, bewusste Auswahl) | FlowStat, ECOHESION | – | offen |
| Risikogewichtete Auswahl | ECOHESION `_draw_risk_based` | – | offen (gehört zu auditcore_risk) |
| High-Value-Segmentierung | FlowStat `run_population_segmentation` | – | offen |
| Fehlerprojektion (Tainting, ULE/LLE) | FlowStat `run_error_projection` (Normalapproximation; Stringer offen) | – | offen: keine Bibliotheksmethode; Aufnahme erst nach Charakterisierung |
| Differenz-, Verhältnis-, Regressionsschätzung | FlowStat `run_difference_estimation_*` | – | offen, wie oben |
| Forest-Plot je Schicht | FlowStat `ForestPlot.vue` | – | offen (folgt mit der Fehlerprojektion) |
| Monte-Carlo MUS vs. Zufall | riskanalysis `montecarlo.py` | – | offen (Simulationswerkzeug, kein Stichprobenrechner) |
| Export der Auswahl | FlowStat: Tabellen als XLSX über `/flowstat/export/excel`; riskanalysis XLSX | CSV (Excel-tauglich, Formelschutz) und JSON mit Seed und Fingerabdruck | abweichend (ohne XLSX-Abhängigkeit; XLSX über auditcore_reporting möglich) |

## Benford

| Funktion | Vorbild | Gemeinsame Komponente | Stand |
|---|---|---|---|
| Erste Ziffer, erste zwei Ziffern | FlowStat `benford_test` (`digit_position` 1/2) | Tests `first`, `first_two` | übernommen |
| Zweite Ziffer | FlowStat `"second"` (nur im Wizard wählbar, nicht in der Card) | Test `second` (Aggregation der Gruppen 10–99) | übernommen |
| Letzte Ziffer(n) gegen Gleichverteilung | FlowStat `"last"`, `"last_two"` | – | offen (kein Benford-Test; eigene Methode nötig) |
| Werte mit einer signifikanten Ziffer bei zweistelligen Tests | FlowStat: Gruppe 0 (Chi²-Fehler möglich) | Pflichtwahl `exclude`/`pad`, Anzahl ausgewiesen | abweichend (siehe behavior-changes der Bibliothek) |
| Mindestwert | FlowStat-Wizard „Mindestwert“ (Standard 1) | – | offen; Filterung vor der Übergabe |
| Chi² und p-Wert | FlowStat (SciPy), riskanalysis manuell | Chi², Freiheitsgrade, p-Wert, Vergleich mit α des Profils | übernommen |
| MAD mit Bändern | FlowStat `_interpret_benford_mad` (englische Labels, Card färbt immer nach Erstziffer-Grenzen) | Profil `nigrini.2012`, Grenzen je Test, deutsche Stufen | übernommen, Färbung korrigiert |
| z-Wert je Ziffer (1,96, Stetigkeitskorrektur) | nirgends (Wizard-Kommentar erwähnt ±1,96σ) | z je Ziffer, Überschreitungen im Diagramm und in der Tabelle hervorgehoben | ergänzt |
| Referenz = Hausverteilung je Gruppe | riskanalysis A-13 (MAD je Begünstigtengruppe gegen Gesamtverteilung, ≥ 300 Belege) | – | offen (anderer Vergleich; eigene Methode nötig) |
| Diagramm | FlowStat Plotly (MIT), riskanalysis ECharts (Apache-2.0) | eigenes SVG ohne Diagrammbibliothek: Balken beobachtet, Punkte/Linie erwartet, Hervorhebung | abweichend (keine schwere Abhängigkeit) |
| Kacheln N, Chi², p, MAD | FlowStat `BenfordCard.vue` | Kennzahlen mit Stufe und Ausschlüssen | übernommen |
| Pflichthinweis „nur Einordnung“ | riskanalysis `HINWEIS` | Hinweis „Bewertungsstufen sind keine Feststellungen“ | übernommen |
| Datenübergabe | FlowStat: Spaltenname in der Pipeline | Datei-Upload (CSV/TXT, Spaltenwahl, Dezimalkomma) oder Werte als Eigenschaft | ergänzt |

## Konsequenzen

1. Die Oberflächen bieten nur Methoden an, die die Bibliotheken benennen. Auswertungsverfahren
   (Fehlerprojektion, Schätzer) folgen erst, wenn `auditcore_sampling` sie charakterisiert
   anbietet; die Komponenten sind dafür als eigene Ansicht vorgesehen.
2. Die z-Prüfung je Ziffer ist neu und im Profil `nigrini.2012` als Ergänzung gekennzeichnet.
3. Die Konfidenzniveau-Ersetzung, die Umfangsheuristik des Wizards und der feste Seed 42
   werden bewusst nicht übernommen.
