// Vue-Anbindung des VVT-Zustandsautomaten aus @auditcore/ui-core.

import { computed, onScopeDispose, getCurrentScope, type ComputedRef, type Ref } from 'vue'
import {
  createVvtController,
  vvtView,
  type DataProtectionPort,
  type DataProtectionTranslate,
  type VvtController,
  type VvtData,
  type VvtHooks,
  type VvtView,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { VvtExport, VvtExportFormat, VvtHooks } from '@auditcore/ui-core'

export interface VvtState {
  controller: VvtController
  state: Readonly<Ref<VvtData>>
  view: ComputedRef<VvtView>
}

export function useVvt(port: () => DataProtectionPort | null, t: () => DataProtectionTranslate, hooks: VvtHooks = {}): VvtState {
  const controller = createVvtController({ ...hooks, port, t })
  const state = useStore(controller.store)
  if (getCurrentScope()) onScopeDispose(controller.dispose)
  return { controller, state, view: computed(() => vvtView(state.value)) }
}
