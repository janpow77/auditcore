<script setup lang="ts">
import { watch } from 'vue'
import type { DownloadFile } from '@flowaudit/common'
import { saveFile } from '@flowaudit/common/browser'
import {
  reportingErrorKey,
  reportingMessages,
  reportingTablesText,
  reportingWorkbookText,
  type ReportingPort,
  type ReportTableInput,
  type WorkbookPreview,
} from '@flowaudit/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import ReportPreview from './ReportPreview.vue'
import { useReportExport } from './useReportExport'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createReportingRestPort({ baseUrl: '/api/reporting' })`. */
  port?: ReportingPort | null
  /** Tabellen der Anwendung (je Tabelle ein Blatt). */
  tables?: readonly ReportTableInput[]
  /** Vorschlag für den Dateinamen (ohne oder mit `.xlsx`). */
  filename?: string
  locale?: Locale
}>(), { port: null, tables: () => [], filename: '', locale: undefined })

const emit = defineEmits<{ 'preview-completed': [result: WorkbookPreview]; 'export-completed': [file: DownloadFile]; error: [message: string] }>()
const { t, locale: active } = useI18n(reportingMessages, () => props.locale)
const id = useId('fa-report')
const { controller, state, profile } = useReportExport(() => props.port, () => props.tables, {
  previewed: (result) => emit('preview-completed', result),
  exported: (file) => emit('export-completed', file),
  failed: (message) => emit('error', message),
})

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => props.filename, (name) => controller.setFilename(name), { immediate: true })
watch(() => props.tables, () => controller.tablesChanged())

async function runExport(): Promise<void> {
  const file = await controller.exportWorkbook()
  if (file && typeof URL.createObjectURL === 'function') saveFile(file)
}

const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value
</script>

<template>
  <div class="fa-report" :lang="active">
    <p v-if="!port" class="fa-report__muted" role="status">{{ t('noPort') }}</p>
    <p v-if="state.busy === 'load'" class="fa-report__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-report__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <form v-if="state.catalogue" class="fa-report__card" :aria-labelledby="`${id}-h`" novalidate @submit.prevent="controller.preview">
      <h3 :id="`${id}-h`" class="fa-report__heading">{{ t('title') }}</h3>
      <p class="fa-report__muted" data-testid="report-tables">{{ reportingTablesText(tables, t, active) }}</p>
      <div class="fa-report__form">
        <label class="fa-report__field">
          <span class="fa-report__label">{{ t('profile') }}</span>
          <select :value="state.profileId ?? ''" class="fa-report__input" data-testid="report-profile" @change="controller.setProfile(value($event) || null)">
            <option value="">{{ t('choose') }}</option>
            <option v-for="entry in state.catalogue.profiles" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
          </select>
        </label>
        <label class="fa-report__field">
          <span class="fa-report__label">{{ t('filename') }}</span>
          <input :value="state.filename" class="fa-report__input" autocomplete="off" placeholder="bericht.xlsx" data-testid="report-filename" @input="controller.setFilename(value($event))" />
        </label>
      </div>
      <details v-if="profile" class="fa-report__source">
        <summary>{{ t('profileSource') }}</summary>
        <p>{{ profile.description }}</p>
        <p>{{ t('profileVersion', { version: profile.version, status: profile.status }) }}</p>
        <p v-if="profile.source">{{ profile.source }}</p>
      </details>
      <p v-if="!state.catalogue.excel_available" class="fa-report__muted">{{ t('excelMissing') }}</p>
      <p v-if="state.validation" class="fa-report__error" role="alert">{{ t(reportingErrorKey(state.validation)) }}</p>
      <div class="fa-report__actions">
        <FaButton type="submit" :loading="state.busy === 'preview'" data-testid="report-preview">{{ t('preview') }}</FaButton>
        <FaButton variant="primary" :disabled="!state.catalogue.excel_available" :loading="state.busy === 'export'" data-testid="report-export" @click="runExport">{{ t('export') }}</FaButton>
      </div>
      <p class="fa-report__muted" aria-live="polite" data-testid="report-status">{{ state.exportedName ? t('exported', { filename: state.exportedName }) : '' }}</p>
    </form>
    <section v-if="state.preview" class="fa-report__card" :aria-labelledby="`${id}-p`" aria-live="polite">
      <h3 :id="`${id}-p`" class="fa-report__heading">{{ t('preview') }}</h3>
      <p v-if="state.stale" class="fa-report__notice" data-testid="report-stale">{{ t('previewStale') }}</p>
      <p class="fa-report__muted" data-testid="report-workbook">{{ reportingWorkbookText(state.preview, t, active) }}</p>
      <p class="fa-report__muted">{{ t('notice') }}</p>
      <ReportPreview v-for="(table, index) in state.preview.tables" :key="table.name" :table="table" :index="index" :locale="locale" />
    </section>
  </div>
</template>
