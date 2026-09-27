<!-- Schichten des Planers (geschichtete Verfahren); Zustand im Kern. -->
<script setup lang="ts">
import { computed } from 'vue'
import { samplesizeMessages, samplesizeStrataColumns, type SamplesizeController, type SamplesizeData, type StratumColumn } from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{
  controller: SamplesizeController
  state: SamplesizeData
  locale?: Locale
}>(), { locale: undefined })
const { t } = useI18n(samplesizeMessages, () => props.locale)
const columns = computed(() => samplesizeStrataColumns(props.state, t))
const text = (key: StratumColumn, index: number): string => {
  const row = props.state.form.strata[index]
  return row && key !== 'exhaustive' ? row[key] : ''
}
const change = (key: StratumColumn, index: number, event: Event): void => {
  const target = event.target as HTMLInputElement
  props.controller.setStratum(index, key === 'exhaustive' ? { exhaustive: target.checked } : { [key]: target.value })
}
</script>

<template>
  <fieldset class="fa-samplesize__strata">
    <legend class="fa-samplesize__label">{{ t('strata') }}</legend>
    <table class="fa-samplesize__table" data-testid="samplesize-strata">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key" scope="col">{{ column.label }}</th>
          <td />
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in state.form.strata" :key="index">
          <td v-for="column in columns" :key="column.key">
            <input v-if="column.key === 'exhaustive'" type="checkbox" :checked="row.exhaustive" :aria-label="t('stratumRow', { column: column.label, row: index + 1 })" @change="change(column.key, index, $event)" />
            <input v-else class="fa-samplesize__input" :inputmode="column.key === 'name' ? undefined : 'decimal'" :value="text(column.key, index)" :aria-label="t('stratumRow', { column: column.label, row: index + 1 })" @input="change(column.key, index, $event)" />
          </td>
          <td>
            <button type="button" class="fa-samplesize__remove" :aria-label="t('removeStratum', { row: index + 1 })" @click="controller.removeStratum(index)">×</button>
          </td>
        </tr>
      </tbody>
    </table>
    <button type="button" class="fa-samplesize__add" @click="controller.addStratum()">{{ t('addStratum') }}</button>
  </fieldset>
</template>
