<script setup lang="ts">
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'
import type { TableColumn, TableRow } from '../table'
import RiskFlagState from './RiskFlagState.vue'
import { riskMessages } from './messages'
import type { FlagState } from './view/state'

const props = withDefaults(defineProps<{
  columns?: readonly TableColumn[]
  rows?: readonly TableRow[]
  /** Codes der Regelspalten (Zellen zeigen den Zustand). */
  codes?: readonly string[]
  selected?: number | null
  locale?: Locale
}>(), { columns: () => [], rows: () => [], codes: () => [], selected: null, locale: undefined })

const emit = defineEmits<{ 'record-select': [index: number] }>()
const { t } = useI18n(riskMessages, () => props.locale)

function state(value: unknown): FlagState {
  return typeof value === 'string' && ['hit', 'clear', 'undetermined', 'skipped'].includes(value) ? (value as FlagState) : 'absent'
}

function onRow(row: TableRow): void {
  if (typeof row.id === 'number') emit('record-select', row.id)
}
</script>

<template>
  <div class="fa-risk-table" :data-selected="selected ?? undefined">
    <FaTable
      :columns="columns"
      :rows="rows"
      row-key="id"
      :caption="t('tableCaption')"
      :empty-text="t('noRecords')"
      clickable
      :locale="locale"
      @row-click="onRow"
    >
      <template #cell-record="{ row }">
        <span class="fa-risk-table__record" :aria-current="row.id === selected ? 'true' : undefined">{{ row.record }}</span>
      </template>
      <template v-for="code in codes" :key="code" #[`cell-${code}`]="{ value }">
        <RiskFlagState :state="state(value)" :code="code" compact :locale="locale" />
      </template>
    </FaTable>
  </div>
</template>

<style>
.fa-risk-table .fa-table td { padding-block: var(--fa-space-1); }
.fa-risk-table__record { font-family: var(--fa-font-mono); font-size: var(--fa-font-size-sm); }
.fa-risk-table__record[aria-current='true'] { font-weight: 700; color: var(--fa-color-accent); }
.fa-risk-table__record[aria-current='true']::before { content: '▸ '; }
</style>
