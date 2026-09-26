# @flowaudit/kanban-core

## Zweck

Framework-freie Kanban-Logik in TypeScript mit denselben Regeln wie das Python-Paket `auditcore_kanban`: Rang-Schlüssel, Übergänge, WIP-Limits, Filter, Fristen, Rechte, Validierung und reine Befehle.

Für Oberflächen und Dienste, die Kanban-Boards anzeigen oder ändern – allen
voran die Kanban-Komponenten in `@flowaudit/ui` (Vue) und
`@flowaudit/ui-react` (React). Die Fachlogik läuft ohne DOM und ohne
Framework; Speicherung und Nutzerverwaltung liegen hinter einem Port
(`BoardPort`) beim Consumer. Seit 0.2.0 enthält das Paket auch die
gemeinsame Ansichtslogik beider Oberflächen (Zustandsautomaten mit
`subscribe`, reine Selektoren, Tastatur- und Zeigerbedienung) sowie für die
Datenbankansicht als Kanban `groupRecords` und den Port `RecordPort` mit
`createMemoryRecordPort`.

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                                    # im Repository-Stamm
npm run build -w @flowaudit/kanban-core   # dist/: ESM und Typen
```

Im Anwendungsrepository:

```sh
npm install @flowaudit/kanban-core
```

Das Paket ist noch nicht in einer npm-Registry veröffentlicht; bis dahin
Bezug über den Workspace oder ein mit `npm pack -w @flowaudit/kanban-core`
erzeugtes Tarball (`npm install ./flowaudit-kanban-core-0.1.0.tgz`).

## Schnellstart

```ts run
import { cardsIn, checkMove, createBoard, createCard, moveCard } from '@flowaudit/kanban-core'

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
- **Oberfläche:** `KanbanBoard`/`<flowaudit-kanban-board>` aus `@flowaudit/ui`
  und `FlowauditKanbanBoard` aus `@flowaudit/ui-react` arbeiten ausschließlich
  über einen solchen Port ([Kanban-Oberfläche](../../docs/kanban/oberflaeche.md)).
- **Ansichtslogik** für eigene Oberflächen: `createBoardController`,
  `selectBoardView`, `createMoveController`, `createPointerDrag`,
  `createBoardListController`, `createColumnEditor`, `createShareSearch`
  (je ein `store` mit `get`/`set`/`subscribe`, gleiche Form wie `Store` aus
  `@flowaudit/ui-core`).

