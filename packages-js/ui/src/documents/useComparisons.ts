// Vue-Anbindung des Zustandsautomaten der Vergleichsverwaltung aus @flowaudit/ui-core.

import { computed, type ComputedRef, type Ref } from 'vue'
import {
  comparisonsView,
  createComparisonsController,
  type ComparisonsController,
  type ComparisonsData,
  type ComparisonsHooks,
  type ComparisonsPort,
  type ComparisonsTranslate,
  type ComparisonsView,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'

export interface ComparisonsSource {
  port: () => ComparisonsPort | null
  t: () => ComparisonsTranslate
  lang: () => string
  maxBytes: () => number
}

export interface UseComparisons {
  controller: ComparisonsController
  state: Readonly<Ref<ComparisonsData>>
  view: ComputedRef<ComparisonsView>
}

export function useComparisons(source: ComparisonsSource, hooks: ComparisonsHooks = {}): UseComparisons {
  const controller = createComparisonsController({ ...hooks, ...source })
  const state = useStore(controller.store)
  const view = computed(() => comparisonsView(state.value, source.t(), { lang: source.lang(), maxBytes: source.maxBytes() }))
  return { controller, state, view }
}
