# @auditcore/kanban-core

## Zweck

Framework-freie Kanban-Logik in TypeScript mit denselben Regeln wie das Python-Paket `auditcore_kanban`: Rang-Schlüssel, Übergänge, WIP-Limits, Filter, Fristen, Rechte, Validierung und reine Befehle.

Für Oberflächen und Dienste, die Kanban-Boards anzeigen oder ändern – allen
voran die Kanban-Komponenten in `@auditcore/ui` (Vue) und
`@auditcore/ui-react` (React). Die Fachlogik läuft ohne DOM und ohne
Framework; Speicherung und Nutzerverwaltung liegen hinter einem Port
(`BoardPort`) beim Consumer. Seit 0.2.0 enthält das Paket auch die
gemeinsame Ansichtslogik beider Oberflächen (Zustandsautomaten mit
`subscribe`, reine Selektoren, Tastatur- und Zeigerbedienung) sowie für die
Datenbankansicht als Kanban `groupRecords` und den Port `RecordPort` mit
`createMemoryRecordPort`.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/kanban-core
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/kanban-core@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-kanban-core-0.2.1.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Keine Peer-Abhängigkeiten, kein CSS, keine weiteren `@auditcore`-Pakete.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/kanban-core`).

## Schnellstart

```ts run
import { cardsIn, checkMove, createBoard, createCard, moveCard } from '@auditcore/kanban-core'

let counter = 0
const ctx = { actor: 'u1', now: '2026-09-25T12:00:00+00:00', newId: () => `k${++counter}` }

const board = createBoard(ctx, 'b1', 'Prüfung 2026').board
const [open, doing] = board.columns
if (!open || !doing) throw new Error('Standardspalten fehlen')

const created = createCard(board, ctx, { title: 'Beleg prüfen', column_id: open.id })
if (!created.card) throw new Error('Karte nicht angelegt')
const decision = checkMove(created.board, created.card, doing.id) // Übergang, dann WIP
if (!decision.allowed) throw new Error(decision.message)

const moved = moveCard(created.board, ctx, created.card.id, doing.id)
if (cardsIn(moved.board, doing.id).length !== 1) throw new Error('Karte fehlt in der Zielspalte')
if (moved.board.version !== 3) throw new Error('Jeder Befehl erhöht die Version')
console.log(moved.changes.map((change) => change.kind)) // [ 'card.moved' ]
```

Befehle sind reine Funktionen: Sie geben ein neues Board, die Änderungen
(`changes`) und Warnungen zurück und verändern die Eingabe nicht. Abgelehnte
Befehle werfen `KanbanError` mit `code` (z. B. `FORBIDDEN`,
`WIP_LIMIT_REACHED`) und HTTP-Status `status`.

## Einbindung

- **Direkt** in beliebigem TypeScript/JavaScript (Browser oder Node):
  Befehle und Prüfungen wie im Schnellstart.
- **Über einen Port** für Oberflächen: `BoardPort` beschreibt Laden, Karten-
  und Board-Befehle, Freigaben und optional Boardliste, Nutzersuche und
  Ereignisse. Mitgeliefert sind `MemoryBoardPort` (Demo, Tests, lokale
  Bearbeitung) und `RestBoardPort` für den REST-Vertrag
  [`docs/kanban/rest-api.md`](../../docs/kanban/rest-api.md) (Server:
  `auditcore_kanban.rest.KanbanApi`).
- **Oberfläche:** `KanbanBoard`/`<flowaudit-kanban-board>` aus `@auditcore/ui`
  und `FlowauditKanbanBoard` aus `@auditcore/ui-react` arbeiten ausschließlich
  über einen solchen Port ([Kanban-Oberfläche](../../docs/kanban/oberflaeche.md)).
- **Ansichtslogik** für eigene Oberflächen: `createBoardController`,
  `selectBoardView`, `createMoveController`, `createPointerDrag`,
  `createBoardListController`, `createColumnEditor`, `createShareSearch`
  (je ein `store` mit `get`/`set`/`subscribe`, gleiche Form wie `Store` aus
  `@auditcore/ui-core`).

```ts
import { MemoryBoardPort, RestBoardPort } from '@auditcore/kanban-core'

