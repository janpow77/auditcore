/** Zählung je Spalte und Fortschritt (Erledigt-Spalte, sonst letzte Spalte). */
import { doneColumn, findColumn, type Board } from './model'

/** Gerundeter Prozentwert, halbe Werte aufgerundet (= Math.round, wie stats.py). */
export function percent(part: number, total: number): number {
  if (total <= 0) return 0
  return Math.floor((200 * part + total) / (2 * total))
}

export interface BoardStats {
  total: number
  by_column: Record<string, number>
  done_column: string
  done: number
  progress: number
}

export function boardStats(board: Board): BoardStats {
  const byColumn: Record<string, number> = {}
  for (const column of board.columns) byColumn[column.id] = board.cards.filter((card) => card.column_id === column.id).length
  const known = board.cards.filter((card) => findColumn(board, card.column_id)).length
  const doneId = doneColumn(board).id
  const done = board.cards.filter((card) => card.column_id === doneId).length
  return { total: known, by_column: byColumn, done_column: doneId, done, progress: percent(done, known) }
}

export function checklistProgress(done: number, total: number): { done: number; total: number; percent: number } {
  return { done, total, percent: percent(done, total) }
}
