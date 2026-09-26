import { computed, type ComputedRef, type Ref } from 'vue'
import {
  benfordProfile,
  benfordValues,
  createBenfordController,
  type BenfordCallbacks,
  type BenfordController,
  type BenfordData,
  type BenfordPort,
  type ConformityProfile,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'

export type { BenfordCallbacks } from '@flowaudit/ui-core'

export interface UseBenford {
  controller: BenfordController
  state: Readonly<Ref<BenfordData>>
  values: ComputedRef<readonly (number | null)[]>
  profile: ComputedRef<ConformityProfile | null>
}

/** Vue-Anbindung der Benford-Analyse aus `@flowaudit/ui-core` (`createBenfordController`). */
export function useBenford(
  port: () => BenfordPort | null,
  given: () => readonly (number | null)[],
  callbacks: BenfordCallbacks = {},
): UseBenford {
  const controller = createBenfordController({ port, values: given, callbacks: () => callbacks })
  const state = useStore(controller.store)
  return {
    controller,
    state,
    values: computed(() => benfordValues(state.value, given())),
    profile: computed(() => benfordProfile(state.value)),
  }
}
