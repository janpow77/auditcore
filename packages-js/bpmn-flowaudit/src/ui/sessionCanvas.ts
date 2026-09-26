/**
 * Canvas side of an editor session: viewbox and size for the page grid,
 * palette entries of the running editor and the context-pad popovers
 * (colour and role choice).
 */

import { COLOR_PICKER_EVENT, rolesFor, type DiagramElement, type Palette, type ProfileData, type Viewbox } from '../index'
import type { EditorCore } from './editorCore'
import type { EditorLike } from './editorFactory'
import { readPaletteEntries, type PaletteItem } from './paletteEntries'
import type { Store } from './store'

export interface Popover {
  kind: 'color' | 'role'
  x: number
  y: number
  element: DiagramElement
  mode?: 'assign' | 'add-lane'
}

export interface CanvasState {
  viewbox: Viewbox
  size: { width: number; height: number }
  palette: PaletteItem[]
  popover: Popover | null
}

export function initialCanvasState(): CanvasState {
  return { viewbox: { x: 0, y: 0, width: 0, height: 0, scale: 1 }, size: { width: 0, height: 0 }, palette: [], popover: null }
}

interface CanvasOptions {
  host: () => HTMLElement | null
  profile: () => ProfileData | null
}

export function sessionCanvas(parts: { editor: EditorCore; canvas: Store<CanvasState> }, options: CanvasOptions) {
  const { editor, canvas } = parts
  let resize: ResizeObserver | null = null

  function readPalette(): void {
    const service = editor.instance()?.get<Palette>('palette', false)
    canvas.set({ palette: service?.getEntries ? readPaletteEntries(service.getEntries() as never, rolesFor(options.profile())) : [] })
  }

  function trigger(id: string, event: Event): void {
    editor.instance()?.get<Palette>('palette', false)?.triggerEntry?.(id, event.type === 'dragstart' ? 'dragstart' : 'click', event, true)
  }

  function toPopover(event: unknown, kind: Popover['kind']): void {
    const payload = event as { element: DiagramElement; event?: MouseEvent; mode?: Popover['mode'] }
    const box = options.host()?.getBoundingClientRect()
    canvas.set({ popover: { kind, element: payload.element, mode: payload.mode, x: (payload.event?.clientX ?? 0) - (box?.left ?? 0), y: (payload.event?.clientY ?? 0) - (box?.top ?? 0) } })
  }

  function measure(): void {
    const host = options.host()
    canvas.set({ size: { width: host?.clientWidth ?? 0, height: host?.clientHeight ?? 0 } })
  }

  function bind(created: EditorLike): void {
    created.on('canvas.viewbox.changed', (event) => canvas.set({ viewbox: (event as { viewbox: Viewbox }).viewbox }))
    created.on(COLOR_PICKER_EVENT, (event) => toPopover(event, 'color'))
    created.on('flowaudit.role.choose', (event) => toPopover(event, 'role'))
    created.on('element.click', () => canvas.set({ popover: null }))
    readPalette()
    const host = options.host()
    resize = typeof ResizeObserver === 'undefined' || !host ? null : new ResizeObserver(measure)
    if (host) resize?.observe(host)
  }

  return {
    bind,
    readPalette,
    trigger,
    closePopover: () => canvas.set({ popover: null }),
    unbind: () => resize?.disconnect(),
  }
}
