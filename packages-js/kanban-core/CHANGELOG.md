# Changelog @flowaudit/kanban-core

## 0.1.0 – 2026-09-25

Erste Fassung (PR #84).

- Framework-freie Kanban-Logik mit denselben Regeln wie `auditcore_kanban`:
  Rang-Schlüssel, Übergänge, WIP-Limits, Filter, Fristen, Rechte,
  Validierung, reine Befehle, Serialisierung, Vorlagen und Statistik.
- Geprüft gegen die gemeinsamen Paritätsfixtures aus
  `packages/auditcore_kanban/tests/fixtures/parity/`.
- Ports `MemoryBoardPort` und `RestBoardPort` (REST-Vertrag
  `docs/kanban/rest-api.md`), REST-Vertragsprüfung gegen den Python-Server
  `auditcore_kanban.rest.KanbanApi` (nur mit `KANBAN_API_URL`).
