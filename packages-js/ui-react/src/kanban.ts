import type { Board, BoardPort, UserRef } from '@flowaudit/kanban-core'
import type { Locale } from '@flowaudit/ui'
import { createElementComponent } from './createElementComponent'

export interface FlowauditKanbanBoardProps {
  /** Speicher-/Rechte-Port (z. B. RestBoardPort); alternativ `board` + `userId` für lokale Bearbeitung. */
  port?: BoardPort | null
  boardId?: string
  board?: Board | null
  userId?: string
  users?: readonly UserRef[]
  readOnly?: boolean
  sharedByName?: string
  showFullscreen?: boolean
  today?: string
  locale?: Locale
}

/** `<flowaudit-kanban-board>` als React-Komponente. */
export const FlowauditKanbanBoard = createElementComponent<
  FlowauditKanbanBoardProps,
  { onBoardChange: string; onError: string; onFullscreen: string; onNavigate: string; onAttachment: string; onCardOpen: string }
>('flowaudit-kanban-board', {
  properties: ['port', 'boardId', 'board', 'userId', 'users', 'readOnly', 'sharedByName', 'showFullscreen', 'today', 'locale'],
  events: { onBoardChange: 'board-change', onError: 'error', onFullscreen: 'fullscreen', onNavigate: 'navigate', onAttachment: 'attachment', onCardOpen: 'card-open' },
})

export interface FlowauditKanbanBoardsProps {
  port?: BoardPort | null
  activeId?: string
  locale?: Locale
}

/** `<flowaudit-kanban-boards>` (Boardliste) als React-Komponente. */
export const FlowauditKanbanBoards = createElementComponent<FlowauditKanbanBoardsProps, { onBoardSelect: string; onCreated: string }>('flowaudit-kanban-boards', {
  properties: ['port', 'activeId', 'locale'],
  events: { onBoardSelect: 'board-select', onCreated: 'created' },
})
