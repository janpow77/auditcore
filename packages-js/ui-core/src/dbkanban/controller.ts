// Zustandsautomat der Datenbankansicht als Kanban (<flowaudit-db-kanban>, Vue und React):
// Tabelle über einen RecordPort laden, nach einer Auswahl-Eigenschaft gruppieren,
// Karten per Ziehen oder Tastatur verschieben (setzt den Zellwert), Einträge anlegen.

import { RestError } from '@auditcore/common'
import {
  dropValue,
  groupableProperties,
  groupOf,
  groupRecords,
  matchesRecord,
  neighbourGroup,
  withCell,
  withRow,
  type RecordPort,
  type RecordRow,
  type RecordTable,
} from '@auditcore/kanban-core'
import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { DbKanbanTranslate } from './messages'
import { cellText, columnLabel, titleProperty } from './view'

export interface DbKanbanError {
  code: string
  message: string
  status: number
}

export type DbKanbanBusy = 'load' | 'move' | 'add'

export interface DbKanbanData extends RequestState<DbKanbanError> {
  table: RecordTable | null
  /** Eigenschaft, nach der gruppiert wird (`select`). */
  groupBy: string
  query: string
  /** Gezogene Karte (Maus) bzw. aufgenommene Karte (Tastatur). */
  dragging: string | null
  /** Spalte unter dem Mauszeiger beim Ziehen. */
  dropTarget: string | null
}

/** Verschiebung einer Karte: der gesetzte Zellwert (`null` = ohne Wert). */
export interface RecordMove {
  rowId: string
  propertyId: string
  value: string | null
}

export interface DbKanbanHooks {
  onMoved?: (move: RecordMove) => void
  onAdded?: (row: RecordRow) => void
  onGroupBy?: (propertyId: string) => void
  onError?: (error: DbKanbanError) => void
}

export interface DbKanbanControllerOptions extends DbKanbanHooks {
  port: () => RecordPort | null
  t: () => DbKanbanTranslate
  editable?: () => boolean
  lang?: () => string
}

export const INITIAL_DB_KANBAN: DbKanbanData = { ...IDLE, table: null, groupBy: '', query: '', dragging: null, dropTarget: null }

export function asDbKanbanError(error: unknown, t: DbKanbanTranslate): DbKanbanError {
  if (error instanceof RestError) return { code: error.code, message: error.message, status: error.status }
  const raw = error instanceof Error ? error.message : String(error)
  return { code: 'network_error', message: t('networkError', { message: raw }), status: 0 }
}

/** Vorgabe: gewünschte Eigenschaft, falls gruppierbar, sonst die erste Auswahl-Eigenschaft. */
export function initialGroupBy(table: RecordTable, preferred: string | undefined): string {
  const options = groupableProperties(table).map((property) => property.id)
  return preferred && options.includes(preferred) ? preferred : (options[0] ?? '')
}

type Run = ReturnType<typeof createRunner<RecordPort, DbKanbanError, DbKanbanData>>

function titleOf(table: RecordTable, rowId: string, t: DbKanbanTranslate, lang: string): string {
  const title = titleProperty(table)
  const row = table.rows.find((entry) => entry.id === rowId)
  return (title && row ? cellText(row.cells[title.id], t, lang) : '') || t('untitled')
}

function moveActions(store: Store<DbKanbanData>, run: Run, options: DbKanbanControllerOptions) {
  const editable = (): boolean => options.editable?.() ?? true
  const lang = (): string => options.lang?.() ?? 'de'

  /** Datensatz, wenn er in `column` verschoben werden darf und dort noch nicht liegt. */
  function movable(rowId: string, column: string): RecordRow | null {
    const { table, groupBy } = store.get()
    const row = table?.rows.find((entry) => entry.id === rowId)
    if (!table || !row || !groupBy || !editable()) return null
    return groupOf(table, row, groupBy) === column ? null : row
  }

  function announce(table: RecordTable, rowId: string, column: string): void {
    const t = options.t()
    store.set({ notice: t('moved', { title: titleOf(table, rowId, t, lang()), label: columnLabel(column, t) }) })
  }

  /** Karte in eine Spalte legen: sofort anzeigen, bei Fehler zurücknehmen. */
  async function move(rowId: string, column: string): Promise<boolean> {
    const { table, groupBy } = store.get()
    const row = movable(rowId, column)
    store.set({ dragging: null, dropTarget: null })
    if (!table || !row) return false
    const value = dropValue(column)
    const patch = (cell: RecordRow['cells'][string] | null) => (state: DbKanbanData) => ({ table: state.table ? withCell(state.table, rowId, groupBy, cell) : null })
    store.set(patch(value))
    const outcome = await run('move', async (port) => ({ row: (await port.updateCell(rowId, groupBy, value)) ?? null }))
    if (!outcome) {
      store.set(patch(row.cells[groupBy] ?? null))
      return false
    }
    const saved = outcome.row
    if (saved) store.set((state) => ({ table: state.table ? withRow(state.table, saved) : null }))
    announce(table, rowId, column)
    options.onMoved?.({ rowId, propertyId: groupBy, value })
    return true
  }

  /** Tastatur: in die Nachbarspalte der sichtbaren Spalten. */
  async function moveBy(rowId: string, direction: 1 | -1): Promise<boolean> {
    const { table, groupBy, query } = store.get()
    const row = table?.rows.find((entry) => entry.id === rowId)
    if (!table || !row) return false
    const groups = groupRecords(table, groupBy, table.rows.filter((entry) => matchesRecord(entry, query)))
    const target = neighbourGroup(groups, groupOf(table, row, groupBy), direction)
    return target === null ? false : move(rowId, target)
  }

  async function addCard(column: string): Promise<RecordRow | null> {
    const { table, groupBy } = store.get()
    if (!table || !groupBy || !editable() || !options.port()?.addRow) return null
    const cells = { [groupBy]: dropValue(column) }
    const row = await run('add', (port) => port.addRow?.(cells) ?? Promise.reject(new Error('addRow')))
    if (!row) return null
    store.set((state) => ({ table: state.table ? withRow(state.table, row) : null, notice: options.t()('added', { label: columnLabel(column, options.t()) }) }))
    options.onAdded?.(row)
    return row
  }

  return { move, moveBy, addCard }
}

export function createDbKanbanController(options: DbKanbanControllerOptions) {
  const store = createStore<DbKanbanData>(INITIAL_DB_KANBAN)
  const run = createRunner(store, options.port, (error) => asDbKanbanError(error, options.t()), options.onError)

  async function load(preferredGroupBy?: string): Promise<void> {
    const table = await run('load', (port) => port.load())
    if (table) store.set((state) => ({ table, groupBy: initialGroupBy(table, preferredGroupBy || state.groupBy) }))
  }

  function setGroupBy(propertyId: string): void {
    if (propertyId === store.get().groupBy) return
    store.set({ groupBy: propertyId })
    options.onGroupBy?.(propertyId)
  }

  return {
    store,
    load,
    setGroupBy,
    ...moveActions(store, run, options),
    setQuery: (query: string) => store.set({ query }),
    startDrag: (rowId: string | null) => store.set({ dragging: rowId, dropTarget: null }),
    setDropTarget: (column: string | null) => store.set({ dropTarget: column }),
    dismissError: () => store.set({ error: null }),
  }
}

export type DbKanbanController = ReturnType<typeof createDbKanbanController>
