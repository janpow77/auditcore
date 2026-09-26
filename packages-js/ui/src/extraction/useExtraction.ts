import type { Ref } from 'vue'
import {
  createExtractionController,
  type ExtractionCallbacks,
  type ExtractionController,
  type ExtractionData,
  type ExtractionPort,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { ExtractionCallbacks } from '@auditcore/ui-core'

export interface UseExtraction {
  controller: ExtractionController
  state: Readonly<Ref<ExtractionData>>
}

/** Vue-Anbindung der Belegerkennung aus `@auditcore/ui-core` (`createExtractionController`). */
export function useExtraction(port: () => ExtractionPort | null, callbacks: ExtractionCallbacks = {}): UseExtraction {
  const controller = createExtractionController({ port, callbacks: () => callbacks })
  return { controller, state: useStore(controller.store) }
}