const local = new MemoryBoardPort({ userId: 'u1' })
const remote = new RestBoardPort({ baseUrl: '/api/kanban', userId: 'u1', optimisticLocking: true })
```

## API-Überblick

Gliederung: Modell (`auditcore_kanban.board/1`, snake_case, REST-Antworten
fließen ohne Abbildung durch), Rang (`rankBetween`, `spreadRanks`), Regeln
(`checkMove`, `movableTargets`, WIP), Filter/Fristen (`deadlineState`,
`groupByValue`), Rechte (`authorize`, `capabilities`, `checkShare`,
`checkRevoke`), Befehle, Serialisierung, Vorlagen (`TEMPLATES`), Statistik
(`boardStats`), Ports.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (242):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/kanban-core` | `ACTIONS` | Konstante | – | `permissions` |
| `@auditcore/kanban-core` | `ALLOWED` | Konstante | – | `errors` |
| `@auditcore/kanban-core` | `Action` | Typ | – | `permissions` |
| `@auditcore/kanban-core` | `AgeKey` | Typ | – | `view/cardView` |
| `@auditcore/kanban-core` | `Attachment` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `BADGE_COLORS` | Konstante | Badge-Farben je Präfix (WorkspaceTaskCard: VP, SYS/SP, JKB, PRJ), sonst grau. | `view/cardView` |
| `@auditcore/kanban-core` | `Board` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `BoardController` | Schnittstelle | – | `view/boardController` |
| `@auditcore/kanban-core` | `BoardControllerOptions` | Schnittstelle | – | `view/boardController` |
| `@auditcore/kanban-core` | `BoardEvent` | Schnittstelle | – | `port` |
| `@auditcore/kanban-core` | `BoardListController` | Schnittstelle | – | `view/boardList` |
| `@auditcore/kanban-core` | `BoardListState` | Schnittstelle | – | `view/boardList` |
| `@auditcore/kanban-core` | `BoardListView` | Schnittstelle | – | `view/boardList` |
| `@auditcore/kanban-core` | `BoardPatch` | Schnittstelle | – | `boardCommands` |
| `@auditcore/kanban-core` | `BoardPort` | Schnittstelle | – | `port` |
| `@auditcore/kanban-core` | `BoardShortcut` | Typ | – | `view/keys` |
| `@auditcore/kanban-core` | `BoardState` | Schnittstelle | – | `view/boardController` |
| `@auditcore/kanban-core` | `BoardStats` | Schnittstelle | – | `stats` |
| `@auditcore/kanban-core` | `BoardSummary` | Schnittstelle | – | `port` |
| `@auditcore/kanban-core` | `BoardTemplate` | Schnittstelle | – | `templates` |
| `@auditcore/kanban-core` | `BoardView` | Schnittstelle | – | `view/boardController` |
| `@auditcore/kanban-core` | `BoardViewInputs` | Schnittstelle | – | `view/boardController` |
| `@auditcore/kanban-core` | `CARD_COLORS` | Konstante | Kartenfarben zur Auswahl (TaskDetail colorPresets). | `view/cardView` |
| `@auditcore/kanban-core` | `CARD_FIELDS` | Konstante | Feldtabelle: JSON-Name → Prüfer. `column_id` behandelt die Verschiebelogik. | `fields` |
| `@auditcore/kanban-core` | `CARD_FIELD_NAMES` | Konstante | Geprüfte Werte der bekannten Felder, die in `fields` vorkommen. | `fields` |
| `@auditcore/kanban-core` | `COLUMN_COLORS` | Konstante | Spaltenfarben (BoardSettingsDialog PRESET_COLORS). | `view/cardView` |
| `@auditcore/kanban-core` | `COLUMN_ID_PATTERN` | Konstante | – | `validation` |
| `@auditcore/kanban-core` | `Card` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `CardFieldName` | Typ | – | `fields` |
| `@auditcore/kanban-core` | `CardFilter` | Schnittstelle | – | `filtering` |
| `@auditcore/kanban-core` | `CardLink` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `CardPatch` | Typ | Geprüfte Teiländerung einer Karte. | `fields` |
| `@auditcore/kanban-core` | `Change` | Schnittstelle | – | `commands` |
| `@auditcore/kanban-core` | `ChecklistItem` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `Column` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `ColumnEditor` | Schnittstelle | – | `view/columnEditor` |
| `@auditcore/kanban-core` | `ColumnEditorState` | Schnittstelle | – | `view/columnEditor` |
| `@auditcore/kanban-core` | `ColumnEditorView` | Schnittstelle | – | `view/columnEditor` |
| `@auditcore/kanban-core` | `ColumnView` | Schnittstelle | – | `view/board` |
| `@auditcore/kanban-core` | `CommandContext` | Schnittstelle | – | `commands` |
| `@auditcore/kanban-core` | `CommandResult` | Schnittstelle | – | `commands` |
| `@auditcore/kanban-core` | `DEFAULT_COLUMNS` | Konstante | audit_designer DEFAULT_COLUMNS: gelten, wenn ein Board keine eigenen Spalten hat. | `model` |
| `@auditcore/kanban-core` | `DEFAULT_LIMITS` | Konstante | – | `validation` |
| `@auditcore/kanban-core` | `DUE_SOON_DAYS` | Konstante | – | `filtering` |
| `@auditcore/kanban-core` | `DUE_STATES` | Konstante | – | `filtering` |
| `@auditcore/kanban-core` | `Decision` | Schnittstelle | Ergebnis einer Regelprüfung; `warnings` trägt nicht blockierende Codes (WIP-Warnmodus). | `errors` |
| `@auditcore/kanban-core` | `DragState` | Schnittstelle | – | `view/pointerDrag` |
| `@auditcore/kanban-core` | `DueState` | Typ | – | `filtering` |
| `@auditcore/kanban-core` | `EMPTY_FILTER` | Konstante | – | `view/filter` |
| `@auditcore/kanban-core` | `ErrorCode` | Typ | Fehler- und Entscheidungsvertrag, gleich zu `auditcore_kanban.errors`. | `errors` |
| `@auditcore/kanban-core` | `FREE_TRANSITIONS` | Konstante | – | `model` |
| `@auditcore/kanban-core` | `FetchLike` | Typ | – | `restPort` |
| `@auditcore/kanban-core` | `JsonObject` | Typ | – | `model` |
| `@auditcore/kanban-core` | `JsonValue` | Typ | – | `model` |
| `@auditcore/kanban-core` | `KanbanActions` | Schnittstelle | – | `view/actions` |
| `@auditcore/kanban-core` | `KanbanError` | Klasse | – | `errors` |
| `@auditcore/kanban-core` | `KanbanFilterState` | Schnittstelle | – | `view/filter` |
| `@auditcore/kanban-core` | `KanbanStore` | Schnittstelle | Kleinster Zustandsspeicher der Kanban-Ansicht. | `view/store` |
| `@auditcore/kanban-core` | `KeyInput` | Schnittstelle | Die Teile eines Tastaturereignisses, die die Belegung braucht (DOM- und React-Ereignis). | `view/keys` |
| `@auditcore/kanban-core` | `Label` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `Limits` | Schnittstelle | – | `validation` |
| `@auditcore/kanban-core` | `LocalChange` | Typ | – | `view/mutator` |
| `@auditcore/kanban-core` | `MAX_CARD_IMAGE_BYTES` | Konstante | Größte Bilddatei für das Kartendesign (2 MB wie im Original). | `view/cardView` |
| `@auditcore/kanban-core` | `MemoryBoardPort` | Klasse | – | `memoryPort` |
| `@auditcore/kanban-core` | `MemoryPortOptions` | Schnittstelle | – | `memoryPort` |
| `@auditcore/kanban-core` | `MemoryRecordPortOptions` | Schnittstelle | – | `recordPort` |
| `@auditcore/kanban-core` | `MoveController` | Schnittstelle | – | `view/moveController` |
| `@auditcore/kanban-core` | `MoveControllerOptions` | Schnittstelle | – | `view/moveController` |
| `@auditcore/kanban-core` | `MoveMessageKey` | Typ | – | `view/moveController` |
| `@auditcore/kanban-core` | `MovePreview` | Schnittstelle | – | `view/movePreview` |
| `@auditcore/kanban-core` | `MoveState` | Schnittstelle | – | `view/moveController` |
| `@auditcore/kanban-core` | `MoveTranslate` | Typ | – | `view/moveController` |
| `@auditcore/kanban-core` | `Mutate` | Typ | – | `view/mutator` |
| `@auditcore/kanban-core` | `MutationResult` | Schnittstelle | – | `port` |
| `@auditcore/kanban-core` | `MutatorHooks` | Schnittstelle | – | `view/mutator` |
| `@auditcore/kanban-core` | `PERMISSIONS` | Konstante | – | `permissions` |
| `@auditcore/kanban-core` | `PRIORITIES` | Konstante | – | `model` |
| `@auditcore/kanban-core` | `PRIORITY_TONES` | Konstante | – | `view/cardView` |
| `@auditcore/kanban-core` | `Placement` | Schnittstelle | – | `commands` |
| `@auditcore/kanban-core` | `PointerDrag` | Schnittstelle | – | `view/pointerDrag` |
| `@auditcore/kanban-core` | `PointerDragOptions` | Schnittstelle | – | `view/pointerDrag` |
| `@auditcore/kanban-core` | `PointerInput` | Schnittstelle | Die Teile eines Zeigerereignisses, die das Ziehen braucht (DOM- und React-Ereignis). | `view/pointerDrag` |
| `@auditcore/kanban-core` | `Priority` | Typ | – | `model` |
| `@auditcore/kanban-core` | `PriorityTone` | Typ | Farbton eines Badges (gleiche Namen wie `BadgeTone` in `@auditcore/ui-core`). | `view/cardView` |
| `@auditcore/kanban-core` | `RANK_DIGITS` | Konstante | Rang-Schlüssel für die Reihenfolge in einer Spalte (fraktionale Indizes). Zwischen zwei Karten entsteht immer ein neuer Schlüssel, ohne die übrigen umzunummerieren. | `rank` |
| `@auditcore/kanban-core` | `ROLE_ACTIONS` | Konstante | Deklarative Rollentabelle; configure, share, delete_board und pin nur für den Eigentümer. | `permissions` |
| `@auditcore/kanban-core` | `RankError` | Klasse | – | `rank` |
| `@auditcore/kanban-core` | `RecordGroup` | Schnittstelle | – | `records` |
| `@auditcore/kanban-core` | `RecordPort` | Schnittstelle | Datenzugang der Datenbankansicht; `addRow` ist optional (sonst keine neue Karte). | `records` |
| `@auditcore/kanban-core` | `RecordProperty` | Schnittstelle | – | `records` |
| `@auditcore/kanban-core` | `RecordPropertyType` | Typ | – | `records` |
| `@auditcore/kanban-core` | `RecordRow` | Schnittstelle | – | `records` |
| `@auditcore/kanban-core` | `RecordTable` | Schnittstelle | – | `records` |
| `@auditcore/kanban-core` | `RecordValue` | Typ | – | `records` |
| `@auditcore/kanban-core` | `RelativeKey` | Typ | – | `view/cardView` |
| `@auditcore/kanban-core` | `RemoteChange` | Typ | – | `view/mutator` |
| `@auditcore/kanban-core` | `RestBoardPort` | Klasse | – | `restPort` |
| `@auditcore/kanban-core` | `RestPortOptions` | Schnittstelle | – | `restPort` |
| `@auditcore/kanban-core` | `Role` | Typ | – | `model` |
| `@auditcore/kanban-core` | `SCHEMA_VERSION` | Konstante | Domänenmodell in der JSON-Form von `auditcore_kanban` (snake_case), damit REST-Antworten ohne Abbildung in Oberfläche und Logik fließen. | `model` |
| `@auditcore/kanban-core` | `SHARE_RESULT_LIMIT` | Konstante | – | `view/shareSearch` |
| `@auditcore/kanban-core` | `STATUS_BY_CODE` | Konstante | HTTP-Status je Code (REST-Vertrag docs/kanban/rest-api.md). | `errors` |
| `@auditcore/kanban-core` | `Share` | Schnittstelle | – | `model` |
| `@auditcore/kanban-core` | `SharePermission` | Typ | – | `model` |
| `@auditcore/kanban-core` | `ShareSearch` | Schnittstelle | – | `view/shareSearch` |
| `@auditcore/kanban-core` | `ShareSearchState` | Schnittstelle | – | `view/shareSearch` |
| `@auditcore/kanban-core` | `TEMPLATES` | Konstante | – | `templates` |
| `@auditcore/kanban-core` | `TransitionPolicy` | Schnittstelle | Bewegungsregeln. `mode: 'free'` erlaubt jeden Spaltenwechsel (audit_designer), `restricted` nur die Paare in `allowed`. | `model` |
| `@auditcore/kanban-core` | `UiCapabilities` | Typ | – | `view/board` |
| `@auditcore/kanban-core` | `UiCapability` | Typ | – | `view/board` |
| `@auditcore/kanban-core` | `UserRef` | Schnittstelle | – | `port` |
| `@auditcore/kanban-core` | `WipMode` | Typ | – | `model` |
| `@auditcore/kanban-core` | `WipState` | Schnittstelle | – | `rules` |
| `@auditcore/kanban-core` | `allowedActions` | Funktion | – | `permissions` |
| `@auditcore/kanban-core` | `applyPreview` | Funktion | Spaltenansicht mit der bewegten Karte an der Vorschauposition. | `view/movePreview` |
| `@auditcore/kanban-core` | `asOptionalString` | Funktion | – | `fields` |
| `@auditcore/kanban-core` | `asString` | Funktion | – | `fields` |
| `@auditcore/kanban-core` | `authorize` | Funktion | – | `permissions` |
| `@auditcore/kanban-core` | `badgePrefix` | Funktion | – | `view/cardView` |
| `@auditcore/kanban-core` | `badgeStyle` | Funktion | – | `view/cardView` |
| `@auditcore/kanban-core` | `boardFromJson` | Funktion | Liest und prüft ein Board-Dokument strukturell. | `serialization` |
| `@auditcore/kanban-core` | `boardShortcut` | Funktion | – | `view/keys` |
| `@auditcore/kanban-core` | `boardStats` | Funktion | – | `stats` |
| `@auditcore/kanban-core` | `boardToJson` | Funktion | Board-Dokument mit Karten in Board-Reihenfolge (stabile Ausgabe wie board_to_json). | `serialization` |
| `@auditcore/kanban-core` | `bump` | Funktion | Nächste Fassung des Boards. | `commands` |
| `@auditcore/kanban-core` | `capabilities` | Funktion | Aktionen, die der Nutzer ausführen darf (für die Oberfläche). | `permissions` |
| `@auditcore/kanban-core` | `cardAge` | Funktion | Alter einer Karte in Stufen wie WorkspaceTaskCard (neu, Stunden, Tage, Wochen, Monate). | `view/cardView` |
| `@auditcore/kanban-core` | `cardStyle` | Funktion | Inline-Stil einer Karte mit eigener Farbe bzw. Hintergrundbild (CSS-Variablen wie im Original). | `view/cardView` |
| `@auditcore/kanban-core` | `cardsIn` | Funktion | Karten einer Spalte in Anzeigereihenfolge. | `model` |
| `@auditcore/kanban-core` | `checkCapacity` | Funktion | Passt eine weitere Karte in die Spalte? Im Warnmodus ja, mit Warnung. | `rules` |
| `@auditcore/kanban-core` | `checkMove` | Funktion | Vollständige Prüfung für das Verschieben einer Karte (Übergang, dann WIP). | `rules` |
| `@auditcore/kanban-core` | `checkRevoke` | Funktion | – | `permissions` |
| `@auditcore/kanban-core` | `checkShare` | Funktion | – | `permissions` |
| `@auditcore/kanban-core` | `checkTransition` | Funktion | Spaltenwechsel ohne Kapazität; `source === target` ist ein Umsortieren. | `rules` |
| `@auditcore/kanban-core` | `checklistProgress` | Funktion | – | `stats` |
| `@auditcore/kanban-core` | `cloneJson` | Funktion | Tiefe Kopie reiner JSON-Daten. Anders als structuredClone funktioniert sie auch mit reaktiven Proxys (Vue), die Oberflächen an den Port übergeben. | `model` |
| `@auditcore/kanban-core` | `columnForStatus` | Funktion | Spalte zu einem externen Status (ID oder Alias, cockpit `spalteVon`). | `model` |
| `@auditcore/kanban-core` | `columnLoad` | Funktion | Kartenzahl einer Spalte, ohne die gerade bewegte Karte. | `rules` |
| `@auditcore/kanban-core` | `columnViews` | Funktion | Spaltenansicht: sichtbare (gefilterte) Karten, Gesamtzahl und WIP-Zustand je Spalte. | `view/board` |
| `@auditcore/kanban-core` | `columnsFromJson` | Funktion | Spaltenliste eines Anfragekörpers (Teilangaben erhalten Standardwerte). | `serialization` |
| `@auditcore/kanban-core` | `compareCards` | Funktion | Stabile Reihenfolge in einer Spalte: Rang, dann Anlagezeit, dann ID. | `model` |
| `@auditcore/kanban-core` | `compareRanks` | Funktion | Sortiervergleich nach Rang (Code-Einheiten-Reihenfolge wie Python-str). | `rank` |
| `@auditcore/kanban-core` | `configureColumns` | Funktion | Ersetzt den Spaltensatz (nur Eigentümer); Karten entfernter Spalten wandern in die erste Spalte. | `boardCommands` |
| `@auditcore/kanban-core` | `createBoard` | Funktion | – | `boardCommands` |
| `@auditcore/kanban-core` | `createBoardController` | Funktion | – | `view/boardController` |
| `@auditcore/kanban-core` | `createBoardListController` | Funktion | – | `view/boardList` |
| `@auditcore/kanban-core` | `createCard` | Funktion | Neue Karte in `column_id` (Standard: erste Spalte), angehängt, sofern keine Position angegeben ist. | `commands` |
| `@auditcore/kanban-core` | `createColumnEditor` | Funktion | – | `view/columnEditor` |
| `@auditcore/kanban-core` | `createKanbanActions` | Funktion | – | `view/actions` |
| `@auditcore/kanban-core` | `createKanbanStore` | Funktion | – | `view/store` |
| `@auditcore/kanban-core` | `createMemoryRecordPort` | Funktion | – | `recordPort` |
| `@auditcore/kanban-core` | `createMoveController` | Funktion | – | `view/moveController` |
| `@auditcore/kanban-core` | `createMutator` | Funktion | – | `view/mutator` |
| `@auditcore/kanban-core` | `createPointerDrag` | Funktion | – | `view/pointerDrag` |
| `@auditcore/kanban-core` | `createShareSearch` | Funktion | – | `view/shareSearch` |
| `@auditcore/kanban-core` | `deadlineState` | Funktion | `none`, `overdue`, `due_soon` (≤ 3 Tage) oder `later` – `today` als ISO-Datum. | `filtering` |
| `@auditcore/kanban-core` | `decisionToJson` | Funktion | JSON-Form der Paritätsfixtures. | `errors` |
| `@auditcore/kanban-core` | `deleteCard` | Funktion | – | `commands` |
| `@auditcore/kanban-core` | `deny` | Funktion | – | `errors` |
| `@auditcore/kanban-core` | `doneColumn` | Funktion | Erste als erledigt markierte Spalte, sonst die letzte (audit_designer). | `model` |
| `@auditcore/kanban-core` | `dropTarget` | Funktion | Spalte und Einfügeposition unter dem Zeiger innerhalb des Boards. | `view/pointerDrag` |
| `@auditcore/kanban-core` | `dropValue` | Funktion | Zellwert für das Ablegen in einer Spalte: `""` wird `null` (wie `updateCell(…, value \|\| null)`). | `records` |
| `@auditcore/kanban-core` | `fileSize` | Funktion | Dateigröße als Zahl und Einheit (B, KB, MB, GB); die Zahl formatiert die Oberfläche je Sprache. | `view/cardView` |
| `@auditcore/kanban-core` | `filterCards` | Funktion | Passende Karten in Board-Reihenfolge. | `filtering` |
| `@auditcore/kanban-core` | `filterCriteria` | Funktion | – | `view/filter` |
| `@auditcore/kanban-core` | `findCard` | Funktion | – | `model` |
| `@auditcore/kanban-core` | `findColumn` | Funktion | – | `model` |
| `@auditcore/kanban-core` | `findTemplate` | Funktion | – | `templates` |
| `@auditcore/kanban-core` | `firstColumn` | Funktion | – | `model` |
| `@auditcore/kanban-core` | `getCard` | Funktion | – | `commands` |
| `@auditcore/kanban-core` | `groupByValue` | Funktion | Gruppiert Einträge je Option (useDbKanban). Leere oder unbekannte Werte landen in einem führenden Eimer `""`, der nur existiert, wenn er nicht leer ist. | `filtering` |
| `@auditcore/kanban-core` | `groupOf` | Funktion | Aktueller Spaltenwert eines Datensatzes (`""` für leer oder unbekannt). | `records` |
| `@auditcore/kanban-core` | `groupRecords` | Funktion | Spalten je Option; ohne gültige Gruppierung keine Spalten (wie das Original). | `records` |
| `@auditcore/kanban-core` | `groupableProperties` | Funktion | Eigenschaften, nach denen gruppiert werden kann (nur `select` mit Optionen). | `records` |
| `@auditcore/kanban-core` | `handleCardKey` | Funktion | Verarbeitet eine Taste auf einer Karte; true, wenn sie verbraucht wurde. | `view/keys` |
| `@auditcore/kanban-core` | `indexAt` | Funktion | Einfügeposition in einer Kartenliste anhand der Zeigerhöhe (Kartenmitte). | `view/pointerDrag` |
| `@auditcore/kanban-core` | `initials` | Funktion | Initialen aus einem Namen: erster und letzter Namensteil. | `view/cardView` |
| `@auditcore/kanban-core` | `invalidField` | Funktion | – | `fields` |
| `@auditcore/kanban-core` | `isFilterActive` | Funktion | – | `filtering` |
| `@auditcore/kanban-core` | `isJson` | Funktion | – | `fields` |
| `@auditcore/kanban-core` | `isPlainObject` | Funktion | – | `fields` |
| `@auditcore/kanban-core` | `isPriority` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `isTyping` | Funktion | Tastenkürzel des Boards (N, F, /, Escape), nicht während der Texteingabe. | `view/keys` |
| `@auditcore/kanban-core` | `isValidRank` | Funktion | Gültig: nicht leer, nur Base-62-Zeichen, letzte Stelle nicht '0'. | `rank` |
| `@auditcore/kanban-core` | `listenBoardShortcuts` | Funktion | Meldet die Tastenkürzel N, F und / am Dokument an, wenn der Fokus im Board oder auf der Seite (body) liegt; liefert die Abmeldung. | `view/keys` |
| `@auditcore/kanban-core` | `locate` | Funktion | Aktuelle Spalte und Position einer Karte in der Ansicht. | `view/movePreview` |
| `@auditcore/kanban-core` | `matches` | Funktion | – | `filtering` |
| `@auditcore/kanban-core` | `matchesQuery` | Funktion | Groß-/Kleinschreibung ignorierende Teilzeichenkettensuche in Titel, Beschreibung, Badge und Tags. | `filtering` |
| `@auditcore/kanban-core` | `matchesRecord` | Funktion | Suche über Text-, Zahl- und Auswahlzellen, ohne Groß-/Kleinschreibung. | `records` |
| `@auditcore/kanban-core` | `movableTargets` | Funktion | Spalten, in die die Karte derzeit verschoben werden darf (Tastatur, Menü). | `rules` |
| `@auditcore/kanban-core` | `moveCard` | Funktion | Verschiebt vor/hinter eine Karte oder an `index` (Standard: Ende). | `commands` |
| `@auditcore/kanban-core` | `neighbourColumn` | Funktion | Nächste Spalte in Richtung `step` (±1), in die `allowed` die Karte lässt. | `view/movePreview` |
| `@auditcore/kanban-core` | `neighbourGroup` | Funktion | Nachbarspalte für Tastaturbedienung; `null`, wenn es keine gibt. | `records` |
| `@auditcore/kanban-core` | `normalizeDue` | Funktion | Datum bleibt Datum, Datum-Zeit wird wie Pythons `datetime.isoformat()` normalisiert (`Z` → `+00:00`); leer löscht, Ungültiges wird abgelehnt. | `validation` |
| `@auditcore/kanban-core` | `nudgeTarget` | Funktion | Ziel für Strg+Pfeil (cockpit): eine Position bzw. die nächste erlaubte Spalte bei gleicher Position. | `view/movePreview` |
| `@auditcore/kanban-core` | `orderedCards` | Funktion | Alle Karten: Spaltenreihenfolge, dann Rang; Karten unbekannter Spalten zuletzt. | `model` |
| `@auditcore/kanban-core` | `parseCardFields` | Funktion | – | `fields` |
| `@auditcore/kanban-core` | `parseDueDay` | Funktion | Tagesnummer (UTC) eines ISO-Datums bzw. des Datumsteils; null bei fehlend/ungültig. | `filtering` |
| `@auditcore/kanban-core` | `percent` | Funktion | Gerundeter Prozentwert, halbe Werte aufgerundet (= Math.round, wie stats.py). | `stats` |
| `@auditcore/kanban-core` | `place` | Funktion | Rang für eine Karte an `slot`; verteilt die Spalte nur neu, wenn Ränge kollidieren. | `commands` |
| `@auditcore/kanban-core` | `placementFor` | Funktion | Platzierung für den Port aus der sichtbaren Nachbarschaft: vor der Karte an `index`, sonst hinter der letzten sichtbaren Karte, sonst ans Ende. | `view/movePreview` |
| `@auditcore/kanban-core` | `policyFromJson` | Funktion | `mode` free ignoriert `allowed`; restricted erlaubt nur die genannten Paare. | `serialization` |
| `@auditcore/kanban-core` | `preview` | Funktion | – | `view/cardView` |
| `@auditcore/kanban-core` | `previewColumns` | Funktion | Spalten mit der bewegten Karte an der Vorschauposition (für die Anzeige). | `view/moveController` |
| `@auditcore/kanban-core` | `raiseIfDenied` | Funktion | – | `errors` |
| `@auditcore/kanban-core` | `rankBetween` | Funktion | Neuer Schlüssel echt zwischen `before` und `after` (null = offenes Ende). | `rank` |
| `@auditcore/kanban-core` | `relativeTime` | Funktion | Relative Zeit für die Boardliste (WorkspaceSidebar.relativeTime). | `view/cardView` |
| `@auditcore/kanban-core` | `requireAction` | Funktion | – | `commands` |
| `@auditcore/kanban-core` | `resolveSlot` | Funktion | Einfügeposition unter den Geschwistern (Standard: Ende; Index wird geklemmt). | `commands` |
| `@auditcore/kanban-core` | `respreadColumn` | Funktion | Ersetzt die Ränge einer Spalte durch gleichmäßig verteilte Schlüssel (Reihenfolge bleibt). | `boardCommands` |
| `@auditcore/kanban-core` | `revokeShare` | Funktion | Eigentümer widerruft jede Freigabe, Empfänger die eigene. | `boardCommands` |
| `@auditcore/kanban-core` | `roleOf` | Funktion | Rolle: Eigentümer, eigene Freigabe, sonst geerbte Freigabe (z. B. Notizbuch). | `permissions` |
| `@auditcore/kanban-core` | `selectBoardList` | Funktion | – | `view/boardList` |
| `@auditcore/kanban-core` | `selectBoardView` | Funktion | Alles, was die Oberfläche aus Stand und Eingaben anzeigt (reine Funktion). | `view/boardController` |
| `@auditcore/kanban-core` | `selectColumnEditor` | Funktion | – | `view/columnEditor` |
| `@auditcore/kanban-core` | `shareBoard` | Funktion | Freigabe anlegen oder ändern (Upsert); nur der Eigentümer darf teilen. | `boardCommands` |
| `@auditcore/kanban-core` | `shareFor` | Funktion | – | `model` |
| `@auditcore/kanban-core` | `shareName` | Funktion | Anzeigename einer freigegebenen Person: Suchtreffer, sonst bekannte Nutzer, sonst Kennung. | `view/shareSearch` |
| `@auditcore/kanban-core` | `siblingsOf` | Funktion | Sichtbare Karten einer Spalte ohne die bewegte Karte. | `view/movePreview` |
| `@auditcore/kanban-core` | `slugify` | Funktion | Spalten-ID aus einer Beschriftung (BoardSettingsDialog.slugify ohne wirkungslose Ersetzungen). | `validation` |
| `@auditcore/kanban-core` | `sortBoards` | Funktion | Angeheftete zuerst, dann zuletzt geändert (WorkspaceSidebar.sortedBoards). | `view/board` |
| `@auditcore/kanban-core` | `spreadRanks` | Funktion | `count` gleichmäßig verteilte, aufsteigende Schlüssel (Neuaufbau einer Spalte). | `rank` |
| `@auditcore/kanban-core` | `stepPreview` | Funktion | Nächste Vorschau bei einer Pfeiltaste im Aufnahmemodus; null, wenn kein Ziel erlaubt ist. | `view/movePreview` |
| `@auditcore/kanban-core` | `textLength` | Funktion | Länge in Unicode-Codepunkten (wie Pythons len), nicht in UTF-16-Einheiten. | `validation` |
| `@auditcore/kanban-core` | `textOn` | Funktion | Lesbare Schriftfarbe auf einer Kartenfarbe (Luminanzschwelle wie im Original). | `view/cardView` |
| `@auditcore/kanban-core` | `toKanbanError` | Funktion | – | `view/board` |
| `@auditcore/kanban-core` | `todayIso` | Funktion | Heutiges Datum als ISO-Zeichenkette in lokaler Zeit. | `filtering` |
| `@auditcore/kanban-core` | `toggleDone` | Funktion | Erledigt-Spalte → oben in die erste Spalte; sonst → ans Ende der Erledigt-Spalte. | `commands` |
| `@auditcore/kanban-core` | `uiCapabilities` | Funktion | Rechte des Nutzers für die Oberfläche; `locked` (readOnly) sperrt alle Schreibrechte. | `view/board` |
| `@auditcore/kanban-core` | `uniqueColumnId` | Funktion | Eindeutige Spalten-ID: Slug, bei Kollision mit _2, _3 …; Rückfall `spalte`. | `validation` |
| `@auditcore/kanban-core` | `updateBoard` | Funktion | Umbenennen (Eigentümer, Bearbeiten), Anheften/Archivieren (nur Eigentümer). | `boardCommands` |
| `@auditcore/kanban-core` | `updateCard` | Funktion | Ändert Felder; eine andere `column_id` verschiebt ans Ende dieser Spalte. | `commands` |
| `@auditcore/kanban-core` | `validateBadge` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `validateBoardTitle` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `validateColumns` | Funktion | Spaltensatz in der Prüfreihenfolge des Originals: Anzahl, eindeutige IDs, dann je Spalte. | `validation` |
| `@auditcore/kanban-core` | `validateDescription` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `validatePriority` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `validateTags` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `validateTitle` | Funktion | – | `validation` |
| `@auditcore/kanban-core` | `wipStates` | Funktion | – | `rules` |
| `@auditcore/kanban-core` | `withCell` | Funktion | Neue Tabelle mit geändertem Zellwert (unveränderlich). | `records` |
| `@auditcore/kanban-core` | `withRow` | Funktion | Neue Tabelle mit ersetztem oder angehängtem Datensatz. | `records` |
<!-- api-overview:end -->

