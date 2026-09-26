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
`Dockerfile.verwk`): 777 RBVK-Zeilen, 125 Ex-ante-Merkmalszeilen, 3
Kalibrierungsläufe (alle im Basisgewichts-Fallback). Alle reproduziert.

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| RK-L08 | RBVK-Punkte der Zwischengeschalteten Stelle (K1–K28 ohne 6/15/27), Stufen 8/19 im Code; die RBVK-Profildatei der Anwendung wird nicht gelesen und weicht ab (K10, K21/K22, K12/K16). | Profil `flowinvoice.rbvk_intermediate_body` bildet das **Codeverhalten** ab. | Legacy exakt; Abweichung zur Profildatei ist fachlich zu klären. |
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

## DECIDED (Nutzerentscheidung vom 23.09.2026, Zitat: „alle empfehlungen“)

Legacyprofile und ihre Replay-Nachweise bleiben bitgenau. Jede Entscheidung ist
als neue, freigegebene (`APPROVED`) Profilversion umgesetzt; die Legacyprofile
bleiben für die Reproduktion bestehen.

| Nr. | Entscheidung | Umsetzung |
|---|---|---|
| K1 | Kein gemeinsamer Risikoscore. | Festgeschrieben: die Bibliothek bietet keinen profilübergreifenden Score; Scores gibt es nur als Bewertung eines einzelnen Profils. |
| K2 | Schwellenprüfung netto. | `riskanalysis.year_bound 2026.09.2`: RF02 und RF08 prüfen `nettobetrag` (Pflichtspalte, kein stiller Rückfall auf brutto); runde Beträge und Volumen bleiben brutto. |
| K3 | `riskanalysis.year_bound` freigeben. | `riskanalysis.year_bound 2026.09.2`, fortgeführt in 2026.09.3 (`APPROVED`): nationale Wertgrenzen 1.000–100.000 plus EU-Schwelle des Rechnungsjahres aus `auditcore_procurement` (`procurement.hvtg 2026.09.2`, 2026: 216.000 €). Der Kandidat 2026.09.1 bleibt als abgelöste Fassung. |
| K4 | RF09 auf „mueller“-Umschrift. | `riskanalysis.year_bound 2026.09.3` (`APPROVED`, empfohlen): RF09 normalisiert mit `riskanalysis.payee 2026.09.2` aus `auditcore_entity_matching` 0.2.0 (Müller → mueller, auch zerlegte Umlaute); sonst identisch mit 2026.09.2, das als abgelöste Fassung bleibt. |
| K5 | RF12 nur innerhalb derselben Gruppe. | Parameter `propagation: same_group` in `riskanalysis.year_bound 2026.09.2`. |
| K6 | BL_RF08/09 vs. RF08 wie bisher je Profil. | Keine Änderung. |
| K7 | RiskChecker nicht aktivieren. | Consumer-Dokumentation; `flowinvoice.risk_checker 2026.09.2` steht nur für eine spätere Aktivierung bereit. |
| K8 | TED-Legitimität 0–1; Warnungen nach Dublettenentfernung zählen. | `flowinvoice.fraud_signals 2026.09.2` (`policy`: `after_dedup`, `unit_interval`, Werte außerhalb 0–1 → `InputError`), `flowinvoice.ted_contractor 2026.09.2` (Legitimitätswert als Anteil, Rating unverändert). |
| K9 | Splitting-Schwellen an jahresbezogene EU-Schwellen koppeln. | `flowinvoice.risk_checker 2026.09.2`: Schwellenliste um die EU-Schwelle des Rechnungsjahres ergänzt; ohne belegten Zeitraum und ohne nationalen Treffer „unbestimmt“. |
| K10 | flowinvoice-Benford auf `benford_test`. | `auditcore_statistics.recommended_flowinvoice_benford` (`digits=1`, `significance_level=0.05`); `legacy_flowinvoice_benford` bleibt. |
| K11 | RBVK der Zwischengeschalteten Stelle nach Profildatei V1.21. | `flowinvoice.rbvk_intermediate_body 2026.09.2`: K10 je offene Auflage bis 2 Punkte, K12 (externe Prüfungsfeststellungen) getrennt von K16–K19 (frühere Verwaltungskontrollen), K20–K22 nach Kürzungsgrund-Codes (1.1–1.24; 5.1/5.2; 8.1–8.3, 8.8, 13.1). Der Consumer übergibt die Codes auch eigener früherer Mittelabrufe (`prior_familie` korrekt setzen). |
| K12 | Ex-ante-Klassen 30/55 wie bisher. | Keine Änderung, bis Kalibrierdaten vorliegen. |
| C2 | Historische EU-Vergabeschwellen je Jahr nachtragen (Zitat: „c2. ja“). | `riskanalysis.year_bound 2026.09.4` (RF02) und `flowinvoice.risk_checker 2026.09.3` (SPLIT_INVOICE) verweisen auf `procurement.hvtg 2026.09.3` (EU-Schwellen 2014–2027 mit amtlicher Fundstelle, `auditcore_procurement` 0.2.0) statt 2026.09.2; übrige Regeln unverändert. Rechnungen 2014–2023 werden gegen die Schwelle ihres Jahres geprüft statt „unbestimmt“ (z. B. 2019: 7.000 € netto → kein Merkmal; 200.000 € → RF02). Vor 2014 und ab 2028 bleibt „unbestimmt“. Die Fassungen 2026.09.3 bzw. 2026.09.2 bleiben unverändert. |
| K2a | Nettodaten „nur im Code vorgesehen“ (Nutzerklarstellung vom 24.09.2026, Zitat: „nur im Code vorgesehen sein“): Quellen ohne Nettobetrag sollen auswertbar bleiben. | `riskanalysis.year_bound 2026.09.5`: RF02 und RF08 mit `missing_value: null`, `missing_amount_reason` „Nettobetrag fehlt in der Quelle“ und `when_missing_columns: "undetermined"`. Fehlt die Spalte `nettobetrag` oder ist der Wert leer, ist der Beleg für RF02 unbestimmt; RF08 ist unbestimmt nur ohne echte Vergabekennung bei vergaberelevanter Kostenart, sonst kein Merkmal. Bisher (2026.09.4): fehlende Spalte → Abbruch (`InputError`), leerer Wert → Ersatzbetrag 0 → stilles „kein Merkmal“. Kein Rückfall auf brutto (K2 bleibt); mit Nettobetrag rechnet 2026.09.5 wie 2026.09.4. 2026.09.4 bleibt unverändert. |
