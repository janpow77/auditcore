<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import { formatNumber, useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'
import type { TableColumn } from '../table/sort'
import { samplingMessages } from './messages'
import type { ExportFormat, SelectionResult } from './types'

const props = withDefaults(defineProps<{ result: SelectionResult; busy?: boolean; locale?: Locale }>(), {
  busy: false,
  locale: undefined,
})
const emit = defineEmits<{ export: [format: ExportFormat] }>()
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const amount = (value: unknown): string =>
  typeof value === 'number' ? formatNumber(value, active.value, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : ''
const plain = (value: unknown): string => (value === null || value === undefined ? '' : String(value))

const stratified = computed(() => props.result.strata.some((stratum) => stratum.stratum !== null))
const columns = computed<TableColumn[]>(() => [
  { key: 'order', label: t('colOrder'), align: 'end', sortable: true },
  { key: 'position', label: t('colPosition'), align: 'end', sortable: true },
  { key: 'id', label: t('colId'), sortable: true },
  { key: 'value', label: t('colValue'), align: 'end', sortable: true, format: amount },
  ...(stratified.value ? [{ key: 'stratum', label: t('colStratum'), sortable: true, format: plain }] : []),
  ...(props.result.method === 'mus' ? [{ key: 'hits', label: t('colHits'), align: 'end' as const }] : []),
])
const strataColumns = computed<TableColumn[]>(() => [
  { key: 'stratum', label: t('stratum'), format: (value) => (value === null ? t('noStratum') : String(value)) },
  { key: 'population', label: t('stratumPopulation'), align: 'end' },
  { key: 'sample_size', label: t('stratumSample'), align: 'end' },
  ...(props.result.method === 'mus'
    ? [
        { key: 'interval', label: t('stratumInterval'), align: 'end' as const, format: amount },
        { key: 'start', label: t('stratumStart'), align: 'end' as const, format: amount },
      ]
    : []),
])
const strataRows = computed(() => props.result.strata.map((stratum, index) => ({ id: index, ...stratum })))
const rows = computed(() => props.result.rows.map((row) => ({ ...row })))
const excluded = computed(() =>
  props.result.strata.flatMap((stratum) => [
    ...(stratum.excluded_negative?.length ? [t('excludedNegative', { ids: stratum.excluded_negative.join(', ') })] : []),
    ...(stratum.excluded_zero_or_missing?.length ? [t('excludedZero', { ids: stratum.excluded_zero_or_missing.join(', ') })] : []),
  ]),
)
</script>

<template>
  <div class="fa-sampling__selection" aria-live="polite">
    <p class="fa-sampling__seed" data-testid="sampling-seed-used">
      <FaBadge tone="accent">{{ t('seedUsed', { seed: result.seed }) }}</FaBadge>
      <span class="fa-sampling__muted">{{ result.seed_generated ? t('seedGenerated') : t('seedGiven') }}</span>
      <span>{{ t('selectedSummary', { selected: formatNumber(result.selected, active), population: formatNumber(result.population, active) }) }}</span>
    </p>
    <p class="fa-sampling__hint">{{ t('reproducible', { hash: result.items_sha256.slice(0, 12) }) }}</p>
    <FaTable :columns="strataColumns" :rows="strataRows" :caption="t('allocationTable')" :locale="locale" data-testid="sampling-strata" />
    <ul v-if="excluded.length" class="fa-sampling__warnings">
      <li v-for="line in excluded" :key="line">{{ line }}</li>
    </ul>
    <FaTable :columns="columns" :rows="rows" row-key="order" :caption="t('selection')" :locale="locale" data-testid="sampling-rows" />
    <div class="fa-sampling__actions">
      <FaButton :loading="busy" data-testid="sampling-export-csv" @click="emit('export', 'csv')">{{ t('exportCsv') }}</FaButton>
      <FaButton :disabled="busy" data-testid="sampling-export-json" @click="emit('export', 'json')">{{ t('exportJson') }}</FaButton>
    </div>
  </div>
</template>
