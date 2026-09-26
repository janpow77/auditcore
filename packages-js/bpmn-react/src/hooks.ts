/** Small React helpers shared by the components (counterparts of the Vue bindings). */

import { useId, useSyncExternalStore } from 'react'
import type { Store } from '@auditcore/bpmn-flowaudit/ui'

/** State of a core controller (`@auditcore/bpmn-flowaudit/ui`) as React state. */
export function useStoreState<S extends object>(store: Store<S>): S {
  return useSyncExternalStore(store.subscribe, store.get, store.get)
}

/** Stable, CSS-safe id per instance for aria references. */
export function useElementId(prefix = 'fa'): string {
  return `${prefix}-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
}

/** Class list like Vue's `:class` binding: falsy entries are dropped. */
export function classes(...names: ReadonlyArray<string | false | null | undefined>): string {
  return names.filter(Boolean).join(' ')
}
