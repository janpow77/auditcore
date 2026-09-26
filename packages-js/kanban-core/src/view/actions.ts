/** Board-Aktionen: je eine lokale Kernoperation (optimistisch) und der passende Port-Aufruf. */
import { configureColumns, updateBoard, revokeShare, shareBoard } from '../boardCommands'
import { deleteCard, moveCard, toggleDone, updateCard, type Placement } from '../commands'
import { doneColumn, firstColumn, type Board, type Card, type Column, type SharePermission } from '../model'
import type { MutationResult } from '../port'
import type { Mutate } from './mutator'

type Result = Promise<MutationResult | null>

export interface KanbanActions {
  addCard: (columnId: string, fields: Readonly<Record<string, unknown>>) => Result
  editCard: (cardId: string, fields: Readonly<Record<string, unknown>>) => Result
  move: (cardId: string, columnId: string, placement: Placement) => Result
  remove: (cardId: string) => Result
  /** Erledigt-Spalte ↔ erste Spalte (Toggle-Done der Karte). */
  toggle: (card: Card) => Result
  configure: (columns: readonly Column[]) => Result
  rename: (title: string) => Result
  share: (userId: string, permission: SharePermission) => Result
  revoke: (userId: string) => Result
}

function toggleAction(mutate: Mutate, board: () => Board | null) {
  return (card: Card): Result => {
    const current = board()
    if (!current) return Promise.resolve(null)
    const reopen = card.column_id === doneColumn(current).id
    const target = reopen ? firstColumn(current).id : doneColumn(current).id
    const placement: Placement = reopen ? { index: 0 } : {}
    return mutate((next, ctx) => toggleDone(next, ctx, card.id), (port, boardId) => port.moveCard(boardId, card.id, target, placement))
  }
}

export function createKanbanActions(mutate: Mutate, board: () => Board | null): KanbanActions {
  return {
    addCard: (columnId, fields) => mutate(null, (port, boardId) => port.createCard(boardId, { ...fields, column_id: columnId })),
    editCard: (cardId, fields) => mutate((next, ctx) => updateCard(next, ctx, cardId, fields), (port, boardId) => port.updateCard(boardId, cardId, fields)),
    move: (cardId, columnId, placement) => mutate((next, ctx) => moveCard(next, ctx, cardId, columnId, placement), (port, boardId) => port.moveCard(boardId, cardId, columnId, placement)),
    remove: (cardId) => mutate((next, ctx) => deleteCard(next, ctx, cardId), (port, boardId) => port.deleteCard(boardId, cardId)),
    toggle: toggleAction(mutate, board),
    configure: (columns) => mutate((next, ctx) => configureColumns(next, ctx, columns), (port, boardId) => port.configureColumns(boardId, columns)),
    rename: (title) => mutate((next, ctx) => updateBoard(next, ctx, { title }), (port, boardId) => port.updateBoard(boardId, { title })),
    share: (userId, permission) => mutate((next, ctx) => shareBoard(next, ctx, userId, permission), (port, boardId) => port.share(boardId, userId, permission)),
    revoke: (userId) => mutate((next, ctx) => revokeShare(next, ctx, userId), (port, boardId) => port.revokeShare(boardId, userId)),
  }
}
