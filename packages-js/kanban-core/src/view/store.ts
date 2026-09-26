/**
 * Kleinster Zustandsspeicher der Kanban-Ansicht. Jeder Stand ist ein neues,
 * unveränderliches Objekt; React liest ihn über `useSyncExternalStore`, Vue
 * spiegelt ihn in ein `shallowRef`. Gleiche Form wie `Store` aus
 * `@auditcore/ui-core`, damit `useStoreState`/`useStore` ihn direkt lesen.
 */
export interface KanbanStore<S extends object> {
  get: () => S
  /** Teilstand übernehmen; Beobachter werden nur bei einer Änderung benachrichtigt. */
  set: (patch: Partial<S> | ((state: S) => Partial<S>)) => void
  subscribe: (listener: () => void) => () => void
}

function changes<S extends object>(state: S, patch: Partial<S>): boolean {
  return (Object.keys(patch) as (keyof S)[]).some((key) => !Object.is(state[key], patch[key]))
}

export function createKanbanStore<S extends object>(initial: S): KanbanStore<S> {
  let state = initial
  const listeners = new Set<() => void>()
  return {
    get: () => state,
    set(patch) {
      const next = typeof patch === 'function' ? patch(state) : patch
      if (!changes(state, next)) return
      state = { ...state, ...next }
      for (const listener of [...listeners]) listener()
    },
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
  }
}
