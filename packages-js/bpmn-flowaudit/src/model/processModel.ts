/**
 * Framework-free snapshot of a diagram.
 *
 * From moddle definitions (headless) or from a running editor the same flat
 * list of elements is built: type, name, documentation, lane/pool with
 * actor, FlowAudit data, colour and bounds. Validation, reports,
 * comparison, walk-through and key filter work on this form only.
 */

import type { ModdleElement } from '../diagram/services'
import type { Actor, DiagramInfo, Extensions } from '../schema/types'
import { readExtensions } from './extensions'

export interface Bounds {
  x: number
  y: number
  width: number
  height: number
}

export interface ElementActor extends Actor {
  /** Lane or pool that carries the actor (or the innermost lane). */
  sourceId: string
  sourceName: string
}

export interface ModelElement {
  id: string
  /** BPMN type, e.g. `bpmn:Task`. */
  type: string
  name: string
  documentation: string
  extensions: Extensions
  laneId?: string
  poolId?: string
  actor?: ElementActor
  incoming: string[]
  outgoing: string[]
  sourceId?: string
  targetId?: string
  eventDefinitions: string[]
  /** Unqualified legacy attributes (FlowStat), e.g. `costEstimate`. */
  attributes: Record<string, string>
  color?: { fill?: string; stroke?: string }
  bounds?: Bounds
  defaultFlow?: string
  calledElement?: string
  parentId?: string
  processId?: string
  conditional?: boolean
  attachedTo?: string
  isCompensation?: boolean
  isEventSubProcess?: boolean
  linkName?: string
  dataRef?: string
  hasDataAssociation?: boolean
  /** Data objects/stores connected by data associations (input or output). */
  dataObjects?: string[]
}

export interface ProcessModel {
  info: DiagramInfo | null
  /** Id of the main element (collaboration or first process). */
  mainId: string | null
  elements: ModelElement[]
  byId: Map<string, ModelElement>
}

function getList(bo: ModdleElement, name: string): ModdleElement[] {
  return (bo.get(name) as ModdleElement[] | undefined) ?? []
}

function getRef(bo: ModdleElement, name: string): string | undefined {
  const value = bo.get(name) as ModdleElement | undefined
  return value && typeof value === 'object' && value.id ? String(value.id) : undefined
}

function documentationOf(bo: ModdleElement): string {
  return getList(bo, 'documentation')
    .map((doc) => String(doc.get('text') ?? ''))
    .filter(Boolean)
    .join('\n')
}

function legacyAttributes(bo: ModdleElement): Record<string, string> {
  return Object.fromEntries(Object.entries(bo.$attrs ?? {}).filter(([name, value]) => !name.includes(':') && typeof value === 'string'))
}

function dataObjectsOf(bo: ModdleElement): string[] | undefined {
  const outputs = getList(bo, 'dataOutputAssociations').map((association) => getRef(association, 'targetRef'))
  const inputs = getList(bo, 'dataInputAssociations').flatMap((association) => getList(association, 'sourceRef').map((ref) => ref.id))
  const ids = [...outputs, ...inputs].filter((id): id is string => Boolean(id)).map(String)
  return ids.length ? [...new Set(ids)] : undefined
}

