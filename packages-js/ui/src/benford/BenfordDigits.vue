<script setup lang="ts">
import { computed } from 'vue'
import { formatNumber, formatPercent, useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'
import type { TableColumn } from '../table/sort'
import { benfordMessages } from './messages'
import type { Conformity } from './types'

const props = withDefaults(defineProps<{ conformity: Conformity; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const share = (value: unknown): string => (typeof value === 'number' ? formatPercent(value, active.value, 2) : '')
const signedShare = (value: unknown): string =>
  typeof value === 'number' ? `${value > 0 ? '+' : ''}${formatPercent(value, active.value, 2)}` : ''
const decimal = (value: unknown): string =>
  typeof value === 'number' ? formatNumber(value, active.value, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : ''

const columns = computed<TableColumn[]>(() => [
  { key: 'digit', label: t('colDigit'), align: 'end', sortable: true },
  { key: 'observed_count', label: t('colCount'), align: 'end', sortable: true },
  { key: 'observed_share', label: t('colObserved'), align: 'end', sortable: true, format: share },
  { key: 'expected_share', label: t('colExpected'), align: 'end', format: share },
  { key: 'deviation', label: t('colDeviation'), align: 'end', sortable: true, format: signedShare },
  { key: 'z', label: t('colZ'), align: 'end', sortable: true, format: decimal },
  { key: 'exceeds', label: t('colExceeds'), align: 'center', format: (value) => (value === true ? t('yes') : '') },
])
const rows = computed(() => props.conformity.rows.map((row) => ({ id: row.digit, ...row })))
</script>

<template>
  <details class="fa-benford__digits" :open="conformity.rows.length <= 10">
    <summary>{{ t('table') }}</summary>
    <FaTable :columns="columns" :rows="rows" :caption="t('table')" :locale="locale" data-testid="benford-table">
      <template #cell-exceeds="{ value }">
        <span v-if="value === true" class="fa-benford__flag">{{ t('yes') }}</span>
      </template>
    </FaTable>
  </details>
</template>
