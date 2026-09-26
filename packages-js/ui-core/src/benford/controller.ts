// Zustandsautomat von <flowaudit-benford> (Vue und React): Tests und Profile
// laden, Werte übernehmen, Analyse anstoßen. Berechnet wird ausschließlich
// über den Port.

import { createRunner, createStore, IDLE, type RequestState } from '../store'
import { buildAnalyseRequest, type AnalyseError } from './model'
import type { BenfordAnalysis, BenfordCatalogue, BenfordPort, BenfordTest, ConformityProfile, ShortValues } from './types'

export type BenfordBusy = 'load' | 'analyse'

export interface BenfordCallbacks {
  analysed?: (result: BenfordAnalysis) => void
  failed?: (message: string) => void
}

/** Stand der Benford-Analyse; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface BenfordData extends RequestState<string> {
  catalogue: BenfordCatalogue | null
  /** Importierte Werte; `null` = Eigenschaft `values`. */
  imported: readonly (number | null)[] | null
  test: BenfordTest | null
  profileId: string | null
  shortValues: ShortValues | null
  result: BenfordAnalysis | null
  validation: AnalyseError | null
}

export interface BenfordSource {
  port: () => BenfordPort | null | undefined
  values: () => readonly (number | null)[]
  callbacks?: () => BenfordCallbacks
}

export const INITIAL_BENFORD: BenfordData = {
  ...IDLE, catalogue: null, imported: null, test: 'first', profileId: null, shortValues: null, result: null, validation: null,
}

export function benfordValues(state: BenfordData, given: readonly (number | null)[]): readonly (number | null)[] {
  return state.imported ?? given
}

export function benfordProfile(state: BenfordData): ConformityProfile | null {
  return state.catalogue?.profiles.find((entry) => entry.id === state.profileId) ?? null
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function createBenfordController(source: BenfordSource) {
  const store = createStore<BenfordData>({ ...INITIAL_BENFORD })
  const run = createRunner<BenfordPort, string, BenfordData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))

  async function load(): Promise<void> {
    const loaded = await run('load', (active) => active.profiles())
    if (!loaded) return
    store.set({ catalogue: loaded, profileId: loaded.profiles[0]?.id ?? null })
  }

  async function analyse(): Promise<void> {
    const state = store.get()
    if (!state.catalogue) return
    const checked = buildAnalyseRequest({
      catalogue: state.catalogue, test: state.test, profile: state.profileId, shortValues: state.shortValues,
      values: benfordValues(state, source.values()),
    })
    store.set({ validation: checked.ok ? null : checked.error })
    if (!checked.ok) return
    const analysed = await run('analyse', (active) => active.analyse(checked.request))
    if (!analysed) return
    store.set({ result: analysed })
    source.callbacks?.().analysed?.(analysed)
  }

  return {
    store,
    load,
    analyse,
    /** Importierte Werte übernehmen; `null` kehrt zur Eigenschaft `values` zurück. */
    useValues: (imported: readonly (number | null)[] | null) => store.set({ imported, result: null }),
    setTest: (test: BenfordTest | null) => store.set({ test }),
    setProfile: (profileId: string | null) => store.set({ profileId }),
    setShortValues: (shortValues: ShortValues | null) => store.set({ shortValues }),
  }
}

export type BenfordController = ReturnType<typeof createBenfordController>
