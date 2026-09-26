// Zustandsautomat von <flowaudit-batch-checks> (Vue und React): lädt die Einträge über
// den Port und verwaltet die Auswahl. Vue bindet ihn mit useStore, React mit
// useStoreState.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { BatchchecksItem, BatchchecksPort } from './types'

export interface BatchchecksCallbacks {
  selected?: (item: BatchchecksItem) => void
  failed?: (message: string) => void
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface BatchchecksData extends RequestState<string> {
  items: readonly BatchchecksItem[]
  selectedId: string | null
}

export interface BatchchecksSource {
  port: () => BatchchecksPort | null | undefined
  callbacks?: () => BatchchecksCallbacks
}

export interface BatchchecksController {
  store: Store<BatchchecksData>
  load: () => Promise<void>
  select: (id: string) => void
}

export const INITIAL_BATCHCHECKS: BatchchecksData = { ...IDLE, items: [], selectedId: null }

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function createBatchchecksController(source: BatchchecksSource): BatchchecksController {
  const store = createStore<BatchchecksData>({ ...INITIAL_BATCHCHECKS })
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
