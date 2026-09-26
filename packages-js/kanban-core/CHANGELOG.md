# Changelog @flowaudit/kanban-core

## 0.2.0 – unveröffentlicht

- Gemeinsame Ansichtslogik der Kanban-Oberflächen (Vue `@flowaudit/ui`,
  React `@flowaudit/ui-react`), aus den Vue-Composables herausgelöst:
  `createBoardController` + `selectBoardView` (optimistische Änderungen in
  fester Reihenfolge, Rückrollen, Neuladen bei Versionskonflikt),
  `createKanbanActions`, `createMoveController` (Tastatur-Verschieben mit
  Ansagen), `createPointerDrag`, `handleCardKey`/`boardShortcut`/
  `listenBoardShortcuts`, `createBoardListController`/`selectBoardList`,
  `createColumnEditor`/`selectColumnEditor`, `createShareSearch`/`shareName`,
  `filterCriteria`/`EMPTY_FILTER`, `columnViews`, `uiCapabilities`,
  `sortBoards`, Vorschau-Funktionen (`applyPreview`, `placementFor`, …) und
  Darstellungshilfen (`badgeStyle`, `cardAge`, `cardStyle`, `fileSize`, …).
- Jeder Automat hat einen `store` (`get`/`set`/`subscribe`, gleiche Form wie
  `Store` in `@flowaudit/ui-core`).
- Gemeinsame Paritätsfälle Vue ↔ React unter `test/parity/cases.ts`.

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
