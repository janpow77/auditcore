/**
 * Selection store: the selected element, its FlowAudit extensions and
 * undoable writes (framework-free `createSelectionCore`, mirrored into Vue).
 */

import { computed } from 'vue'
import { createSelectionCore, type SelectionCore } from '@auditcore/bpmn-flowaudit/ui'
import type { FlowstatField } from '@auditcore/bpmn-flowaudit'
import { useStore } from '../composables/useStore'
import type { EditorStore } from './editorStore'

export type SelectionStore = ReturnType<typeof bindSelectionCore>

export function bindSelectionCore(core: SelectionCore) {
  const state = useStore(core.store)
  const version = computed(() => state.value.version)
  return {
    ...core,
    core,
    element: computed(() => state.value.element),
    extensions: computed(() => state.value.extensions),
    type: computed(() => state.value.type),
    version,
    flowstat: () => (void version.value, core.flowstat()),
    setFlowstat: (field: FlowstatField, value: number | string | null) => core.setFlowstat(field, value),
    property: (name: string) => (void version.value, core.property(name)),
    documentation: () => (void version.value, core.documentation()),
  }
}

export function createSelectionStore(editorStore: EditorStore): SelectionStore {
  return bindSelectionCore(createSelectionCore(editorStore.core))
}
