<!-- ReportTemplates: Berichtsvorlage wählen, Datenvertrag sehen, Vorschau und Bericht; Logik im Kern (createReporttemplatesController). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import type { DownloadFile } from '@auditcore/common'
import { saveFile } from '@auditcore/common/browser'
import {
  createReporttemplatesController,
  formatOptions,
  reporttemplatesCanRender,
  reporttemplatesIsEmpty,
  reporttemplatesMessages,
  type ReporttemplatesPort,
  type TemplateData,
  type TemplateDetail,
  type TemplateFormat,
  type TemplatePreview,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useStore } from '../composables/useStore'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import TemplateContract from './TemplateContract.vue'
import TemplatePreviewPane from './TemplatePreviewPane.vue'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createReportTemplatesRestPort({ baseUrl: '/api/reporting' })`. */
  port?: ReporttemplatesPort | null
  /** Daten gemäß Datenvertrag; ohne Daten gelten die Beispieldaten der Vorlage. */
  data?: TemplateData | null
  /** Vorschlag für den Dateinamen (ohne Endung). */
  filename?: string
  locale?: Locale
}>(), { port: null, data: null, filename: '', locale: undefined })

const emit = defineEmits<{
  'template-select': [detail: TemplateDetail]
  'preview-completed': [result: TemplatePreview]
  'report-rendered': [file: DownloadFile]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(reporttemplatesMessages, () => props.locale)
const id = useId('fa-reporttemplates')
const controller = createReporttemplatesController({
  port: () => props.port,
  data: () => props.data,
  callbacks: () => ({
    selected: (detail) => emit('template-select', detail),
    previewed: (result) => emit('preview-completed', result),
    rendered: (file) => emit('report-rendered', file),
    failed: (message) => emit('error', message),
  }),
})
const state = useStore(controller.store)
const formats = computed(() => formatOptions(state.value))
const missing = computed(() => formats.value.find((entry) => entry.format === state.value.format && !entry.available))

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => props.filename, (name) => controller.setFilename(name), { immediate: true })
watch(() => props.data, () => controller.dataChanged())

async function runRender(): Promise<void> {
  const file = await controller.render()
  if (file && typeof URL.createObjectURL === 'function') saveFile(file)
}

const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value
</script>

<template>
  <div class="fa-reporttemplates" :lang="active">
    <p v-if="!port" class="fa-reporttemplates__muted" role="status">{{ t('noPort') }}</p>
    <p v-if="state.busy === 'load'" class="fa-reporttemplates__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-reporttemplates__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="reporttemplatesIsEmpty(state)" class="fa-reporttemplates__muted">{{ t('empty') }}</p>
    <form v-if="state.catalogue?.templates.length" class="fa-reporttemplates__card" :aria-labelledby="`${id}-h`" novalidate @submit.prevent="controller.preview">
      <h3 :id="`${id}-h`" class="fa-reporttemplates__heading">{{ t('title') }}</h3>
      <div class="fa-reporttemplates__form">
        <label class="fa-reporttemplates__field">
          <span class="fa-reporttemplates__label">{{ t('template') }}</span>
          <select :value="state.templateId ?? ''" class="fa-reporttemplates__input" data-testid="template-select" @change="controller.select(value($event) || null)">
            <option value="">{{ t('choose') }}</option>
            <option v-for="entry in state.catalogue.templates" :key="entry.id" :value="entry.id">{{ entry.title }}</option>
          </select>
        </label>
        <label class="fa-reporttemplates__field">
          <span class="fa-reporttemplates__label">{{ t('format') }}</span>
          <select :value="state.format ?? ''" class="fa-reporttemplates__input" data-testid="template-format" @change="controller.setFormat((value($event) || null) as TemplateFormat | null)">
            <option v-for="entry in formats" :key="entry.format" :value="entry.format">{{ entry.format.toUpperCase() }}</option>
          </select>
        </label>
        <label class="fa-reporttemplates__field">
          <span class="fa-reporttemplates__label">{{ t('design') }}</span>
          <select :value="state.designId ?? ''" class="fa-reporttemplates__input" data-testid="template-design" @change="controller.setDesign(value($event) || null)">
            <option v-for="entry in state.catalogue.designs" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
          </select>
        </label>
        <label class="fa-reporttemplates__field">
          <span class="fa-reporttemplates__label">{{ t('filename') }}</span>
          <input :value="state.filename" class="fa-reporttemplates__input" autocomplete="off" data-testid="template-filename" @input="controller.setFilename(value($event))" />
        </label>
      </div>
      <p v-if="state.busy === 'detail'" class="fa-reporttemplates__muted" role="status">{{ t('loadingDetail') }}</p>
      <template v-if="state.detail">
        <p class="fa-reporttemplates__muted" data-testid="template-version">{{ t('version', { version: state.detail.version, status: state.detail.status }) }} · {{ t(`kind${state.detail.kind}`) }}</p>
        <p class="fa-reporttemplates__muted">{{ state.detail.description }}</p>
        <p class="fa-reporttemplates__muted" data-testid="template-data">{{ t('data') }}: {{ data ? t('dataGiven') : t('dataSample') }}</p>
      </template>
      <p v-if="missing" class="fa-reporttemplates__failure" role="alert">{{ t('formatMissing', { format: missing.format.toUpperCase() }) }}</p>
      <div class="fa-reporttemplates__actions">
        <FaButton type="submit" :disabled="!state.detail" :loading="state.busy === 'preview'" data-testid="template-preview-button">{{ t('preview') }}</FaButton>
        <FaButton variant="primary" :disabled="!reporttemplatesCanRender(state)" :loading="state.busy === 'render'" data-testid="template-render" @click="runRender">{{ t('render') }}</FaButton>
      </div>
      <p class="fa-reporttemplates__muted" aria-live="polite" data-testid="template-status">{{ state.renderedName ? t('rendered', { filename: state.renderedName }) : '' }}</p>
    </form>
    <TemplateContract v-if="state.detail" :detail="state.detail" :locale="locale" />
    <TemplatePreviewPane v-if="state.preview" :preview="state.preview" :stale="state.stale" :locale="locale" />
  </div>
</template>
