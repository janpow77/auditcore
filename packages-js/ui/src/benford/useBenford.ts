import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import { createRunner } from '../rest'
import { buildAnalyseRequest, type AnalyseError } from './model'
import type { BenfordAnalysis, BenfordCatalogue, BenfordPort, BenfordTest, ConformityProfile, ShortValues } from './types'

export interface BenfordCallbacks {
  analysed?: (result: BenfordAnalysis) => void
  failed?: (message: string) => void
}

export interface UseBenford {
  catalogue: ShallowRef<BenfordCatalogue | null>
  values: ComputedRef<readonly (number | null)[]>
  test: Ref<BenfordTest | null>
  profileId: Ref<string | null>
  profile: ComputedRef<ConformityProfile | null>
  shortValues: Ref<ShortValues | null>
  result: ShallowRef<BenfordAnalysis | null>
  error: Ref<AnalyseError | null>
  busy: Ref<'load' | 'analyse' | null>
  failure: Ref<string>
  load: () => Promise<void>
  useValues: (values: readonly (number | null)[] | null) => void
  analyse: () => Promise<void>
}

/** Zustand und Ablauf der Benford-Analyse; Berechnung ausschließlich über den Port. */
export function useBenford(
  port: () => BenfordPort | null,
  given: () => readonly (number | null)[],
  callbacks: BenfordCallbacks = {},
): UseBenford {
  const catalogue = shallowRef<BenfordCatalogue | null>(null)
  const imported = shallowRef<readonly (number | null)[] | null>(null)
  const values = computed(() => imported.value ?? given())
  const test = ref<BenfordTest | null>('first')
  const profileId = ref<string | null>(null)
  const profile = computed(() => catalogue.value?.profiles.find((entry) => entry.id === profileId.value) ?? null)
  const shortValues = ref<ShortValues | null>(null)
  const result = shallowRef<BenfordAnalysis | null>(null)
  const error = ref<AnalyseError | null>(null)
  const { busy, failure, run: guarded } = createRunner<BenfordPort, 'load' | 'analyse'>(port, callbacks.failed)

  async function load(): Promise<void> {
    const loaded = await guarded('load', (active) => active.profiles())
    if (!loaded) return
    catalogue.value = loaded
    profileId.value = loaded.profiles[0]?.id ?? null
  }

  async function analyse(): Promise<void> {
    if (!catalogue.value) return
    const checked = buildAnalyseRequest({
      catalogue: catalogue.value,
      test: test.value,
      profile: profileId.value,
      shortValues: shortValues.value,
      values: values.value,
    })
    error.value = checked.ok ? null : checked.error
    if (!checked.ok) return
    const analysed = await guarded('analyse', (active) => active.analyse(checked.request))
    if (!analysed) return
    result.value = analysed
    callbacks.analysed?.(analysed)
  }

  return {
    catalogue, values, test, profileId, profile, shortValues, result, error, busy, failure, load, analyse,
    useValues: (next) => {
      imported.value = next
      result.value = null
    },
  }
}
