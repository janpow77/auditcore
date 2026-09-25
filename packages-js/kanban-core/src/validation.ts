/** Eingabeprüfung mit Grenzen und Meldungen des audit_designer-Backends (workspace.py). */
import { KanbanError } from './errors'
import { PRIORITIES, type Column, type Priority } from './model'

export const COLUMN_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,49}$/

export interface Limits {
  title_max: number
  description_max: number
  tags_max: number
  tag_length_max: number
  columns_min: number
  columns_max: number
  column_label_max: number
  board_title_max: number
  badge_max: number
  checklist_max: number
}

export const DEFAULT_LIMITS: Readonly<Limits> = Object.freeze({
  title_max: 300,
  description_max: 10000,
  tags_max: 20,
  tag_length_max: 80,
  columns_min: 1,
  columns_max: 10,
  column_label_max: 80,
  board_title_max: 500,
  badge_max: 20,
  checklist_max: 200,
})

/** Länge in Unicode-Codepunkten (wie Pythons len), nicht in UTF-16-Einheiten. */
export function textLength(value: string): number {
  return [...value].length
}

function fail(message: string): KanbanError {
  return new KanbanError('VALIDATION_ERROR', message)
}

export function validateTitle(title: string, limits: Limits = DEFAULT_LIMITS): string {
  const stripped = title.trim()
  if (!stripped) throw fail('Titel darf nicht leer sein')
  if (textLength(stripped) > limits.title_max) throw fail('Titel ist zu lang')
  return stripped
}

export function validateDescription(description: string, limits: Limits = DEFAULT_LIMITS): string {
  if (textLength(description) > limits.description_max) throw fail('Beschreibung ist zu lang')
  return description
}

export function validateTags(tags: readonly string[], limits: Limits = DEFAULT_LIMITS): string[] {
  if (tags.length > limits.tags_max) throw fail('Zu viele Tags')
  if (tags.some((tag) => textLength(tag) > limits.tag_length_max)) throw fail('Tag ist zu lang')
  return [...tags]
}

export function isPriority(value: string): value is Priority {
  return (PRIORITIES as readonly string[]).includes(value)
}

export function validatePriority(priority: string): Priority {
  if (!isPriority(priority)) throw fail(`Ungültige Priorität '${priority}'. Erlaubt: ['hoch', 'mittel', 'niedrig']`)
  return priority
}

export function validateBadge(badge: string | null | undefined, limits: Limits = DEFAULT_LIMITS): string | null {
  if (!badge) return null
  if (textLength(badge) > limits.badge_max) throw fail('Badge ist zu lang')
  return badge
}

export function validateBoardTitle(title: string, limits: Limits = DEFAULT_LIMITS): string {
  const stripped = title.trim()
  if (!stripped) throw fail('Titel darf nicht leer sein')
  if (textLength(stripped) > limits.board_title_max) throw fail('Titel ist zu lang')
  return stripped
}

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/
const DATE_TIME = /^(\d{4}-\d{2}-\d{2})[T ](\d{2})(?::(\d{2})(?::(\d{2})(?:[.,](\d{1,6}))?)?)?(Z|[+-]\d{2}(?::?\d{2})?)?$/

function validDate(value: string): boolean {
  const [year, month, day] = value.split('-').map(Number) as [number, number, number]
  const date = new Date(Date.UTC(year, month - 1, day))
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
}

function formatOffset(offset: string | undefined): string {
  if (offset === undefined) return ''
  if (offset === 'Z') return '+00:00'
  const digits = offset.slice(1).replace(':', '')
  const minutes = digits.slice(2) || '00'
  if (Number(digits.slice(0, 2)) > 23 || Number(minutes) > 59) throw fail('Ungültiges Deadline-Format')
  return `${offset.charAt(0)}${digits.slice(0, 2)}:${minutes}`
}

function formatTime(hour: string, minute = '00', second = '00', fraction = ''): string {
  if (Number(hour) > 23 || Number(minute) > 59 || Number(second) > 59) throw fail('Ungültiges Deadline-Format')
  const micro = fraction.padEnd(6, '0')
  return `${hour}:${minute}:${second}${Number(micro) > 0 ? `.${micro}` : ''}`
}

/**
 * Datum bleibt Datum, Datum-Zeit wird wie Pythons `datetime.isoformat()`
 * normalisiert (`Z` → `+00:00`); leer löscht, Ungültiges wird abgelehnt.
 */
export function normalizeDue(value: string | null | undefined): string | null {
  if (value === null || value === undefined || value === '') return null
  if (DATE_ONLY.test(value)) {
    if (!validDate(value)) throw fail('Ungültiges Deadline-Format')
    return value
  }
  const match = DATE_TIME.exec(value)
  const date = match?.[1]
  if (!match || !date || !validDate(date)) throw fail('Ungültiges Deadline-Format')
  return `${date}T${formatTime(match[2] ?? '00', match[3], match[4], match[5])}${formatOffset(match[6])}`
}

function checkColumn(column: Column, limits: Limits): Column {
  if (!COLUMN_ID_PATTERN.test(column.id)) throw fail('Spalten-ID darf nur Kleinbuchstaben, Zahlen, _ und - enthalten')
  if (!column.label || textLength(column.label) > limits.column_label_max) throw fail('Spaltenlabel ist ungültig')
  if (column.wip_limit !== null && column.wip_limit < 1) throw fail('WIP-Limit muss mindestens 1 sein')
  return column
}

/** Spaltensatz in der Prüfreihenfolge des Originals: Anzahl, eindeutige IDs, dann je Spalte. */
export function validateColumns(columns: readonly Column[], limits: Limits = DEFAULT_LIMITS): Column[] {
  if (columns.length < limits.columns_min) throw fail('Mindestens eine Spalte erforderlich')
  if (columns.length > limits.columns_max) throw fail(`Maximal ${limits.columns_max} Spalten erlaubt`)
  const stripped = columns.map((column) => ({ ...column, id: column.id.trim(), label: column.label.trim() }))
  if (new Set(stripped.map((column) => column.id)).size !== stripped.length) throw fail('Spalten-IDs müssen eindeutig sein')
  return stripped.map((column) => checkColumn(column, limits))
}

/** Spalten-ID aus einer Beschriftung (BoardSettingsDialog.slugify ohne wirkungslose Ersetzungen). */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40)
}

/** Eindeutige Spalten-ID: Slug, bei Kollision mit _2, _3 …; Rückfall `spalte`. */
export function uniqueColumnId(label: string, existing: readonly string[]): string {
  const slug = slugify(label) || 'spalte'
  if (!existing.includes(slug)) return slug
  for (let suffix = 2; ; suffix += 1) {
    const candidate = `${slug}_${suffix}`
    if (!existing.includes(candidate)) return candidate
  }
}
