<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  extrapolationFormMessage,
  extrapolationInputNumber,
  extrapolationMessages,
  type EvaluationResult,
  type ExtrapolationExportFormat,
  type ExtrapolationPort,
  type ResidualResult,
  type StratumInput,
  type UnitInput,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import { saveFile } from '../rest/download'
import ExtrapolationResidual from './ExtrapolationResidual.vue'
import ExtrapolationResult from './ExtrapolationResult.vue'
import ExtrapolationSettings from './ExtrapolationSettings.vue'
import ExtrapolationStrata from './ExtrapolationStrata.vue'
import ExtrapolationUnits from './ExtrapolationUnits.vue'
import { useExtrapolation } from './useExtrapolation'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createExtrapolationRestPort({ baseUrl: '/api/extrapolation' })`. */
  port?: ExtrapolationPort | null
  /** Schichten der Grundgesamtheit (vorbelegt, in der Komponente bearbeitbar). */
  strata?: readonly StratumInput[]
  /** Geprüfte Einheiten der Stichprobe mit ihren Fehlern. */
  units?: readonly UnitInput[]
  locale?: Locale
}>(), { port: null, strata: () => [], units: () => [], locale: undefined })

const emit = defineEmits<{
  'evaluation-completed': [result: EvaluationResult]
  'residual-computed': [result: ResidualResult]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(extrapolationMessages, () => props.locale)
const { controller, state, method } = useExtrapolation(
  () => props.port,
  () => props.strata,
  () => props.units,
  (value) => extrapolationInputNumber(active.value)(value),
  {
    evaluated: (result) => emit('evaluation-completed', result),
    residualComputed: (result) => emit('residual-computed', result),
    failed: (message) => emit('error', message),
  },
)
const formMessage = computed(() => extrapolationFormMessage(state.value.formError, state.value.issues, t))

watch(() => props.port, () => void controller.load(), { immediate: true })
watch([() => props.strata, () => props.units], () => controller.applyInputs())

async function onExport(format: ExtrapolationExportFormat): Promise<void> {
  const file = await controller.exportEvaluation(format)
  if (file) saveFile(file)
}
</script>

<template>
  <div class="fa-extrapolation" :lang="active">
    <p v-if="state.busy === 'load'" class="fa-extrapolation__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-extrapolation__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <template v-if="state.catalogue">
      <ExtrapolationSettings :controller="controller" :state="state" :method="method" :locale="locale" />
      <ExtrapolationStrata :controller="controller" :state="state" :locale="locale" />
      <ExtrapolationUnits :controller="controller" :state="state" :locale="locale" />
      <div class="fa-extrapolation__actions">
        <FaButton variant="primary" :loading="state.busy === 'evaluate'" data-testid="extrapolation-evaluate" @click="controller.evaluate">{{ t('evaluate') }}</FaButton>
        <p v-if="formMessage" class="fa-extrapolation__error" role="alert" data-testid="extrapolation-form-error">{{ formMessage }}</p>
      </div>
      <template v-if="state.result">
        <ExtrapolationResult :result="state.result" :catalogue="state.catalogue" :busy="state.busy === 'export'" :locale="locale" @export="onExport" />
        <ExtrapolationResidual :controller="controller" :state="state" :locale="locale" />
      </template>
    </template>
  </div>
</template>
