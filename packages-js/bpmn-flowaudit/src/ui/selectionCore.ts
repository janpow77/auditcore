/**
 * Selection controller: the selected element, its FlowAudit extensions and
 * undoable writes through `modeling`. The state holds the element object
 * itself (never proxied), a version counter and the extensions.
 */

import {
  emptyExtensions,
  readExtensions,
  readFlowstatValues,
  writeExtensions,
  writeFlowstatValues,
  type DiagramElement,
  type Extensions,
  type FlowstatField,
} from '../index'
import type { EditorCore } from './editorCore'
import type { EditorLike } from './editorFactory'
import { createStore } from './store'

export interface SelectionState {
  element: DiagramElement | null
  extensions: Extensions
  type: string | null
  version: number
}

export type SelectionCore = ReturnType<typeof createSelectionCore>

/** Reading and undoable writing of the selected element's properties. */
function selectionEditing(element: () => DiagramElement | null, editor: EditorCore) {
  function write(patch: Partial<Extensions>): void {
    const current = element()
    if (current) writeExtensions(current, patch, editor.services())
  }

  function rename(name: string): void {
    const current = element()
    if (current) editor.services().modeling.updateProperties(current, { name })
  }

  function setDocumentation(text: string): void {
    const current = element()
    if (!current) return
    const { modeling, moddle } = editor.services()
    const documentation = text.trim() ? [moddle.create('bpmn:Documentation', { text })] : []
    modeling.updateProperties(current, { documentation })
  }

  function flowstat() {
    const current = element()
    return current ? readFlowstatValues(current.businessObject) : null
  }

  function setFlowstat(field: FlowstatField, value: number | string | null): void {
    const current = element()
    if (current) writeFlowstatValues(current, { [field]: value }, editor.services().modeling)
  }

  function property(name: string): string {
    const value = element()?.businessObject.get(name)
    return typeof value === 'string' ? value : ''
  }

  function documentation(): string {
    const docs = (element()?.businessObject.get('documentation') as { text?: string }[] | undefined) ?? []
    return docs.map((doc) => doc.text ?? '').join('\n')
  }

  return { write, rename, setDocumentation, flowstat, setFlowstat, property, documentation }
}

export function createSelectionCore(editor: EditorCore) {
  const store = createStore<SelectionState>({ element: null, extensions: emptyExtensions(), type: null, version: 0 })
  const element = () => store.get().element

  function show(current: DiagramElement | null): void {
    store.set((state) => ({
      element: current,
      extensions: current ? readExtensions(current.businessObject) : emptyExtensions(),
      type: current?.businessObject?.$type ?? null,
      version: state.version + 1,
    }))
  }

  const refresh = () => show(element())

  function onSelection(event: unknown): void {
    const selection = (event as { newSelection?: DiagramElement[] }).newSelection ?? []
    const [first] = selection.filter((item) => !item.labelTarget)
    show(first ?? null)
  }

  function bind(next: EditorLike | null, previous: EditorLike | null): void {
    previous?.off('selection.changed', onSelection)
    next?.on('selection.changed', onSelection)
    show(null)
  }

  bind(editor.instance(), null)
  const stopInstance = editor.onInstance(bind)
  const stopChange = editor.onChange(refresh)

  return {
    store,
    element,
    ...selectionEditing(element, editor),
    refresh,
    dispose: () => (stopInstance(), stopChange()),
  }
}
