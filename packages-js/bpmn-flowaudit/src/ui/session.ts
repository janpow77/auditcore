/**
 * Editor session: the controllers of one editor (editor, selection,
 * validation), mounting, two-way XML sync, palette entries, context-pad
 * popovers and the effects of the view state (key filter, decorations,
 * flow direction). The view state itself is passed in as `StateAccess`, so
 * Vue can keep a `reactive` and React a store.
 */

import { applyDirection, elementsForKey, keepDirection, type Direction, type FlowauditDecorations, type FlowauditHighlight, type FlowauditModuleOptions, type ProfileData, type RolePaletteProvider, type ValidationPort } from '../index'
import { createEditorCore, type EditorCore } from './editorCore'
import type { EditorFactory } from './editorFactory'
import type { EditorPorts } from './ports'
import { createSelectionCore } from './selectionCore'
import { createStore, type StateAccess } from './store'
import { createValidationCore, type ValidationCore } from './validationCore'
import { initialCanvasState, sessionCanvas, type CanvasState } from './sessionCanvas'
import type { UiState } from './uiState'

export interface EditorSessionOptions {
  ui: StateAccess<UiState>
  host: () => HTMLElement | null
  profile: () => ProfileData | null
  readonly: () => boolean
  locale: 'de' | 'en'
  ports: EditorPorts & { validation?: ValidationPort }
  factory: EditorFactory
  flowaudit?: FlowauditModuleOptions
  onXml: (xml: string) => void
  onError: (message: string) => void
}

export type EditorSession = ReturnType<typeof createEditorSession>

/** Two-way XML sync: import on new input, report after commands (no echo). */
function xmlSync(session: { editor: EditorCore; validation: ValidationCore }, options: EditorSessionOptions) {
  let lastXml = ''
  const { editor, validation } = session

  async function load(xml: string): Promise<void> {
    if (!xml || xml === lastXml) return
    lastXml = xml
    try {
      await editor.importXml(xml)
    } catch (error) {
      options.onError((error as Error).message)
      return
    }
    // A hidden container has no size; fitting would produce an invalid viewbox.
    if (options.host()?.clientWidth) editor.zoom('fit')
    validation.runLocal()
  }

  async function emitXml(): Promise<void> {
    try {
      lastXml = await editor.exportXml()
      options.onXml(lastXml)
    } catch {
      // Temporarily invalid states during editing are not reported.
    }
  }

  return { load, stop: editor.onChange(emitXml) }
}

/** Effects of the view state on the running editor. */
function uiEffects(session: { editor: EditorCore }, options: EditorSessionOptions) {
  const { editor } = session
  const ui = options.ui
  const service = <T>(name: string) => editor.instance()?.get<T>(name, false)

  function refreshKeyFilter(): void {
    const layer = service<FlowauditHighlight>('flowauditHighlight')
    if (!layer || !editor.store.get().ready) return
    const { filterOpen, filterValue, filterKind } = ui.get()
    if (!filterOpen || !filterValue.trim()) {
      layer.clear('filter')
      ui.set({ filterHits: 0 })
      return
    }
    ui.set({ filterHits: layer.filter(elementsForKey(editor.model(), filterKind, filterValue)) })
  }

  function applyDecorations(): void {
    const show = ui.get().decorations
    service<FlowauditDecorations>('flowauditDecorations')?.setVisibility({ actors: show, markers: show, auditReferences: show })
  }

  function setDirection(direction: Direction): void {
    ui.set({ direction })
    const created = editor.instance()
    if (created && applyDirection(created, direction) === 0) ui.set({ message: 'toolbar.directionHint' })
  }

  /** Applies a view-state change and its effects (React path; Vue watches). */
  function updateUi(patch: Partial<UiState>): void {
    ui.set(patch)
    if ('decorations' in patch) applyDecorations()
    if ('filterOpen' in patch || 'filterKind' in patch || 'filterValue' in patch) refreshKeyFilter()
  }

  return { refreshKeyFilter, applyDecorations, setDirection, updateUi }
}

export function createEditorSession(options: EditorSessionOptions) {
  const editor = createEditorCore({ factory: options.factory, locale: options.locale, flowaudit: { profile: options.profile(), locale: options.locale, ...options.flowaudit } })
  const selection = createSelectionCore(editor)
  const validation = createValidationCore(editor, { profile: options.profile, port: options.ports.validation })
  const canvas = createStore<CanvasState>(initialCanvasState())
  const view = sessionCanvas({ editor, canvas }, options)
  const effects = uiEffects({ editor }, options)
  const sync = xmlSync({ editor, validation }, options)
  let stopDirection: (() => void) | null = null
  let lastChanges = -1
  const stopChanges = editor.store.subscribe(() => {
    const { changes } = editor.store.get()
    if (changes === lastChanges) return
    lastChanges = changes
    effects.refreshKeyFilter()
  })

  function mount(): void {
    const host = options.host()
    if (!host) return
    const created = editor.mount(host, host)
    view.bind(created)
    stopDirection = keepDirection(created, () => options.ui.get().direction)
  }

  function applyProfile(): void {
    const profile = options.profile()
    editor.instance()?.get<FlowauditDecorations>('flowauditDecorations', false)?.setProfile(profile)
    editor.instance()?.get<RolePaletteProvider>('flowauditRolePalette', false)?.setProfile(profile)
    view.readPalette()
    validation.runLocal()
  }

  function dispose(): void {
    stopDirection?.()
    view.unbind()
    sync.stop()
    stopChanges()
    selection.dispose()
    validation.dispose()
    editor.destroy()
  }

  return { editor, selection, validation, canvas, ui: options.ui, mount, load: sync.load, applyProfile, ...effects, trigger: view.trigger, readPalette: view.readPalette, closePopover: view.closePopover, readonly: options.readonly, dispose }
}
