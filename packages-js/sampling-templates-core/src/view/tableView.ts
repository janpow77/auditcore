/** Anzeigemodell einer Nachschlagetabelle (Blatt X1a): Kopfzeilen und formatierte Werte. */
import { formatNumber } from '@auditcore/common'
import type { DataTable } from '../model/table'
import type { CellValue } from '../model/types'

export interface DataTableView {
  title: string
  source: string
  /** Gemeinsame Überschriften über mehreren Spalten, in Spaltenreihenfolge; leer, wenn es keine gibt. */
  groups: readonly { label: string; span: number }[]
  columns: readonly { key: string; label: string }[]
  /** Je Zeile die formatierten Werte; die erste Spalte ist die Zeilenüberschrift. */
  rows: readonly (readonly string[])[]
  notes: readonly string[]
}

/** Nachkommastellen aus dem Zahlenformat der Spalte (`0.00` → 2). */
const digitsOf = (format: string | undefined): number => (format?.split('.')[1] ?? '').length

function display(value: CellValue, format: string | undefined): string {
  if (typeof value !== 'number') return value ?? ''
  const digits = digitsOf(format)
  return formatNumber(value, { digits })
}

/** Aufeinanderfolgende Spalten mit derselben Gruppenüberschrift zusammenfassen. */
function groupsOf(table: DataTable): { label: string; span: number }[] {
  const groups: { label: string; span: number }[] = []
  for (const column of table.columns) {
    const label = (column.group ?? '').trim()
    const last = groups.at(-1)
    if (last && last.label === label) last.span += 1
    else groups.push({ label, span: 1 })
  }
  return groups.some((group) => group.label) ? groups : []
}

export function buildDataTable(table: DataTable): DataTableView {
  return {
    title: table.title,
    source: table.source,
    groups: groupsOf(table),
    columns: table.columns.map((column) => ({ key: column.key, label: column.label.trim() })),
    rows: table.rows.map((row) => row.map((value, index) => display(value, table.columns[index]?.format))),
    notes: table.notes,
  }
}
