import { computed, watch, type ComputedRef, type Ref, type WritableComputedRef } from 'vue'
import {
  createRiskController,
  selectRisk,
  type Evaluation,
  type FlagEntry,
  type RecordView,
  type RiskController,
  type RiskDistributionRow,
  type RiskFilter,
  type RuleView,
  type Totals,
} from '@auditcore/ui-core'
import type { TableColumn, TableRow } from '../table'
import { useStore } from '../composables/useStore'

export interface UseRiskFlags {
  filter: WritableComputedRef<RiskFilter>
  selectedIndex: Readonly<Ref<number | null>>
  rules: ComputedRef<RuleView[]>
  rows: ComputedRef<RiskDistributionRow[]>
  totals: ComputedRef<Totals>
  dataset: ComputedRef<Evaluation['dataset']>
  records: ComputedRef<RecordView[]>
  tableColumns: ComputedRef<TableColumn[]>
  tableRows: ComputedRef<TableRow[]>
  selected: ComputedRef<RecordView | null>
  entries: ComputedRef<FlagEntry[]>
  select: (index: number | null) => void
  controller: RiskController
}

/** Vue-Anbindung des Zustandsautomaten aus `@auditcore/ui-core` (Filter, Auswahl, abgeleitete Daten). */
export function useRiskFlags(evaluation: () => Evaluation | null | undefined, recordLabelText: string): UseRiskFlags {
  const controller = createRiskController()
  const state = useStore(controller.store)
  const selection = computed(() => selectRisk(state.value, evaluation(), recordLabelText))
  watch(evaluation, () => controller.resetSelection())
  const pick = <K extends keyof ReturnType<typeof selectRisk>>(key: K) => computed(() => selection.value[key])
  return {
    filter: computed({ get: () => state.value.filter, set: (value) => controller.setFilter(value) }),
    selectedIndex: computed(() => state.value.selectedIndex),
    rules: pick('rules'),
    rows: pick('rows'),
    totals: pick('totals'),
    dataset: pick('dataset'),
    records: pick('records'),
    tableColumns: pick('tableColumns'),
    tableRows: pick('tableRows'),
    selected: pick('selected'),
    entries: pick('entries'),
    select: controller.select,
    controller,
  }
}
