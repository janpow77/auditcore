import { computed, type ComputedRef, type Ref } from 'vue'
import {
  createExtrapolationController,
  extrapolationMethod,
  type ExtrapolationCallbacks,
  type ExtrapolationController,
  type ExtrapolationData,
  type ExtrapolationMethod,
  type ExtrapolationPort,
  type StratumInput,
  type UnitInput,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'

export type { ExtrapolationCallbacks } from '@flowaudit/ui-core'

export interface UseExtrapolation {
  controller: ExtrapolationController
  state: Readonly<Ref<ExtrapolationData>>
  method: ComputedRef<ExtrapolationMethod | null>
}

/** Vue-Anbindung der Hochrechnung aus `@flowaudit/ui-core` (`createExtrapolationController`). */
export function useExtrapolation(
  port: () => ExtrapolationPort | null,
  strata: () => readonly StratumInput[],
  units: () => readonly UnitInput[],
  format: (value: number) => string,
  callbacks: ExtrapolationCallbacks = {},
): UseExtrapolation {
  const controller = createExtrapolationController({ port, strata, units, format, callbacks: () => callbacks })
  const state = useStore(controller.store)
  return { controller, state, method: computed(() => extrapolationMethod(state.value)) }
}
