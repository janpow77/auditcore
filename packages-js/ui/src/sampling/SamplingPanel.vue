<script setup lang="ts">
import { computed, watch } from 'vue'
import { formatNumber, useI18n, type Locale } from '../i18n'
import { saveFile } from '../rest/download'
import { samplingMessages } from './messages'
import { strataOf } from './model'
import SamplingDraw from './SamplingDraw.vue'
import SamplingMethod from './SamplingMethod.vue'
import SamplingParameters from './SamplingParameters.vue'
import SamplingPopulation from './SamplingPopulation.vue'
import SamplingResult from './SamplingResult.vue'
import SamplingSelectionResult from './SamplingSelectionResult.vue'
import type { ExportFormat, PopulationItem, SamplingPort, SelectionResult, SizeResult } from './types'
import { useSampling } from './useSampling'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createSamplingRestPort({ baseUrl: '/api/sampling' })`. */
  port?: SamplingPort | null
  /** Grundgesamtheit; alternativ Datei-Import in der Komponente. */
  items?: readonly PopulationItem[]
  locale?: Locale
}>(), { port: null, items: () => [], locale: undefined })

const emit = defineEmits<{
  'size-calculated': [result: SizeResult]
  'selection-drawn': [result: SelectionResult]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const state = useSampling(
  () => props.port,
  () => props.items,
  (value) => formatNumber(value, active.value, { maximumFractionDigits: 6, useGrouping: false }),
  {
    sizeCalculated: (result) => emit('size-calculated', result),
    selectionDrawn: (result) => emit('selection-drawn', result),
    failed: (message) => emit('error', message),
  },
)
const { catalogue, profile, size, selection, busy, failure } = state
const stratified = computed(() => strataOf(state.population.value).length > 0)

watch(() => props.port, () => void state.load(), { immediate: true })
watch(() => props.items, () => state.usePopulation(null))

async function onExport(format: ExportFormat): Promise<void> {
  const file = await state.exportSelection(format)
  if (file) saveFile(file)
}
</script>

<template>
  <div class="fa-sampling" :lang="active">
    <p v-if="busy === 'load'" class="fa-sampling__muted" role="status">{{ t('loading') }}</p>
    <p v-if="failure" class="fa-sampling__failure" role="alert">{{ t('failed', { message: failure }) }}</p>
    <template v-if="catalogue">
      <div class="fa-sampling__grid">
        <SamplingMethod :model-value="state.methodId.value" :catalogue="catalogue" :profile="profile" :locale="locale" @update:model-value="state.selectMethod" />
        <SamplingParameters
          v-if="profile"
          v-model:texts="state.texts.value"
          v-model:confidence="state.confidence.value"
          :profile="profile"
          :errors="state.fieldErrors.value"
          :busy="busy === 'size'"
          :has-population="state.population.value.length > 0"
          :locale="locale"
          @calculate="state.calculate"
          @suggest="state.applySuggestions"
        />
        <SamplingResult v-if="size" :result="size" :locale="locale" />
      </div>
      <SamplingPopulation :items="state.population.value" :locale="locale" @import="state.usePopulation" />
      <section v-if="profile" class="fa-sampling__card">
        <SamplingDraw
          v-model:sample-size="state.sampleSize.value"
          v-model:seed="state.seed.value"
          v-model:variant="state.variant.value"
          v-model:allocation="state.allocation.value"
          :profile="profile"
          :variants="catalogue.selection_variants"
          :allocations="catalogue.allocation_methods"
          :stratified="stratified"
          :error="state.selectionError.value"
          :busy="busy === 'selection'"
          :can-redraw="selection !== null"
          :locale="locale"
          @draw="state.draw"
        />
        <SamplingSelectionResult v-if="selection" :result="selection" :busy="busy === 'export'" :locale="locale" @export="onExport" />
      </section>
    </template>
  </div>
</template>

<style>
.fa-sampling { display: flex; flex-direction: column; gap: var(--fa-space-4); font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); color: var(--fa-color-text); }
.fa-sampling__grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: var(--fa-space-4); align-items: start; }
.fa-sampling__card { display: flex; flex-direction: column; gap: var(--fa-space-3); padding: var(--fa-space-4); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius-lg); background: var(--fa-color-surface); box-shadow: var(--fa-shadow-sm); min-width: 0; }
.fa-sampling__card--result { border-color: var(--fa-color-accent); grid-column: 1 / -1; }
.fa-sampling__draw-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--fa-space-3); align-items: start; }
.fa-sampling__heading { margin: 0; font-size: var(--fa-font-size-md); font-weight: 600; }
.fa-sampling__form { display: flex; flex-direction: column; gap: var(--fa-space-3); }
.fa-sampling__field { display: flex; flex-direction: column; gap: var(--fa-space-1); }
.fa-sampling__label { font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-sampling__input, .fa-sampling__select { min-height: 2.25rem; width: 100%; box-sizing: border-box; padding: 0 var(--fa-space-3); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface); color: var(--fa-color-text); font: inherit; }
.fa-sampling__input { text-align: end; font-variant-numeric: tabular-nums; }
.fa-sampling__input--mono { font-family: var(--fa-font-mono); text-align: start; }
.fa-sampling__input:focus-visible, .fa-sampling__select:focus-visible { outline: none; border-color: var(--fa-color-accent); box-shadow: var(--fa-focus-ring); }
.fa-sampling__input-wrap { display: flex; align-items: center; gap: var(--fa-space-2); }
.fa-sampling__unit { min-width: 1rem; color: var(--fa-color-text-muted); }
.fa-sampling__field--error .fa-sampling__input, .fa-sampling__field--error .fa-sampling__select { border-color: var(--fa-color-danger); }
.fa-sampling__error { margin: 0; font-size: var(--fa-font-size-xs); color: var(--fa-color-danger); }
.fa-sampling__hint, .fa-sampling__muted { margin: 0; color: var(--fa-color-text-muted); font-size: var(--fa-font-size-xs); }
.fa-sampling__actions { display: flex; flex-wrap: wrap; gap: var(--fa-space-2); }
.fa-sampling__profile p { margin: 0 0 var(--fa-space-2); }
.fa-sampling__formula { font-family: var(--fa-font-mono); font-size: var(--fa-font-size-xs); }
.fa-sampling__id { font-family: var(--fa-font-mono); font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-sampling__note { color: var(--fa-color-text-muted); }
.fa-sampling__source code { display: block; margin-top: var(--fa-space-1); font-size: var(--fa-font-size-xs); overflow-wrap: anywhere; }
.fa-sampling__size { margin: 0; font-size: 1.75rem; font-weight: 600; font-variant-numeric: tabular-nums; color: var(--fa-color-accent); }
.fa-sampling__warnings { margin: 0; padding: var(--fa-space-2) var(--fa-space-3) var(--fa-space-2) var(--fa-space-5); border-radius: var(--fa-radius); background: var(--fa-color-warning-soft); color: var(--fa-color-warning); }
.fa-sampling__failure { margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border-radius: var(--fa-radius); background: var(--fa-color-danger-soft); color: var(--fa-color-danger); }
.fa-sampling__selection { display: flex; flex-direction: column; gap: var(--fa-space-3); border-top: 1px solid var(--fa-color-border); padding-top: var(--fa-space-3); }
.fa-sampling__seed { display: flex; flex-wrap: wrap; gap: var(--fa-space-2); align-items: center; margin: 0; }
</style>
