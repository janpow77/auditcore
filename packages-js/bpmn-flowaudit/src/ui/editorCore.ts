/**
 * Editor controller: owns the core editor instance and keeps its state in a
 * store (dirty flag, undo/redo, zoom, diagram info, change counter). Vue and
 * React bind to `store`; diagram-js objects are never put into the state.
 */

import {
  editorAccess,
  editorServices,
  modelFromEditor,
  readDiagramInfoFromEditor,
  writeDiagramInfo,
  type CommandStack,
  type DiagramInfo,
  type EditorServices,
  type FlowauditModuleOptions,
  type ModelAccess,
  type ProcessModel,
  type Viewbox,
} from '../index'
import type { EditorFactory, EditorLike } from './editorFactory'
import { createEmitter, createStore, type Store } from './store'

export interface EditorState {
  ready: boolean
  dirty: boolean
  canUndo: boolean
  canRedo: boolean
  scale: number
  changes: number
  info: DiagramInfo | null
  warnings: string[]
  error: string | null
}

export interface EditorCoreOptions {
  factory: EditorFactory
  locale?: 'de' | 'en'
  flowaudit?: FlowauditModuleOptions
}

export type EditorCore = ReturnType<typeof createEditorCore>

export const INITIAL_EDITOR_STATE: EditorState = { ready: false, dirty: false, canUndo: false, canRedo: false, scale: 1, changes: 0, info: null, warnings: [], error: null }

interface Holder {
  editor: EditorLike | null
}

function required(holder: Holder): EditorLike {
  if (!holder.editor) throw new Error('Editor ist nicht bereit.')
  return holder.editor
}

/** Viewport, selection and model access of the editor. */
function editorView(holder: Holder, store: Store<EditorState>, services: () => EditorServices) {
  function zoom(factor: number | 'fit'): void {
    const canvas = holder.editor ? services().canvas : null
    if (!canvas) return
    if (factor === 'fit') canvas.zoom('fit-viewport', 'auto')
    else canvas.zoom(canvas.viewbox().scale * factor)
    store.set({ scale: canvas.viewbox().scale })
  }

  function select(id: string): boolean {
    if (!holder.editor) return false
    const { elementRegistry, selection, canvas } = services()
    const element = elementRegistry.get(id)
    if (!element) return false
    selection?.select(element)
    canvas.scrollToElement(element)
    return true
  }

  return {
    zoom,
    select,
    model: (): ProcessModel => modelFromEditor(services()),
    access: (): ModelAccess => editorAccess(services()),
    setInfo: (info: DiagramInfo): void => writeDiagramInfo(services(), info),
  }
}

/** Keeps the state in line with the editor (commands, viewbox, import). */
function editorSync(holder: Holder, store: Store<EditorState>, services: () => EditorServices, changed: () => void) {
  function commandState(): Pick<EditorState, 'canUndo' | 'canRedo'> {
    const stack = holder.editor?.get<CommandStack>('commandStack')
    return { canUndo: Boolean(stack?.canUndo()), canRedo: Boolean(stack?.canRedo()) }
  }

  function onCommand(): void {
    store.set((state) => ({ dirty: true, changes: state.changes + 1, info: readDiagramInfoFromEditor(services()), ...commandState() }))
    changed()
  }

  function onViewbox(event: unknown): void {
    const viewbox = (event as { viewbox?: Viewbox }).viewbox
    if (viewbox) store.set({ scale: viewbox.scale })
  }

  async function importXml(xml: string): Promise<void> {
    if (!holder.editor) return
    store.set({ error: null })
    try {
      const result = await holder.editor.importXML(xml)
      store.set((state) => ({ warnings: result.warnings ?? [], ready: true, dirty: false, changes: state.changes + 1, info: readDiagramInfoFromEditor(services()), ...commandState() }))
    } catch (error) {
      store.set({ error: (error as Error).message })
      throw error
    }
  }

  return { onCommand, onViewbox, importXml }
}

export function createEditorCore(options: EditorCoreOptions) {
  const store = createStore<EditorState>({ ...INITIAL_EDITOR_STATE })
  const holder: Holder = { editor: null }
  const changes = createEmitter()
  const instances = createEmitter<[EditorLike | null, EditorLike | null]>()

  const services = (): EditorServices => editorServices(required(holder))
  const sync = editorSync(holder, store, services, changes.emit)
  const commandStack = () => holder.editor?.get<CommandStack>('commandStack')

  function setInstance(next: EditorLike | null): void {
    const previous = holder.editor
    holder.editor = next
    instances.emit(next, previous)
  }

  function destroy(): void {
    holder.editor?.destroy()
    setInstance(null)
    store.set({ ready: false })
  }

  function mount(container: HTMLElement, keyboardTarget?: EventTarget): EditorLike {
    destroy()
    const instance = options.factory({ container, locale: options.locale ?? 'de', flowaudit: options.flowaudit ?? {}, keyboardTarget })
    instance.on('commandStack.changed', sync.onCommand)
    instance.on('canvas.viewbox.changed', sync.onViewbox)
    setInstance(instance)
    return instance
  }

  return {
    store,
    instance: (): EditorLike | null => holder.editor,
    mount,
    importXml: sync.importXml,
    exportXml: async (): Promise<string> => (await required(holder).saveXML({ format: true })).xml,
    exportSvg: async (): Promise<string> => (await required(holder).saveSVG()).svg,
    markSaved: (): void => store.set({ dirty: false }),
    undo: () => commandStack()?.undo(),
    redo: () => commandStack()?.redo(),
    ...editorView(holder, store, services),
    services,
    /** Subscribe to model changes (commands); returns an unsubscribe function. */
    onChange: changes.on,
    /** Subscribe to a new or removed editor instance. */
    onInstance: instances.on,
    destroy,
  }
}
