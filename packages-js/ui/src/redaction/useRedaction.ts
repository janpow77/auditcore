import { onBeforeUnmount, type Ref } from 'vue'
import {
  createRedactionController,
  type RedactionCallbacks,
  type RedactionController,
  type RedactionData,
  type RedactionPort,
  type RedactionUrls,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export interface UseRedaction {
  controller: RedactionController
  state: Readonly<Ref<RedactionData>>
}

/** Vue-Anbindung von „PDF schwärzen“ aus `@auditcore/ui-core`; gibt Objekt-URLs beim Entfernen frei. */
export function useRedaction(port: () => RedactionPort | null, callbacks: RedactionCallbacks = {}, urls?: RedactionUrls): UseRedaction {
  const controller = createRedactionController({ port, callbacks: () => callbacks, urls })
  onBeforeUnmount(() => controller.dispose())
  return { controller, state: useStore(controller.store) }
}
