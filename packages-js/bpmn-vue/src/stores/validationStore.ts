/**
 * Validation store: local rules after changes (debounced) and optionally a
 * server validation (framework-free `createValidationCore`, mirrored into Vue).
 */

import { computed } from 'vue'
import { createValidationCore, validationView, type ValidationCore, type ValidationCoreOptions } from '@flowaudit/bpmn-flowaudit/ui'
import { useStore } from '../composables/useStore'
import type { EditorStore } from './editorStore'

export type ValidationStoreOptions = ValidationCoreOptions
export type ValidationStore = ReturnType<typeof bindValidationCore>

export function bindValidationCore(core: ValidationCore) {
  const state = useStore(core.store)
  const view = computed(() => validationView(state.value))
  return {
    core,
    issues: computed(() => view.value.issues),
    count: computed(() => view.value.count),
    byElement: computed(() => view.value.byElement),
    running: computed(() => state.value.running),
    error: computed(() => state.value.error),
    runLocal: core.runLocal,
    runServer: core.runServer,
    schedule: core.schedule,
    hasServer: core.hasServer,
  }
}

export function createValidationStore(editorStore: EditorStore, options: ValidationStoreOptions): ValidationStore {
  return bindValidationCore(createValidationCore(editorStore.core, options))
}
