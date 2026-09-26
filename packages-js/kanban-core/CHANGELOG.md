# Changelog @auditcore/kanban-core

## 0.2.1 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/kanban-core` statt `@flowaudit/kanban-core` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-kanban-core-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Erste Veröffentlichung als Release-Datei. Enthält alles unter 0.2.0 und den Build mit Vite 8 und vite-plugin-dts 5 (#169). Ein vor dem Release gepackter Stand 0.2.0 war bereits als Tarball in Anwendungen eingebunden (audit_designer); deshalb neue Versionsnummer.

## 0.2.0 – nicht als Release-Datei veröffentlicht

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
- Datenbankansicht als Kanban (useDbKanban aus audit_designer): Datentypen
  `RecordTable`/`RecordProperty`/`RecordRow`/`RecordValue`, Port `RecordPort`
  (`load`, `updateCell`, optional `addRow`), `createMemoryRecordPort`,
  `groupRecords` (auf `groupByValue`), `groupableProperties`, `groupOf`,
  `dropValue` (Spalte „ohne Wert“ setzt `null`), `neighbourGroup`,
  `withCell`, `withRow`, `matchesRecord`.
- Paritätsfixture `group.json` aus `auditcore_kanban.group_by_value`
  (Python erzeugt, TypeScript prüft).

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
