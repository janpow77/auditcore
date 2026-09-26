<script setup lang="ts">
/**
 * Root of the web component `<flowaudit-bpmn-editor>`: wraps
 * `FlowauditEditor`, resolves the data source and dispatches DOM events
 * (`CustomEvent` with the payload as `detail`, bubbling and composed).
 */
import { ref, useHost } from 'vue'
import type { Comment, DiagramInfo, ProfileData, StoragePort, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import FlowauditEditor from '../components/FlowauditEditor.vue'
import type { EditorPorts } from '../stores/context'
import type { ElementEventMap, ElementEventName, Theme } from '@flowaudit/bpmn-flowaudit/ui'
import { useElementSource } from './useElementSource'

const props = withDefaults(
  defineProps<{
    xml?: string
    src?: string
    apiBase?: string
    diagramId?: string
    name?: string
    locale?: 'de' | 'en'
    theme?: Theme
    readonly?: boolean
    profile?: string
    author?: string
    profileData?: ProfileData | null
    storage?: StoragePort
    ports?: EditorPorts & { validation?: ValidationPort }
    comments?: Comment[]
  }>(),
  { xml: undefined, src: undefined, apiBase: undefined, diagramId: undefined, profile: undefined, storage: undefined, ports: undefined, name: '', locale: 'de', theme: 'auto', readonly: false, author: '', profileData: undefined, comments: () => [] },
)

const host = useHost()
const editor = ref<InstanceType<typeof FlowauditEditor> | null>(null)
const saving = ref(false)

function dispatch<K extends ElementEventName>(name: K, detail: ElementEventMap[K]): void {
  host?.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }))
}

const source = useElementSource(props, (message) => dispatch('error', { message }))

function onXml(xml: string): void {
  source.xml.value = xml
  dispatch('change', { xml })
}

async function onSave(payload: { xml: string; info: DiagramInfo | null }): Promise<void> {
  saving.value = true
  try {
    await source.persist(payload.xml)
    dispatch('save', payload)
  } catch (error) {
    dispatch('error', { message: (error as Error).message })
  } finally {
    saving.value = false
  }
}

defineExpose({
  getXml: () => editor.value?.getXml() ?? Promise.resolve(source.xml.value),
  getSvg: () => editor.value?.getSvg(),
  select: (id: string) => editor.value?.select(id),
  reload: source.reload,
})
</script>

<template>
  <FlowauditEditor
    ref="editor"
    :xml="source.xml.value"
    :name="name || diagramId || ''"
    :diagram-id="diagramId"
    :profile="source.profile.value"
    :ports="source.ports.value"
    :locale="locale"
    :theme="theme"
    :readonly="readonly"
    :author="author"
    :comments="comments"
    :saving="saving"
    @update:xml="onXml"
    @save="onSave"
    @ready="dispatch('ready', { diagramId })"
    @selection-change="dispatch('selection-change', { elementId: $event })"
    @info-change="dispatch('diagram-info-change', { info: $event })"
    @error="dispatch('error', { message: $event })"
  />
</template>
