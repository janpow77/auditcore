<script setup lang="ts">
import { computed, ref } from 'vue'
import { useId } from '../composables/useId'
import type { Locale } from '../i18n/i18n'
import SynopsisCommands from './SynopsisCommands.vue'
import SynopsisHeader from './SynopsisHeader.vue'
import SynopsisRow from './SynopsisRow.vue'
import SynopsisToolbar, { type ServerExportLink } from './SynopsisToolbar.vue'
import type { SynopsisPort } from './port'
import type { Comparison, ComparisonResult, ExportPayload, RowUpdate, ServerExportFormat, SynopsisLayout } from './types'
import { useSynopsis } from './useSynopsis'
import { useSynopsisExport } from './useSynopsisExport'
import { useSynopsisNavigation } from './useSynopsisNavigation'

const props = withDefaults(
  defineProps<{
    /** Gespeicherter Vergleich (`GET /comparisons/{id}`). */
    comparison?: Comparison | null
    /** Alternativ nur das Ergebnisobjekt (`ComparisonResult.to_dict()`). */
    result?: ComparisonResult | null
    /** Mit `port`: Vergleich selbst laden. */
    comparisonId?: string
    port?: SynopsisPort | null
    title?: string
    oldLabel?: string
    newLabel?: string
    /** Auswahl und Grund je Zeile bearbeiten (Vorschau vor der Ausgabe). */
    editable?: boolean
    locale?: Locale
  }>(),
  { comparison: null, result: null, comparisonId: undefined, port: null, title: '', oldLabel: '', newLabel: '', editable: false, locale: undefined },
)

const emit = defineEmits<{
  'row-update': [update: RowUpdate]
  export: [payload: ExportPayload]
  navigate: [rowId: string]
}>()

const layout = defineModel<SynopsisLayout>('layout', { default: 'side-by-side' })
const root = ref<HTMLElement | null>(null)
const headingId = useId('fa-synopsis')

const synopsis = useSynopsis({
  comparison: () => props.comparison,
  result: () => props.result,
  comparisonId: () => props.comparisonId,
  port: () => props.port,
  title: () => props.title,
  oldLabel: () => props.oldLabel,
  newLabel: () => props.newLabel,
  locale: () => props.locale,
})
const { t, view, rows, filter, loading, error } = synopsis
const navigation = useSynopsisNavigation(rows, t, root, (id) => emit('navigate', id))
const exporter = useSynopsisExport(view, rows, t, synopsis.locale, (payload) => emit('export', payload))

const highlight = computed(() => filter.highlight ?? synopsis.result.value?.metadata?.highlight_words ?? true)
const serverExports = computed<ServerExportLink[]>(() => {
  const id = synopsis.currentId.value
  const port = props.port
  if (!id || !port?.exportUrl) return []
  const formats: Array<[ServerExportFormat, 'serverDocx' | 'serverPdf' | 'serverJson']> = [
    ['docx', 'serverDocx'],
    ['pdf', 'serverPdf'],
    ['json', 'serverJson'],
  ]
  return formats.map(([format, key]) => ({ label: t(key), href: port.exportUrl?.(id, format) ?? '' }))
})

async function onRowUpdate(id: string, patch: Omit<RowUpdate, 'row_id'>): Promise<void> {
  emit('row-update', await synopsis.updateRow(id, patch))
}

function activate(id: string, isChange: boolean): void {
  if (isChange) navigation.activeId.value = id
}

defineExpose({ next: () => navigation.go(1), previous: () => navigation.go(-1), exportAs: exporter.build })
</script>

<template>
  <section ref="root" class="fa-synopsis" :aria-labelledby="view ? headingId : undefined" :aria-busy="loading || undefined" @keydown="navigation.onKeydown">
    <p v-if="loading" class="fa-synopsis__state" role="status">{{ t('loading') }}</p>
    <p v-if="error" class="fa-synopsis__state fa-synopsis__state--error" role="alert">{{ error }}</p>
    <p v-if="!view && !loading && !error" class="fa-synopsis__state">{{ t('empty') }}</p>
    <template v-if="view">
      <SynopsisHeader :view="view" :selected-text="synopsis.selectedText.value" :editable="editable" :heading-id="headingId" :t="t" />
      <SynopsisToolbar
        v-model:layout="layout"
        v-model:query="filter.query"
        v-model:only-selected="filter.onlySelected"
        :highlight="highlight"
        :statuses="filter.statuses"
        :editable="editable"
        :position="navigation.position.value"
        :can-prev="navigation.canPrev.value"
        :can-next="navigation.canNext.value"
        :server-exports="serverExports"
        :t="t"
        @update:highlight="filter.highlight = $event"
        @toggle-status="synopsis.toggleStatus"
        @all-changes="synopsis.setAllChanges"
        @navigate="navigation.go"
        @export="exporter.run"
      />
      <div class="fa-synopsis__rows">
        <p v-if="rows.length === 0" class="fa-synopsis__state">{{ t('noMatches') }}</p>
        <SynopsisRow
          v-for="row in rows"
          :key="row.id"
          :row="row"
          :layout="layout"
          :old-label="view.oldLabel"
          :new-label="view.newLabel"
          :reason-label="view.reasonLabel"
          :editable="editable"
          :active="navigation.activeId.value === row.id"
          :t="t"
          @update="onRowUpdate(row.id, $event)"
          @activate="activate(row.id, row.isChange)"
        />
      </div>
      <SynopsisCommands :view="view" :t="t" />
    </template>
  </section>
</template>

<style>
.fa-synopsis { display: flex; flex-direction: column; gap: var(--fa-space-4); color: var(--fa-color-text); font: var(--fa-font-size-md) / var(--fa-line-height) var(--fa-font-sans); }
.fa-synopsis__rows { display: flex; flex-direction: column; gap: var(--fa-space-3); }
.fa-synopsis__state { margin: 0; padding: var(--fa-space-4); border: 1px dashed var(--fa-color-border-strong); border-radius: var(--fa-radius); color: var(--fa-color-text-muted); text-align: center; }
.fa-synopsis__state--error { border-style: solid; border-color: var(--fa-color-danger); background: var(--fa-color-danger-soft); color: var(--fa-color-danger); }
</style>
