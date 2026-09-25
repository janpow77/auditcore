# auditcore_kanban 0.1.0 – Paketbericht

Stand 25.09.2026, Branch `feat/kanban`.

| Prüfung | Ergebnis |
|---|---|
| `pytest` (Paket) | PASS, 264 Tests |
| `ruff check .`, `mypy --strict src`, `bandit -ll -r src` | PASS |
| Code-Qualitätsgate (`feat/code-quality-gate`, `--package auditcore_kanban`) | alle Metriken 0 |
| Paritätsfixtures `tools/build_parity_fixtures.py --check` | PASS (8 Dateien) |
| `scripts/verify_domain_packages.py` (pip: Build, Hash-Index, Installation, Isolation, Rauchtest, selektive Installation, Entfernen) | PASS |
| dieselbe Prüfung mit `--apt` (Debian-Paket Revision 1 → 2, signierte Quelle, Install/Upgrade/Remove im Bookworm-Image) | PASS |
| `tests/test_release_preparation.py` | PASS |

Charakterisierung: 77 ausgeführte Fälle des audit_designer-Backends
(`workspace.py`, `user_scoped.py` @ `2c726f3c`) und die per node ausgeführten
cockpit-Regeln (`df203d4c`, 9 Status, 45 Verschiebefälle). Bewusste
Abweichungen B1–B10: `packages/auditcore_kanban/docs/behavior-changes.md`.
Inventur: `docs/kanban/paritaet-audit-designer.md`. REST-Vertrag:
`docs/kanban/rest-api.md`.

Nicht ausgeführt: Veröffentlichung (macht der Hauptagent), Consumer-Umstellung
(audit_designer, cockpit), `@flowaudit/kanban-core` und `@flowaudit/ui`
(eigener Branch).
