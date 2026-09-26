import { computed, type ComputedRef, type Ref } from 'vue'
import {
  createSamplingController,
  samplingPopulation,
  samplingProfile,
  type MethodProfile,
  type PopulationItem,
  type SamplingCallbacks,
  type SamplingController,
  type SamplingData,
  type SamplingPort,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { SamplingBusy, SamplingCallbacks, SelectionError } from '@auditcore/ui-core'

export interface UseSampling {
  controller: SamplingController
  state: Readonly<Ref<SamplingData>>
  profile: ComputedRef<MethodProfile | null>
  population: ComputedRef<readonly PopulationItem[]>
}

/**
 * Vue-Anbindung des Stichprobenrechners aus `@auditcore/ui-core`
 * (`createSamplingController`); Getter halten Props reaktiv.
 */
export function useSampling(
  port: () => SamplingPort | null,
  items: () => readonly PopulationItem[],
  format: (value: number) => string,
  callbacks: SamplingCallbacks = {},
): UseSampling {
  const controller = createSamplingController({ port, items, format, callbacks: () => callbacks })
  const state = useStore(controller.store)
  return {
    controller,
    state,
    profile: computed(() => samplingProfile(state.value)),
    population: computed(() => samplingPopulation(state.value, items())),
  }
}
