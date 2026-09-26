/** Reine Ableitungen der Boardansicht (Spalten, Rechte, Fehler, Boardliste). */
import { KanbanError } from '../errors'
import { filterCards, type CardFilter } from '../filtering'
import { cardsIn, type Board, type Card, type Column } from '../model'
import { capabilities } from '../permissions'
import type { BoardSummary } from '../port'
import { wipStates, type WipState } from '../rules'

export interface ColumnView {
  column: Column
  cards: Card[]
  total: number
  wip: WipState | undefined
}

export type UiCapability = 'read' | 'create' | 'edit' | 'move' | 'delete' | 'rename' | 'configure' | 'share'
export type UiCapabilities = Record<UiCapability, boolean>

export function toKanbanError(error: unknown): KanbanError {
  if (error instanceof KanbanError) return error
  const message = error instanceof Error ? error.message : String(error)
  return new KanbanError('INVALID_REQUEST', message)
}

/** Rechte des Nutzers für die Oberfläche; `locked` (readOnly) sperrt alle Schreibrechte. */
export function uiCapabilities(board: Board | null, userId: string, locked: boolean): UiCapabilities {
  const allowed = board ? capabilities(board, userId) : null
  const grant = (action: keyof NonNullable<typeof allowed>): boolean => !locked && Boolean(allowed?.[action])
  return {
    read: Boolean(allowed?.read), create: grant('create_card'), edit: grant('edit_card'), move: grant('move_card'),
    delete: grant('delete_card'), rename: grant('rename'), configure: grant('configure'), share: grant('share'),
  }
}

/** Spaltenansicht: sichtbare (gefilterte) Karten, Gesamtzahl und WIP-Zustand je Spalte. */
export function columnViews(board: Board | null, criteria: CardFilter, today: string): ColumnView[] {
  if (!board) return []
  const visible = new Set(filterCards(board, criteria, today).map((card) => card.id))
  const wip = wipStates(board)
  return board.columns.map((column) => {
    const all = cardsIn(board, column.id)
    return { column, cards: all.filter((card) => visible.has(card.id)), total: all.length, wip: wip.find((state) => state.column_id === column.id) }
  })
}

/** Angeheftete zuerst, dann zuletzt geändert (WorkspaceSidebar.sortedBoards). */
export function sortBoards(boards: readonly BoardSummary[]): BoardSummary[] {
  return [...boards].sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.updated_at.localeCompare(a.updated_at))
}
