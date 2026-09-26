/**
 * Smallest shared state container of the UI controllers (same contract as
 * `createStore` of @auditcore/ui-core). Every state is a new immutable
 * object; React reads it with `useSyncExternalStore`, Vue mirrors it into a
 * `shallowRef`/`reactive`.
 */

export interface Store<S extends object> {
  get: () => S
  /** Applies a partial state; listeners are only notified on a change. */
  set: (patch: Partial<S> | ((state: S) => Partial<S>)) => void
  subscribe: (listener: () => void) => () => void
}

/** Read/write access to a state object (a `Store` or a Vue `reactive`). */
export interface StateAccess<S extends object> {
  get: () => S
  set: (patch: Partial<S>) => void
}

function changes<S extends object>(state: S, patch: Partial<S>): boolean {
  return (Object.keys(patch) as (keyof S)[]).some((key) => !Object.is(state[key], patch[key]))
}

export function createStore<S extends object>(initial: S): Store<S> {
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

/** Plain listener list (`on` returns the unsubscribe function). */
export function createEmitter<A extends unknown[] = []>() {
  const listeners = new Set<(...args: A) => void>()
  return {
    on(listener: (...args: A) => void): () => void {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    emit(...args: A): void {
      for (const listener of [...listeners]) listener(...args)
    },
  }
}