/** Optional properties read from the business object (declarative). */
const OPTIONAL_READERS: [keyof ModelElement, (bo: ModdleElement) => unknown][] = [
  ['sourceId', (bo) => getRef(bo, 'sourceRef')],
  ['targetId', (bo) => getRef(bo, 'targetRef')],
  ['defaultFlow', (bo) => getRef(bo, 'default')],
  ['attachedTo', (bo) => getRef(bo, 'attachedToRef')],
  ['dataRef', (bo) => getRef(bo, 'dataObjectRef') ?? getRef(bo, 'dataStoreRef')],
  ['conditional', (bo) => (bo.get('conditionExpression') ? true : undefined)],
  ['isCompensation', (bo) => (bo.get('isForCompensation') ? true : undefined)],
  ['isEventSubProcess', (bo) => (bo.get('triggeredByEvent') ? true : undefined)],
  ['calledElement', (bo) => (bo.$type === 'bpmn:CallActivity' ? String(bo.get('calledElement') ?? '') || undefined : undefined)],
  ['linkName', (bo) => getList(bo, 'eventDefinitions').find((d) => d.$type === 'bpmn:LinkEventDefinition')?.get('name') ?? undefined],
  [
    'hasDataAssociation',
    (bo) => (getList(bo, 'dataInputAssociations').length + getList(bo, 'dataOutputAssociations').length ? true : undefined),
  ],
  ['dataObjects', dataObjectsOf],
]

export function createModelElement(bo: ModdleElement): ModelElement {
  const element: ModelElement = {
    id: String(bo.id ?? ''),
    type: bo.$type,
    // Text annotations carry their label in `text`.
    name: String(bo.get(bo.$type === 'bpmn:TextAnnotation' ? 'text' : 'name') ?? '').trim(),
    documentation: documentationOf(bo),
    extensions: readExtensions(bo),
    incoming: getList(bo, 'incoming').map((el) => String(el.id)),
    outgoing: getList(bo, 'outgoing').map((el) => String(el.id)),
    eventDefinitions: getList(bo, 'eventDefinitions').map((d) => d.$type),
    attributes: legacyAttributes(bo),
  }
  const target = element as unknown as Record<string, unknown>
  for (const [key, read] of OPTIONAL_READERS) {
    const value = read(bo)
    if (value !== undefined) target[key] = value
  }
  return element
}

/** Reads a colour from the DI (`bioc:` or `color:` namespace). */
export function colorFromDi(di: ModdleElement | undefined): { fill?: string; stroke?: string } | undefined {
  if (!di) return undefined
  const read = (names: string[]) => {
    for (const name of names) {
      const value = di.get(name) ?? di.$attrs?.[name]
      if (typeof value === 'string' && value) return value.toLowerCase()
    }
    return undefined
  }
  const fill = read(['bioc:fill', 'color:background-color'])
  const stroke = read(['bioc:stroke', 'color:border-color'])
  return fill || stroke ? { fill, stroke } : undefined
}

export const TASK_TYPES = new Set(['task', 'userTask', 'manualTask', 'serviceTask', 'scriptTask', 'businessRuleTask', 'sendTask', 'receiveTask'])
const SUB_PROCESS_TYPES = new Set(['subProcess', 'adHocSubProcess', 'transaction'])
const EVENT_TYPES = new Set(['startEvent', 'endEvent', 'intermediateThrowEvent', 'intermediateCatchEvent', 'boundaryEvent', 'implicitThrowEvent'])
const GATEWAY_TYPES = new Set(['exclusiveGateway', 'inclusiveGateway', 'parallelGateway', 'complexGateway', 'eventBasedGateway'])

/** `bpmn:UserTask` → `userTask`. */
export function localType(type: string): string {
  const name = type.includes(':') ? type.split(':')[1] ?? type : type
  return name.charAt(0).toLowerCase() + name.slice(1)
}

export const isTask = (type: string): boolean => TASK_TYPES.has(localType(type))
export const isActivity = (type: string): boolean =>
  isTask(type) || SUB_PROCESS_TYPES.has(localType(type)) || localType(type) === 'callActivity'
export const isEvent = (type: string): boolean => EVENT_TYPES.has(localType(type))
export const isGateway = (type: string): boolean => GATEWAY_TYPES.has(localType(type))
export const isFlowNode = (type: string): boolean => isActivity(type) || isEvent(type) || isGateway(type)

export function activities(model: ProcessModel): ModelElement[] {
  return model.elements.filter((element) => isActivity(element.type))
}

export function displayName(element: ModelElement): string {
  return element.name.trim() || element.id
}
