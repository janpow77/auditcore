/**
 * Kleinster gemeinsamer Zustandsspeicher der Controller. Jeder Stand ist ein
 * neues, unveränderliches Objekt; React liest ihn über
 * `useSyncExternalStore`, Vue spiegelt ihn in ein `shallowRef`.
 */
export interface Store<S extends object> {
  get: () => S
  /** Teilstand übernehmen; Beobachter werden nur bei einer Änderung benachrichtigt. */
  set: (patch: Partial<S> | ((state: S) => Partial<S>)) => void
  subscribe: (listener: () => void) => () => void
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

/** Beschäftigt-Status, Fehler und Erfolgsmeldung einer Portanfrage (gemeinsam für alle Controller). */
export interface RequestState<E> {
  busy: string | null
  error: E | null
  /** Letzte Erfolgsmeldung (für `aria-live`). */
  notice: string
}

export const IDLE: RequestState<never> = { busy: null, error: null, notice: '' }

/**
 * Führt eine Portanfrage aus: setzt `busy`, fängt Fehler (über `toError`) und
 * meldet sie an `onError`. Ohne Port geschieht nichts (`null`).
 */
export function createRunner<P, E, S extends RequestState<E>>(
  store: Store<S>,
  port: () => P | null,
  toError: (error: unknown) => E,
  onError?: (error: E) => void,
) {
  return async function run<T>(kind: string, task: (active: P) => Promise<T>): Promise<T | null> {
    const active = port()
    if (!active) return null
    store.set({ busy: kind, error: null } as Partial<S>)
    try {
      return await task(active)
    } catch (caught) {
      const error = toError(caught)
      store.set({ error } as Partial<S>)
      onError?.(error)
      return null
    } finally {
      store.set({ busy: null } as Partial<S>)
    }
  }
}

/** Verzögerter Aufruf, der bei jeder neuen Eingabe neu startet (Vorschau, Vollständigkeitsprüfung). */
export function createDelay(ms: () => number) {
  let timer: ReturnType<typeof setTimeout> | undefined
  return {
    schedule(task: () => void): void {
      clearTimeout(timer)
      timer = setTimeout(task, ms())
    },
    cancel(): void {
      clearTimeout(timer)
      timer = undefined
    },
  }
}
