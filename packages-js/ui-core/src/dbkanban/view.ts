/** Anzeige der Datenbankansicht: Spalten, Karten und Feldtexte (reine Funktionen). */
import { groupableProperties, groupRecords, matchesRecord, type RecordValue, type RecordProperty, type RecordRow, type RecordTable } from '@flowaudit/kanban-core'
import type { DbKanbanData } from './controller'
import type { DbKanbanMessageKey, DbKanbanTranslate } from './messages'

export interface DbFieldView {
  id: string
  label: string
  text: string
}

export interface DbCardView {
  id: string
  title: string
  fields: DbFieldView[]
  /** Spalte der Karte (`""` = ohne Wert). */
  column: string
}

export interface DbColumnView {
  value: string
  label: string
  countText: string
  cards: DbCardView[]
}

export interface DbGroupOption {
  value: string
  label: string
}

export interface DbKanbanView {
  groupOptions: DbGroupOption[]
  columns: DbColumnView[]
  /** Hinweis statt Spalten (keine Gruppierung möglich/gewählt), sonst `null`. */
  notice: string | null
  noMatches: boolean
  busyText: string
}

/** Anzeigetext eines Zellwerts; leere Werte ergeben `""`. */
export function cellText(value: RecordValue | undefined, t: DbKanbanTranslate, lang: string): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? t('yes') : t('no')
  if (typeof value === 'number') return new Intl.NumberFormat(lang).format(value)
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

/** Titel-Eigenschaft: die erste Texteigenschaft (wie die erste Spalte der Tabellenansicht). */
export function titleProperty(table: RecordTable): RecordProperty | undefined {
  return table.properties.find((property) => property.type === 'text')
}

export function columnLabel(value: string, t: DbKanbanTranslate): string {
  return value === '' ? t('withoutValue') : value
}

function cardView(table: RecordTable, row: RecordRow, groupBy: string, column: string, context: { t: DbKanbanTranslate; lang: string }): DbCardView {
  const title = titleProperty(table)
  const fields = table.properties
    .filter((property) => property.id !== groupBy && property.id !== title?.id)
    .map((property) => ({ id: property.id, label: property.name, text: cellText(row.cells[property.id], context.t, context.lang) }))
    .filter((field) => field.text !== '')
  const titleText = title ? cellText(row.cells[title.id], context.t, context.lang) : ''
  return { id: row.id, title: titleText || context.t('untitled'), fields, column }
}

function columns(state: DbKanbanData, t: DbKanbanTranslate, lang: string): DbColumnView[] {
  const table = state.table
  if (!table) return []
  const rows = table.rows.filter((row) => matchesRecord(row, state.query))
  return groupRecords(table, state.groupBy, rows).map((group) => ({
    value: group.value,
    label: columnLabel(group.value, t),
    countText: group.rows.length === 1 ? t('columnCountOne') : t('columnCount', { count: group.rows.length }),
    cards: group.rows.map((row) => cardView(table, row, state.groupBy, group.value, { t, lang })),
  }))
}

function notice(state: DbKanbanData, groupOptions: readonly DbGroupOption[], t: DbKanbanTranslate): string | null {
  if (!state.table) return null
  if (groupOptions.length === 0) return t('noGroupable')
  return groupOptions.some((option) => option.value === state.groupBy) ? null : t('noGroupBy')
}

export function dbKanbanView(state: DbKanbanData, t: DbKanbanTranslate, lang = 'de'): DbKanbanView {
  const groupOptions = state.table ? groupableProperties(state.table).map((property) => ({ value: property.id, label: property.name })) : []
  const shown = columns(state, t, lang)
  return {
    groupOptions,
    columns: shown,
    notice: notice(state, groupOptions, t),
    noMatches: shown.length > 0 && state.query.trim() !== '' && shown.every((column) => column.cards.length === 0),
    busyText: state.busy ? t(`busy_${state.busy}` as DbKanbanMessageKey) : '',
  }
}
