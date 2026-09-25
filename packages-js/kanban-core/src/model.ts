/**
 * Domänenmodell in der JSON-Form von `auditcore_kanban` (snake_case), damit
 * REST-Antworten ohne Abbildung in Oberfläche und Logik fließen.
 */
export const SCHEMA_VERSION = 'auditcore_kanban.board/1'

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }
export type JsonObject = { [key: string]: JsonValue }

export type Priority = 'hoch' | 'mittel' | 'niedrig'
export const PRIORITIES: readonly Priority[] = ['hoch', 'mittel', 'niedrig']

export type SharePermission = 'read' | 'edit'
export type Role = 'owner' | SharePermission
export type WipMode = 'block' | 'warn'

export interface Column {
  id: string
  label: string
  color: string
  wip_limit: number | null
  done: boolean
  status_aliases: string[]
}

export interface ChecklistItem {
  text: string
  done: boolean
}

export interface CardLink {
  kind: string
  target: string
  title: string
}

export interface Attachment {
  id: string
  filename: string
  mime_type: string
  size: number
}

export interface Card {
  id: string
  column_id: string
  rank: string
  title: string
  description: string
  priority: Priority
  tags: string[]
  assignees: string[]
  due: string | null
  color: string | null
  image: string | null
  badge: string | null
  checklist: ChecklistItem[]
  links: CardLink[]
  attachments: Attachment[]
  created_at: string
  updated_at: string
  extra: JsonObject
}

export interface Label {
  id: string
  name: string
  color: string
}

export interface Share {
  user_id: string
  permission: SharePermission
  shared_by: string | null
  created_at: string | null
}

/**
 * Bewegungsregeln. `mode: 'free'` erlaubt jeden Spaltenwechsel (audit_designer),
 * `restricted` nur die Paare in `allowed`. Aus `locked_columns` verlässt keine
 * Karte ihre Spalte (cockpit „läuft“); in `fixed_order_columns` ist die
 * Reihenfolge fest.
 */
export interface TransitionPolicy {
  mode: 'free' | 'restricted'
  allowed: [string, string][]
  locked_columns: string[]
  fixed_order_columns: string[]
}

export interface Board {
  schema_version: typeof SCHEMA_VERSION
  id: string
  title: string
  icon: string
  owner_id: string
  version: number
  pinned: boolean
  archived: boolean
  created_at: string
  updated_at: string
  columns: Column[]
  cards: Card[]
  labels: Label[]
  shares: Share[]
  transitions: TransitionPolicy
  wip_mode: WipMode
  extra: JsonObject
}

export const FREE_TRANSITIONS: TransitionPolicy = Object.freeze({
  mode: 'free',
  allowed: [],
  locked_columns: [],
  fixed_order_columns: [],
})

/** audit_designer DEFAULT_COLUMNS: gelten, wenn ein Board keine eigenen Spalten hat. */
export const DEFAULT_COLUMNS: readonly Column[] = Object.freeze([
  { id: 'offen', label: 'Offen', color: '#7c3aed', wip_limit: null, done: false, status_aliases: [] },
  { id: 'in_arbeit', label: 'In Arbeit', color: '#f59e0b', wip_limit: null, done: false, status_aliases: [] },
  { id: 'erledigt', label: 'Erledigt', color: '#10b981', wip_limit: null, done: false, status_aliases: [] },
])

export function findColumn(board: Board, columnId: string): Column | undefined {
  return board.columns.find((column) => column.id === columnId)
}

export function findCard(board: Board, cardId: string): Card | undefined {
  return board.cards.find((card) => card.id === cardId)
}

/** Stabile Reihenfolge in einer Spalte: Rang, dann Anlagezeit, dann ID. */
export function compareCards(a: Card, b: Card): number {
  for (const [left, right] of [[a.rank, b.rank], [a.created_at, b.created_at], [a.id, b.id]] as const) {
    if (left !== right) return left < right ? -1 : 1
  }
  return 0
}

/** Karten einer Spalte in Anzeigereihenfolge. */
export function cardsIn(board: Board, columnId: string): Card[] {
  return board.cards.filter((card) => card.column_id === columnId).sort(compareCards)
}

/** Alle Karten: Spaltenreihenfolge, dann Rang; Karten unbekannter Spalten zuletzt. */
export function orderedCards(board: Board): Card[] {
  const known = new Set(board.columns.map((column) => column.id))
  const stray = board.cards.filter((card) => !known.has(card.column_id)).sort(compareCards)
  return [...board.columns.flatMap((column) => cardsIn(board, column.id)), ...stray]
}

export function firstColumn(board: Board): Column {
  const column = board.columns[0]
  if (!column) throw new Error('Board ohne Spalten')
  return column
}

/** Erste als erledigt markierte Spalte, sonst die letzte (audit_designer). */
export function doneColumn(board: Board): Column {
  const flagged = board.columns.find((column) => column.done)
  const last = board.columns[board.columns.length - 1]
  if (flagged) return flagged
  if (!last) throw new Error('Board ohne Spalten')
  return last
}

/** Spalte zu einem externen Status (ID oder Alias, cockpit `spalteVon`). */
export function columnForStatus(board: Board, status: string): Column | undefined {
  return board.columns.find((column) => column.id === status || column.status_aliases.includes(status))
}

export function shareFor(board: Board, userId: string): Share | undefined {
  return board.shares.find((share) => share.user_id === userId)
}

/**
 * Tiefe Kopie reiner JSON-Daten. Anders als structuredClone funktioniert sie
 * auch mit reaktiven Proxys (Vue), die Oberflächen an den Port übergeben.
 */
export function cloneJson<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}
