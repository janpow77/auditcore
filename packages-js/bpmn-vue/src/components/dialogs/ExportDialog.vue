<script setup lang="ts">
/**
 * Export dialog (legacy `BpmnExportDialog`, extended): SVG/PNG/PDF/BPMN/MyST,
 * process table CSV/MyST, RCM, findings list; header, legends, legal bases,
 * metadata, neutral mode and page format.
 */
import { reactive, watch } from 'vue'
import { CONFIDENTIALITY, DEFAULT_EXPORT_CHOICE, label, type ExportChoice, type ExportData, type ExportFormat } from '@flowaudit/bpmn-flowaudit'
import { EXPORT_FORMATS, FORMAT_ICONS as ICONS, initialExportChoice, ORIENTATIONS } from '@flowaudit/bpmn-flowaudit/ui'
import BaseDialog from '../base/BaseDialog.vue'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; defaultTitle: string; subtitle?: string; data: ExportData; confidentiality?: string; excel?: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'export', choice: ExportChoice): void }>()
const { t, locale } = useI18n()
const choice = reactive<Omit<ExportChoice, 'format'>>({ ...DEFAULT_EXPORT_CHOICE })


watch(
  () => props.open,
  (open) => {
    if (open) Object.assign(choice, initialExportChoice(props.defaultTitle, props.subtitle, props.data, props.confidentiality))
  },
  { immediate: true },
)

function run(format: ExportFormat): void {
  emit('export', { ...choice, format })
  emit('update:open', false)
}
</script>

<template>
  <BaseDialog :open="open" :title="t('export.title')" width="620px" @update:open="emit('update:open', $event)">
    <div class="fa-grid-2">
      <label class="fa-field fa-field--wide"><span class="fa-label">{{ t('export.docTitle') }}</span><input v-model="choice.title" class="fa-input" /></label>
      <label class="fa-field fa-field--wide"><span class="fa-label">{{ t('export.subtitle') }}</span><input v-model="choice.subtitle" class="fa-input" /></label>
    </div>
    <fieldset class="fa-export__options">
      <legend class="fa-label">{{ t('export.attachments') }}</legend>
      <label class="fa-check"><input v-model="choice.showHeader" type="checkbox" />{{ t('export.header') }}</label>
      <label class="fa-check"><input v-model="choice.showLegend" type="checkbox" />{{ t('export.legend') }} <span class="fa-help">({{ t('export.legendCount', { count: data.colors.length }) }})</span></label>
      <label class="fa-check"><input v-model="choice.showMarkerLegend" type="checkbox" />{{ t('export.markerLegend') }}</label>
      <label class="fa-check"><input v-model="choice.showLegalBases" type="checkbox" />{{ t('export.legalBases') }} <span class="fa-help">({{ t('export.legalCount', { count: data.legalBases.length }) }})</span></label>
      <label class="fa-check"><input v-model="choice.showMetadata" type="checkbox" />{{ t('export.metadata') }}</label>
    </fieldset>
    <div class="fa-export__neutral fa-card">
      <label class="fa-check"><input v-model="choice.neutral" type="checkbox" /><FaIcon name="neutral" :size="16" /><strong>{{ t('export.neutral') }}</strong></label>
      <p class="fa-help">{{ t('export.neutralHelp') }}</p>
      <p v-if="confidentiality" class="fa-badge fa-badge--warning">{{ t('export.confidentiality', { level: label(CONFIDENTIALITY[confidentiality], locale) || confidentiality }) }}</p>
    </div>
    <div class="fa-grid-2 fa-section">
      <label class="fa-field">
        <span class="fa-label">{{ t('export.page') }}</span>
        <select v-model="choice.pageFormat" class="fa-select"><option value="a4">DIN A4</option><option value="a3">DIN A3</option></select>
      </label>
      <label class="fa-field">
        <span class="fa-label">&nbsp;</span>
        <select v-model="choice.orientation" class="fa-select">
          <option v-for="option in ORIENTATIONS" :key="option" :value="option">{{ t(`export.orientation.${option}`) }}</option>
        </select>
      </label>
    </div>
    <h3 class="fa-section__title fa-section">{{ t('export.formats') }}</h3>
    <div class="fa-export__formats">
      <button v-for="format in EXPORT_FORMATS" :key="format" type="button" class="fa-btn" @click="run(format)">
        <FaIcon :name="ICONS[format] ?? 'analysis'" :size="16" />{{ t(`export.format.${format}`) }}
      </button>
      <button v-if="excel" type="button" class="fa-btn" @click="run('excel')"><FaIcon name="analysis" :size="16" />{{ t('export.format.excel') }}</button>
    </div>
  </BaseDialog>
</template>
