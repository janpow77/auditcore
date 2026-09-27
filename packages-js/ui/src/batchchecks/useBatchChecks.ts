import type { Ref } from 'vue'
import {
  createBatchchecksController,
  type BatchchecksCallbacks,
  type BatchchecksController,
  type BatchchecksData,
  type BatchchecksPort,
  type TableImportData,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export interface UseBatchChecks {
  controller: BatchchecksController
  state: Readonly<Ref<BatchchecksData>>
  /** Stand des Tabellenimports (gemeinsamer TableImport-Controller). */
  table: Readonly<Ref<TableImportData>>
}

/** Vue-Anbindung der Bestandsprüfung aus `@auditcore/ui-core` (`createBatchchecksController`). */
export function useBatchChecks(port: () => BatchchecksPort | null, callbacks: BatchchecksCallbacks = {}): UseBatchChecks {
  const controller = createBatchchecksController({ port, callbacks: () => callbacks })
  return { controller, state: useStore(controller.store), table: useStore(controller.table.store) }
}
