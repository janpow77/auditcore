/**
 * Editor context of the React components: the controllers of one editor
 * session plus ports, profile and read-only state (counterpart of
 * `provideEditorContext` in Vue).
 */

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { validationView, type EditorCore, type EditorPorts, type EditorState, type SelectionCore, type SelectionState, type ValidationCore, type ValidationView } from '@flowaudit/bpmn-flowaudit/ui'
import type { ProfileData } from '@flowaudit/bpmn-flowaudit'
import { useStoreState } from './hooks'

export interface EditorContext {
  editor: EditorCore
  selection: SelectionCore
  validation: ValidationCore
  ports: EditorPorts
  profile: () => ProfileData | null
  readonly: () => boolean
}

const Context = createContext<EditorContext | null>(null)

/** Provides the context; `null` before the session exists (consumers render only afterwards). */
export function EditorContextProvider({ value, children }: { value: EditorContext | null; children?: ReactNode }) {
  return <Context.Provider value={value}>{children}</Context.Provider>
}

export function useEditorContext(): EditorContext {
  const context = useContext(Context)
  if (!context) throw new Error('FlowAudit-Editorkontext fehlt (Komponente außerhalb von <FlowauditEditor> verwendet).')
  return context
}

export const useEditorState = (): EditorState => useStoreState(useEditorContext().editor.store)
export const useSelectionState = (): SelectionState => useStoreState(useEditorContext().selection.store)

export function useValidationView(): ValidationView & { running: boolean; error: string | null } {
  const state = useStoreState(useEditorContext().validation.store)
  return useMemo(() => ({ ...validationView(state), running: state.running, error: state.error }), [state])
}
