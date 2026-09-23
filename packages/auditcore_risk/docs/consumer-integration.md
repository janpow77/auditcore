# Consumer-Umstellung

Stand 23.09.2026. Die Consumer werden erst nach dem zentralen Release v0.3.0
per Requirements umgestellt; bis dahin sind die Umstellungen lokal gegen die
installierten Wheels geprüft (keine Pushes in die Consumer-Repositories, keine
Produktionsdatenbank).

## riskanalysis (Consumer, geprüft)

* Stelle: `janpow77/riskanalysis` `backend/app/pipeline/red_flags.py`
  (`compute_red_flags`, `red_flag_summary`, `_name_match`, `_hat_echte_vergabe`,
  `RED_FLAG_CODES`, `RED_FLAG_LABELS`); Aufrufer `pipeline/aggregation.py:73, 381–390`,
  `services/pseudonymization.py:27, 274`.
* Umstellung: `backend/requirements.txt` um
  `auditcore_risk[fuzzy,pandas]==0.1.0` ergänzen (zieht
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
  `auditcore_risk[fuzzy,pandas]==0.1.0` ergänzen und die Datei durch dieselbe
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

## Weitere geplante Consumer

* flowinvoice `services/risk_checker.py`, `services/fraud_detection/*` und
  `verwk/pipeline/{rbvk_wibank_scorer,exante_score,auffaelligkeiten}.py`:
  eigene Legacyprofile in einem Folge-PR (Status: geplant).