## Konfiguration

- `CommandContext`: `actor` (Nutzer), `now` (ISO-Zeitstempel), optional
  `newId` (Kennungen), `inherited` (geerbte Rechte je Nutzer) und `limits`
  (Grenzen für Titel, Spalten, Karten; Standard `DEFAULT_LIMITS`).
- Board-Regeln stehen im Board selbst: `transitions` (`free`/`restricted`,
  erlaubte Übergänge, gesperrte Spalten, feste Reihenfolge) und `wip_mode`
  (`block` wirft, `warn` liefert `WIP_LIMIT_REACHED` als Warnung).
- `MemoryPortOptions`: `userId`, Start-`boards`, `users`, `latency`, `clock`,
  `newId`.
- `RestPortOptions`: `baseUrl`, `userId`, injizierbares `fetch`, `headers`,
  `optimisticLocking` (erwartete Version mitsenden, 409 `VERSION_CONFLICT`),
  `searchUsers`.
- Ansichtslogik: `BoardControllerOptions` (`port`, `boardId`, `onError`,
  `onChange` als Funktionen, damit sich Eingaben ändern dürfen),
  `BoardViewInputs` (`userId`, `criteria`, `readOnly`, `today`),
  `MoveControllerOptions` (`board`, `columns`, `canMove`, Übersetzung `t`,
  `focusCard`).
