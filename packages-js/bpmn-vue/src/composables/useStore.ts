/**
 * Mirrors a core store (`@auditcore/bpmn-flowaudit/ui`) into a `shallowRef`
 * (the Vue counterpart of React's `useSyncExternalStore`). Unsubscribes with
 * the surrounding effect scope, if any.
 */

import { getCurrentScope, onScopeDispose, shallowRef, type ShallowRef } from 'vue'
import type { Store } from '@auditcore/bpmn-flowaudit/ui'

export function useStore<S extends object>(store: Store<S>): Readonly<ShallowRef<S>> {
  const state = shallowRef(store.get()) as ShallowRef<S>
  const stop = store.subscribe(() => (state.value = store.get()))
  if (getCurrentScope()) onScopeDispose(stop)
  return state
}
