# Consumer-Umstellung

Stand 23.09.2026. Die Consumer werden erst nach dem nächsten zentralen Release
(v0.3.0 enthält noch 0.1.0) per Requirements umgestellt; bis dahin sind die Umstellungen lokal gegen die
installierten Wheels geprüft (keine Pushes in die Consumer-Repositories, keine
Produktionsdatenbank).

## riskanalysis (Consumer, geprüft)

* Stelle: `janpow77/riskanalysis` `backend/app/pipeline/red_flags.py`
  (`compute_red_flags`, `red_flag_summary`, `_name_match`, `_hat_echte_vergabe`,
  `RED_FLAG_CODES`, `RED_FLAG_LABELS`); Aufrufer `pipeline/aggregation.py:73, 381–390`,
  `services/pseudonymization.py:27, 274`.
* Umstellung: `backend/requirements.txt` um
  `auditcore_risk[fuzzy,pandas]==0.3.0` ergänzen (zieht
  `auditcore_entity_matching[fuzzy]==0.2.0`) und `red_flags.py` durch
  [`consumers/riskanalysis_red_flags.py`](consumers/riskanalysis_red_flags.py)
  ersetzen. Die Symbole bleiben erhalten; Aufrufer ändern sich nicht.
* Nachweis (lokal, Checkout-Kopie von `b5c523b`, venv mit
  `backend/requirements.txt`, pandas 3.0.5, installierte Wheels):
  * Testsuite vorher/nachher identisch: 178 bestanden, 9 fehlgeschlagen,
    9 übersprungen; die 9 Fehlschläge brauchen `Database.mdb` und schlagen
    ohne Umstellung genauso fehl. Alle 26 Tests in `tests/test_red_flags.py`
    und 4 in `tests/test_pseudonymization.py` bestehen.
  * Frame-Vergleich Original gegen umgestellt im Consumer-venv: 453 Frames,
    8.583 Belege, Spalten `rf01 … rf15`, `name_match`, `red_flag_codes` und
    `red_flag_summary` identisch.

## flowinvoice (Consumer, geprüft)

* Stelle: `janpow77/flowinvoice` `backend/app/verwk/pipeline/red_flags.py`
  (inhaltsgleich zu riskanalysis, nur Importpfad und `zip(strict=True)`);
  Aufrufer `verwk/pipeline/aggregation.py:74, 382`,
  `verwk/services/pseudonymization.py:32`.
* Umstellung: `backend/requirements-verwk.txt` um
  `auditcore_risk[fuzzy,pandas]==0.3.0` ergänzen und die Datei durch dieselbe
  Vorlage ersetzen.
* Nachweis (Checkout-Kopie von `fb2d185`, venv mit
  `requirements-production.txt` + `requirements-verwk.txt`, `--noconftest`, weil
  die Session-Fixture Postgres/pgvector verlangt):
  * `tests/verwk` vorher/nachher identisch: 564 bestanden, 8 übersprungen.
  * Mit synthetischem Demobestand des flowinvoice-Generators
    (`generate_demo`, Seed 20260923, 40 Vorhaben, 3.789 Belege) als
    `PSEUDONYMIZED_DATA_DIR`: `test_verwk_pipeline.py` + `test_red_flags.py`
    34 bestanden (vorher und nachher); `build_levels` liefert vorher und
    nachher identische Red-Flag-Spalten und `red_flag_summary`.

## audit_designer / audit-portal Flowstat (Consumer, Profil vorhanden)

* Stelle: `backend/app/modules/flowstat/services/belegliste_analysis_service.py:_red_flags`
  (Aufrufer `analyze_belegliste` → `api/data_sources.py`,
  `vorhaben_context_service.py`, `node_handlers/template_handlers.py`).
* Umstellung (Vorschlag):

  ```python
  from auditcore_risk import evaluate, load_profile

  _PROFIL = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")


  def _red_flags(data: pd.DataFrame) -> list[dict[str, Any]]:
      records = data.to_dict("records")
      return [dict(s) for s in evaluate(records, _PROFIL, columns=list(data.columns)).summary]
  ```
* Nachweis: Replay aller 112 Originalfälle im Paket (RK-L02). Eine lokale
  Ausführung der Designer-/Portal-Testsuite ist **NOT_EXECUTED** (umfangreiche
  Anwendungsabhängigkeiten); Status: geplant.

## flowinvoice Betrugsprüfung (Consumer, Profile vorhanden)

