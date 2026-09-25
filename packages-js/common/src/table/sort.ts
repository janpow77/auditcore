export type SortDirection = 'asc' | 'desc'
export type CellValue = string | number | boolean | Date | null | undefined
export type TableRow = Readonly<Record<string, unknown>>

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  align?: 'start' | 'end' | 'center'
  /** Anzeigeformat; ohne Angabe wird der Wert als Text ausgegeben. */
  format?: (value: unknown, row: TableRow) => string
}

export interface SortState {
  key: string
  direction: SortDirection
}

function rank(value: unknown): number {
  return value === null || value === undefined || value === '' ? 1 : 0
}

/** Vergleich: leere Werte immer zuletzt, Zahlen/Daten numerisch, Text sprachsensitiv. */
export function compareValues(a: unknown, b: unknown, locale = 'de'): number {
  const emptiness = rank(a) - rank(b)
  if (emptiness !== 0 || rank(a) === 1) return emptiness
  if (typeof a === 'number' && typeof b === 'number') return a - b
  if (a instanceof Date && b instanceof Date) return a.getTime() - b.getTime()
  if (typeof a === 'boolean' && typeof b === 'boolean') return Number(a) - Number(b)
  return String(a).localeCompare(String(b), locale, { numeric: true, sensitivity: 'base' })
}

/** Stabile Sortierung einer Kopie; die Eingabe bleibt unverändert. */
export function sortRows<R extends TableRow>(rows: readonly R[], sort: SortState | null, locale = 'de'): R[] {
  const copy = rows.map((row, index) => ({ row, index }))
  if (!sort) return copy.map((entry) => entry.row)
  const factor = sort.direction === 'asc' ? 1 : -1
  copy.sort((left, right) => {
    const emptiness = rank(left.row[sort.key]) - rank(right.row[sort.key])
    if (emptiness !== 0) return emptiness
    const result = compareValues(left.row[sort.key], right.row[sort.key], locale) * factor
    return result === 0 ? left.index - right.index : result
  })
  return copy.map((entry) => entry.row)
}

/** Umschaltzyklus für `nextSort`. */
export interface NextSortOptions {
  /** `tri` (Standard): aufsteigend → absteigend → unsortiert; `bi`: nur aufsteigend ↔ absteigend. */
  cycle?: 'bi' | 'tri'
}

/** Nächster Zustand beim Klick auf eine Spalte: aufsteigend → absteigend → unsortiert (bzw. zurück zu aufsteigend bei `bi`). */
export function nextSort(current: SortState | null, key: string, options: NextSortOptions = {}): SortState | null {
  if (!current || current.key !== key) return { key, direction: 'asc' }
  if (current.direction === 'asc') return { key, direction: 'desc' }
  return options.cycle === 'bi' ? { key, direction: 'asc' } : null
}

export function ariaSort(current: SortState | null, key: string): 'ascending' | 'descending' | 'none' {
  if (!current || current.key !== key) return 'none'
  return current.direction === 'asc' ? 'ascending' : 'descending'
}
