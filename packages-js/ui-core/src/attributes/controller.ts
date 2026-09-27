// Zustandsautomat von <flowaudit-attribute-sampling> (Vue und React): lädt die
// Profile, hält das Formular, wertet über den Port aus (Leitfaden 7.9).

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { AttributesCatalogue, AttributesPort, AttributesResult } from './types'
import { buildAttributesRequest, EMPTY_ATTRIBUTES_FORM, type AttributesForm, type AttributesIssues } from './view'

export interface AttributesCallbacks {
  evaluated?: (result: AttributesResult) => void
  failed?: (message: string) => void
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface AttributesData extends RequestState<string> {
  catalogue: AttributesCatalogue | null
  form: AttributesForm
  issues: AttributesIssues
  result: AttributesResult | null
}

export interface AttributesSource {
  port: () => AttributesPort | null | undefined
  callbacks?: () => AttributesCallbacks
}

export interface AttributesController {
  store: Store<AttributesData>
  load: () => Promise<void>
  update: (patch: Partial<AttributesForm>) => void
  evaluate: () => Promise<void>
}

export const INITIAL_ATTRIBUTES: AttributesData = { ...IDLE, catalogue: null, form: EMPTY_ATTRIBUTES_FORM, issues: {}, result: null }

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function createAttributesController(source: AttributesSource): AttributesController {
  const store = createStore<AttributesData>({ ...INITIAL_ATTRIBUTES })
  const run = createRunner(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  return {
    store,
    async load() {
      const catalogue = await run('load', (port) => port.profiles())
      if (catalogue) store.set((state) => ({ catalogue, form: { ...state.form, profileId: state.form.profileId ?? catalogue.recommended_profile } }))
    },
    update(patch) {
      store.set((state) => ({ form: { ...state.form, ...patch } }))
    },
    async evaluate() {
      const checked = buildAttributesRequest(store.get().form)
      store.set({ issues: checked.ok ? {} : checked.issues })
      if (!checked.ok) return
      const result = await run('evaluate', (port) => port.evaluate(checked.request))
      if (!result) return
      store.set({ result })
      source.callbacks?.().evaluated?.(result)
    },
  }
}
