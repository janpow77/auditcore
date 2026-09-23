# Legacyverhalten und bewusst korrigiertes Verhalten

Quellen, tatsächlich ausgeführt:

* riskanalysis@b5c523b `backend/app/pipeline/red_flags.py` (Blob `b6196a7`),
  `tools/capture_riskanalysis.py`, pandas 3.0.5, NumPy 2.5.1, rapidfuzz 3.14.5
  (Versionen aus `backend/requirements.txt`): 173 Frames mit 2.500+ Belegen,
  darunter die Frames der 26 Originaltests, Grenzfälle je Regel und 120
  zufällige Frames (Seed 20260923).
* audit_designer@1254591 und audit-portal@ac1ccc7
  `…/flowstat/services/belegliste_analysis_service.py:_red_flags` (identischer
  Blob `d03738c`), `tools/capture_flowstat.py`, pandas 2.1.4, NumPy 1.26.2:
  112 Frames; beide Kopien liefern identische Ergebnisse.

## RK-L — Legacyprofile reproduzieren das Original

| ID | Aussage | Nachweis |
|---|---|---|
| RK-L01 | `riskanalysis.legacy` liefert für alle 173 Frames dieselben Flags RF01–RF15, `name_match`-Werte, `red_flag_codes` und dieselbe `red_flag_summary` (einschließlich Volumen und Anteil) wie das Original. | `tests/test_replay_riskanalysis.py`, `tests/test_frame.py` |
| RK-L02 | `audit_designer.flowstat_belegliste` liefert für alle 112 Frames dieselben Codes und Zähler; Konzentrationsanteile siehe RK-C06. | `tests/test_replay_flowstat.py` |
| RK-L03 | Erhaltene Eigenheiten der Quelle (nicht korrigiert, weil Treffer sich sonst ändern): RF12 überträgt das Merkmal über die gleiche Vorhabenkennung auch auf Belege anderer oder fehlender Gruppen; RF09 zerlegt Umlaute (`Müller → mu ller`); RF02 wendet als netto kommentierte Schwellen auf Bruttobeträge an; `_pseudonym_rf09` wird per Wahrheitswert übernommen (`"False"` gilt als wahr); BL_RF09 trifft Teilzeichenketten (`"Jahresvertrag"`, `"10 Angebote"`). | Grenzfälle `rf12-gleicher-antrag-andere-gruppe`, `rf09-pseudonym-override`, `rf08-rf09-vergabe` |

Die Unterschiede zwischen den Varianten bleiben getrennte Profile: RF08 prüft
„> 25.000 ohne echte Vergabekennung“ mit Platzhaltermuster und
Kostenartfilter, BL_RF08 nur leere Werte (`""`, `"nan"`, `"None"`, ohne
Groß-/Kleinschreibung zu falten) und keine Kostenart. RF02 zählt einen Treffer
je Beleg, BL_RF02 Treffer je Schwelle. Nichts davon wird vereinheitlicht.

