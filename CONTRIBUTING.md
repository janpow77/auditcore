# Contributing

Read AUDITCORE_LASTENHEFT.md, docs/analysis.md and
`docs/architecture/ADR-001-multi-package-monorepo.md` before changes. The accepted
architecture is one repository hosting the platform and independently installable
domain distributions under `packages/`. Applications remain separate repositories.
Domain cores cannot import platform tools, web frameworks or application infrastructure;
explicitly selected renderer/source adapters declare their optional dependencies.
Do not invent business rules, legal thresholds or successful test outcomes.

Use a virtual environment and install `python -m pip install -e ".[dev]"`.
Run `pytest`, `ruff check .`, `mypy src` and the five quality self-checks documented
in README.md. Tests use synthetic data and fake providers; real integrations are
explicit separate runs. Never run repository code merely to inventory it.

Before extraction capture legacy outputs and exceptions, preserve source revision
and licensing, assess framework applicability, and generate a reviewable plan.
Before merging changes to shared APIs compare the API snapshot and run consumer
tests. An unresolved human decision blocks only its dependent work.

Changes to framework adapters require re-reading the exact source commit and
updating source hashes plus applicability tests. Updating hashes without reviewing
the changed semantics is not acceptable. Offline snapshots remain STALE.

Small logical commits; no force push, history rewrite or automatic production
migration. A green CI is not a policy, privacy or operating authorization.

## Pflicht: fachlicher Rauchtest nach Produktions-Deploys

Nach jedem Deploy außerhalb von `internal_test` ist ein fachlicher Rauchtest
über die echte API Pflicht; ein Health-Check reicht nicht. Durchgesetzt durch
`auditcore-deploy plan` (Blocker ohne `functional_smoke`-Fälle) und
`auditcore-deploy smoke` (Exitcode 1 bei Fehlschlag). Details:
[docs/deployment/functional-smoke.md](docs/deployment/functional-smoke.md).

