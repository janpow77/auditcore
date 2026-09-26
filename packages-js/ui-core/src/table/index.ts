/** Anzeige-Logik von FaTable/FlowauditTable; Sortierung selbst aus `@flowaudit/common`. */
import { ariaSort, type SortState, type TableColumn, type TableRow } from '@flowaudit/common'

export function cellText(column: TableColumn, row: TableRow): string {
  const value = row[column.key]
  if (column.format) return column.format(value, row)
  return value === null || value === undefined ? '' : String(value)
}

export function sortIcon(sort: SortState | null, key: string): 'sort' | 'sort-asc' | 'sort-desc' {
  const state = ariaSort(sort, key)
  return state === 'ascending' ? 'sort-asc' : state === 'descending' ? 'sort-desc' : 'sort'
}

/** Schlüssel einer Zeile aus `rowKey`, sonst Position. */
export function rowKeyOf(row: TableRow, rowKey: string, index: number): string {
  const value = row[rowKey]
  return typeof value === 'string' || typeof value === 'number' ? String(value) : `row-${index}`
}

export function cellAlignClass(column: TableColumn): string {
  return `fa-table__cell--${column.align ?? 'start'}`
}
