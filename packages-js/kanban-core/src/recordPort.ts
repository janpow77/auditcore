/** In-Memory-Datenzugang der Datenbankansicht (Demo, Tests, Anwendungen mit eigenem Speichern). */
import { withCell, withRow, type RecordValue, type RecordPort, type RecordRow, type RecordTable } from './records'

export interface MemoryRecordPortOptions {
  /** Nach jeder Änderung mit der neuen Tabelle aufgerufen (z. B. `v-model` der Anwendung). */
  onChange?: (table: RecordTable) => void
  newId?: () => string
  clock?: () => string
}

function cloneTable(table: RecordTable): RecordTable {
  return JSON.parse(JSON.stringify(table)) as RecordTable
}

let counter = 0

export function createMemoryRecordPort(initial: RecordTable, options: MemoryRecordPortOptions = {}): RecordPort & { snapshot(): RecordTable } {
  let table = cloneTable(initial)
  const commit = (next: RecordTable): void => {
    table = next
    options.onChange?.(cloneTable(table))
  }
  return {
    load: async () => cloneTable(table),
    snapshot: () => cloneTable(table),
    async updateCell(rowId: string, propertyId: string, value: RecordValue): Promise<RecordRow> {
      const row = table.rows.find((entry) => entry.id === rowId)
      if (!row) throw new Error(`Datensatz '${rowId}' nicht gefunden`)
      commit(withCell(table, rowId, propertyId, value))
      return table.rows.find((entry) => entry.id === rowId) as RecordRow
    },
    async addRow(cells: Readonly<Record<string, RecordValue>>): Promise<RecordRow> {
      counter += 1
      const row: RecordRow = {
        id: options.newId?.() ?? `row-${Date.now().toString(36)}-${counter}`,
        cells: { ...cells },
        created_at: options.clock?.() ?? new Date().toISOString(),
      }
      commit(withRow(table, row))
      return row
    },
  }
}
