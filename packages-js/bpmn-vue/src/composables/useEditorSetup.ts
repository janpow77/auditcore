/**
 * Setup of one editor: stores, context, mounting, two-way XML sync, palette
 * entries, context-pad popovers and view state (panels, modes, page view).
 */

import { computed, onBeforeUnmount, reactive, ref, shallowRef, watch, type Ref } from 'vue'
import {
  applyDirection,
  COLOR_PICKER_EVENT,
  keepDirection,
  rolesFor,
  type DiagramElement,
  type Direction,
  type FlowauditDecorations,
  type FlowauditModuleOptions,
  type KeyKind,
  type Palette,
  type ProfileData,
  type RolePaletteProvider,
  type ValidationPort,
  type Viewbox,
} from '@flowaudit/bpmn-flowaudit'
import type { EditorFactory } from '../editor/createEditor'
import { readPaletteEntries, type PaletteItem } from '../components/palette/paletteEntries'
import { createEditorStore, type EditorStore } from '../stores/editorStore'
import { createSelectionStore } from '../stores/selectionStore'
import { createValidationStore, type ValidationStore } from '../stores/validationStore'
import { provideEditorContext, type EditorPorts } from '../stores/context'

export type SideView = 'properties' | 'issues' | 'walkthrough' | 'compare'
export type DialogId = 'info' | 'export' | 'enrich' | 'esi' | 'search' | 'shortcuts' | 'xml'

export interface EditorSetupOptions {
  xml: () => string
  profile: () => ProfileData | null
  readonly: () => boolean
  locale: 'de' | 'en'
  ports: EditorPorts & { validation?: ValidationPort }
  factory?: EditorFactory
  flowaudit?: FlowauditModuleOptions
  onXml: (xml: string) => void
  onError: (message: string) => void
}

export interface Popover {
  kind: 'color' | 'role'
  x: number
  y: number
  element: DiagramElement
  mode?: 'assign' | 'add-lane'
}

/** View state of the editor: panels, side view, dialogs, key filter, modes. */
function createUiState() {
  return reactive({
    leftOpen: true,
    rightOpen: true,
    side: 'properties' as SideView,
    dialogs: { info: false, export: false, enrich: false, esi: false, search: false, shortcuts: false, xml: false } as Record<DialogId, boolean>,
    filterOpen: false,
    filterKind: 'ka' as KeyKind,
    filterValue: '',
    filterHits: 0,
    pageView: 'aus',
    direction: 'waagerecht' as Direction,
    message: '',
    decorations: true,
    minimap: false,
  })
}

/** Palette entries of the running editor and triggering them from the Vue palette. */
function usePaletteItems(editor: EditorStore, profile: () => ProfileData | null) {
  const palette = shallowRef<PaletteItem[]>([])
  const instance = () => editor.editor.value

  function readPalette(): void {
    const service = instance()?.get<Palette>('palette', false)
    palette.value = service?.getEntries ? readPaletteEntries(service.getEntries() as never, rolesFor(profile())) : []
  }

  function trigger(id: string, event: Event): void {
    instance()?.get<Palette>('palette', false)?.triggerEntry?.(id, event.type === 'dragstart' ? 'dragstart' : 'click', event, true)
  }

  return { palette, readPalette, trigger }
}

/** Two-way XML sync: import on prop changes, emit after commands (no echo). */
function useXmlSync(editor: EditorStore, validation: ValidationStore, host: Ref<HTMLElement | null>, options: EditorSetupOptions) {
  let lastXml = ''

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
    if (host.value?.clientWidth) editor.zoom('fit')
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

  editor.onChange(emitXml)
  watch(options.xml, load)
  return load
}

export function useEditorSetup(host: Ref<HTMLElement | null>, options: EditorSetupOptions) {
  const editor = createEditorStore({ factory: options.factory, locale: options.locale, flowaudit: { profile: options.profile(), locale: options.locale, ...options.flowaudit } })
  const selection = createSelectionStore(editor)
  const validation = createValidationStore(editor, { profile: options.profile, port: options.ports.validation })
  provideEditorContext({ editor, selection, validation, ports: options.ports, profile: options.profile, readonly: options.readonly })

  const ui = createUiState()
  const viewbox = ref<Viewbox>({ x: 0, y: 0, width: 0, height: 0, scale: 1 })
  const size = reactive({ width: 0, height: 0 })
  const { palette, readPalette, trigger } = usePaletteItems(editor, options.profile)
  const popover = shallowRef<Popover | null>(null)
  let stopDirection: (() => void) | null = null
  let resize: ResizeObserver | null = null

  const instance = () => editor.editor.value

  function toPopover(event: unknown, kind: Popover['kind']): void {
    const payload = event as { element: DiagramElement; event?: MouseEvent; mode?: Popover['mode'] }
    const box = host.value?.getBoundingClientRect()
    popover.value = { kind, element: payload.element, mode: payload.mode, x: (payload.event?.clientX ?? 0) - (box?.left ?? 0), y: (payload.event?.clientY ?? 0) - (box?.top ?? 0) }
  }

  function mount(): void {
    if (!host.value) return
    const created = editor.mount(host.value, host.value)
    created.on('canvas.viewbox.changed', (event) => (viewbox.value = (event as { viewbox: Viewbox }).viewbox))
    created.on(COLOR_PICKER_EVENT, (event) => toPopover(event, 'color'))
    created.on('flowaudit.role.choose', (event) => toPopover(event, 'role'))
    created.on('element.click', () => (popover.value = null))
    stopDirection = keepDirection(created, () => ui.direction)
    readPalette()
    resize = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(() => Object.assign(size, { width: host.value?.clientWidth ?? 0, height: host.value?.clientHeight ?? 0 }))
    resize?.observe(host.value)
  }

  const load = useXmlSync(editor, validation, host, options)
  watch(
    () => ui.decorations,
    (show) => instance()?.get<FlowauditDecorations>('flowauditDecorations', false)?.setVisibility({ actors: show, markers: show, auditReferences: show }),
  )
  watch(options.profile, (profile) => {
    instance()?.get<FlowauditDecorations>('flowauditDecorations', false)?.setProfile(profile)
    instance()?.get<RolePaletteProvider>('flowauditRolePalette', false)?.setProfile(profile)
    readPalette()
    validation.runLocal()
  })

  function setDirection(direction: Direction): void {
    ui.direction = direction
    const created = instance()
    if (created && applyDirection(created, direction) === 0) ui.message = 'toolbar.directionHint'
  }

  onBeforeUnmount(() => {
    stopDirection?.()
    resize?.disconnect()
    editor.destroy()
  })

  return { editor, selection, validation, ui, viewbox, size, palette, popover, mount, load, setDirection, trigger, readonlyNow: computed(options.readonly) }
}
