<script setup lang="ts">
import { watch } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { formatNumber, useI18n, type Locale } from '../i18n'
import TableImport from '../tabular/TableImport.vue'
import type { ImportedColumns } from '../tabular/useTableImport'
import BenfordChart from './BenfordChart.vue'
import BenfordDigits from './BenfordDigits.vue'
import BenfordMetrics from './BenfordMetrics.vue'
import { benfordMessages, type BenfordMessageKey } from './messages'
import { needsShortValues, type AnalyseError } from './model'
import type { BenfordAnalysis, BenfordPort } from './types'
import { useBenford } from './useBenford'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createBenfordRestPort({ baseUrl: '/api/benford' })`. */
  port?: BenfordPort | null
  /** Zu prüfende Beträge; alternativ Datei-Import in der Komponente. */
  values?: readonly (number | null)[]
  locale?: Locale
}>(), { port: null, values: () => [], locale: undefined })

const emit = defineEmits<{ 'analysis-completed': [result: BenfordAnalysis]; error: [message: string] }>()
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const id = useId('fa-benford')
const state = useBenford(() => props.port, () => props.values, {
  analysed: (result) => emit('analysis-completed', result),
  failed: (message) => emit('error', message),
})
const { catalogue, result, busy, failure } = state

watch(() => props.port, () => void state.load(), { immediate: true })
watch(() => props.values, () => state.useValues(null))

function errorKey(error: AnalyseError): BenfordMessageKey {
  return `error${error}`
}

function onImport(columns: ImportedColumns): void {
  state.useValues(columns.values)
}
</script>

<template>
  <div class="fa-benford" :lang="active">
    <p v-if="busy === 'load'" class="fa-benford__muted" role="status">{{ t('loading') }}</p>
    <p v-if="failure" class="fa-benford__failure" role="alert">{{ t('failed', { message: failure }) }}</p>
    <template v-if="catalogue">
      <div class="fa-benford__inputs">
        <section class="fa-benford__card" :aria-labelledby="`${id}-data`">
          <h3 :id="`${id}-data`" class="fa-benford__heading">{{ t('data') }}</h3>
          <p class="fa-benford__muted" data-testid="benford-count">
            {{ state.values.value.length ? t('valuesCount', { count: formatNumber(state.values.value.length, active) }) : t('valuesEmpty') }}
          </p>
          <TableImport mode="values" :locale="locale" @import="onImport" />
        </section>
        <form class="fa-benford__card fa-benford__form" novalidate @submit.prevent="state.analyse">
          <label class="fa-benford__field">
            <span class="fa-benford__label">{{ t('test') }}</span>
            <select v-model="state.test.value" class="fa-benford__select" data-testid="benford-test">
              <option v-for="entry in catalogue.tests" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
            </select>
          </label>
          <fieldset v-if="needsShortValues(catalogue, state.test.value)" class="fa-benford__fieldset">
            <legend class="fa-benford__label">{{ t('shortValues') }}</legend>
            <label v-for="option in catalogue.short_values" :key="option.id" class="fa-benford__radio">
              <input v-model="state.shortValues.value" type="radio" :name="`${id}-short`" :value="option.id" :data-testid="`benford-short-${option.id}`" />
              {{ option.label }}
            </label>
          </fieldset>
          <label class="fa-benford__field">
            <span class="fa-benford__label">{{ t('profile') }}</span>
            <select v-model="state.profileId.value" class="fa-benford__select" data-testid="benford-profile">
              <option :value="null">{{ t('choose') }}</option>
              <option v-for="entry in catalogue.profiles" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
            </select>
          </label>
          <details v-if="state.profile.value" class="fa-benford__source">
            <summary>{{ t('profileSource') }}</summary>
            <p>{{ state.profile.value.source }}</p>
            <p>{{ state.profile.value.note }}</p>
          </details>
          <p v-if="state.error.value" class="fa-benford__error" role="alert">{{ t(errorKey(state.error.value)) }}</p>
          <FaButton variant="primary" type="submit" :loading="busy === 'analyse'" data-testid="benford-analyse">{{ t('analyse') }}</FaButton>
        </form>
      </div>
      <section v-if="result" class="fa-benford__card" :aria-labelledby="`${id}-result`" aria-live="polite">
        <h3 :id="`${id}-result`" class="fa-benford__heading">{{ result.test_label }}</h3>
        <p class="fa-benford__notice">{{ t('notice') }}</p>
        <BenfordMetrics :analysis="result" :profile="state.profile.value" :locale="locale" />
        <BenfordChart :conformity="result.conformity" :test-label="result.test_label" :locale="locale" />
        <BenfordDigits :conformity="result.conformity" :locale="locale" />
      </section>
    </template>
  </div>
</template>

<style>
.fa-benford { display: flex; flex-direction: column; gap: var(--fa-space-4); font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); color: var(--fa-color-text); }
.fa-benford__inputs { display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: var(--fa-space-4); align-items: start; }
.fa-benford__card { display: flex; flex-direction: column; gap: var(--fa-space-3); padding: var(--fa-space-4); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius-lg); background: var(--fa-color-surface); box-shadow: var(--fa-shadow-sm); min-width: 0; }
.fa-benford__heading { margin: 0; font-size: var(--fa-font-size-md); font-weight: 600; }
.fa-benford__field { display: flex; flex-direction: column; gap: var(--fa-space-1); }
.fa-benford__fieldset { display: flex; flex-direction: column; gap: var(--fa-space-1); margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); }
.fa-benford__radio { display: inline-flex; gap: var(--fa-space-2); align-items: center; }
.fa-benford__label { font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-benford__select { min-height: 2.25rem; padding: 0 var(--fa-space-3); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface); color: var(--fa-color-text); font: inherit; }
.fa-benford__select:focus-visible, .fa-benford__radio input:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-benford__muted, .fa-benford__source { margin: 0; color: var(--fa-color-text-muted); font-size: var(--fa-font-size-xs); }
.fa-benford__source p { margin: var(--fa-space-1) 0 0; overflow-wrap: anywhere; }
.fa-benford__error { margin: 0; font-size: var(--fa-font-size-xs); color: var(--fa-color-danger); }
.fa-benford__failure { margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border-radius: var(--fa-radius); background: var(--fa-color-danger-soft); color: var(--fa-color-danger); }
.fa-benford__notice { margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border-left: 3px solid var(--fa-color-accent); background: var(--fa-color-accent-soft); border-radius: var(--fa-radius-sm); }
.fa-benford__metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: var(--fa-space-3); margin: 0; }
.fa-benford__metric { display: flex; flex-direction: column; gap: var(--fa-space-1); padding: var(--fa-space-3); border-radius: var(--fa-radius); background: var(--fa-color-surface-raised); border: 1px solid var(--fa-color-border); }
.fa-benford__metric dt { font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-benford__metric dd { margin: 0; }
.fa-benford__value { font-size: var(--fa-font-size-lg); font-weight: 600; font-variant-numeric: tabular-nums; }
.fa-benford__detail { font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-benford__figure { margin: 0; }
.fa-benford__chart { display: block; width: 100%; height: auto; font: var(--fa-font-size-xs) var(--fa-font-sans); }
.fa-benford__grid line { stroke: var(--fa-color-border); stroke-width: 1; }
.fa-benford__grid text, .fa-benford__axis text { fill: var(--fa-color-text-muted); }
.fa-benford__axis line { stroke: var(--fa-color-border-strong); }
.fa-benford__bar { fill: var(--fa-color-accent); opacity: 0.75; }
.fa-benford__bar--exceeds { fill: var(--fa-color-danger); opacity: 0.9; }
.fa-benford__expected { fill: none; stroke: var(--fa-color-text); stroke-width: 2; stroke-dasharray: 5 3; }
.fa-benford__expected-dot { fill: var(--fa-color-surface); stroke: var(--fa-color-text); stroke-width: 1.5; }
.fa-benford__legend { display: flex; flex-wrap: wrap; gap: var(--fa-space-4); margin-top: var(--fa-space-2); font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-benford__legend span { display: inline-flex; align-items: center; gap: var(--fa-space-1); }
.fa-benford__swatch { display: inline-block; width: 0.9rem; height: 0.6rem; border-radius: 2px; background: var(--fa-color-accent); opacity: 0.75; }
.fa-benford__swatch--exceeds { background: var(--fa-color-danger); opacity: 0.9; }
.fa-benford__swatch--expected { height: 0; border-top: 2px dashed var(--fa-color-text); background: none; opacity: 1; }
.fa-benford__digits summary { cursor: pointer; font-weight: 600; margin-bottom: var(--fa-space-2); }
.fa-benford__flag { color: var(--fa-color-danger); font-weight: 600; }
@media (prefers-reduced-motion: no-preference) { .fa-benford__bar { transition: y var(--fa-transition), height var(--fa-transition); } }
</style>
