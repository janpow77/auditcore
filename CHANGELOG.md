# Changelog

## Unreleased

- Neues Paket `auditcore_bpmn` 0.1.0: BPMN 2.0 mit FlowAudit-Erweiterung
  Schema 1.1 (verbindlich in `docs/bpmn/flowaudit-schema-1.1.md`, XSD im
  Paket), gehärtetes Parsen, Elementmodell, Prüfregeln mit stabilen IDs
  (de/en), Profile je Förderperiode (KA nach Anhang XI VO (EU) 2021/1060 und
  Anhang IV Delegierte VO (EU) Nr. 480/2014 aus den amtlichen Texten),
  Diagrammsammlung mit Speicher-Port, Versions- und Soll/Ist-Vergleich,
  Neutralisieren, Anreichern von Altbeständen, Berichte (Prozesstabelle,
  RCM, Feststellungen, KA-Kategorievorschlag) sowie die legacy-treue
  Übernahme von `bpmn_analyzer.py`, `validate_bpmn_bva` und
  `bpmn_export.py` aus audit_designer (charakterisiert, eine dokumentierte
  Abweichung). `EXPECTED_SOURCES` und `packaging/library-extras.json`
  ergänzt.

## 0.2.0

- Pflicht zum fachlichen Rauchtest nach Produktions-Deploys (Rechteinhaber,
  24.09.2026): neues Modul `auditcore.tools.deployer.smoke`, Befehl
  `auditcore-deploy smoke`, Blocker in `auditcore-deploy plan` für jedes
  Ziel außer `internal_test` ohne gültige `functional_smoke`-Fälle, Action
  `.github/actions/functional-smoke`. Health-Endpunkte zählen nicht als
  Rauchtest. Siehe `docs/deployment/functional-smoke.md`.

## 0.1.0

Initial platform: framework-independent core models and reporting function,
policy-aware quality gates, GitHub inventory and consolidation planning,
KIRA/Graphify providers, transactional application migration, Debian builds
and isolated lifecycle validation. Release authorization remains separate from
technical build success; see the platform build report for actual evidence.
