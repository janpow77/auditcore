import { computed, watch, type ComputedRef, type Ref } from 'vue'
import {
  createSynopsisController,
  selectSynopsis,
  synopsisBase,
  synopsisMessages,
  type SynopsisController,
  type SynopsisData,
  type SynopsisInputs,
  type SynopsisSelection,
  type SynopsisTranslate,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n/i18n'

export type { SynopsisFilterState } from '@flowaudit/ui-core'

/** Eingaben der Komponente, als Getter übergeben (Props bleiben reaktiv). */
export interface SynopsisSource {
  inputs: () => SynopsisInputs
  locale: () => Locale | undefined
}

export interface UseSynopsis {
  t: SynopsisTranslate
  locale: ComputedRef<Locale>
  controller: SynopsisController
  state: Readonly<Ref<SynopsisData>>
  selection: ComputedRef<SynopsisSelection>
}

/** Vue-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (Laden, Filter, Zeilenänderungen, Navigation). */
export function useSynopsis(source: SynopsisSource): UseSynopsis {
  const { t, locale } = useI18n(synopsisMessages, source.locale)
  const controller = createSynopsisController(() => t)
  const state = useStore(controller.store)
  const selection = computed(() => selectSynopsis(state.value, source.inputs(), t))
  watch(() => [source.inputs().comparisonId, source.inputs().port], () => void controller.reload(source.inputs()), { immediate: true })
  watch(() => synopsisBase(state.value, source.inputs()), () => controller.resetOverrides())
  return { t, locale, controller, state, selection }
}
