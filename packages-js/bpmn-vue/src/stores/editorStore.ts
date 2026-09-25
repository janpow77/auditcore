/**
 * Editor store: owns the core editor instance and exposes its state
 * reactively (dirty flag, undo/redo, zoom, diagram info, change counter).
 *
 * diagram-js objects are never made reactive (`markRaw`): Vue proxies on
 * shapes break read-only fields (seen in the audit_designer editor).
 */

import { computed, markRaw, reactive, readonly, shallowRef, type ShallowRef } from 'vue'
import {
  editorServices,
  modelFromEditor,
  readDiagramInfoFromEditor,
  writeDiagramInfo,
  editorAccess,
  type CommandStack,
  type DiagramInfo,
  type EditorServices,
  type FlowauditModuleOptions,
  type ModelAccess,
  type ProcessModel,
  type Viewbox,
} from '@flowaudit/bpmn-flowaudit'
import { defaultEditorFactory, type EditorFactory, type EditorLike } from '../editor/createEditor'

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

export interface EditorStoreOptions {
  factory?: EditorFactory
  locale?: 'de' | 'en'
  flowaudit?: FlowauditModuleOptions
}

export type EditorStore = ReturnType<typeof createEditorStore>

function ready(editor: ShallowRef<EditorLike | null>): EditorLike {
  if (!editor.value) throw new Error('Editor ist nicht bereit.')
  return editor.value
}

/** XML and SVG output of the editor. */
function editorOutput(editor: ShallowRef<EditorLike | null>) {
  return {
    exportXml: async (): Promise<string> => (await ready(editor).saveXML({ format: true })).xml,
    exportSvg: async (): Promise<string> => (await ready(editor).saveSVG()).svg,
  }
}

/** Viewport, selection and model access of the editor. */
function editorView(editor: ShallowRef<EditorLike | null>, state: EditorState, services: () => EditorServices) {
  function zoom(factor: number | 'fit'): void {
    const canvas = editor.value ? services().canvas : null
    if (!canvas) return
    if (factor === 'fit') canvas.zoom('fit-viewport', 'auto')
    else canvas.zoom(canvas.viewbox().scale * factor)
    state.scale = canvas.viewbox().scale
  }

  function select(id: string): boolean {
    if (!editor.value) return false
    const { elementRegistry, selection, canvas } = services()
    const element = elementRegistry.get(id)
    if (!element) return false
    selection?.select(element)
    canvas.scrollToElement(element)
    return true
  }

  function model(): ProcessModel {
    return modelFromEditor(services())
  }

  function access(): ModelAccess {
    return editorAccess(services())
  }

  function setInfo(info: DiagramInfo): void {
    writeDiagramInfo(services(), info)
  }

  return { zoom, select, model, access, setInfo }
}

/** Keeps the reactive state in line with the editor (commands, viewbox, import). */
function editorStateSync(editor: ShallowRef<EditorLike | null>, state: EditorState, services: () => EditorServices, listeners: Set<() => void>) {
  function refreshCommandState(): void {
    const stack = editor.value?.get<CommandStack>('commandStack')
    state.canUndo = Boolean(stack?.canUndo())
    state.canRedo = Boolean(stack?.canRedo())
  }

  function onCommand(): void {
    state.dirty = true
    state.changes += 1
    state.info = readDiagramInfoFromEditor(services())
    refreshCommandState()
    for (const listener of listeners) listener()
  }

  function onViewbox(event: unknown): void {
    const viewbox = (event as { viewbox?: Viewbox }).viewbox
    if (viewbox) state.scale = viewbox.scale
  }

  async function importXml(xml: string): Promise<void> {
    if (!editor.value) return
    state.error = null
    try {
      const result = await editor.value.importXML(xml)
      state.warnings = result.warnings ?? []
      state.ready = true
      state.dirty = false
      state.changes += 1
      state.info = readDiagramInfoFromEditor(services())
      refreshCommandState()
    } catch (error) {
      state.error = (error as Error).message
      throw error
    }
  }

  return { onCommand, onViewbox, importXml }
}

export function createEditorStore(options: EditorStoreOptions = {}) {
  const factory = options.factory ?? defaultEditorFactory
  const editor = shallowRef<EditorLike | null>(null)
  const state = reactive<EditorState>({ ready: false, dirty: false, canUndo: false, canRedo: false, scale: 1, changes: 0, info: null, warnings: [], error: null })
  const listeners = new Set<() => void>()

  function services(): EditorServices {
    if (!editor.value) throw new Error('Editor ist nicht bereit.')
    return editorServices(editor.value)
  }

  const sync = editorStateSync(editor, state, services, listeners)

  function mount(container: HTMLElement, keyboardTarget?: EventTarget): EditorLike {
    destroy()
    const instance = markRaw(factory({ container, locale: options.locale ?? 'de', flowaudit: options.flowaudit ?? {}, keyboardTarget }))
    instance.on('commandStack.changed', sync.onCommand)
    instance.on('canvas.viewbox.changed', sync.onViewbox)
    editor.value = instance
    return instance
  }

  const { exportXml, exportSvg } = editorOutput(editor)

  function markSaved(): void {
    state.dirty = false
  }

  const commandStack = () => editor.value?.get<CommandStack>('commandStack')

  const view = editorView(editor, state, services)

  /** Subscribe to model changes (commands); returns an unsubscribe function. */
  function onChange(listener: () => void): () => void {
    listeners.add(listener)
    return () => listeners.delete(listener)
  }

  function destroy(): void {
    editor.value?.destroy()
    editor.value = null
    state.ready = false
  }

  return {
    state: readonly(state),
    editor: computed(() => editor.value),
    mount,
    importXml: sync.importXml,
    exportXml,
    exportSvg,
    markSaved,
    undo: () => commandStack()?.undo(),
    redo: () => commandStack()?.redo(),
    ...view,
    services,
    onChange,
    destroy,
  }
}
