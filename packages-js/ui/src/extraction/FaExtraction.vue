<script setup lang="ts">
import { watch } from 'vue'
import { extractionMessages, type ExtractionPort, type ExtractionRun } from '@flowaudit/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import ExtractionForm from './ExtractionForm.vue'
import ExtractionResult from './ExtractionResult.vue'
import { useExtraction } from './useExtraction'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createExtractionRestPort({ baseUrl: '/api/extraction' })`. */
  port?: ExtractionPort | null
  /** Vorhandenes Ergebnis anzeigen (z. B. aus der Ablage der Anwendung). */
  result?: ExtractionRun | null
  locale?: Locale
}>(), { port: null, result: null, locale: undefined })

const emit = defineEmits<{ 'extraction-completed': [result: ExtractionRun]; error: [message: string] }>()
const { t, locale: active } = useI18n(extractionMessages, () => props.locale)
const id = useId('fa-extraction')
const { controller, state } = useExtraction(() => props.port, {
  completed: (result) => emit('extraction-completed', result),
  failed: (message) => emit('error', message),
})

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => props.result, (result) => controller.showResult(result), { immediate: true })
</script>

<template>
  <div class="fa-extraction" :lang="active" data-testid="extraction">
    <p v-if="!port" class="fa-extraction__muted">{{ t('noPort') }}</p>
    <p v-if="state.busy === 'load'" class="fa-extraction__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-extraction__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="state.catalogue && !state.catalogue.enabled" class="fa-extraction__notice" data-testid="extraction-disabled">{{ t('disabled') }}</p>
    <ExtractionForm v-if="state.catalogue?.enabled" :id="id" :controller="controller" :state="state" :t="t" :locale="active" />
    <ExtractionResult v-if="state.result" :id="id" :result="state.result" :catalogue="state.catalogue" :t="t" :locale="active" />
  </div>
</template>
