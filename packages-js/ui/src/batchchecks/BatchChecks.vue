<!-- Bestandsprüfung über viele Belege (Vertrag documents_batch_checks/1); Logik im Kern (createBatchchecksController). -->
<script setup lang="ts">
import { watch } from 'vue'
import { batchchecksMessages, type BatchchecksAnswer, type BatchchecksPort } from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import BatchChecksInput from './BatchChecksInput.vue'
import BatchChecksResult from './BatchChecksResult.vue'
import { useBatchChecks } from './useBatchChecks'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createBatchchecksRestPort({ baseUrl: '/api/batch-checks' })`. */
  port?: BatchchecksPort | null
  /** Vorhandenes Ergebnis anzeigen (z. B. aus der Ablage der Anwendung). */
  result?: BatchchecksAnswer | null
  locale?: Locale
}>(), { port: null, result: null, locale: undefined })

const emit = defineEmits<{ 'checks-completed': [answer: BatchchecksAnswer]; error: [message: string] }>()
const { t, locale: active } = useI18n(batchchecksMessages, () => props.locale)
const id = useId('fa-batchchecks')
const { controller, state, table } = useBatchChecks(() => props.port, {
  completed: (answer) => emit('checks-completed', answer),
  failed: (message) => emit('error', message),
})

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => props.result, (result) => controller.showAnswer(result), { immediate: true })
</script>

<template>
  <section class="fa-batchchecks" :lang="active" :aria-label="t('title')" data-testid="batchchecks">
    <p v-if="!port" class="fa-batchchecks__muted">{{ t('noPort') }}</p>
    <p v-if="state.busy === 'load'" class="fa-batchchecks__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-batchchecks__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <BatchChecksInput v-if="state.catalogue" :id="id" :controller="controller" :state="state" :table="table" :t="t" />
    <BatchChecksResult v-if="state.answer" :id="id" :controller="controller" :state="state" :answer="state.answer" :t="t" :locale="active" />
  </section>
</template>
