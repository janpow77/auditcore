import { computed, type ComputedRef, type Ref } from 'vue'
import { createTableImportController, importPreview, type ImportedColumns, type TableImportController, type TableImportData } from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { ImportedColumns } from '@auditcore/ui-core'

export interface UseTableImport {
  controller: TableImportController
  state: Readonly<Ref<TableImportData>>
  preview: ComputedRef<ImportedColumns | null>
}

/** Vue-Anbindung des Datei-Imports aus `@auditcore/ui-core` (Datei lesen, Spalten zuordnen, Vorschau). */
export function useTableImport(): UseTableImport {
  const controller = createTableImportController()
  const state = useStore(controller.store)
  return { controller, state, preview: computed(() => importPreview(state.value)) }
}