- Vorlagen: 7 Vorlagen aus dem audit_designer und das Auftragsboard aus
  cockpit (`TEMPLATES`, `findTemplate(key)`).

## Herkunft und Charakterisierung

Neuimplementierung in auditcore, kein Code übernommen. Grundlage ist die
Charakterisierung des Workspace-Boards aus `janpow77/audit_designer` und des
Auftragsboards aus `janpow77/cockpit`
([Paritätsinventur](../../docs/kanban/paritaet-audit-designer.md)). Die
Parität zum Python-Paket `auditcore_kanban` wird über gemeinsame
Paritätsfixtures geprüft: Python erzeugt die Fälle unter
`packages/auditcore_kanban/tests/fixtures/parity/`, die Tests dieses Pakets
(`test/parity.spec.ts`) lesen dieselben Dateien und vergleichen mit
`expected` ([Format](../../docs/kanban/parity-fixtures.md)). Der
`RestBoardPort` wird zusätzlich gegen den Python-Server geprüft
(`test/restIntegration.spec.ts`, nur mit `KANBAN_API_URL`).

## Abhängigkeiten

Keine Laufzeitabhängigkeiten (weder `dependencies` noch
`peerDependencies`). Node ≥ 20.19 für Bau und Tests; im Browser genügt eine
ES2022-Umgebung, `RestBoardPort` nutzt `fetch` (injizierbar). Nur
`createPointerDrag` und `listenBoardShortcuts` brauchen ein DOM.

## Sicherheit und Datenschutz

Die Logik rendert nichts und speichert nichts; Boards können
personenbezogene Daten (Namen, Zuständige, Freigaben) enthalten und liegen
ausschließlich in dem Port, den die Anwendung wählt. `MemoryBoardPort` hält
Daten nur im Arbeitsspeicher. `RestBoardPort` sendet an die konfigurierte
`baseUrl` mit den übergebenen `headers`; Authentifizierung ist Sache des
Consumers. Rechteprüfungen im Client dienen der Anzeige und der
optimistischen Änderung – verbindlich entscheidet der Server
(`auditcore_kanban`) mit denselben Regeln. Unbeteiligte erhalten
`NOT_VISIBLE` statt einer Unterscheidung zwischen „fehlt“ und „verboten“.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neuimplementierung ohne übernommenen Fremdcode; Herkunft der
Regeln siehe Paritätsinventur und Fixtures oben.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
