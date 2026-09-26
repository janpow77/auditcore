import { useId, useSyncExternalStore } from 'react'
import type { Store } from '@flowaudit/ui-core'

/** Stand eines Kern-Controllers (`@flowaudit/ui-core`) als React-Zustand. */
export function useStoreState<S extends object>(store: Store<S>): S {
  return useSyncExternalStore(store.subscribe, store.get, store.get)
}

/** Stabile, CSS-taugliche Kennung je Instanz für aria-Verknüpfungen (wie `useId` der Vue-Fassung). */
export function useElementId(prefix = 'fa'): string {
  return `${prefix}-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
}

/** Klassenliste wie Vues `:class`-Bindung: falsche Werte entfallen. */
export function classes(...names: ReadonlyArray<string | false | null | undefined>): string {
  return names.filter(Boolean).join(' ')
}
