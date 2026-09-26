/**
 * Editor store: the framework-free editor controller
 * (`createEditorCore`) with its state mirrored into Vue reactivity.
 *
 * diagram-js objects are never made reactive (`markRaw`): Vue proxies on
 * shapes break read-only fields (seen in the audit_designer editor).
 */

import { computed, markRaw, reactive, readonly, shallowRef } from 'vue'
import { createEditorCore, type EditorCore, type EditorFactory, type EditorLike, type EditorState } from '@auditcore/bpmn-flowaudit/ui'
import type { FlowauditModuleOptions } from '@auditcore/bpmn-flowaudit'
import { defaultEditorFactory } from '../editor/defaultFactory'

export type { EditorState } from '@auditcore/bpmn-flowaudit/ui'

export interface EditorStoreOptions {
  factory?: EditorFactory
  locale?: 'de' | 'en'
  flowaudit?: FlowauditModuleOptions
}

export type EditorStore = ReturnType<typeof bindEditorCore>

/** Vue view of an editor controller: reactive `state` and the instance as computed. */
export function bindEditorCore(core: EditorCore) {
  const state = reactive<EditorState>({ ...core.store.get() })
  const instance = shallowRef<EditorLike | null>(core.instance())
  core.store.subscribe(() => Object.assign(state, core.store.get()))
  core.onInstance((next) => (instance.value = next ? markRaw(next) : null))
  return { ...core, core, state: readonly(state), editor: computed(() => instance.value) }
}

export function createEditorStore(options: EditorStoreOptions = {}): EditorStore {
  return bindEditorCore(createEditorCore({ factory: options.factory ?? defaultEditorFactory, locale: options.locale, flowaudit: options.flowaudit }))
}