* Stellen: `services/fraud_detection/manager.py` (`_calculate_risk_score`,
  `_determine_risk_level`, Ableitung der Blocker/Warnungen) → `score_signals`
  mit `flowinvoice.fraud_signals`; `ted_checker.py` (`_calculate_statistics`,
  `_detect_red_flags`, `_calculate_legitimacy_score`) → `assess_contractor`
  mit `flowinvoice.ted_contractor`; `duplicate_detector.py` (Python-Teil nach
  der SQL-Vorauswahl) → `find_duplicates` mit `flowinvoice.duplicates`;
  `benfords_law.py` → `auditcore_statistics.legacy_flowinvoice_benford`.
  Laufzeitaufrufer: `api/fraud_detection.py` (`/api/fraud/check-invoice`,
  `/fraud/analyze-benford`, `/projects/{id}/fraud-analysis`, `/fraud/check-ted`)
  und die Pipeline-Regel `FraudDetectionRule`.
* Umstellung: `requirements-production.txt` um `auditcore_risk==0.3.0` und
  `auditcore_statistics==0.2.0` ergänzen; der Manager übergibt seine
  Teilergebnisse als Zuordnungen an `score_signals`, die SQL-Abfragen bleiben.
* Nachweis: Replay aller Originalfälle im Paket. flowinvoice hat für diese
  Module keine Tests; eine Consumer-Testsuite ist **NOT_EXECUTED**. Bekannte
  Consumer-Fehler (nicht Teil der Bibliothek): `FraudDetectionRule` liest
  `risk_factors`/`hit_count`, die es nicht gibt; TED-Legitimität als Wörterbuch.
  Status: geplant.

## Empfohlene Profile nach der Entscheidung vom 23.09.2026

Neue Consumer-Umstellungen verwenden die freigegebenen Profile
`riskanalysis.year_bound 2026.09.5` (Spalte `nettobetrag` aus „Gesamt Netto“,
soweit vorhanden; fehlt sie oder ist ein Wert leer, sind RF02/RF08 je Beleg
unbestimmt – kein Abbruch, kein Rückfall auf brutto; EU-Schwellen 2014–2027 über
das Extra `procurement`), `flowinvoice.rbvk_wibank 2026.09.2` (Eingaben
`offene_auflagen_anzahl`, `externe_kuerzung`, `vorherige_verwk_quote`,
`vorherige_kuerzungsgruende`), `flowinvoice.fraud_signals`/`ted_contractor
2026.09.2` und `auditcore_statistics.recommended_flowinvoice_benford`. Die
Legacyprofile dienen der Nachweisführung (bitgenaue Reproduktion).

## flowinvoice / audit-portal RiskChecker (kein Laufzeit-Consumer, K7: nicht aktivieren)

`services/risk_checker.py` wird in beiden Anwendungen nirgends aufgerufen; die
gespeicherte `RiskCheckerConfig` ist nicht angebunden. Profil
`flowinvoice.risk_checker` steht bereit; eine Anbindung ist fachlich zu
entscheiden (Status: geplant).

## flowinvoice VerwK-Scores (Consumer, geprüft)

* WIBANK-RBVK: `verwk/pipeline/rbvk_wibank_scorer.py:score_mittelabrufe` (Aufrufer
  `pruefplan.py:903`). Umstellung: Merkmalsaufbereitung und Vorhistorie bleiben;
  im Bewertungsschritt wird je Mittelabruf ein Datensatz aus den aufbereiteten
  Feldern plus `prior_k`, `prior_q`, `prior_families`, `erstes_vorhaben` gebildet
  und mit `evaluate([...], load_profile("flowinvoice.rbvk_wibank", "fb2d18568d2e"))`
  bewertet (Punkte `assessment["score"]`, Kriterien `assessment["criteria"]`).
* Nachweis (Checkout-Kopie, Bewertungsschritt ersetzt, installiertes Wheel):
  `score_mittelabrufe` liefert für einen Demobestand und 40 synthetische Rahmen
  (410 Mittelabrufe) identische Ergebnisse; `tests/verwk` mit Demobestand als
  `PSEUDONYMIZED_DATA_DIR` vorher und nachher 572 passed.
* Ex-ante: `verwk/pipeline/exante_score.py:kalibriere_und_score` (Aufrufer
  `aggregation.py:276`). Die Kalibrierung liefert Gewichte; Score, Klasse und
  Detail über `evaluate(..., load_profile("flowinvoice.exante_basis", …), points=…)`.
  Replay aller Läufe im Paket; Consumer-Umstellung Status: geplant.
* riskanalysis enthält dieselben Scorer (fachlich gleich); Umstellung analog (geplant).

## Weitere geplante Consumer

* flowinvoice `verwk/pipeline/auffaelligkeiten.py` (nach Methodenprofil in
  `auditcore_statistics`), `konzentration.py`, `benford.py`, `fuzzy_link.py`: siehe
  `behavior-changes.md` (Status: geplant).
