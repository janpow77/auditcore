/** Suche, Filter, Fälligkeitszustand und Gruppierung nach einer Eigenschaft. */
import { orderedCards, type Board, type Card } from './model'

export const DUE_SOON_DAYS = 3
export type DueState = 'none' | 'overdue' | 'due_soon' | 'later'
export const DUE_STATES: readonly DueState[] = ['none', 'overdue', 'due_soon', 'later']

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/

/** Tagesnummer (UTC) eines ISO-Datums bzw. des Datumsteils; null bei fehlend/ungültig. */
export function parseDueDay(due: string | null | undefined): number | null {
  if (!due) return null
  const match = ISO_DATE.exec(due.slice(0, 10))
  if (!match) return null
  const [year, month, day] = [Number(match[1]), Number(match[2]), Number(match[3])]
  const time = Date.UTC(year, month - 1, day)
  const check = new Date(time)
  if (check.getUTCFullYear() !== year || check.getUTCMonth() !== month - 1 || check.getUTCDate() !== day) return null
  return Math.round(time / 86_400_000)
}

/** `none`, `overdue`, `due_soon` (≤ 3 Tage) oder `later` – `today` als ISO-Datum. */
export function deadlineState(due: string | null | undefined, today: string): DueState {
  const dueDay = parseDueDay(due)
  const todayDay = parseDueDay(today)
  if (dueDay === null || todayDay === null) return 'none'
  const days = dueDay - todayDay
  if (days < 0) return 'overdue'
  return days <= DUE_SOON_DAYS ? 'due_soon' : 'later'
}

export interface CardFilter {
  query?: string
  priorities?: readonly string[]
  tags?: readonly string[]
  assignees?: readonly string[]
  columns?: readonly string[]
  due_states?: readonly DueState[]
}

/** Groß-/Kleinschreibung ignorierende Teilzeichenkettensuche in Titel, Beschreibung, Badge und Tags. */
export function matchesQuery(card: Card, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return [card.title, card.description, card.badge ?? '', ...card.tags].some((text) => text.toLowerCase().includes(needle))
}

function intersects(values: readonly string[], wanted: readonly string[] | undefined): boolean {
  return !wanted || wanted.length === 0 || values.some((value) => wanted.includes(value))
}

function within(value: string, wanted: readonly string[] | undefined): boolean {
  return !wanted || wanted.length === 0 || wanted.includes(value)
}

export function matches(card: Card, criteria: CardFilter, today: string): boolean {
  return (
    matchesQuery(card, criteria.query ?? '') &&
    within(card.priority, criteria.priorities) &&
    intersects(card.tags, criteria.tags) &&
    intersects(card.assignees, criteria.assignees) &&
    within(card.column_id, criteria.columns) &&
    within(deadlineState(card.due, today), criteria.due_states)
  )
}

/** Passende Karten in Board-Reihenfolge. */
export function filterCards(board: Board, criteria: CardFilter, today: string): Card[] {
  return orderedCards(board).filter((card) => matches(card, criteria, today))
}

export function isFilterActive(criteria: CardFilter): boolean {
  return Boolean(criteria.query?.trim()) || [criteria.priorities, criteria.tags, criteria.assignees, criteria.columns, criteria.due_states].some((list) => (list?.length ?? 0) > 0)
}

/**
 * Gruppiert Einträge je Option (useDbKanban). Leere oder unbekannte Werte
 * landen in einem führenden Eimer `""`, der nur existiert, wenn er nicht leer ist.
 */
export function groupByValue<T>(items: readonly T[], key: (item: T) => string | null | undefined, options: readonly string[]): [string, T[]][] {
  const buckets: [string, T[]][] = options.map((option) => [option, items.filter((item) => key(item) === option)])
  const unassigned = items.filter((item) => !options.includes(key(item) ?? ''))
  if (unassigned.length > 0) buckets.unshift(['', unassigned])
  return buckets
}

/** Heutiges Datum als ISO-Zeichenkette in lokaler Zeit. */
export function todayIso(now: Date = new Date()): string {
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}
