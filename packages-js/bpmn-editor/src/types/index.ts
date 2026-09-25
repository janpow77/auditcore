/**
 * Typschicht des Editors.
 *
 * - `ModdleElement`: semantisches BPMN-Objekt bzw. DI-Objekt (moddle).
 * - `BpmnShape`, `BpmnConnection`, … : Diagrammelemente von diagram-js mit
 *   BPMN-Bezug (`businessObject`, `di`).
 * - Dienst-Typen: aus den Typdeklarationen von diagram-js übernommen.
 */

import type DjsCanvas from 'diagram-js/lib/core/Canvas'
import type DjsEventBus from 'diagram-js/lib/core/EventBus'
import type DjsGraphicsFactory from 'diagram-js/lib/core/GraphicsFactory'
import type DjsCommandStack from 'diagram-js/lib/command/CommandStack'
import type DjsSelection from 'diagram-js/lib/features/selection/Selection'
import type DjsOverlays from 'diagram-js/lib/features/overlays/Overlays'
import type {
  Connection as DjsConnection,
  Element as DjsElement,
  Label as DjsLabel,
  Root as DjsRoot,
  Shape as DjsShape,
} from 'diagram-js/lib/model/Types'

// ---------------------------------------------------------------------------
// moddle
// ---------------------------------------------------------------------------

export interface ModdlePropertyDescriptor {
  name: string
  type: string
  isMany?: boolean
  isReference?: boolean
  isVirtual?: boolean
  isAttr?: boolean
  isBody?: boolean
  default?: unknown
}

export interface ModdleDescriptor {
  name: string
  isGeneric?: boolean
  ns?: { prefix: string; localName: string; uri?: string }
  properties?: ModdlePropertyDescriptor[]
  propertiesByName?: Record<string, ModdlePropertyDescriptor | undefined>
}

/** Semantisches BPMN- oder DI-Objekt (moddle). Nur genutzte Eigenschaften sind typisiert. */
export interface ModdleElement {
  $type: string
  $parent?: ModdleElement | null
  $attrs: Record<string, string>
  $descriptor: ModdleDescriptor
  $instanceOf(type: string): boolean
  get<T = unknown>(name: string): T
  set(name: string, value: unknown): void

  id?: string
  name?: string
  text?: string
  value?: string
  documentation?: ModdleElement[]
  extensionElements?: ModdleElement
  values?: ModdleElement[]

  // Ablauf
  incoming?: ModdleElement[]
  outgoing?: ModdleElement[]
  sourceRef?: ModdleElement
  targetRef?: ModdleElement
  default?: ModdleElement
  conditionExpression?: ModdleElement
  flowElements?: ModdleElement[]
  artifacts?: ModdleElement[]
  laneSets?: ModdleElement[]
  lanes?: ModdleElement[]
  childLaneSet?: ModdleElement
  flowNodeRef?: ModdleElement[]

  // Ereignisse, Gateways, Aktivitäten
  eventDefinitions?: ModdleElement[]
  attachedToRef?: ModdleElement
  cancelActivity?: boolean
  isInterrupting?: boolean
  parallelMultiple?: boolean
  instantiate?: boolean
  eventGatewayType?: string
  loopCharacteristics?: ModdleElement
  isSequential?: boolean
  isForCompensation?: boolean
  triggeredByEvent?: boolean
  messageRef?: ModdleElement
  associationDirection?: string

  // Daten und Artefakte
  dataObjectRef?: ModdleElement
  isCollection?: boolean
  categoryValueRef?: ModdleElement
  ioSpecification?: ModdleElement

  // Kollaboration
  processRef?: ModdleElement
  participants?: ModdleElement[]
  messageFlows?: ModdleElement[]
  participantMultiplicity?: ModdleElement
  rootElements?: ModdleElement[]
  diagrams?: ModdleElement[]

  // DI
  plane?: ModdleElement
  planeElement?: ModdleElement[]
  bpmnElement?: ModdleElement
  bounds?: ModdleElement
  waypoint?: ModdleElement[]
  label?: ModdleElement
  isHorizontal?: boolean
  isExpanded?: boolean
  isMarkerVisible?: boolean
  x?: number
  y?: number
  width?: number
  height?: number
}

export interface Moddle {
  create(type: string, attrs?: Record<string, unknown>): ModdleElement
  createAny(name: string, nsUri: string | undefined, properties: Record<string, unknown>): ModdleElement
  fromXML(xml: string, typeName?: string): Promise<{
    rootElement: ModdleElement
    warnings: Array<{ message: string } | string>
    elementsById: Record<string, ModdleElement>
  }>
  toXML(element: ModdleElement, options?: { format?: boolean; preamble?: boolean }): Promise<{ xml: string }>
  ids?: unknown
}

// ---------------------------------------------------------------------------
// Diagrammelemente
// ---------------------------------------------------------------------------

type WithBpmn = { businessObject: ModdleElement; di?: ModdleElement }

export type BpmnElement = DjsElement & WithBpmn
export type BpmnShape = DjsShape & WithBpmn
export type BpmnConnection = DjsConnection & WithBpmn
export type BpmnRoot = DjsRoot & WithBpmn
export type BpmnLabel = DjsLabel & WithBpmn
export type BpmnParent = BpmnShape | BpmnRoot

export interface Point {
  x: number
  y: number
  original?: Point
}

export interface Bounds {
  x: number
  y: number
  width: number
  height: number
}

// ---------------------------------------------------------------------------
// Dienste
// ---------------------------------------------------------------------------

export type EventBus = DjsEventBus
export type Canvas = DjsCanvas
/** Elementregister (typisiert auf BPMN-Elemente). */
export interface ElementRegistry {
  get(id: string): BpmnElement | undefined
  getAll(): BpmnElement[]
  filter(fn: (element: BpmnElement, gfx: SVGElement) => boolean): BpmnElement[]
  find(fn: (element: BpmnElement, gfx: SVGElement) => boolean): BpmnElement | undefined
  forEach(fn: (element: BpmnElement, gfx: SVGElement) => void): void
  getGraphics(element: BpmnElement | string, secondary?: boolean): SVGElement
  updateId(element: BpmnElement, newId: string): void
}
export type GraphicsFactory = DjsGraphicsFactory
export type CommandStack = DjsCommandStack
export type Selection = DjsSelection
export type Overlays = DjsOverlays
export type Translate = (template: string, replacements?: Record<string, unknown>) => string

/** Ereignisobjekt eines Befehls (CommandInterceptor). */
export interface CommandEvent<C = CommandContext> {
  command: string
  context: C
}

/** Befehlskontext – Felder je nach Befehl. */
export interface CommandContext {
  [key: string]: unknown
  hints?: Record<string, unknown>
}

/** Formen, deren Lage bekannt ist (für Hilfsrechnungen). */
export type Positioned = Bounds & Partial<WithBpmn>
