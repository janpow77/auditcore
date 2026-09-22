# Contributing

Read AUDITCORE_LASTENHEFT.md and docs/analysis.md before changes. Keep one project
and release cycle. Domain modules cannot import tools, frameworks or infrastructure.
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
