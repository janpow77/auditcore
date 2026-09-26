// Vue-Anbindung des Zustandsautomaten der Screening-Trefferprüfung aus `@auditcore/ui-core`.

import { computed, type ComputedRef } from 'vue'
import {
  createScreeningController,
  selectScreening,
  type ReviewEvents,
  type ScreeningController,
  type ScreeningData,
  type ScreeningPort,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { ReviewEvents, ScreeningError } from '@auditcore/ui-core'

type Field<K extends keyof ScreeningData> = ComputedRef<ScreeningData[K]>

export interface ScreeningReviewState extends Omit<ScreeningController, 'store'> {
  controller: ScreeningController
  settings: Field<'settings'>
  sources: Field<'sources'>
  runs: Field<'runs'>
  run: Field<'run'>
  log: Field<'log'>
  filter: Field<'filter'>
  busy: Field<'busy'>
  error: Field<'error'>
  selectedHitId: Field<'selectedHitId'>
  selected: ComputedRef<ReturnType<typeof selectScreening>['selected']>
  visibleSubjects: ComputedRef<ReturnType<typeof selectScreening>['visibleSubjects']>
}

/** Stand, Auswahl und Aktionen der Trefferprüfung; die Logik liegt im Kern (`createScreeningController`). */
export function useScreeningReview(port: () => ScreeningPort | null, events: ReviewEvents = {}): ScreeningReviewState {
  const controller = createScreeningController(port, () => events)
  const state = useStore(controller.store)
  const selection = computed(() => selectScreening(state.value))
  const field = <K extends keyof ScreeningData>(key: K): Field<K> => computed(() => state.value[key])
  const { store: _store, ...actions } = controller
  return {
    ...actions,
    controller,
    settings: field('settings'),
    sources: field('sources'),
    runs: field('runs'),
    run: field('run'),
    log: field('log'),
    filter: field('filter'),
    busy: field('busy'),
    error: field('error'),
    selectedHitId: field('selectedHitId'),
    selected: computed(() => selection.value.selected),
    visibleSubjects: computed(() => selection.value.visibleSubjects),
  }
}
