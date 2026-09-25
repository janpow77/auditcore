# Changelog

## Unreleased

- CI-Automatisierung (Rechteinhaber, 25.09.2026): Sammel-Check `ci-ok` als
  Required Check neben `code-quality-gate`, Workflows `autofix` (ruff, ESLint,
  reine Baseline-Absenkungen; Hilfsskript `scripts/ci_baseline_lower_only.py`),
  `update-pr-branches`, `dependabot-automerge` und `nightly` (Vollprüfung mit
  Issue „Nightly rot“), dazu `.github/dependabot.yml` und Auto-Merge im
  Repository. Siehe `docs/deployment/ci-automatisierung.md`.
- Verbindliche Code-Qualitätsmaßstäbe als Ratchet (Rechteinhaber, 25.09.2026):
  neue Module `auditcore.tools.quality.codegate*`, Befehl
  `auditcore-codegate check` bzw. `scripts/verify_code_quality.py`, Baseline
  `quality/baseline.json`, Pflicht-Job `code-quality-gate`, pre-commit-Hook
  und Release-Blocker in `verify_domain_packages.py`/`prepare_library_release.py`.
  Siehe `docs/quality/code-quality.md`.

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
