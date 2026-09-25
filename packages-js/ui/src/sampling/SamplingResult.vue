<script setup lang="ts">
import { computed } from 'vue'
import { useId } from '../composables/useId'
import { formatNumber, useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'
import type { TableColumn } from '../table/sort'
import { samplingMessages } from './messages'
import type { SizeResult } from './types'

const props = withDefaults(defineProps<{ result: SizeResult; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-result')
const number = (value: unknown): string =>
  typeof value === 'number' ? formatNumber(value, active.value, { maximumFractionDigits: 4 }) : ''

const columns = computed<TableColumn[]>(() => [
  { key: 'label', label: t('step') },
  { key: 'formula', label: t('stepFormula') },
  { key: 'value', label: t('stepValue'), align: 'end', format: number },
])
const rows = computed(() => props.result.derivation.map((step, index) => ({ id: index, ...step })))
</script>

<template>
  <section class="fa-sampling__card fa-sampling__card--result" :aria-labelledby="`${id}-title`" aria-live="polite">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('result') }}</h3>
    <p class="fa-sampling__size" data-testid="sampling-size">{{ t('resultSummary', { size: formatNumber(result.sample_size, active) }) }}</p>
    <p v-if="result.kind === 'mus'" class="fa-sampling__muted">
      {{ t('interval', { interval: formatNumber(result.interval, active, { maximumFractionDigits: 2 }) }) }}
    </p>
    <ul v-if="result.warnings.length" class="fa-sampling__warnings">
      <li v-for="warning in result.warnings" :key="warning">{{ warning }}</li>
    </ul>
    <FaTable v-if="rows.length" :columns="columns" :rows="rows" :caption="t('derivation')" :locale="locale" />
  </section>
</template>