## RK-C — bewusste Abweichungen des Bibliotheksvertrags

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| RK-C01 | Nicht numerische Beträge führten zu `TypeError` in pandas; Wahrheitswerte wurden als 1/0 gerechnet. | `InputError` mit Feldname für Texte, Wahrheitswerte und Listen in Betragsfeldern; `Decimal` ist zulässig. | Klarer Fehlervertrag statt stiller Umdeutung. |
| RK-C02 | Fehlende Pflichtspalten (`bruttobetrag`, `Name`, `zahlungsempfaenger`) führten zu `KeyError`; Flowstat übersprang Regeln stillschweigend. | `InputError` mit Regelcode; übersprungene Regeln stehen in `Evaluation.skipped`, `missing_columns()` zeigt sie vorab. Defensive Quellregeln (RF10–RF15) bleiben unverändert. | Nachvollziehbarkeit. |
| RK-C03 | Ohne rapidfuzz fiel `_name_match` still auf `difflib.SequenceMatcher` zurück (andere Werte). | Der Namensabgleich verlangt das Extra `fuzzy`; sonst `DependencyError`. | Ergebnis darf nicht von der Installation abhängen. |
| RK-C04 | Keine jahresbezogenen Schwellen. | Nur im Kandidatenprofil `riskanalysis.year_bound`; fehlt ein belegter Zeitraum oder das Datum, ist RF02 unbestimmt (`None`), nicht „kein Treffer“. | Nutzerentscheidung „Vergabeschwellen pro Jahr“; keine stille Rückfallschwelle. |
| RK-C05 | Nur Wahrheitswerte je Spalte. | Zusätzlich Begründung, Belegwerte, Interpretation (`indicator`/`descriptive_prior`) und Quellfundstelle je Merkmal. | Anforderung „jede Flag mit Begründung/Herkunft“. |
| RK-C06 | Summen mit NumPy (paarweise) bzw. pandas-groupby (Kahan). | Korrekt gerundete Summe (`math.fsum`). In 2 von 112 Flowstat-Frames weicht der ausgegebene Konzentrationsanteil in der letzten Binärstelle ab; alle Entscheidungen, Zähler und alle riskanalysis-Volumina sind identisch. | Reihenfolgeunabhängige, exakte Summen. |
| RK-C07 | `pd.to_numeric(errors="coerce")` auf ganzen Spalten. | Gleiche Skalarregel (Zahl, Dezimaltext mit Vorzeichen/Exponent/Leerraum, `inf`; sonst fehlend), charakterisiert; Wahrheitswerte → `InputError`. | Kein pandas im Kern. |

## flowinvoice: Rechnungsindikatoren und Betrugsprüfungen

Quelle flowinvoice@fb2d185 (gegen GitHub geprüft), tatsächlich ausgeführt:

* `RiskChecker.assess` (`services/risk_checker.py`, Blob `b799e85`; audit-portal
  nur formatverschieden): 338 Anfragen (`tools/capture_flowinvoice_risk_checker.py`).
  `flowinvoice.risk_checker` reproduziert alle Indikatoren, Schweregrade, Texte,
  Score, höchste Schwere und Zusammenfassung exakt.
* `FraudDetectionManager.analyze_invoice` mit Stellvertretern der Teilprüfungen
  (268 Fälle, davon 23 mit dem Originalabbruch `TypeError`), TED-Statistik,
  -Merkmale und -Legitimität (129 Auftragsmengen), Dublettenlogik exakt/unscharf
  (250 Fälle) mit `tools/capture_flowinvoice_fraud.py`: alle exakt reproduziert.
  Die SQL-Auswahl (TED `_load_contracts`, Dubletten-Vorfilter) ist **NOT_EXECUTED**
  (Postgres); `select_contracts` bildet die SQL-Bedingung nach.

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| RK-L04 | Legacy-Score des RiskChecker: Summe der Schweregewichte / 5, höchstens 1. | Unverändert, nur als `assessment` dieses Profils. | Kein profilübergreifender Score. |
| RK-L05 | Namensheuristik der Dubletten: ein gemeinsames Wort unter den ersten drei genügt; europäisches vor US-Datumsformat; USt-IdNr. ungenutzt. | Unverändert im Profil `flowinvoice.duplicates`. | Legacy exakt; fachliche Bewertung offen. |
| RK-L06 | TED: Zeitfenster 12/24/60 Monate = Gesamtzahl (TODO in der Quelle); Konzentrations-Merkmale feuern bei > 0,9 doppelt. | Unverändert. | Legacy exakt. |
| RK-L07 | Summen über `sum()` hängen vom Interpreter ab: Python 3.12 kompensiert Gleitkommasummen, 3.11 nicht. Mit 3.12 ausgeführt weichen 6 von 338 RiskChecker-Scores und 33 von 129 TED-Statistiken in der letzten Stelle ab. | Maßgeblich ist die Produktionslaufzeit der Quelle (Python 3.11, `Dockerfile`/`Dockerfile.production`); die Bibliothek addiert ausdrücklich von links nach rechts und liefert auf jedem Interpreter das 3.11-Ergebnis. Fixtures im Container `python:3.11-slim` erzeugt. | Ergebnis unabhängig von der Laufzeit der Bibliothek. |
| RK-C08 | Warnungen/Blocker über `list(set(...))` in zufälliger Reihenfolge. | Deterministische Reihenfolge der Ableitung, dedupliziert; Zählung für den Score wie im Original vor der Deduplizierung; Score-Komponenten einzeln ausgewiesen. | Reproduzierbarkeit, Nachvollziehbarkeit. |
| RK-C09 | TED-Legitimität kommt als Wörterbuch (0–100) an und bricht die Scoreberechnung mit `TypeError` ab, sobald TED-Merkmale vorliegen. | `InputError` mit Hinweis; eine Zahl 0–1 wird wie im Code vorgesehen verrechnet. | Fehler sichtbar statt Absturz; Skala ist fachlich zu klären. |
| RK-C10 | Unscharfe Dublette bei Betrag 0: `ZeroDivisionError`; Lieferantenname `None`: `AttributeError`. | `InputError` bzw. leerer Name. | Klarer Fehlervertrag. |

