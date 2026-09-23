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
