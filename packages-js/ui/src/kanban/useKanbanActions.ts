/** Board-Aktionen: je eine lokale Kernoperation (optimistisch) und der passende Port-Aufruf. */
import {
  configureColumns,
  deleteCard,
  doneColumn,
  firstColumn,
  moveCard,
  revokeShare,
  shareBoard,
  toggleDone,
  updateBoard,
  updateCard,
  type Card,
  type Column,
  type MutationResult,
  type Placement,
  type SharePermission,
} from '@flowaudit/kanban-core'
import type { KanbanBoardState } from './useKanbanBoard'

export function useKanbanActions(state: KanbanBoardState) {
  const { mutate } = state

  function addCard(columnId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult | null> {
    const payload = { ...fields, column_id: columnId }
    return mutate(null, (port, boardId) => port.createCard(boardId, payload))
  }

  function editCard(cardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult | null> {
    return mutate((board, ctx) => updateCard(board, ctx, cardId, fields), (port, boardId) => port.updateCard(boardId, cardId, fields))
  }

  function move(cardId: string, columnId: string, placement: Placement): Promise<MutationResult | null> {
    return mutate((board, ctx) => moveCard(board, ctx, cardId, columnId, placement), (port, boardId) => port.moveCard(boardId, cardId, columnId, placement))
  }

  function remove(cardId: string): Promise<MutationResult | null> {
    return mutate((board, ctx) => deleteCard(board, ctx, cardId), (port, boardId) => port.deleteCard(boardId, cardId))
  }

  /** Erledigt-Spalte ↔ erste Spalte (Toggle-Done der Karte). */
  function toggle(card: Card): Promise<MutationResult | null> {
    const current = state.board.value
    if (!current) return Promise.resolve(null)
    const reopen = card.column_id === doneColumn(current).id
    const target = reopen ? firstColumn(current).id : doneColumn(current).id
    const placement: Placement = reopen ? { index: 0 } : {}
    return mutate((board, ctx) => toggleDone(board, ctx, card.id), (port, boardId) => port.moveCard(boardId, card.id, target, placement))
  }

  function configure(columns: readonly Column[]): Promise<MutationResult | null> {
    return mutate((board, ctx) => configureColumns(board, ctx, columns), (port, boardId) => port.configureColumns(boardId, columns))
  }

  function rename(title: string): Promise<MutationResult | null> {
    return mutate((board, ctx) => updateBoard(board, ctx, { title }), (port, boardId) => port.updateBoard(boardId, { title }))
  }

  function share(userId: string, permission: SharePermission): Promise<MutationResult | null> {
    return mutate((board, ctx) => shareBoard(board, ctx, userId, permission), (port, boardId) => port.share(boardId, userId, permission))
  }

  function revoke(userId: string): Promise<MutationResult | null> {
    return mutate((board, ctx) => revokeShare(board, ctx, userId), (port, boardId) => port.revokeShare(boardId, userId))
  }

  return { addCard, editCard, move, remove, toggle, configure, rename, share, revoke }
}

export type KanbanActions = ReturnType<typeof useKanbanActions>
