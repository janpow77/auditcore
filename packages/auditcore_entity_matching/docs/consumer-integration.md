# Consumer-Anbindung flowworkshop

Branch `feat/auditcore-entity-matching` in `janpow77/flowworkshop` (lokal,
nicht gepusht), Basis `a05bb21`: Commits `dd7e5c5` (Umstellung) und `2de6a09` (Test).

- Delegiert an `auditcore_entity_matching.legacy`: `normalize_company_name`,
  `sanctions_service.normalize_name`, `_classify`, `is_valid_lei`,
  `extract_lei_from_text` sowie die Kandidatenbewertung in `_find_by_name_fuzzy`.
  SQL-Vorfilter, ORM, Schwellen und Konfidenzen bleiben in der Anwendung.
- Anforderung: `auditcore_entity_matching[fuzzy]==0.1.0` in `requirements.txt`.
- Nachweis mit Wheel per `pip --target` und `PYTHONPATH` (App-Umgebung
  unverändert), wegwerfbarer `pgvector/pgvector:pg16`-Container, Alembic-Migration:
  vor der Umstellung 89 Tests PASS, danach 89 PASS plus 4 neue Bindungstests
  (93 PASS). Replay der 299 anwendbaren Originalfälle durch den umgestellten
  Code: 299 identisch, 0 abweichend.
- Befund der Baseline: Die Migrationen legen `pg_trgm` nicht an, obwohl
  `_find_by_name_fuzzy` `similarity()` nutzt; im Testcontainer wurde die
  Erweiterung vor der Migration angelegt.
- Nicht ausgeführt: Integrations-Tests gegen die laufende Anwendung
  (`tests/conftest.py` zielt auf `localhost:8006`), Harvester-Tests
  (`test_state_aid_smart_mode`, Umfang der Fördermittel-Bibliothek).
