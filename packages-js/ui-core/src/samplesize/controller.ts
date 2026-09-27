// Zustandsautomat von <flowaudit-sample-size-planner> (Vue und React): lädt den
// Katalog über den Port, verwaltet das Formular und lässt den Umfang im
// Backend berechnen. Vue bindet ihn mit useStore, React mit useStoreState.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import { buildRequest, EMPTY_FORM, EMPTY_STRATUM, formFor, formFromRequest, methodById, type SampleSizeForm, type SampleSizeIssues, type StratumDraft } from './model'
import type { SampleSizeCatalogue, SampleSizePlan, SampleSizeRequest, SamplesizePort } from './types'

export type SamplesizeBusy = 'load' | 'plan'

export interface SamplesizeCallbacks {
  planned?: (plan: SampleSizePlan) => void
  failed?: (message: string) => void
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface SamplesizeData extends RequestState<string> {
  catalogue: SampleSizeCatalogue | null
  form: SampleSizeForm
  issues: SampleSizeIssues
  plan: SampleSizePlan | null
}

export interface SamplesizeSource {
  port: () => SamplesizePort | null | undefined
  request?: () => SampleSizeRequest | null | undefined
  callbacks?: () => SamplesizeCallbacks
}

export interface SamplesizeController {
  store: Store<SamplesizeData>
  load: () => Promise<void>
  selectMethod: (id: string) => void
  setValue: (field: string, text: string) => void
  setFiniteCorrection: (on: boolean) => void
  setStratum: (index: number, change: Partial<StratumDraft>) => void
  addStratum: () => void
  removeStratum: (index: number) => void
  calculate: () => Promise<void>
}

export const INITIAL_SAMPLESIZE: SamplesizeData = { ...IDLE, catalogue: null, form: EMPTY_FORM, issues: {}, plan: null }

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function createSamplesizeController(source: SamplesizeSource): SamplesizeController {
  const store = createStore<SamplesizeData>({ ...INITIAL_SAMPLESIZE })
  const run = createRunner(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  const edit = (form: Partial<SampleSizeForm>): void => store.set({ form: { ...store.get().form, ...form }, plan: null })
  const strata = (rows: readonly StratumDraft[]): void => edit({ strata: rows })
  return {
    store,
    async load() {
      const catalogue = await run('load', (port) => port.profiles())
      if (!catalogue) return
      const request = source.request?.()
      store.set({ catalogue, form: request ? formFromRequest(request, catalogue) : EMPTY_FORM, issues: {}, plan: null })
    },
    selectMethod(id) {
      const { catalogue } = store.get()
      store.set({ form: formFor(methodById(catalogue, id), catalogue), issues: {}, plan: null })
    },
    setValue(field, text) {
      edit({ values: { ...store.get().form.values, [field]: text } })
    },
    setFiniteCorrection(on) {
      edit({ finiteCorrection: on })
    },
    setStratum(index, change) {
      strata(store.get().form.strata.map((row, position) => (position === index ? { ...row, ...change } : row)))
    },
    addStratum() {
      strata([...store.get().form.strata, EMPTY_STRATUM])
    },
    removeStratum(index) {
      strata(store.get().form.strata.filter((_, position) => position !== index))
    },
    async calculate() {
      const { catalogue, form } = store.get()
      const method = methodById(catalogue, form.methodId)
      if (!method) return
      const built = buildRequest(form, method)
      if ('issues' in built) {
        store.set({ issues: built.issues, plan: null })
        return
      }
      store.set({ issues: {} })
      const plan = await run('plan', (port) => port.plan(built.request))
      if (!plan) return
      store.set({ plan })
      source.callbacks?.().planned?.(plan)
    },
  }
}