```ts
import { MemoryBoardPort, RestBoardPort } from '@flowaudit/kanban-core'

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
| `@flowaudit/kanban-core` | `ACTIONS` | Konstante | – | `permissions` |
| `@flowaudit/kanban-core` | `ALLOWED` | Konstante | – | `errors` |
| `@flowaudit/kanban-core` | `Action` | Typ | – | `permissions` |
| `@flowaudit/kanban-core` | `AgeKey` | Typ | – | `view/cardView` |
| `@flowaudit/kanban-core` | `Attachment` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `BADGE_COLORS` | Konstante | Badge-Farben je Präfix (WorkspaceTaskCard: VP, SYS/SP, JKB, PRJ), sonst grau. | `view/cardView` |
| `@flowaudit/kanban-core` | `Board` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `BoardController` | Schnittstelle | – | `view/boardController` |
| `@flowaudit/kanban-core` | `BoardControllerOptions` | Schnittstelle | – | `view/boardController` |
| `@flowaudit/kanban-core` | `BoardEvent` | Schnittstelle | – | `port` |
| `@flowaudit/kanban-core` | `BoardListController` | Schnittstelle | – | `view/boardList` |
| `@flowaudit/kanban-core` | `BoardListState` | Schnittstelle | – | `view/boardList` |
| `@flowaudit/kanban-core` | `BoardListView` | Schnittstelle | – | `view/boardList` |
| `@flowaudit/kanban-core` | `BoardPatch` | Schnittstelle | – | `boardCommands` |
| `@flowaudit/kanban-core` | `BoardPort` | Schnittstelle | – | `port` |
| `@flowaudit/kanban-core` | `BoardShortcut` | Typ | – | `view/keys` |
| `@flowaudit/kanban-core` | `BoardState` | Schnittstelle | – | `view/boardController` |
| `@flowaudit/kanban-core` | `BoardStats` | Schnittstelle | – | `stats` |
| `@flowaudit/kanban-core` | `BoardSummary` | Schnittstelle | – | `port` |
| `@flowaudit/kanban-core` | `BoardTemplate` | Schnittstelle | – | `templates` |
| `@flowaudit/kanban-core` | `BoardView` | Schnittstelle | – | `view/boardController` |
| `@flowaudit/kanban-core` | `BoardViewInputs` | Schnittstelle | – | `view/boardController` |
| `@flowaudit/kanban-core` | `CARD_COLORS` | Konstante | Kartenfarben zur Auswahl (TaskDetail colorPresets). | `view/cardView` |
| `@flowaudit/kanban-core` | `CARD_FIELDS` | Konstante | Feldtabelle: JSON-Name → Prüfer. `column_id` behandelt die Verschiebelogik. | `fields` |
| `@flowaudit/kanban-core` | `CARD_FIELD_NAMES` | Konstante | Geprüfte Werte der bekannten Felder, die in `fields` vorkommen. | `fields` |
| `@flowaudit/kanban-core` | `COLUMN_COLORS` | Konstante | Spaltenfarben (BoardSettingsDialog PRESET_COLORS). | `view/cardView` |
| `@flowaudit/kanban-core` | `COLUMN_ID_PATTERN` | Konstante | – | `validation` |
| `@flowaudit/kanban-core` | `Card` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `CardFieldName` | Typ | – | `fields` |
| `@flowaudit/kanban-core` | `CardFilter` | Schnittstelle | – | `filtering` |
| `@flowaudit/kanban-core` | `CardLink` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `CardPatch` | Typ | Geprüfte Teiländerung einer Karte. | `fields` |
| `@flowaudit/kanban-core` | `Change` | Schnittstelle | – | `commands` |
| `@flowaudit/kanban-core` | `ChecklistItem` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `Column` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `ColumnEditor` | Schnittstelle | – | `view/columnEditor` |
| `@flowaudit/kanban-core` | `ColumnEditorState` | Schnittstelle | – | `view/columnEditor` |
| `@flowaudit/kanban-core` | `ColumnEditorView` | Schnittstelle | – | `view/columnEditor` |
| `@flowaudit/kanban-core` | `ColumnView` | Schnittstelle | – | `view/board` |
| `@flowaudit/kanban-core` | `CommandContext` | Schnittstelle | – | `commands` |
| `@flowaudit/kanban-core` | `CommandResult` | Schnittstelle | – | `commands` |
| `@flowaudit/kanban-core` | `DEFAULT_COLUMNS` | Konstante | audit_designer DEFAULT_COLUMNS: gelten, wenn ein Board keine eigenen Spalten hat. | `model` |
| `@flowaudit/kanban-core` | `DEFAULT_LIMITS` | Konstante | – | `validation` |
| `@flowaudit/kanban-core` | `DUE_SOON_DAYS` | Konstante | – | `filtering` |
| `@flowaudit/kanban-core` | `DUE_STATES` | Konstante | – | `filtering` |
| `@flowaudit/kanban-core` | `Decision` | Schnittstelle | Ergebnis einer Regelprüfung; `warnings` trägt nicht blockierende Codes (WIP-Warnmodus). | `errors` |
| `@flowaudit/kanban-core` | `DragState` | Schnittstelle | – | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `DueState` | Typ | – | `filtering` |
| `@flowaudit/kanban-core` | `EMPTY_FILTER` | Konstante | – | `view/filter` |
| `@flowaudit/kanban-core` | `ErrorCode` | Typ | Fehler- und Entscheidungsvertrag, gleich zu `auditcore_kanban.errors`. | `errors` |
| `@flowaudit/kanban-core` | `FREE_TRANSITIONS` | Konstante | – | `model` |
| `@flowaudit/kanban-core` | `FetchLike` | Typ | – | `restPort` |
| `@flowaudit/kanban-core` | `JsonObject` | Typ | – | `model` |
| `@flowaudit/kanban-core` | `JsonValue` | Typ | – | `model` |
| `@flowaudit/kanban-core` | `KanbanActions` | Schnittstelle | – | `view/actions` |
| `@flowaudit/kanban-core` | `KanbanError` | Klasse | – | `errors` |
| `@flowaudit/kanban-core` | `KanbanFilterState` | Schnittstelle | – | `view/filter` |
| `@flowaudit/kanban-core` | `KanbanStore` | Schnittstelle | Kleinster Zustandsspeicher der Kanban-Ansicht. | `view/store` |
| `@flowaudit/kanban-core` | `KeyInput` | Schnittstelle | Die Teile eines Tastaturereignisses, die die Belegung braucht (DOM- und React-Ereignis). | `view/keys` |
| `@flowaudit/kanban-core` | `Label` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `Limits` | Schnittstelle | – | `validation` |
| `@flowaudit/kanban-core` | `LocalChange` | Typ | – | `view/mutator` |
| `@flowaudit/kanban-core` | `MAX_CARD_IMAGE_BYTES` | Konstante | Größte Bilddatei für das Kartendesign (2 MB wie im Original). | `view/cardView` |
| `@flowaudit/kanban-core` | `MemoryBoardPort` | Klasse | – | `memoryPort` |
| `@flowaudit/kanban-core` | `MemoryPortOptions` | Schnittstelle | – | `memoryPort` |
| `@flowaudit/kanban-core` | `MemoryRecordPortOptions` | Schnittstelle | – | `recordPort` |
| `@flowaudit/kanban-core` | `MoveController` | Schnittstelle | – | `view/moveController` |
| `@flowaudit/kanban-core` | `MoveControllerOptions` | Schnittstelle | – | `view/moveController` |
| `@flowaudit/kanban-core` | `MoveMessageKey` | Typ | – | `view/moveController` |
| `@flowaudit/kanban-core` | `MovePreview` | Schnittstelle | – | `view/movePreview` |
| `@flowaudit/kanban-core` | `MoveState` | Schnittstelle | – | `view/moveController` |
| `@flowaudit/kanban-core` | `MoveTranslate` | Typ | – | `view/moveController` |
| `@flowaudit/kanban-core` | `Mutate` | Typ | – | `view/mutator` |
| `@flowaudit/kanban-core` | `MutationResult` | Schnittstelle | – | `port` |
| `@flowaudit/kanban-core` | `MutatorHooks` | Schnittstelle | – | `view/mutator` |
| `@flowaudit/kanban-core` | `PERMISSIONS` | Konstante | – | `permissions` |
| `@flowaudit/kanban-core` | `PRIORITIES` | Konstante | – | `model` |
| `@flowaudit/kanban-core` | `PRIORITY_TONES` | Konstante | – | `view/cardView` |
| `@flowaudit/kanban-core` | `Placement` | Schnittstelle | – | `commands` |
| `@flowaudit/kanban-core` | `PointerDrag` | Schnittstelle | – | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `PointerDragOptions` | Schnittstelle | – | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `PointerInput` | Schnittstelle | Die Teile eines Zeigerereignisses, die das Ziehen braucht (DOM- und React-Ereignis). | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `Priority` | Typ | – | `model` |
| `@flowaudit/kanban-core` | `PriorityTone` | Typ | Farbton eines Badges (gleiche Namen wie `BadgeTone` in `@flowaudit/ui-core`). | `view/cardView` |
| `@flowaudit/kanban-core` | `RANK_DIGITS` | Konstante | Rang-Schlüssel für die Reihenfolge in einer Spalte (fraktionale Indizes). Zwischen zwei Karten entsteht immer ein neuer Schlüssel, ohne die übrigen umzunummerieren. | `rank` |
| `@flowaudit/kanban-core` | `ROLE_ACTIONS` | Konstante | Deklarative Rollentabelle; configure, share, delete_board und pin nur für den Eigentümer. | `permissions` |
| `@flowaudit/kanban-core` | `RankError` | Klasse | – | `rank` |
| `@flowaudit/kanban-core` | `RecordGroup` | Schnittstelle | – | `records` |
| `@flowaudit/kanban-core` | `RecordPort` | Schnittstelle | Datenzugang der Datenbankansicht; `addRow` ist optional (sonst keine neue Karte). | `records` |
| `@flowaudit/kanban-core` | `RecordProperty` | Schnittstelle | – | `records` |
| `@flowaudit/kanban-core` | `RecordPropertyType` | Typ | – | `records` |
| `@flowaudit/kanban-core` | `RecordRow` | Schnittstelle | – | `records` |
| `@flowaudit/kanban-core` | `RecordTable` | Schnittstelle | – | `records` |
| `@flowaudit/kanban-core` | `RecordValue` | Typ | – | `records` |
| `@flowaudit/kanban-core` | `RelativeKey` | Typ | – | `view/cardView` |
| `@flowaudit/kanban-core` | `RemoteChange` | Typ | – | `view/mutator` |
| `@flowaudit/kanban-core` | `RestBoardPort` | Klasse | – | `restPort` |
| `@flowaudit/kanban-core` | `RestPortOptions` | Schnittstelle | – | `restPort` |
| `@flowaudit/kanban-core` | `Role` | Typ | – | `model` |
| `@flowaudit/kanban-core` | `SCHEMA_VERSION` | Konstante | Domänenmodell in der JSON-Form von `auditcore_kanban` (snake_case), damit REST-Antworten ohne Abbildung in Oberfläche und Logik fließen. | `model` |
| `@flowaudit/kanban-core` | `SHARE_RESULT_LIMIT` | Konstante | – | `view/shareSearch` |
| `@flowaudit/kanban-core` | `STATUS_BY_CODE` | Konstante | HTTP-Status je Code (REST-Vertrag docs/kanban/rest-api.md). | `errors` |
| `@flowaudit/kanban-core` | `Share` | Schnittstelle | – | `model` |
| `@flowaudit/kanban-core` | `SharePermission` | Typ | – | `model` |
| `@flowaudit/kanban-core` | `ShareSearch` | Schnittstelle | – | `view/shareSearch` |
| `@flowaudit/kanban-core` | `ShareSearchState` | Schnittstelle | – | `view/shareSearch` |
| `@flowaudit/kanban-core` | `TEMPLATES` | Konstante | – | `templates` |
| `@flowaudit/kanban-core` | `TransitionPolicy` | Schnittstelle | Bewegungsregeln. `mode: 'free'` erlaubt jeden Spaltenwechsel (audit_designer), `restricted` nur die Paare in `allowed`. | `model` |
| `@flowaudit/kanban-core` | `UiCapabilities` | Typ | – | `view/board` |
| `@flowaudit/kanban-core` | `UiCapability` | Typ | – | `view/board` |
| `@flowaudit/kanban-core` | `UserRef` | Schnittstelle | – | `port` |
| `@flowaudit/kanban-core` | `WipMode` | Typ | – | `model` |
| `@flowaudit/kanban-core` | `WipState` | Schnittstelle | – | `rules` |
| `@flowaudit/kanban-core` | `allowedActions` | Funktion | – | `permissions` |
| `@flowaudit/kanban-core` | `applyPreview` | Funktion | Spaltenansicht mit der bewegten Karte an der Vorschauposition. | `view/movePreview` |
| `@flowaudit/kanban-core` | `asOptionalString` | Funktion | – | `fields` |
| `@flowaudit/kanban-core` | `asString` | Funktion | – | `fields` |
| `@flowaudit/kanban-core` | `authorize` | Funktion | – | `permissions` |
| `@flowaudit/kanban-core` | `badgePrefix` | Funktion | – | `view/cardView` |
| `@flowaudit/kanban-core` | `badgeStyle` | Funktion | – | `view/cardView` |
| `@flowaudit/kanban-core` | `boardFromJson` | Funktion | Liest und prüft ein Board-Dokument strukturell. | `serialization` |
| `@flowaudit/kanban-core` | `boardShortcut` | Funktion | – | `view/keys` |
| `@flowaudit/kanban-core` | `boardStats` | Funktion | – | `stats` |
| `@flowaudit/kanban-core` | `boardToJson` | Funktion | Board-Dokument mit Karten in Board-Reihenfolge (stabile Ausgabe wie board_to_json). | `serialization` |
| `@flowaudit/kanban-core` | `bump` | Funktion | Nächste Fassung des Boards. | `commands` |
| `@flowaudit/kanban-core` | `capabilities` | Funktion | Aktionen, die der Nutzer ausführen darf (für die Oberfläche). | `permissions` |
| `@flowaudit/kanban-core` | `cardAge` | Funktion | Alter einer Karte in Stufen wie WorkspaceTaskCard (neu, Stunden, Tage, Wochen, Monate). | `view/cardView` |
| `@flowaudit/kanban-core` | `cardStyle` | Funktion | Inline-Stil einer Karte mit eigener Farbe bzw. Hintergrundbild (CSS-Variablen wie im Original). | `view/cardView` |
| `@flowaudit/kanban-core` | `cardsIn` | Funktion | Karten einer Spalte in Anzeigereihenfolge. | `model` |
| `@flowaudit/kanban-core` | `checkCapacity` | Funktion | Passt eine weitere Karte in die Spalte? Im Warnmodus ja, mit Warnung. | `rules` |
| `@flowaudit/kanban-core` | `checkMove` | Funktion | Vollständige Prüfung für das Verschieben einer Karte (Übergang, dann WIP). | `rules` |
| `@flowaudit/kanban-core` | `checkRevoke` | Funktion | – | `permissions` |
| `@flowaudit/kanban-core` | `checkShare` | Funktion | – | `permissions` |
| `@flowaudit/kanban-core` | `checkTransition` | Funktion | Spaltenwechsel ohne Kapazität; `source === target` ist ein Umsortieren. | `rules` |
| `@flowaudit/kanban-core` | `checklistProgress` | Funktion | – | `stats` |
| `@flowaudit/kanban-core` | `cloneJson` | Funktion | Tiefe Kopie reiner JSON-Daten. Anders als structuredClone funktioniert sie auch mit reaktiven Proxys (Vue), die Oberflächen an den Port übergeben. | `model` |
| `@flowaudit/kanban-core` | `columnForStatus` | Funktion | Spalte zu einem externen Status (ID oder Alias, cockpit `spalteVon`). | `model` |
| `@flowaudit/kanban-core` | `columnLoad` | Funktion | Kartenzahl einer Spalte, ohne die gerade bewegte Karte. | `rules` |
| `@flowaudit/kanban-core` | `columnViews` | Funktion | Spaltenansicht: sichtbare (gefilterte) Karten, Gesamtzahl und WIP-Zustand je Spalte. | `view/board` |
| `@flowaudit/kanban-core` | `columnsFromJson` | Funktion | Spaltenliste eines Anfragekörpers (Teilangaben erhalten Standardwerte). | `serialization` |
| `@flowaudit/kanban-core` | `compareCards` | Funktion | Stabile Reihenfolge in einer Spalte: Rang, dann Anlagezeit, dann ID. | `model` |
| `@flowaudit/kanban-core` | `compareRanks` | Funktion | Sortiervergleich nach Rang (Code-Einheiten-Reihenfolge wie Python-str). | `rank` |
| `@flowaudit/kanban-core` | `configureColumns` | Funktion | Ersetzt den Spaltensatz (nur Eigentümer); Karten entfernter Spalten wandern in die erste Spalte. | `boardCommands` |
| `@flowaudit/kanban-core` | `createBoard` | Funktion | – | `boardCommands` |
| `@flowaudit/kanban-core` | `createBoardController` | Funktion | – | `view/boardController` |
| `@flowaudit/kanban-core` | `createBoardListController` | Funktion | – | `view/boardList` |
| `@flowaudit/kanban-core` | `createCard` | Funktion | Neue Karte in `column_id` (Standard: erste Spalte), angehängt, sofern keine Position angegeben ist. | `commands` |
| `@flowaudit/kanban-core` | `createColumnEditor` | Funktion | – | `view/columnEditor` |
| `@flowaudit/kanban-core` | `createKanbanActions` | Funktion | – | `view/actions` |
| `@flowaudit/kanban-core` | `createKanbanStore` | Funktion | – | `view/store` |
| `@flowaudit/kanban-core` | `createMemoryRecordPort` | Funktion | – | `recordPort` |
| `@flowaudit/kanban-core` | `createMoveController` | Funktion | – | `view/moveController` |
| `@flowaudit/kanban-core` | `createMutator` | Funktion | – | `view/mutator` |
| `@flowaudit/kanban-core` | `createPointerDrag` | Funktion | – | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `createShareSearch` | Funktion | – | `view/shareSearch` |
| `@flowaudit/kanban-core` | `deadlineState` | Funktion | `none`, `overdue`, `due_soon` (≤ 3 Tage) oder `later` – `today` als ISO-Datum. | `filtering` |
| `@flowaudit/kanban-core` | `decisionToJson` | Funktion | JSON-Form der Paritätsfixtures. | `errors` |
| `@flowaudit/kanban-core` | `deleteCard` | Funktion | – | `commands` |
| `@flowaudit/kanban-core` | `deny` | Funktion | – | `errors` |
| `@flowaudit/kanban-core` | `doneColumn` | Funktion | Erste als erledigt markierte Spalte, sonst die letzte (audit_designer). | `model` |
| `@flowaudit/kanban-core` | `dropTarget` | Funktion | Spalte und Einfügeposition unter dem Zeiger innerhalb des Boards. | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `dropValue` | Funktion | Zellwert für das Ablegen in einer Spalte: `""` wird `null` (wie `updateCell(…, value \|\| null)`). | `records` |
| `@flowaudit/kanban-core` | `fileSize` | Funktion | Dateigröße als Zahl und Einheit (B, KB, MB, GB); die Zahl formatiert die Oberfläche je Sprache. | `view/cardView` |
| `@flowaudit/kanban-core` | `filterCards` | Funktion | Passende Karten in Board-Reihenfolge. | `filtering` |
| `@flowaudit/kanban-core` | `filterCriteria` | Funktion | – | `view/filter` |
| `@flowaudit/kanban-core` | `findCard` | Funktion | – | `model` |
| `@flowaudit/kanban-core` | `findColumn` | Funktion | – | `model` |
| `@flowaudit/kanban-core` | `findTemplate` | Funktion | – | `templates` |
| `@flowaudit/kanban-core` | `firstColumn` | Funktion | – | `model` |
| `@flowaudit/kanban-core` | `getCard` | Funktion | – | `commands` |
| `@flowaudit/kanban-core` | `groupByValue` | Funktion | Gruppiert Einträge je Option (useDbKanban). Leere oder unbekannte Werte landen in einem führenden Eimer `""`, der nur existiert, wenn er nicht leer ist. | `filtering` |
| `@flowaudit/kanban-core` | `groupOf` | Funktion | Aktueller Spaltenwert eines Datensatzes (`""` für leer oder unbekannt). | `records` |
| `@flowaudit/kanban-core` | `groupRecords` | Funktion | Spalten je Option; ohne gültige Gruppierung keine Spalten (wie das Original). | `records` |
| `@flowaudit/kanban-core` | `groupableProperties` | Funktion | Eigenschaften, nach denen gruppiert werden kann (nur `select` mit Optionen). | `records` |
| `@flowaudit/kanban-core` | `handleCardKey` | Funktion | Verarbeitet eine Taste auf einer Karte; true, wenn sie verbraucht wurde. | `view/keys` |
| `@flowaudit/kanban-core` | `indexAt` | Funktion | Einfügeposition in einer Kartenliste anhand der Zeigerhöhe (Kartenmitte). | `view/pointerDrag` |
| `@flowaudit/kanban-core` | `initials` | Funktion | Initialen aus einem Namen: erster und letzter Namensteil. | `view/cardView` |
| `@flowaudit/kanban-core` | `invalidField` | Funktion | – | `fields` |
| `@flowaudit/kanban-core` | `isFilterActive` | Funktion | – | `filtering` |
| `@flowaudit/kanban-core` | `isJson` | Funktion | – | `fields` |
| `@flowaudit/kanban-core` | `isPlainObject` | Funktion | – | `fields` |
| `@flowaudit/kanban-core` | `isPriority` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `isTyping` | Funktion | Tastenkürzel des Boards (N, F, /, Escape), nicht während der Texteingabe. | `view/keys` |
| `@flowaudit/kanban-core` | `isValidRank` | Funktion | Gültig: nicht leer, nur Base-62-Zeichen, letzte Stelle nicht '0'. | `rank` |
| `@flowaudit/kanban-core` | `listenBoardShortcuts` | Funktion | Meldet die Tastenkürzel N, F und / am Dokument an, wenn der Fokus im Board oder auf der Seite (body) liegt; liefert die Abmeldung. | `view/keys` |
| `@flowaudit/kanban-core` | `locate` | Funktion | Aktuelle Spalte und Position einer Karte in der Ansicht. | `view/movePreview` |
| `@flowaudit/kanban-core` | `matches` | Funktion | – | `filtering` |
| `@flowaudit/kanban-core` | `matchesQuery` | Funktion | Groß-/Kleinschreibung ignorierende Teilzeichenkettensuche in Titel, Beschreibung, Badge und Tags. | `filtering` |
| `@flowaudit/kanban-core` | `matchesRecord` | Funktion | Suche über Text-, Zahl- und Auswahlzellen, ohne Groß-/Kleinschreibung. | `records` |
| `@flowaudit/kanban-core` | `movableTargets` | Funktion | Spalten, in die die Karte derzeit verschoben werden darf (Tastatur, Menü). | `rules` |
| `@flowaudit/kanban-core` | `moveCard` | Funktion | Verschiebt vor/hinter eine Karte oder an `index` (Standard: Ende). | `commands` |
| `@flowaudit/kanban-core` | `neighbourColumn` | Funktion | Nächste Spalte in Richtung `step` (±1), in die `allowed` die Karte lässt. | `view/movePreview` |
| `@flowaudit/kanban-core` | `neighbourGroup` | Funktion | Nachbarspalte für Tastaturbedienung; `null`, wenn es keine gibt. | `records` |
| `@flowaudit/kanban-core` | `normalizeDue` | Funktion | Datum bleibt Datum, Datum-Zeit wird wie Pythons `datetime.isoformat()` normalisiert (`Z` → `+00:00`); leer löscht, Ungültiges wird abgelehnt. | `validation` |
| `@flowaudit/kanban-core` | `nudgeTarget` | Funktion | Ziel für Strg+Pfeil (cockpit): eine Position bzw. die nächste erlaubte Spalte bei gleicher Position. | `view/movePreview` |
| `@flowaudit/kanban-core` | `orderedCards` | Funktion | Alle Karten: Spaltenreihenfolge, dann Rang; Karten unbekannter Spalten zuletzt. | `model` |
| `@flowaudit/kanban-core` | `parseCardFields` | Funktion | – | `fields` |
| `@flowaudit/kanban-core` | `parseDueDay` | Funktion | Tagesnummer (UTC) eines ISO-Datums bzw. des Datumsteils; null bei fehlend/ungültig. | `filtering` |
| `@flowaudit/kanban-core` | `percent` | Funktion | Gerundeter Prozentwert, halbe Werte aufgerundet (= Math.round, wie stats.py). | `stats` |
| `@flowaudit/kanban-core` | `place` | Funktion | Rang für eine Karte an `slot`; verteilt die Spalte nur neu, wenn Ränge kollidieren. | `commands` |
| `@flowaudit/kanban-core` | `placementFor` | Funktion | Platzierung für den Port aus der sichtbaren Nachbarschaft: vor der Karte an `index`, sonst hinter der letzten sichtbaren Karte, sonst ans Ende. | `view/movePreview` |
| `@flowaudit/kanban-core` | `policyFromJson` | Funktion | `mode` free ignoriert `allowed`; restricted erlaubt nur die genannten Paare. | `serialization` |
| `@flowaudit/kanban-core` | `preview` | Funktion | – | `view/cardView` |
| `@flowaudit/kanban-core` | `previewColumns` | Funktion | Spalten mit der bewegten Karte an der Vorschauposition (für die Anzeige). | `view/moveController` |
| `@flowaudit/kanban-core` | `raiseIfDenied` | Funktion | – | `errors` |
| `@flowaudit/kanban-core` | `rankBetween` | Funktion | Neuer Schlüssel echt zwischen `before` und `after` (null = offenes Ende). | `rank` |
| `@flowaudit/kanban-core` | `relativeTime` | Funktion | Relative Zeit für die Boardliste (WorkspaceSidebar.relativeTime). | `view/cardView` |
| `@flowaudit/kanban-core` | `requireAction` | Funktion | – | `commands` |
| `@flowaudit/kanban-core` | `resolveSlot` | Funktion | Einfügeposition unter den Geschwistern (Standard: Ende; Index wird geklemmt). | `commands` |
| `@flowaudit/kanban-core` | `respreadColumn` | Funktion | Ersetzt die Ränge einer Spalte durch gleichmäßig verteilte Schlüssel (Reihenfolge bleibt). | `boardCommands` |
| `@flowaudit/kanban-core` | `revokeShare` | Funktion | Eigentümer widerruft jede Freigabe, Empfänger die eigene. | `boardCommands` |
| `@flowaudit/kanban-core` | `roleOf` | Funktion | Rolle: Eigentümer, eigene Freigabe, sonst geerbte Freigabe (z. B. Notizbuch). | `permissions` |
| `@flowaudit/kanban-core` | `selectBoardList` | Funktion | – | `view/boardList` |
| `@flowaudit/kanban-core` | `selectBoardView` | Funktion | Alles, was die Oberfläche aus Stand und Eingaben anzeigt (reine Funktion). | `view/boardController` |
| `@flowaudit/kanban-core` | `selectColumnEditor` | Funktion | – | `view/columnEditor` |
| `@flowaudit/kanban-core` | `shareBoard` | Funktion | Freigabe anlegen oder ändern (Upsert); nur der Eigentümer darf teilen. | `boardCommands` |
| `@flowaudit/kanban-core` | `shareFor` | Funktion | – | `model` |
| `@flowaudit/kanban-core` | `shareName` | Funktion | Anzeigename einer freigegebenen Person: Suchtreffer, sonst bekannte Nutzer, sonst Kennung. | `view/shareSearch` |
| `@flowaudit/kanban-core` | `siblingsOf` | Funktion | Sichtbare Karten einer Spalte ohne die bewegte Karte. | `view/movePreview` |
| `@flowaudit/kanban-core` | `slugify` | Funktion | Spalten-ID aus einer Beschriftung (BoardSettingsDialog.slugify ohne wirkungslose Ersetzungen). | `validation` |
| `@flowaudit/kanban-core` | `sortBoards` | Funktion | Angeheftete zuerst, dann zuletzt geändert (WorkspaceSidebar.sortedBoards). | `view/board` |
| `@flowaudit/kanban-core` | `spreadRanks` | Funktion | `count` gleichmäßig verteilte, aufsteigende Schlüssel (Neuaufbau einer Spalte). | `rank` |
| `@flowaudit/kanban-core` | `stepPreview` | Funktion | Nächste Vorschau bei einer Pfeiltaste im Aufnahmemodus; null, wenn kein Ziel erlaubt ist. | `view/movePreview` |
| `@flowaudit/kanban-core` | `textLength` | Funktion | Länge in Unicode-Codepunkten (wie Pythons len), nicht in UTF-16-Einheiten. | `validation` |
| `@flowaudit/kanban-core` | `textOn` | Funktion | Lesbare Schriftfarbe auf einer Kartenfarbe (Luminanzschwelle wie im Original). | `view/cardView` |
| `@flowaudit/kanban-core` | `toKanbanError` | Funktion | – | `view/board` |
| `@flowaudit/kanban-core` | `todayIso` | Funktion | Heutiges Datum als ISO-Zeichenkette in lokaler Zeit. | `filtering` |
| `@flowaudit/kanban-core` | `toggleDone` | Funktion | Erledigt-Spalte → oben in die erste Spalte; sonst → ans Ende der Erledigt-Spalte. | `commands` |
| `@flowaudit/kanban-core` | `uiCapabilities` | Funktion | Rechte des Nutzers für die Oberfläche; `locked` (readOnly) sperrt alle Schreibrechte. | `view/board` |
| `@flowaudit/kanban-core` | `uniqueColumnId` | Funktion | Eindeutige Spalten-ID: Slug, bei Kollision mit _2, _3 …; Rückfall `spalte`. | `validation` |
| `@flowaudit/kanban-core` | `updateBoard` | Funktion | Umbenennen (Eigentümer, Bearbeiten), Anheften/Archivieren (nur Eigentümer). | `boardCommands` |
| `@flowaudit/kanban-core` | `updateCard` | Funktion | Ändert Felder; eine andere `column_id` verschiebt ans Ende dieser Spalte. | `commands` |
| `@flowaudit/kanban-core` | `validateBadge` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `validateBoardTitle` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `validateColumns` | Funktion | Spaltensatz in der Prüfreihenfolge des Originals: Anzahl, eindeutige IDs, dann je Spalte. | `validation` |
| `@flowaudit/kanban-core` | `validateDescription` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `validatePriority` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `validateTags` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `validateTitle` | Funktion | – | `validation` |
| `@flowaudit/kanban-core` | `wipStates` | Funktion | – | `rules` |
| `@flowaudit/kanban-core` | `withCell` | Funktion | Neue Tabelle mit geändertem Zellwert (unveränderlich). | `records` |
| `@flowaudit/kanban-core` | `withRow` | Funktion | Neue Tabelle mit ersetztem oder angehängtem Datensatz. | `records` |
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
