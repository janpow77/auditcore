/** Bewegungsregeln: Spaltenübergänge, gesperrte Spalten, feste Reihenfolge, WIP-Limits. */
import { ALLOWED, deny, type Decision } from './errors'
import { findColumn, type Board, type Card } from './model'

export interface WipState {
  column_id: string
  count: number
  limit: number | null
  full: boolean
  over: boolean
}

/** Kartenzahl einer Spalte, ohne die gerade bewegte Karte. */
export function columnLoad(board: Board, columnId: string, excludeCardId: string | null = null): number {
  return board.cards.filter((card) => card.column_id === columnId && card.id !== excludeCardId).length
}

export function wipStates(board: Board): WipState[] {
  return board.columns.map((column) => {
    const count = columnLoad(board, column.id)
    const limit = column.wip_limit
    return { column_id: column.id, count, limit, full: limit !== null && count >= limit, over: limit !== null && count > limit }
  })
}

/** Passt eine weitere Karte in die Spalte? Im Warnmodus ja, mit Warnung. */
export function checkCapacity(board: Board, columnId: string, excludeCardId: string | null = null): Decision {
  const column = findColumn(board, columnId)
  if (!column) return deny('UNKNOWN_COLUMN', `Unbekannte Spalte '${columnId}'`)
  if (column.wip_limit === null) return ALLOWED
  if (columnLoad(board, columnId, excludeCardId) < column.wip_limit) return ALLOWED
  if (board.wip_mode === 'warn') return { allowed: true, code: 'OK', message: '', warnings: ['WIP_LIMIT_REACHED'] }
  return deny('WIP_LIMIT_REACHED', `WIP-Limit der Spalte „${column.label}“ (${column.wip_limit}) ist erreicht`)
}

function pairAllowed(board: Board, source: string, target: string): boolean {
  if (board.transitions.mode === 'free') return true
  return board.transitions.allowed.some(([from, to]) => from === source && to === target)
}

/** Spaltenwechsel ohne Kapazität; `source === target` ist ein Umsortieren. */
export function checkTransition(board: Board, source: string, target: string): Decision {
  const policy = board.transitions
  if (!findColumn(board, target)) return deny('UNKNOWN_COLUMN', `Unbekannte Spalte '${target}'`)
  if (source === target) {
    if (policy.fixed_order_columns.includes(source)) return deny('ORDER_FIXED', 'Die Reihenfolge dieser Spalte ist fest')
    return ALLOWED
  }
  if (policy.locked_columns.includes(source)) {
    return deny('COLUMN_LOCKED', 'Karten dieser Spalte können nicht verschoben werden')
  }
  if (!pairAllowed(board, source, target)) {
    return deny('TRANSITION_NOT_ALLOWED', `Übergang von '${source}' nach '${target}' ist nicht erlaubt`)
  }
  return ALLOWED
}

/** Vollständige Prüfung für das Verschieben einer Karte (Übergang, dann WIP). */
export function checkMove(board: Board, card: Card, target: string): Decision {
  const decision = checkTransition(board, card.column_id, target)
  if (!decision.allowed || card.column_id === target) return decision
  return checkCapacity(board, target, card.id)
}

/** Spalten, in die die Karte derzeit verschoben werden darf (Tastatur, Menü). */
export function movableTargets(board: Board, card: Card): string[] {
  return board.columns
    .filter((column) => column.id !== card.column_id && checkMove(board, card, column.id).allowed)
    .map((column) => column.id)
}
