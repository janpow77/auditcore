import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'
import type { TableColumn, TableRow } from '../table'
import type { Evaluation, RecordView, RuleView } from './types'
import {
  DEFAULT_FILTER,
  distribution,
  filterRecords,
  flagState,
  recordEntries,
  recordLabel,
  recordRules,
  totals,
  triggeredDataset,
  type RiskDistributionRow,
  type FlagEntry,
  type RiskFilter,
  type Totals,
} from './view/state'

export interface UseRiskFlags {
  filter: Ref<RiskFilter>
  selectedIndex: Ref<number | null>
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
}

const EMPTY: Evaluation = {
  library: '', profile: { id: '', version: '', fingerprint: '', status: '' }, records: [], dataset: [], skipped: {}, summary: [],
}

/** Zustand und abgeleitete Daten der Gesamtansicht; ohne DOM testbar. */
export function useRiskFlags(evaluation: () => Evaluation | null | undefined, recordLabelText: string): UseRiskFlags {
  const current = computed(() => evaluation() ?? EMPTY)
  const filter = ref<RiskFilter>({ ...DEFAULT_FILTER })
  const selectedIndex = ref<number | null>(null)
  const rules = computed(() => recordRules(current.value))
  const records = computed(() => filterRecords(current.value, filter.value))

  const tableColumns = computed<TableColumn[]>(() => [
    { key: 'record', label: recordLabelText, sortable: true },
    ...rules.value.map((rule) => ({ key: rule.code, label: rule.code, sortable: true, align: 'center' as const })),
  ])

  const tableRows = computed<TableRow[]>(() => records.value.map((record) => {
    const row: Record<string, unknown> = { id: record.index, record: recordLabel(record) }
    for (const rule of rules.value) row[rule.code] = flagState(record, rule.code, current.value.skipped)
    return row
  }))

  const selected = computed(() => current.value.records.find((record) => record.index === selectedIndex.value) ?? null)
  const entries = computed(() => (selected.value ? recordEntries(selected.value, rules.value) : []))

  watch(current, () => { selectedIndex.value = null })

  return {
    filter,
    selectedIndex,
    rules,
    rows: computed(() => distribution(current.value)),
    totals: computed(() => totals(current.value)),
    dataset: computed(() => triggeredDataset(current.value)),
    records,
    tableColumns,
    tableRows,
    selected,
    entries,
    select: (index) => { selectedIndex.value = index },
  }
}
