import { getCurrentScope, onScopeDispose, shallowRef, type ShallowRef } from 'vue'
import type { Store } from '@auditcore/ui-core'

/** Stand eines Kern-Controllers (`@auditcore/ui-core`) als reaktive Vue-Referenz. */
export function useStore<S extends object>(store: Store<S>): Readonly<ShallowRef<S>> {
  const state = shallowRef(store.get()) as ShallowRef<S>
  const stop = store.subscribe(() => {
    state.value = store.get()
  })
  if (getCurrentScope()) onScopeDispose(stop)
  return state
}
