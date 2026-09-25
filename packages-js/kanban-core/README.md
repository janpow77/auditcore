# @flowaudit/kanban-core

Framework-freie Kanban-Logik in TypeScript – dieselben Regeln wie das
Python-Paket `auditcore_kanban`, geprüft über gemeinsame Paritätsfixtures
(`packages/auditcore_kanban/tests/fixtures/parity/`, Format in
`docs/kanban/parity-fixtures.md`).

- **Modell** in der JSON-Form `auditcore_kanban.board/1` (snake_case, REST-Antworten fließen ohne Abbildung durch).
- **Rang-Schlüssel** (`rankBetween`, `spreadRanks`): Einfügen zwischen zwei Karten ohne Umnummerieren.
- **Regeln**: Übergänge (`free`/`restricted`, gesperrte Spalten, feste Reihenfolge), WIP-Limits (`block`/`warn`), `checkMove`, `movableTargets`.
- **Filter/Suche**, Fälligkeit (`deadlineState`), Gruppierung (`groupByValue`).
- **Rechte** (`authorize`, `capabilities`, `checkShare`, `checkRevoke`): owner/edit/read, Unbeteiligte sehen nichts (`NOT_VISIBLE`).
- **Befehle** (`createCard`, `moveCard`, `updateCard`, `deleteCard`, `toggleDone`, `configureColumns`, `shareBoard`, …) als reine Funktionen: neues Board plus Änderungen.
- **Ports**: `BoardPort`-Schnittstelle, `MemoryBoardPort` (Demo/Tests), `RestBoardPort` (REST-Vertrag `docs/kanban/rest-api.md`, `fetch` injizierbar).
- **Vorlagen** (7 Vorlagen aus audit_designer, cockpit-Auftragsboard), Statistik (`boardStats`).

Herkunft: Neuimplementierung in auditcore nach der Charakterisierung des
Workspace-Boards aus janpow77/audit_designer und des Auftragsboards aus
janpow77/cockpit (Paritätsinventur `docs/kanban/paritaet-audit-designer.md`);
kein Code übernommen. Keine Laufzeitabhängigkeiten. Lizenz: MIT.
