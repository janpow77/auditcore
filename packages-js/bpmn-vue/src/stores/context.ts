/**
 * Injection keys of the stores and ports shared by the editor components.
 */

import { inject, provide, type InjectionKey } from 'vue'
import type { CataloguePort, EsiPort, LegalSearchPort, ProfileData } from '@flowaudit/bpmn-flowaudit'
import type { EditorStore } from './editorStore'
import type { SelectionStore } from './selectionStore'
import type { ValidationStore } from './validationStore'

export interface EditorPorts {
  legalSearch?: LegalSearchPort
  catalogue?: CataloguePort
  esi?: EsiPort
}

export interface EditorContext {
  editor: EditorStore
  selection: SelectionStore
  validation: ValidationStore
  ports: EditorPorts
  profile: () => ProfileData | null
  readonly: () => boolean
}

const KEY: InjectionKey<EditorContext> = Symbol('flowaudit-editor')

export function provideEditorContext(context: EditorContext): EditorContext {
  provide(KEY, context)
  return context
}

export function useEditorContext(): EditorContext {
  const context = inject(KEY, null)
  if (!context) throw new Error('FlowAudit-Editorkontext fehlt (Komponente außerhalb von <FlowauditEditor> verwendet).')
  return context
}
