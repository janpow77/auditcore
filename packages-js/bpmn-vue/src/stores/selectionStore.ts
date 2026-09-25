/**
 * Selection store: the selected element, its FlowAudit extensions and a
 * write function that goes through `modeling` (undoable).
 */

import { computed, markRaw, shallowRef, watch } from 'vue'
import {
  emptyExtensions,
  readExtensions,
  writeExtensions,
  readFlowstatValues,
  writeFlowstatValues,
  type DiagramElement,
  type Extensions,
  type FlowstatField,
} from '@flowaudit/bpmn-flowaudit'
import type { EditorStore } from './editorStore'

export type SelectionStore = ReturnType<typeof createSelectionStore>

export function createSelectionStore(editorStore: EditorStore) {
  const element = shallowRef<DiagramElement | null>(null)
  const extensions = shallowRef<Extensions>(emptyExtensions())
  const version = shallowRef(0)

  function refresh(): void {
    const current = element.value
    extensions.value = current ? readExtensions(current.businessObject) : emptyExtensions()
    version.value += 1
  }

  function onSelection(event: unknown): void {
    const selection = (event as { newSelection?: DiagramElement[] }).newSelection ?? []
    const [first] = selection.filter((item) => !item.labelTarget)
    element.value = first ? markRaw(first) : null
    refresh()
  }

  watch(
    () => editorStore.editor.value,
    (editor, previous) => {
      previous?.off('selection.changed', onSelection)
      editor?.on('selection.changed', onSelection)
      element.value = null
      refresh()
    },
    { immediate: true },
  )
  editorStore.onChange(refresh)

  const type = computed(() => {
    void version.value
    return element.value?.businessObject?.$type ?? null
  })

  function write(patch: Partial<Extensions>): void {
    if (!element.value) return
    writeExtensions(element.value, patch, editorStore.services())
  }

  function rename(name: string): void {
    if (element.value) editorStore.services().modeling.updateProperties(element.value, { name })
  }

  function setDocumentation(text: string): void {
    const current = element.value
    if (!current) return
    const { modeling, moddle } = editorStore.services()
    const documentation = text.trim() ? [moddle.create('bpmn:Documentation', { text })] : []
    modeling.updateProperties(current, { documentation })
  }

  function flowstat() {
    void version.value
    return element.value ? readFlowstatValues(element.value.businessObject) : null
  }

  function setFlowstat(field: FlowstatField, value: number | string | null): void {
    if (element.value) writeFlowstatValues(element.value, { [field]: value }, editorStore.services().modeling)
  }

  function property(name: string): string {
    void version.value
    const value = element.value?.businessObject.get(name)
    return typeof value === 'string' ? value : ''
  }

  function documentation(): string {
    void version.value
    const docs = (element.value?.businessObject.get('documentation') as { text?: string }[] | undefined) ?? []
    return docs.map((doc) => doc.text ?? '').join('\n')
  }

  return { element, extensions, type, version, write, rename, setDocumentation, flowstat, setFlowstat, property, documentation, refresh }
}
