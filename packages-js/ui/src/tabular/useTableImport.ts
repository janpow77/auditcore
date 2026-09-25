import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import {
  columnCells,
  detectDecimal,
  guessNumberColumn,
  numberColumn,
  parseTable,
  type DecimalSeparator,
  type ParsedTable,
} from './parse'

/** Übernommene Spalten einer Datei. */
export interface ImportedColumns {
  filename: string
  values: (number | null)[]
  /** Kennungen und Schichten der übernommenen Zeilen (gleiche Länge wie `values`). */
  ids: string[] | null
  strata: string[] | null
  rejected: number[]
}

export interface UseTableImport {
  filename: Ref<string>
  table: ShallowRef<ParsedTable | null>
  hasHeader: Ref<boolean>
  valueColumn: Ref<number>
  idColumn: Ref<number | null>
  stratumColumn: Ref<number | null>
  decimal: Ref<DecimalSeparator>
  preview: ComputedRef<ImportedColumns | null>
  read: (file: File) => Promise<void>
  load: (name: string, text: string) => void
  /** Nach Umschalten von `hasHeader` neu einlesen. */
  reparse: () => void
}

/** Datei lesen, Spalten zuordnen und eine Vorschau der übernommenen Werte bilden. */
export function useTableImport(): UseTableImport {
  const filename = ref('')
  const text = ref('')
  const table = shallowRef<ParsedTable | null>(null)
  const hasHeader = ref(true)
  const valueColumn = ref(0)
  const idColumn = ref<number | null>(null)
  const stratumColumn = ref<number | null>(null)
  const decimal = ref<DecimalSeparator>(',')

  function reparse(): void {
    table.value = parseTable(text.value, hasHeader.value)
    valueColumn.value = guessNumberColumn(table.value)
    decimal.value = detectDecimal(columnCells(table.value, valueColumn.value), table.value.delimiter)
  }

  function load(name: string, content: string): void {
    filename.value = name
    text.value = content
    idColumn.value = null
    stratumColumn.value = null
    reparse()
  }

  const preview = computed<ImportedColumns | null>(() => {
    const current = table.value
    if (!current) return null
    const parsed = numberColumn(current, valueColumn.value, decimal.value)
    const rejected = new Set(parsed.rejected)
    const kept = current.rows.filter((_, index) => !rejected.has(index + 1))
    const pick = (column: number | null): string[] | null =>
      column === null ? null : kept.map((row) => row[column] ?? '')
    return {
      filename: filename.value,
      values: parsed.values,
      ids: pick(idColumn.value),
      strata: pick(stratumColumn.value),
      rejected: parsed.rejected,
    }
  })

  return {
    filename,
    table,
    hasHeader,
    valueColumn,
    idColumn,
    stratumColumn,
    decimal,
    preview,
    read: async (file) => load(file.name, await file.text()),
    load,
    reparse,
  }
}
