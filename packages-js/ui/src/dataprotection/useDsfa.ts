// Vue-Anbindung des DSFA-Zustandsautomaten aus @flowaudit/ui-core.

import { computed, getCurrentScope, onScopeDispose, type ComputedRef, type Ref } from 'vue'
import {
  createDsfaController,
  dsfaDerived,
  type DataProtectionPort,
  type DataProtectionTranslate,
  type DsfaController,
  type DsfaData,
  type DsfaDerived,
  type DsfaHooks,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'

export type { DsfaHooks, DsfaStep } from '@flowaudit/ui-core'

export interface DsfaState {
  controller: DsfaController
  state: Readonly<Ref<DsfaData>>
  derived: ComputedRef<DsfaDerived>
}

export function useDsfa(port: () => DataProtectionPort | null, t: () => DataProtectionTranslate, hooks: DsfaHooks = {}): DsfaState {
  const controller = createDsfaController({ ...hooks, port, t })
  const state = useStore(controller.store)
  if (getCurrentScope()) onScopeDispose(controller.dispose)
  return { controller, state, derived: computed(() => dsfaDerived(state.value)) }
}
