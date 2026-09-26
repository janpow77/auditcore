<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Comparison, ComparisonResult, ExportPayload, RowUpdate, SynopsisLayout, SynopsisPort } from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import type { Locale } from '../i18n/i18n'
import SynopsisCommands from './SynopsisCommands.vue'
import SynopsisHeader from './SynopsisHeader.vue'
import SynopsisRow from './SynopsisRow.vue'
import SynopsisToolbar from './SynopsisToolbar.vue'
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

const { t, locale, controller, state, selection } = useSynopsis({
  inputs: () => ({
    comparison: props.comparison,
    result: props.result,
    comparisonId: props.comparisonId,
    port: props.port,
    title: props.title,
    oldLabel: props.oldLabel,
    newLabel: props.newLabel,
  }),
  locale: () => props.locale,
})
const navigation = useSynopsisNavigation(controller, selection, root, (id) => emit('navigate', id))
const exporter = useSynopsisExport(selection, t, locale, (payload) => emit('export', payload))
const view = computed(() => selection.value.view)
const rows = computed(() => selection.value.rows)
const filter = computed(() => state.value.filter)

async function onRowUpdate(id: string, patch: Omit<RowUpdate, 'row_id'>): Promise<void> {
  emit('row-update', await controller.updateRow(props, id, patch))
}

function activate(id: string, isChange: boolean): void {
  if (isChange) controller.activate(id)
}

defineExpose({ next: () => navigation.go(1), previous: () => navigation.go(-1), exportAs: exporter.build })
</script>

<template>
  <section ref="root" class="fa-synopsis" :aria-labelledby="view ? headingId : undefined" :aria-busy="state.loading || undefined" @keydown="navigation.onKeydown">
    <p v-if="state.loading" class="fa-synopsis__state" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-synopsis__state fa-synopsis__state--error" role="alert">{{ state.error }}</p>
    <p v-if="!view && !state.loading && !state.error" class="fa-synopsis__state">{{ t('empty') }}</p>
    <template v-if="view">
      <SynopsisHeader :view="view" :selected-text="selection.selectedText" :editable="editable" :heading-id="headingId" :t="t" />
      <SynopsisToolbar
        v-model:layout="layout"
        :query="filter.query"
        :only-selected="filter.onlySelected"
        :highlight="selection.highlight"
        :statuses="filter.statuses"
        :editable="editable"
        :position="selection.position"
        :can-prev="selection.canPrev"
        :can-next="selection.canNext"
        :server-exports="selection.serverExports"
        :t="t"
        @update:query="controller.setQuery"
        @update:only-selected="controller.setOnlySelected"
        @update:highlight="controller.setHighlight"
        @toggle-status="controller.toggleStatus"
        @all-changes="controller.setAllChanges"
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
          :active="selection.activeId === row.id"
          :t="t"
          @update="onRowUpdate(row.id, $event)"
          @activate="activate(row.id, row.isChange)"
        />
      </div>
      <SynopsisCommands :view="view" :t="t" />
    </template>
  </section>
</template>
