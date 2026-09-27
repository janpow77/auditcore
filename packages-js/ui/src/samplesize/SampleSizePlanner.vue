<!-- SampleSizePlanner: Stichprobenumfang nach KOM-Leitfaden planen; Logik im Kern (createSamplesizeController). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import { createSamplesizeController, hasFiniteCorrection, hasStrata, samplesizeFields, samplesizeMessages, samplesizeMethod, type SampleSizePlan, type SampleSizeRequest, type SamplesizePort } from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'
import SampleSizeResult from './SampleSizeResult.vue'
import SampleSizeStrata from './SampleSizeStrata.vue'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createSamplesizeRestPort({ baseUrl: '/api/sampling' })`. */
  port?: SamplesizePort | null
  /** Vorbelegung des Formulars (Anfrage des Vertrags `auditcore_sampling.guidance/1`). */
  request?: SampleSizeRequest | null
  locale?: Locale
}>(), { port: null, request: null, locale: undefined })

const emit = defineEmits<{
  'plan-calculated': [plan: SampleSizePlan]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(samplesizeMessages, () => props.locale)
const controller = createSamplesizeController({
  port: () => props.port,
  request: () => props.request,
  callbacks: () => ({
    planned: (plan) => emit('plan-calculated', plan),
    failed: (message) => emit('error', message),
  }),
})
const state = useStore(controller.store)
const method = computed(() => samplesizeMethod(state.value))
const fields = computed(() => samplesizeFields(state.value, t, active.value))
const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value
const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked

watch(() => [props.port, props.request], () => void controller.load(), { immediate: true })
</script>

<template>
  <section class="fa-samplesize" :lang="active" :aria-label="t('title')">
    <p v-if="state.busy" class="fa-samplesize__muted" role="status">{{ t(state.busy === 'load' ? 'loading' : 'calculating') }}</p>
    <p v-if="state.error" class="fa-samplesize__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <form v-if="state.catalogue" class="fa-samplesize__form" novalidate @submit.prevent="controller.calculate()">
      <label class="fa-samplesize__field">
        <span class="fa-samplesize__label">{{ t('method') }}</span>
        <select class="fa-samplesize__select" :value="state.form.methodId" data-testid="samplesize-method" @change="controller.selectMethod(value($event))">
          <option value="">{{ t('choose') }}</option>
          <option v-for="entry in state.catalogue.methods" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
        </select>
      </label>
      <details v-if="method" class="fa-samplesize__source">
        <summary>{{ t('source') }}</summary>
        <p>{{ state.catalogue.status_label }} · {{ method.source }}</p>
        <code>{{ method.formula }}</code>
      </details>
      <div v-if="fields.length" class="fa-samplesize__fields">
        <label v-for="field in fields" :key="field.key" class="fa-samplesize__field">
          <span class="fa-samplesize__label">{{ field.label }}</span>
          <select v-if="field.kind === 'choice'" class="fa-samplesize__select" :value="field.value" :aria-invalid="field.issue ? 'true' : undefined" :data-testid="`samplesize-${field.key}`" @change="controller.setValue(field.key, value($event))">
            <option v-if="field.key !== 'assurance_level'" value="">{{ t('choose') }}</option>
            <option v-for="option in field.options" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
          <input v-else class="fa-samplesize__input" :inputmode="field.inputMode" :value="field.value" :aria-invalid="field.issue ? 'true' : undefined" :data-testid="`samplesize-${field.key}`" @input="controller.setValue(field.key, value($event))" />
          <span v-if="field.issue" class="fa-samplesize__error">{{ field.issue }}</span>
        </label>
      </div>
      <label v-if="hasFiniteCorrection(method)" class="fa-samplesize__check">
        <input type="checkbox" :checked="state.form.finiteCorrection" data-testid="samplesize-fpc" @change="controller.setFiniteCorrection(checked($event))" />
        <span>{{ t('finite_population_correction') }}</span>
      </label>
      <SampleSizeStrata v-if="hasStrata(method)" :controller="controller" :state="state" :locale="active" />
      <button v-if="method" type="submit" class="fa-samplesize__submit" data-testid="samplesize-calculate" :disabled="state.busy !== null">{{ t('calculate') }}</button>
    </form>
    <SampleSizeResult v-if="state.plan" :plan="state.plan" :locale="active" />
  </section>
</template>