Sanktions-, PEP- und Firmenprüfungen werden nicht nachgebaut; ihre Ergebnisse
gehen als Signale (Port-Vertrag, einfache Zuordnungen) in `score_signals` ein.
Die Benford-Prüfung (`benfords_law.py`) liegt als Legacyvariante in
`auditcore_statistics` 0.2.0.

## flowinvoice VerwK: Punkte-Scores (Verwaltungskontrolle)

Quelle `flowinvoice@fb2d185 backend/app/verwk/pipeline/{rbvk_wibank_scorer,exante_score}.py`
(Blobs `24e04c0`, `1f05d3f`; in riskanalysis fachlich gleich, Blobs `6ebd3a2`,
`bc1725b`). Mit `tools/capture_flowinvoice_verwk_scores.py` wurden die
unveränderten Funktionen auf drei Demobeständen des flowinvoice-Generators und
60 synthetischen Mittelabruf-Rahmen ausgeführt und ihre lokalen Variablen am
Bewertungsschritt per `sys.settrace` gelesen (Python 3.12 wie
`Dockerfile.verwk`): 777 WIBANK-Zeilen, 125 Ex-ante-Merkmalszeilen, 3
Kalibrierungsläufe (alle im Basisgewichts-Fallback). Alle reproduziert.

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| RK-L08 | WIBANK-Punkte (K1–K28 ohne 6/15/27), Stufen 8/19 im Code; die Profildatei `rbvk_wibank.json` wird nicht gelesen und weicht ab (K10, K21/K22, K12/K16). | Profil `flowinvoice.rbvk_wibank` bildet das **Codeverhalten** ab. | Legacy exakt; Abweichung zur Profildatei ist fachlich zu klären. |
| RK-L09 | Ex-ante: Gewichte zur Laufzeit per Logit kalibriert, Fallback-Basisgewichte 20/15/6/10/10/10/15, Klassen 30/55, Vergleichsheuristik `heuristik_score` (Deckel 100). | `flowinvoice.exante_basis` (Basisgewichte; kalibrierte Gewichte nur ausdrücklich über `points`), `flowinvoice.exante_heuristik`. | Kalibrierung bleibt Modellierung beim Consumer. |
| RK-C11 | Merkmalsaufbereitung, Vorhistorie (CSV, MA-Versionen) und „nicht abbildbar“ im selben Aufruf. | Die Bibliothek bewertet aufbereitete Merkmale (`prior_k`, `prior_q`, `prior_families`, `erstes_vorhaben` …); Aufbereitung und Historie bleiben in der Anwendung. | Anwendungsspezifische Feldaliase und Datenquellen. |

Geprüft und **nicht** in `auditcore_risk` übernommen (Stand, Begründung):

* `auffaelligkeiten.py` (nur flowinvoice): Gruppen-Übermaß mit einseitigem
  Binomialtest und Benjamini-Hochberg. Wiederverwendbares Merkmal, aber der
  statistische Kern gehört nach `auditcore_statistics` und existiert dort noch
  nicht. Status: geplant (erst Methodenprofil in statistics, dann Regelart hier).
* `konzentration.py` (Pareto, Gini/Lorenz, HHI; beschreibend, ohne Merkmale):
  gehört nach `auditcore_statistics`. Status: geplant.
* `benford.py` (VerwK): Erstziffern gegen die **eigene** Bestandsverteilung,
  MAD/χ² ohne p-Wert je Gruppe ≥ 300 Belege – methodisch verschieden von
  `benford_test` und `legacy_flowinvoice_benford`. Status: geplant als eigenes
  Methodenprofil in `auditcore_statistics`.
