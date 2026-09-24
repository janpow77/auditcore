# Changelog

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
