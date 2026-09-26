<script setup lang="ts">
/** All dialogs of the editor, driven by the editor setup and actions. */
import { computed, ref, shallowRef, watch } from 'vue'
import { collectExportData, type Approval, type DiagramInfo, type ProcessModel, type ProfileSummary } from '@auditcore/bpmn-flowaudit'
import { elementNames, EMPTY_EXPORT_DATA } from '@auditcore/bpmn-flowaudit/ui'
import DiagramInfoDialog from './dialogs/DiagramInfoDialog.vue'
import ElementSearch from './dialogs/ElementSearch.vue'
import EnrichmentDialog from './dialogs/EnrichmentDialog.vue'
import EsiDialog from './dialogs/EsiDialog.vue'
import ExportDialog from './dialogs/ExportDialog.vue'
import ShortcutHelp from './dialogs/ShortcutHelp.vue'
import XmlDialog from './dialogs/XmlDialog.vue'
import type { useEditorActions } from '../composables/useEditorActions'
import type { useEditorSetup } from '../composables/useEditorSetup'
import type { EditorPorts } from '../stores/context'

const props = defineProps<{
  setup: ReturnType<typeof useEditorSetup>
  actions: ReturnType<typeof useEditorActions>
  name: string
  diagramId?: string
  profiles: ProfileSummary[]
  approvals: Approval[]
  ports: EditorPorts
}>()
const emit = defineEmits<{ (e: 'apply-xml', xml: string): void }>()

const dialogs = computed(() => props.setup.ui.dialogs)
const editor = props.setup.editor
const model = shallowRef<ProcessModel | null>(null)
const xml = ref('')

watch(
  () => [dialogs.value.search, dialogs.value.export, dialogs.value.enrich],
  (open) => {
    if (open.some(Boolean) && editor.state.ready) model.value = editor.model()
  },
)
watch(
  () => dialogs.value.xml,
  async (open) => {
    if (open) xml.value = await editor.exportXml()
  },
)

const exportData = computed(() => (model.value ? collectExportData(model.value) : EMPTY_EXPORT_DATA))
const names = computed(() => elementNames(model.value))
const info = computed(() => editor.state.info as DiagramInfo | null)
</script>

<template>
  <DiagramInfoDialog
    v-model:open="dialogs.info"
    :info="info"
    :profiles="profiles"
    :approvals="approvals"
    :fallback-title="name"
    @apply="actions.applyInfo"
    @approve="actions.approve"
    @new-version="actions.newVersion"
  />
  <ExportDialog
    v-model:open="dialogs.export"
    :default-title="info?.title || name"
    :subtitle="info?.subtitle"
    :data="exportData"
    :confidentiality="info?.confidentiality"
    excel
    @export="actions.runExport"
  />
  <EnrichmentDialog v-model:open="dialogs.enrich" :suggestions="actions.suggestions.value" :names="names" @apply="actions.applyEnrichment" />
  <EsiDialog v-model:open="dialogs.esi" :port="ports.esi" :xml="() => editor.exportXml()" :diagram-id="diagramId" @jump="editor.select" />
  <ElementSearch v-model:open="dialogs.search" :model="model" @jump="editor.select" />
  <ShortcutHelp v-model:open="dialogs.shortcuts" />
  <XmlDialog v-model:open="dialogs.xml" :xml="xml" :readonly="setup.readonlyNow.value" @apply="emit('apply-xml', $event)" />
</template>