* `montecarlo.py`: Simulationsvergleich PPS-mit-Zurücklegen gegen Zufallsauswahl
  (numpy-Generator), passt zu keiner Funktion in `auditcore_sampling`; Population
  unterscheidet sich zwischen flowinvoice (2021–2029) und riskanalysis (2014–2024).
  Status: bleibt in der Anwendung, ggf. später Werkzeug in `auditcore_sampling`.
* `fuzzy_link.py`/`payee_normalizer._fuzzy_merge`: transitive Namensclusterung
  gehört nach `auditcore_entity_matching` (Normalisierung dort bereits als
  `riskanalysis.payee`). Status: geplant.
* `eu_typologie.py`, `fehlerursachen.py`: Berichtsklassifikationen an den
  ACR-Katalog bzw. die Nummerierung 2014–2020 gebunden und zwischen den Repos
  auseinandergelaufen – bleiben in der Anwendung.

## Nicht übernommen (geprüft)

* `audit_designer` `vp_ai/services/scorecard_service.py:ScorecardService` —
  Bearbeitungsstands-Score (Checkliste, Validierung, Ausgabenbilanz …) über
  ORM-Abfragen; keine wiederverwendbare Risikomechanik.
* `audit_designer` `vp_ai/services/rule_validation_service.py:RuleValidationService` —
  Checklisten-Konsistenzregeln R01–R16 über ORM; gehört zu einem künftigen
  Checklistenpaket, nicht zu Risikomerkmalen.
* KPAnG-Tatbildung aus regulierung — bleibt laut Migrationsplan in regulierung.

## HUMAN_DECISION_REQUIRED

1. **Kein gemeinsamer Risikoscore.** Ob und wie Merkmale verschiedener Profile
   gewichtet zusammengefasst werden, ist fachlich zu entscheiden; die
   Bibliothek bietet bewusst keinen Score.
2. **RF02 brutto/netto:** Schwellen sind als netto kommentiert, geprüft wird der Bruttobetrag.
3. **RF02 Jahresbezug:** 221.000 ist die EU-Schwelle 2024–2025 (Liefer-/Dienstleistungen,
   subzentral); seit 01.01.2026 gilt 216.000. Freigabe des Kandidaten
   `riskanalysis.year_bound` einschließlich Stichtag (Rechnungs-, Vergabedatum,
   Geschäftsjahr), Auftraggebertyp und Leistungskategorie je Beleg; ob auch die
   nationalen Wertgrenzen 1.000 … 100.000 jahresbezogen gepflegt werden.
4. **RF09:** Umstellung der Rechnungssteller-Normalisierung auf die empfohlene
   Transliteration (`flowworkshop.state_aid`, „mueller“) — ändert Treffer.
5. **RF12:** Übertragung über gleiche Vorhabenkennung aus fremden Gruppen beibehalten oder beheben.
6. **BL_RF08/BL_RF09 vs. RF08:** unterschiedliche Vergaberegeln bleiben getrennt;
   eine Angleichung ist eine fachliche Entscheidung.
7. **flowinvoice RiskChecker:** ohne Laufzeit-Consumer; ob er aktiviert und mit
   `RiskCheckerConfig` verbunden wird, ist offen. Bezugsgröße der
   Lieferantenhäufung (Rechnungen oder Lieferanten) klären.
8. **Betrugs-Signalscore:** Skala der TED-Legitimität (0–1 oder 0–100) und ob
   Warnungen vor oder nach der Deduplizierung zählen.
9. **Rechnungssplitting-Schwellen** (1.000–50.000, 80 %) weichen von RF02 und den
   jahresbezogenen EU-Schwellen ab; keine Angleichung ohne Entscheidung.
10. **WIBANK-RBVK:** Codeverhalten gegen Profildatei V1.21 (K10 +1 statt bis 2;
    13.* als Beihilfe; K22 greift für jede eigene Vorgeschichte, weil
    `prior_familie` nie gesetzt wird).
11. **Ex-ante-Score:** Kalibrierung (Logit, Signifikanz p < 0,10, Skalierung auf
    25) und Klassen 30/55 sind Methodikhoheit der Verwaltungsbehörde.
