// Zustandsautomat von <flowaudit-runner-console> (Vue und React): lädt die Einträge über
// den Port und verwaltet die Auswahl. Vue bindet ihn mit useStore, React mit
// useStoreState.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { RunnerItem, RunnerPort } from './types'

export interface RunnerCallbacks {
  selected?: (item: RunnerItem) => void
  failed?: (message: string) => void
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface RunnerData extends RequestState<string> {
  items: readonly RunnerItem[]
  selectedId: string | null
}

export interface RunnerSource {
  port: () => RunnerPort | null | undefined
  callbacks?: () => RunnerCallbacks
}

export interface RunnerController {
  store: Store<RunnerData>
  load: () => Promise<void>
  select: (id: string) => void
}

export const INITIAL_RUNNER: RunnerData = { ...IDLE, items: [], selectedId: null }

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function createRunnerController(source: RunnerSource): RunnerController {
  const store = createStore<RunnerData>({ ...INITIAL_RUNNER })
  const run = createRunner(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  return {
    store,
    async load() {
      const items = await run('load', (port) => port.list())
      if (items) store.set({ items, selectedId: null })
    },
    select(id) {
      const item = store.get().items.find((entry) => entry.id === id)
      if (!item) return
      store.set({ selectedId: id })
      source.callbacks?.().selected?.(item)
    },
  }
}
