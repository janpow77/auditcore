/**
 * Hilfsfunktionen für den Zugriff auf das semantische Modell (moddle) und
 * die Diagramm-Information (DI) eines Diagrammelements.
 *
 * Konvention (kompatibel zu den audit_designer-Erweiterungen):
 * - `element.businessObject` ist das moddle-Element (z. B. `bpmn:Task`),
 * - `element.di` ist das zugehörige `bpmndi:BPMNShape` / `bpmndi:BPMNEdge`
 *   bzw. bei der Wurzel die `bpmndi:BPMNPlane`.
 */

import type { Element as DjsElement } from 'diagram-js/lib/model/Types'

import type { BpmnElement, ModdleElement } from '../types'

/** Diagrammelement oder moddle-Objekt. */
export type BpmnLike = DjsElement | BpmnElement | ModdleElement

function hasBusinessObject(value: BpmnLike): value is BpmnElement {
  return 'businessObject' in value && !!(value as BpmnElement).businessObject
}

/** Liefert das semantische Objekt eines Diagrammelements (oder das Objekt selbst). */
export function getBusinessObject(element: BpmnLike): ModdleElement
export function getBusinessObject(element: BpmnLike | null | undefined): ModdleElement | undefined
export function getBusinessObject(element: BpmnLike | null | undefined): ModdleElement | undefined {
  if (!element) return undefined
  return hasBusinessObject(element) ? element.businessObject : (element as ModdleElement)
}

/** Liefert die DI eines Diagrammelements; Beschriftungen teilen die DI ihres Ziels. */
export function getDi(element: DjsElement | null | undefined): ModdleElement | undefined {
  if (!element) return undefined
  if (element.di) return element.di
  const target = element.labelTarget as BpmnElement | undefined
  return target ? target.di : undefined
}

/** Prüft, ob ein Element (oder moddle-Objekt) vom angegebenen Typ ist. */
export function is(element: BpmnLike | null | undefined, type: string): boolean {
  const bo = getBusinessObject(element)
  return !!bo && typeof bo.$instanceOf === 'function' && bo.$instanceOf(type)
}

/** Prüft, ob ein Element einem der Typen entspricht. */
export function isAny(element: BpmnLike | null | undefined, types: readonly string[]): boolean {
  return types.some((type) => is(element, type))
}

/** Aufgeklappt? Gilt für Teilprozesse, Pools und Aufrufaktivitäten. */
export function isExpanded(element: BpmnLike | null | undefined, di?: ModdleElement): boolean {
  if (!element) return false
  if (is(element, 'bpmn:CallActivity')) return false
  if (is(element, 'bpmn:SubProcess')) {
    const shapeDi = di || (hasBusinessObject(element) ? getDi(element) : undefined)
    if (shapeDi && is(shapeDi, 'bpmndi:BPMNPlane')) return true
    return !!shapeDi && !!shapeDi.isExpanded
  }
  if (is(element, 'bpmn:Participant')) return !!getBusinessObject(element).processRef
  return true
}

/** Waagerechte Ausrichtung eines Pools bzw. einer Bahn (Standard: ja). */
export function isHorizontal(element: DjsElement | null | undefined): boolean {
  if (!isAny(element, ['bpmn:Participant', 'bpmn:Lane'])) return true
  const di = getDi(element)
  const value = di ? di.get<boolean | undefined>('isHorizontal') : undefined
  return value === undefined ? true : !!value
}

export function isEventSubProcess(element: BpmnLike | null | undefined): boolean {
  return is(element, 'bpmn:SubProcess') && !!getBusinessObject(element)?.triggeredByEvent
}

/** Unterbrechend? Randereignisse über `cancelActivity`, Startereignisse über `isInterrupting`. */
export function isInterrupting(element: BpmnLike): boolean {
  const bo = getBusinessObject(element)
  if (is(bo, 'bpmn:BoundaryEvent')) return bo.cancelActivity !== false
  if (is(bo, 'bpmn:StartEvent')) return bo.isInterrupting !== false
  return true
}

export function getEventDefinitions(element: BpmnLike | null | undefined): ModdleElement[] {
  return getBusinessObject(element)?.eventDefinitions || []
}

export function getEventDefinition(element: BpmnLike | null | undefined, type?: string): ModdleElement | undefined {
  const definitions = getEventDefinitions(element)
  if (!type) return definitions[0]
  return definitions.find((definition) => is(definition, type))
}

export function hasEventDefinition(element: BpmnLike | null | undefined, type: string): boolean {
  return !!getEventDefinition(element, type)
}

export function isLabel(element: DjsElement | null | undefined): boolean {
  return !!element && !!element.labelTarget
}

export function isConnection(element: DjsElement | null | undefined): boolean {
  return !!element && !!element.waypoints
}

/**
 * Diagrammwurzel? Wurzeln haben weder Elternteil noch Lage (keine Breite);
 * neu erzeugte, noch nicht eingefügte Formen dagegen schon.
 */
export function isRoot(element: DjsElement | null | undefined): boolean {
  return !!element && !element.parent && !element.labelTarget && !element.waypoints && typeof element.width !== 'number'
}

/** Mehrfachinstanz- oder Schleifencharakteristik. */
export function getLoopType(element: BpmnLike): 'loop' | 'parallel' | 'sequential' | null {
  const loop = getBusinessObject(element).loopCharacteristics
  if (!loop) return null
  if (is(loop, 'bpmn:StandardLoopCharacteristics')) return 'loop'
  if (is(loop, 'bpmn:MultiInstanceLoopCharacteristics')) return loop.isSequential ? 'sequential' : 'parallel'
  return null
}

/** Wurzel-Definitionen eines moddle-Elements. */
export function getDefinitions(bo: ModdleElement | null | undefined): ModdleElement | undefined {
  let current = bo || undefined
  while (current && !is(current, 'bpmn:Definitions')) current = current.$parent || undefined
  return current
}

/** Fügt ein Element idempotent in eine Liste ein. */
export function addToList<T>(list: T[], item: T, index?: number): void {
  if (list.includes(item)) return
  if (typeof index === 'number' && index >= 0 && index <= list.length) list.splice(index, 0, item)
  else list.push(item)
}

/** Entfernt ein Element aus einer Liste und liefert den bisherigen Index. */
export function removeFromList<T>(list: T[] | undefined, item: T): number {
  if (!list) return -1
  const index = list.indexOf(item)
  if (index !== -1) list.splice(index, 1)
  return index
}

/** Liest eine Listen-Eigenschaft, sofern der Typ sie kennt. */
export function getList(container: ModdleElement | null | undefined, property: string): ModdleElement[] | undefined {
  if (!container || typeof container.get !== 'function') return undefined
  const descriptor = container.$descriptor
  if (descriptor && !descriptor.isGeneric && !descriptor.propertiesByName?.[property]) return undefined
  return container.get<ModdleElement[]>(property)
}

/** Oberster Vorfahr (Diagrammwurzel) eines Elements. */
export function getRootOf(element: DjsElement): BpmnElement {
  let current = element
  while (current.parent) current = current.parent
  return current as BpmnElement
}
