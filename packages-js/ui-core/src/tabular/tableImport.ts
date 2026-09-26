// Zustandsautomat des Datei-Imports (Stichprobe, Benford) für Vue und React:
// Datei lesen, Spalten zuordnen, Vorschau der übernommenen Werte.

import {
  columnCells,
  detectDecimal,
  guessNumberColumn,
  numberColumn,
  parseTable,
  type DecimalSeparator,
  type ParsedTable,
} from '@auditcore/common'
import { createStore } from '../store'

/** Übernommene Spalten einer Datei. */
export interface ImportedColumns {
  filename: string
  values: (number | null)[]
  /** Kennungen und Schichten der übernommenen Zeilen (gleiche Länge wie `values`). */
  ids: string[] | null
  strata: string[] | null
  rejected: number[]
}

export interface TableImportData {
  filename: string
  text: string
  table: ParsedTable | null
  hasHeader: boolean
  valueColumn: number
  idColumn: number | null
  stratumColumn: number | null
  decimal: DecimalSeparator
}

const INITIAL: TableImportData = {
  filename: '', text: '', table: null, hasHeader: true, valueColumn: 0, idColumn: null, stratumColumn: null, decimal: ',',
}

/** Vorschau der übernommenen Werte (reine Funktion). */
export function importPreview(state: TableImportData): ImportedColumns | null {
  const current = state.table
  if (!current) return null
  const parsed = numberColumn(current, state.valueColumn, state.decimal)
  const rejected = new Set(parsed.rejected)
  const kept = current.rows.filter((_, index) => !rejected.has(index + 1))
  const pick = (column: number | null): string[] | null => (column === null ? null : kept.map((row) => row[column] ?? ''))
  return { filename: state.filename, values: parsed.values, ids: pick(state.idColumn), strata: pick(state.stratumColumn), rejected: parsed.rejected }
}

/** Anzeige des Trennzeichens („Tabulator“ für `\t`). */
export function importDelimiterText(table: ParsedTable | null, tab: string): string {
  return table?.delimiter === '\t' ? tab : (table?.delimiter ?? '')
}

/** Die ersten zehn unlesbaren Zeilen als Liste. */
export function importRejectedLines(preview: ImportedColumns | null): string {
  return (preview?.rejected ?? []).slice(0, 10).join(', ')
}

/** Optionale Spalte aus einem Auswahlwert (`''` = keine). */
export function importOptionalColumn(value: string): number | null {
  return value === '' ? null : Number(value)
}

export function createTableImportController() {
  const store = createStore<TableImportData>({ ...INITIAL })

  /** Nach Umschalten von `hasHeader` neu einlesen. */
  function reparse(): void {
    const state = store.get()
    const table = parseTable(state.text, state.hasHeader)
    const valueColumn = guessNumberColumn(table)
    store.set({ table, valueColumn, decimal: detectDecimal(columnCells(table, valueColumn), table.delimiter) })
  }

  function load(filename: string, text: string): void {
    store.set({ filename, text, idColumn: null, stratumColumn: null })
    reparse()
  }

  return {
    store,
    load,
    reparse,
    read: async (file: File) => load(file.name, await file.text()),
    setHasHeader: (hasHeader: boolean) => store.set({ hasHeader }),
    setValueColumn: (valueColumn: number) => store.set({ valueColumn }),
    setIdColumn: (idColumn: number | null) => store.set({ idColumn }),
    setStratumColumn: (stratumColumn: number | null) => store.set({ stratumColumn }),
    setDecimal: (decimal: DecimalSeparator) => store.set({ decimal }),
  }
}

export type TableImportController = ReturnType<typeof createTableImportController>
