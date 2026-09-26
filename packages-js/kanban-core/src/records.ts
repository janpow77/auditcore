/**
 * Datenbankansicht als Kanban (useDbKanban aus audit_designer): Datensätze
 * einer Tabelle werden nach einer Auswahl-Eigenschaft (`select`) in Spalten
 * gruppiert; Ablegen in einer Spalte setzt den Wert, die führende Spalte
 * „ohne Wert“ (`""`) nimmt leere und unbekannte Werte auf und setzt `null`.
 * Reine Funktionen ohne Framework; die Tabelle kommt über einen {@link RecordPort}.
 */
import { groupByValue } from './filtering'

export type RecordPropertyType = 'text' | 'number' | 'select' | 'multi_select' | 'date' | 'checkbox' | 'person' | 'url'
export type RecordValue = string | number | boolean | readonly string[] | null

export interface RecordProperty {
  id: string
  name: string
  type: RecordPropertyType | string
  /** Zulässige Werte bei `select`/`multi_select`, in Anzeigereihenfolge. */
  options?: readonly string[]
}

export interface RecordRow {
  id: string
  cells: Readonly<Record<string, RecordValue>>
  created_at?: string
}

export interface RecordTable {
  properties: readonly RecordProperty[]
  rows: readonly RecordRow[]
}

/** Datenzugang der Datenbankansicht; `addRow` ist optional (sonst keine neue Karte). */
export interface RecordPort {
  load(): Promise<RecordTable>
  /** Einen Zellwert setzen; liefert optional den gespeicherten Datensatz. */
  updateCell(rowId: string, propertyId: string, value: RecordValue): Promise<RecordRow | void>
  addRow?(cells: Readonly<Record<string, RecordValue>>): Promise<RecordRow>
}

export interface RecordGroup {
  /** Option der Spalte; `""` ist die Spalte „ohne Wert“. */
  value: string
  rows: RecordRow[]
}

/** Eigenschaften, nach denen gruppiert werden kann (nur `select` mit Optionen). */
export function groupableProperties(table: RecordTable): RecordProperty[] {
  return table.properties.filter((property) => property.type === 'select')
}

function keyOf(row: RecordRow, propertyId: string): string | null {
  const value = row.cells[propertyId]
  return typeof value === 'string' || typeof value === 'number' ? String(value) : null
}

/** Spalten je Option; ohne gültige Gruppierung keine Spalten (wie das Original). */
export function groupRecords(table: RecordTable, groupBy: string, rows: readonly RecordRow[] = table.rows): RecordGroup[] {
  const property = groupableProperties(table).find((entry) => entry.id === groupBy)
  if (!property) return []
  return groupByValue(rows, (row) => keyOf(row, property.id), property.options ?? []).map(([value, items]) => ({ value, rows: items }))
}

/** Zellwert für das Ablegen in einer Spalte: `""` wird `null` (wie `updateCell(…, value || null)`). */
export function dropValue(columnValue: string): string | null {
  return columnValue === '' ? null : columnValue
}

/** Nachbarspalte für Tastaturbedienung; `null`, wenn es keine gibt. */
export function neighbourGroup(groups: readonly RecordGroup[], current: string, direction: 1 | -1): string | null {
  const index = groups.findIndex((group) => group.value === current)
  const target = groups[index + direction]
  return index < 0 || !target ? null : target.value
}

/** Aktueller Spaltenwert eines Datensatzes (`""` für leer oder unbekannt). */
export function groupOf(table: RecordTable, row: RecordRow, groupBy: string): string {
  const options = groupableProperties(table).find((entry) => entry.id === groupBy)?.options ?? []
  const value = keyOf(row, groupBy)
  return value !== null && options.includes(value) ? value : ''
}

/** Neue Tabelle mit geändertem Zellwert (unveränderlich). */
export function withCell(table: RecordTable, rowId: string, propertyId: string, value: RecordValue): RecordTable {
  return {
    ...table,
    rows: table.rows.map((row) => (row.id === rowId ? { ...row, cells: { ...row.cells, [propertyId]: value } } : row)),
  }
}

/** Neue Tabelle mit ersetztem oder angehängtem Datensatz. */
export function withRow(table: RecordTable, row: RecordRow): RecordTable {
  const exists = table.rows.some((entry) => entry.id === row.id)
  return { ...table, rows: exists ? table.rows.map((entry) => (entry.id === row.id ? row : entry)) : [...table.rows, row] }
}

/** Suche über Text-, Zahl- und Auswahlzellen, ohne Groß-/Kleinschreibung. */
export function matchesRecord(row: RecordRow, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return Object.values(row.cells).some((value) => {
    const text = Array.isArray(value) ? value.join(' ') : typeof value === 'boolean' || value === null ? '' : String(value)
    return text.toLowerCase().includes(needle)
  })
}
