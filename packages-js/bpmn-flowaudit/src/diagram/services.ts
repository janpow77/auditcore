/**
 * Structural types for the diagram-js services this package uses.
 *
 * This is the adapter boundary to diagram-js: everything the FlowAudit
 * layer needs from the editor core is described here, so the rest of the
 * package stays free of `any`. The shapes follow the service contract of
 * `@flowaudit/bpmn-editor` (bpmn-js compatible names and semantics).
 */

export interface ModdleElement {
  $type: string
  $parent?: ModdleElement
  $attrs?: Record<string, string>
  id?: string
  name?: string
  get(name: string): unknown
  set(name: string, value: unknown): void
  [key: string]: unknown
}

export interface Point {
  x: number
  y: number
}

export interface DiagramElement {
  id: string
  type: string
  businessObject: ModdleElement
  di?: ModdleElement
  x?: number
  y?: number
  width?: number
  height?: number
  parent?: DiagramElement
  children?: DiagramElement[]
  labelTarget?: DiagramElement
  waypoints?: Point[]
}

export interface ModdleFactory {
  create(type: string, attrs?: Record<string, unknown>): ModdleElement
}

export interface Modeling {
  updateProperties(element: DiagramElement, props: Record<string, unknown>): void
  updateModdleProperties(element: DiagramElement, moddleElement: ModdleElement, props: Record<string, unknown>): void
  setColor(elements: DiagramElement[], colors: { fill?: string | null; stroke?: string | null }): void
  resizeShape(element: DiagramElement, bounds: { x: number; y: number; width: number; height: number }): void
  updateLabel?(element: DiagramElement, text: string): void
  addLane?(element: DiagramElement, location: 'top' | 'bottom' | 'left' | 'right'): DiagramElement
}

export type EventCallback = (event: Record<string, unknown>) => unknown

export interface EventBus {
  on(event: string | string[], priority: number, callback: EventCallback): void
  on(event: string | string[], callback: EventCallback): void
  off(event: string | string[], callback?: EventCallback): void
  fire(event: string, payload?: Record<string, unknown>): unknown
}

export interface ElementRegistry {
  get(id: string): DiagramElement | undefined
  getAll(): DiagramElement[]
  filter(predicate: (element: DiagramElement) => boolean): DiagramElement[]
  getGraphics(element: DiagramElement | string): SVGElement | undefined
}

export interface Viewbox {
  x: number
  y: number
  width: number
  height: number
  scale: number
  inner?: { x: number; y: number; width: number; height: number }
  outer?: { width: number; height: number }
}

export interface Canvas {
  getRootElement(): DiagramElement
  addMarker(element: DiagramElement | string, marker: string): void
  removeMarker(element: DiagramElement | string, marker: string): void
  hasMarker(element: DiagramElement | string, marker: string): boolean
  viewbox(box?: Partial<Viewbox>): Viewbox
  zoom(level?: number | 'fit-viewport', center?: Point | 'auto'): number
  scrollToElement(element: DiagramElement | string, padding?: number): void
  getContainer(): HTMLElement
}

export interface Selection {
  get(): DiagramElement[]
  select(elements: DiagramElement | DiagramElement[] | null, add?: boolean): void
}

export interface CommandStack {
  undo(): void
  redo(): void
  canUndo(): boolean
  canRedo(): boolean
}

export interface ElementFactory {
  createShape(attrs: Record<string, unknown>): DiagramElement
  createParticipantShape?(attrs?: Record<string, unknown> | boolean): DiagramElement
}

export interface Create {
  start(event: Event, shape: DiagramElement | DiagramElement[], context?: Record<string, unknown>): void
}

export interface PaletteEntry {
  group: string
  className?: string
  title: string
  html?: string
  imageUrl?: string
  action: { click?: (event: Event) => void; dragstart?: (event: Event) => void }
}

export interface Palette {
  registerProvider(priority: number, provider: { getPaletteEntries(): (entries: Record<string, PaletteEntry>) => Record<string, PaletteEntry> }): void
  getEntries?(): Record<string, PaletteEntry>
  triggerEntry?(id: string, action: string, event: Event, autoActivate?: boolean): void
}

export interface ContextPadEntry {
  group: string
  className?: string
  title: string
  html?: string
  imageUrl?: string
  action: { click: (event: Event, element: DiagramElement) => unknown }
}

export interface ContextPad {
  registerProvider(
    priority: number,
    provider: { getContextPadEntries(element: DiagramElement): (entries: Record<string, ContextPadEntry>) => Record<string, ContextPadEntry> },
  ): void
}

export type Translate = (template: string, replacements?: Record<string, string>) => string

/** The `get(name)` accessor of the editor (diagram-js injector). */
export interface ServiceLocator {
  get<T = unknown>(name: string, strict?: boolean): T
}

/** Minimal editor surface used by the FlowAudit helpers. */
export interface EditorServices {
  canvas: Canvas
  elementRegistry: ElementRegistry
  modeling: Modeling
  moddle: ModdleFactory
  selection?: Selection
  eventBus?: EventBus
}

export function editorServices(locator: ServiceLocator): EditorServices {
  return {
    canvas: locator.get<Canvas>('canvas'),
    elementRegistry: locator.get<ElementRegistry>('elementRegistry'),
    modeling: locator.get<Modeling>('modeling'),
    moddle: locator.get<ModdleFactory>('moddle'),
    selection: locator.get<Selection>('selection'),
    eventBus: locator.get<EventBus>('eventBus'),
  }
}
