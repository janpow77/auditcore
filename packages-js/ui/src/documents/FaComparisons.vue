<script setup lang="ts">
import { computed, watch } from 'vue'
import { comparisonsMessages, DEFAULT_MAX_UPLOAD_BYTES, synopsisPortOf, type Comparison, type ComparisonsError, type ComparisonsPort } from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import FaDialog from '../base/FaDialog.vue'
import { useId } from '../composables/useId'
import { provideLocale, useI18n, type Locale } from '../i18n'
import FaSynopsis from '../synopsis/FaSynopsis.vue'
import ComparisonForm from './ComparisonForm.vue'
import ComparisonList from './ComparisonList.vue'
import { useComparisons } from './useComparisons'

const props = withDefaults(defineProps<{
  /** Datenzugang, z. B. `createSynopsisRestClient({ baseUrl: '/api/synopsis' })` (auditcore_documents.web). */
  port?: ComparisonsPort | null
  /** Größte Datei je Seite in Byte; wie `ServiceSettings.max_upload_bytes` des Servers. */
  maxUploadBytes?: number
  /** `false`: nur Liste und Ansicht, kein Hochladen, Import oder Löschen. */
  editable?: boolean
  /** Geöffneten Vergleich als Synopse einbetten (braucht `port.load`); sonst nur Ereignis `comparison-open`. */
  showSynopsis?: boolean
  locale?: Locale
}>(), { port: null, maxUploadBytes: DEFAULT_MAX_UPLOAD_BYTES, editable: true, showSynopsis: true, locale: undefined })

const emit = defineEmits<{
  'comparison-created': [comparison: Comparison]
  'comparison-imported': [comparison: Comparison]
  'comparison-removed': [id: string]
  'comparison-open': [id: string]
  error: [error: ComparisonsError]
}>()

const { t, locale: active } = useI18n(comparisonsMessages, () => props.locale)
provideLocale(active)
const headingId = useId('fa-comparisons')
const { controller, state, view } = useComparisons(
  { port: () => props.port, t: () => t, lang: () => active.value, maxBytes: () => props.maxUploadBytes },
  {
    onCreated: (comparison) => emit('comparison-created', comparison),
    onImported: (comparison) => emit('comparison-imported', comparison),
    onRemoved: (id) => emit('comparison-removed', id),
    onError: (error) => emit('error', error),
  },
)
const synopsisPort = computed(() => (props.showSynopsis ? synopsisPortOf(props.port) : null))
const embedded = computed(() => synopsisPort.value !== null && state.value.openId !== null)
const busy = computed(() => state.value.busy !== null)
watch(() => props.port, () => void controller.load(), { immediate: true })

function open(id: string): void {
  if (synopsisPort.value) controller.open(id)
  emit('comparison-open', id)
}

defineExpose({ reload: controller.load, open })
</script>

<template>
  <section class="fa-comparisons" :aria-labelledby="headingId" :aria-busy="busy || undefined">
    <header class="fa-comparisons__head">
      <h2 :id="headingId" class="fa-comparisons__heading">{{ t('title') }}</h2>
      <p class="fa-comparisons__note">{{ t('workAid') }}</p>
    </header>
    <p class="fa-sr-only" role="status" aria-live="polite">{{ view.busyText || state.notice }}</p>
    <p v-if="!port" class="fa-comparisons__state fa-comparisons__state--error" role="alert">{{ t('noPort') }}</p>
    <p v-else-if="state.error" class="fa-comparisons__state fa-comparisons__state--error" role="alert">{{ state.error.message }}</p>
    <div v-if="embedded" class="fa-comparisons__open">
      <FaButton size="sm" variant="secondary" @click="controller.open(null)">{{ t('back') }}</FaButton>
      <FaSynopsis :comparison-id="state.openId ?? undefined" :port="synopsisPort" :editable="editable" />
    </div>
    <div v-else class="fa-comparisons__layout" :class="{ 'fa-comparisons__layout--single': !editable }">
      <ComparisonForm
        v-if="editable && port"
        :form="state.form" :view="view" :busy="state.busy === 'create'"
        @form-update="controller.updateForm" @section-toggle="controller.toggleSection"
        @form-submit="controller.submit" @form-reset="controller.resetForm"
      />
      <ComparisonList
        v-if="port"
        :rows="view.rows" :query="state.query" :count-text="view.countText" :empty-text="view.emptyText" :busy="busy"
        :editable="editable" :can-import="Boolean(port.importResult)"
        @update:query="controller.setQuery" @comparison-open="open" @comparison-remove="controller.askRemove" @result-import="controller.importText"
      />
    </div>
    <FaDialog :open="view.pendingTitle !== null" :title="t('confirmTitle')" size="sm" @close="controller.cancelRemove">
      <p class="fa-comparisons__confirm">{{ t('confirmText', { title: view.pendingTitle ?? '' }) }}</p>
      <template #footer>
        <FaButton variant="ghost" @click="controller.cancelRemove">{{ t('cancel') }}</FaButton>
        <FaButton variant="danger" icon="trash" :loading="state.busy === 'remove'" data-testid="comparisons-confirm-remove" @click="controller.confirmRemove">{{ t('remove') }}</FaButton>
      </template>
    </FaDialog>
  </section>
</template>
