<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  isStratifiedPopulation,
  samplingInputNumber,
  samplingMessages,
  type ExportFormat,
  type PopulationItem,
  type SamplingPort,
  type SelectionResult,
  type SizeResult,
} from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'
import { saveFile } from '../rest/download'
import SamplingDraw from './SamplingDraw.vue'
import SamplingMethod from './SamplingMethod.vue'
import SamplingParameters from './SamplingParameters.vue'
import SamplingPopulation from './SamplingPopulation.vue'
import SamplingResult from './SamplingResult.vue'
import SamplingSelectionResult from './SamplingSelectionResult.vue'
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
const { controller, state, profile, population } = useSampling(
  () => props.port,
  () => props.items,
  (value) => samplingInputNumber(active.value)(value),
  {
    sizeCalculated: (result) => emit('size-calculated', result),
    selectionDrawn: (result) => emit('selection-drawn', result),
    failed: (message) => emit('error', message),
  },
)
const stratified = computed(() => isStratifiedPopulation(population.value))

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => props.items, () => controller.usePopulation(null))

async function onExport(format: ExportFormat): Promise<void> {
  const file = await controller.exportSelection(format)
  if (file) saveFile(file)
}
</script>

<template>
  <div class="fa-sampling" :lang="active">
    <p v-if="state.busy === 'load'" class="fa-sampling__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-sampling__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <template v-if="state.catalogue">
      <div class="fa-sampling__grid">
        <SamplingMethod :model-value="state.methodId" :catalogue="state.catalogue" :profile="profile" :locale="locale" @update:model-value="controller.selectMethod" />
        <SamplingParameters
          v-if="profile"
          :texts="state.texts"
          :confidence="state.confidence"
          :profile="profile"
          :errors="state.fieldErrors"
          :busy="state.busy === 'size'"
          :has-population="population.length > 0"
          :locale="locale"
          @update:texts="controller.setTexts"
          @update:confidence="controller.setConfidence"
          @calculate="controller.calculate"
          @suggest="controller.applySuggestions"
        />
        <SamplingResult v-if="state.size" :result="state.size" :locale="locale" />
      </div>
      <SamplingPopulation :items="population" :locale="locale" @import="controller.usePopulation" />
      <section v-if="profile" class="fa-sampling__card">
        <SamplingDraw
          :sample-size="state.sampleSize"
          :seed="state.seed"
          :variant="state.variant"
          :allocation="state.allocation"
          :profile="profile"
          :variants="state.catalogue.selection_variants"
          :allocations="state.catalogue.allocation_methods"
          :stratified="stratified"
          :error="state.selectionError"
          :busy="state.busy === 'selection'"
          :can-redraw="state.selection !== null"
          :locale="locale"
          @update:sample-size="controller.setSampleSize"
          @update:seed="controller.setSeed"
          @update:variant="controller.setVariant"
          @update:allocation="controller.setAllocation"
          @draw="controller.draw"
        />
        <SamplingSelectionResult v-if="state.selection" :result="state.selection" :busy="state.busy === 'export'" :locale="locale" @export="onExport" />
      </section>
    </template>
  </div>
</template>
