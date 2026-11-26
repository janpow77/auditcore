<!-- PDF schwärzen: Kriterien, Prüfansicht mit Seitenbild, nachgeprüftes Ergebnis; Logik im Kern (createRedactionController). -->
<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { focusRedactionHeading, redactionMessages, redactionStep, type RedactionPlan, type RedactionPort, type RedactionResult, type RedactionUrls } from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import RedactionForm from './RedactionForm.vue'
import RedactionResultView from './RedactionResult.vue'
import RedactionReview from './RedactionReview.vue'
import { useRedaction } from './useRedaction'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createRedactionRestPort({ baseUrl: '/api/redaction' })`. */
  port?: RedactionPort | null
  locale?: Locale
  /** Objekt-URLs für Seitenbild und Download (Standard: `URL.createObjectURL`). */
  urls?: RedactionUrls
  /** Von der Anwendung bereitgestellte PDF; das Dateifeld entfällt. */
  file?: Blob | null
  /** Dateiname zu `file` (Standard: Name der Datei oder `dokument.pdf`). */
  filename?: string
  /** Startwerte der eigenen Begriffe (änderbar). */
  terms?: readonly string[]
  /** Startwerte der Muster (Kennungen aus dem Katalog, änderbar). */
  patterns?: readonly string[]
}>(), { port: null, locale: undefined, urls: undefined, file: null, filename: undefined, terms: undefined, patterns: undefined })

const emit = defineEmits<{
  'redaction-planned': [plan: RedactionPlan]
  'redaction-completed': [result: RedactionResult]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(redactionMessages, () => props.locale)
const id = useId('fa-redaction')
const { controller, state } = useRedaction(() => props.port, {
  planned: (plan) => emit('redaction-planned', plan),
  completed: (result) => emit('redaction-completed', result),
  failed: (message) => emit('error', message),
}, props.urls)
const step = computed(() => redactionStep(state.value))
const root = ref<HTMLElement | null>(null)

// Schrittwechsel: Fokus auf die neue Überschrift, damit er nicht auf <body> fällt.
watch(step, async () => {
  await nextTick()
  focusRedactionHeading(root.value)
})

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => [props.file, props.filename] as const, ([file, filename]) => controller.provideFile(file ?? null, filename), { immediate: true })
// Vorgaben nur bei geändertem Inhalt übernehmen, nicht bei jedem neuen Array.
watch(
  () => JSON.stringify([props.terms ?? null, props.patterns ?? null]),
  (key) => {
    const [terms, patterns] = JSON.parse(key) as [string[] | null, string[] | null]
    if (terms || patterns) controller.presetCriteria({ terms: terms ?? undefined, patterns: patterns ?? undefined })
  },
  { immediate: true },
)
</script>

<template>
  <div ref="root" class="fa-redaction" :lang="active" data-testid="redaction">
    <p v-if="!port" class="fa-redaction__muted">{{ t('noPort') }}</p>
    <p v-if="state.busy === 'load'" class="fa-redaction__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-redaction__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <RedactionForm v-if="state.catalogue && step === 'form'" :id="id" :controller="controller" :state="state" :t="t" :locale="active" />
    <RedactionReview v-if="step === 'review'" :id="id" :controller="controller" :state="state" :t="t" />
    <RedactionResultView v-if="step === 'result'" :id="id" :controller="controller" :state="state" :t="t" :locale="active" />
  </div>
</template>
