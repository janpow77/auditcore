import { computed, type ComputedRef, type Ref } from 'vue'
import {
  benfordProfile,
  benfordValues,
  createBenfordController,
  type BenfordCallbacks,
  type BenfordController,
  type BenfordData,
  type BenfordMetricsRequest,
  type BenfordPort,
  type ConformityProfile,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { BenfordCallbacks } from '@auditcore/ui-core'

export interface UseBenford {
  controller: BenfordController
  state: Readonly<Ref<BenfordData>>
  values: ComputedRef<readonly (number | null)[]>
  profile: ComputedRef<ConformityProfile | null>
}

/** Vue-Anbindung der Benford-Analyse aus `@auditcore/ui-core` (`createBenfordController`). */
export interface BenfordOptions {
  metrics?: () => BenfordMetricsRequest | null | undefined
  autoAnalyse?: () => boolean | undefined
}

export function useBenford(
  port: () => BenfordPort | null,
  given: () => readonly (number | null)[],
  callbacks: BenfordCallbacks = {},
  options: BenfordOptions = {},
): UseBenford {
  const controller = createBenfordController({ port, values: given, callbacks: () => callbacks, ...options })
  const state = useStore(controller.store)
  return {
    controller,
    state,
    values: computed(() => benfordValues(state.value, given())),
    profile: computed(() => benfordProfile(state.value)),
  }
}
