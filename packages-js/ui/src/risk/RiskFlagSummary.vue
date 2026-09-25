<script setup lang="ts">
import { computed } from 'vue'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'
import type { TableColumn, TableRow } from '../table'
import RiskFlagState from './RiskFlagState.vue'
import { riskMessages } from './messages'
import type { DatasetFinding } from './types'
import { formatAmount, formatShare, formatValue } from './view/format'
import type { RiskDistributionRow, Totals } from './view/state'

const props = withDefaults(defineProps<{
  rows?: readonly RiskDistributionRow[]
  totals?: Totals | null
  dataset?: readonly DatasetFinding[]
  missingColumns?: Readonly<Record<string, readonly string[]>>
  locale?: Locale
}>(), { rows: () => [], totals: null, dataset: () => [], missingColumns: () => ({}), locale: undefined })

const emit = defineEmits<{ 'code-select': [code: string] }>()
const { t, locale: active } = useI18n(riskMessages, () => props.locale)

const hasVolume = computed(() => props.rows.some((row) => row.volume !== null))
const maxHits = computed(() => Math.max(1, ...props.rows.map((row) => row.hit)))
const columns = computed<TableColumn[]>(() => [
  { key: 'code', label: t('colCode') },
  { key: 'label', label: t('colLabel') },
  { key: 'hit', label: t('colHits'), align: 'end' },
  { key: 'share', label: t('colShare'), align: 'end' },
  { key: 'undetermined', label: t('colUndetermined'), align: 'end' },
  ...(hasVolume.value
    ? [{ key: 'volume', label: t('colVolume'), align: 'end' as const, format: (value: unknown) => formatAmount(typeof value === 'number' ? value : null, active.value) }]
    : []),
])
const tableRows = computed<TableRow[]>(() => props.rows.map((row) => ({ ...row, id: row.code })))

function row(value: TableRow): RiskDistributionRow {
  return value as unknown as RiskDistributionRow
}
</script>

<template>
  <section class="fa-risk-summary" :aria-label="t('summaryTitle')">
    <ul v-if="totals" class="fa-risk-summary__totals">
      <li>{{ t('totalsRecords', { count: totals.records }) }}</li>
      <li><RiskFlagState state="hit" compact :locale="locale" /> {{ t('totalsHits', { count: totals.withHits }) }}</li>
      <li><RiskFlagState state="undetermined" compact :locale="locale" /> {{ t('totalsUndetermined', { count: totals.withUndetermined }) }}</li>
      <li v-if="totals.skippedRules"><RiskFlagState state="skipped" compact :locale="locale" /> {{ t('totalsSkipped', { count: totals.skippedRules }) }}</li>
    </ul>
    <FaTable :columns="columns" :rows="tableRows" row-key="code" :caption="t('summaryCaption', { count: totals?.records ?? 0 })" :locale="locale">
      <template #cell-code="{ row: item }">
        <button type="button" class="fa-risk-summary__code" @click="emit('code-select', row(item).code)">{{ row(item).code }}</button>
      </template>
      <template #cell-label="{ row: item }">
        <span>{{ row(item).label }}</span>
        <span v-if="row(item).skipped" class="fa-risk-summary__skipped">
          <RiskFlagState state="skipped" :locale="locale" /> {{ row(item).skipped }}
        </span>
        <span v-else-if="missingColumns[row(item).code]?.length" class="fa-risk-summary__skipped">
          {{ t('missingColumns', { columns: missingColumns[row(item).code]?.join(', ') ?? '' }) }}
        </span>
      </template>
      <template #cell-hit="{ row: item }">
        <span v-if="row(item).skipped" :aria-label="t('stateSkipped')">–</span>
        <span v-else class="fa-risk-summary__count">
          <span class="fa-risk-summary__bar" aria-hidden="true"><span :style="{ width: `${(row(item).hit / maxHits) * 100}%` }" /></span>
          {{ formatValue(row(item).hit, active, '0') }}
        </span>
      </template>
      <template #cell-share="{ row: item }">{{ row(item).skipped ? '–' : formatShare(row(item).share, active) }}</template>
      <template #cell-undetermined="{ row: item }">
        <span v-if="row(item).skipped">–</span>
        <span v-else-if="row(item).undetermined" class="fa-risk-summary__undetermined">
          <span class="fa-risk-summary__count"><RiskFlagState state="undetermined" compact :locale="locale" /> {{ row(item).undetermined }}</span>
          <small v-for="(count, reason) in row(item).reasons" :key="reason">{{ t('reasonCount', { reason, count }) }}</small>
        </span>
        <span v-else>0</span>
      </template>
    </FaTable>
    <div v-if="dataset.length" class="fa-risk-summary__dataset">
      <h3>{{ t('datasetTitle') }}</h3>
      <p v-for="finding in dataset" :key="finding.code"><strong>{{ finding.code }}</strong> {{ finding.label }} – {{ finding.reason }}</p>
    </div>
  </section>
</template>

<style>
.fa-risk-summary { display: grid; gap: var(--fa-space-3); }
.fa-risk-summary__totals { display: flex; flex-wrap: wrap; gap: var(--fa-space-4); margin: 0; padding: 0; list-style: none; font-size: var(--fa-font-size-sm); color: var(--fa-color-text); }
.fa-risk-summary__totals li { display: inline-flex; align-items: center; gap: var(--fa-space-1); }
.fa-risk-summary__code { padding: 0; border: 0; background: none; color: var(--fa-color-accent); font: 600 var(--fa-font-size-sm) var(--fa-font-mono); cursor: pointer; text-decoration: underline dotted; }
.fa-risk-summary__code:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); border-radius: var(--fa-radius-sm); }
.fa-risk-summary__skipped { display: block; margin-top: var(--fa-space-1); font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-risk-summary__count { display: inline-flex; align-items: center; gap: var(--fa-space-1); white-space: nowrap; }
.fa-risk-summary__bar { display: inline-block; width: 4rem; height: 0.4rem; margin-inline-end: var(--fa-space-2); border-radius: 999px; background: var(--fa-color-surface-sunken); vertical-align: middle; overflow: hidden; }
.fa-risk-summary__bar span { display: block; height: 100%; background: var(--fa-color-danger); }
.fa-risk-summary__undetermined { display: inline-grid; justify-items: end; gap: 2px; }
.fa-risk-summary__undetermined small { font-size: var(--fa-font-size-xs); color: var(--fa-color-warning); }
.fa-risk-summary__dataset h3 { margin: 0 0 var(--fa-space-2); font-size: var(--fa-font-size-md); }
.fa-risk-summary__dataset p { margin: 0; font-size: var(--fa-font-size-sm); }
</style>
