import type { ElementDefinition } from '../elements/define'
import KanbanBoard from './KanbanBoard.vue'
import KanbanBoardList from './KanbanBoardList.vue'

/**
 * `<flowaudit-kanban-board>`: Eigenschaften `port` (BoardPort) und `boardId`
 * oder `board` (+ `userId`) für lokale Bearbeitung; Ereignisse `board-change`,
 * `error`, `fullscreen`, `navigate`, `attachment`, `card-open`.
 */
export const kanbanBoardElement: ElementDefinition = { tag: 'flowaudit-kanban-board', component: KanbanBoard }

/** `<flowaudit-kanban-boards>`: Boardliste mit Eigenschaft `port`; Ereignisse `board-select`, `created`. */
export const kanbanBoardListElement: ElementDefinition = { tag: 'flowaudit-kanban-boards', component: KanbanBoardList }
