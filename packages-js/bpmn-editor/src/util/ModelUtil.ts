/**
 * Hilfsfunktionen für den Zugriff auf das semantische Modell (moddle) und
 * die Diagramm-Information (DI) eines Diagrammelements.
 *
 * Konvention (kompatibel zu den audit_designer-Erweiterungen):
 * - `element.businessObject` ist das moddle-Element (z. B. `bpmn:Task`),
 * - `element.di` ist das zugehörige `bpmndi:BPMNShape` / `bpmndi:BPMNEdge`
 *   bzw. bei der Wurzel die `bpmndi:BPMNPlane`.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export type ModdleElement = any
export type DiagramElement = any

/** Liefert das semantische Objekt eines Diagrammelements (oder das Objekt selbst). */
export function getBusinessObject(element: DiagramElement): ModdleElement {
  return (element && element.businessObject) || element
}

/** Liefert die DI eines Diagrammelements; Beschriftungen teilen die DI ihres Ziels. */
export function getDi(element: DiagramElement): ModdleElement {
  if (!element) return undefined
  if (element.di) return element.di
  if (element.labelTarget) return element.labelTarget.di
  return undefined
}

/** Prüft, ob ein Element (oder moddle-Objekt) vom angegebenen Typ ist. */
export function is(element: DiagramElement, type: string): boolean {
  const bo = getBusinessObject(element)
  return !!bo && typeof bo.$instanceOf === 'function' && bo.$instanceOf(type)
}

/** Prüft, ob ein Element einem der Typen entspricht. */
export function isAny(element: DiagramElement, types: string[]): boolean {
  return types.some((type) => is(element, type))
}

/** Liefert den nächsten Vorfahren (einschließlich des Elements) eines Typs. */
export function getParent(element: DiagramElement, anyType: string | string[]): DiagramElement | null {
  const types = Array.isArray(anyType) ? anyType : [anyType]
  let current = element?.parent
  while (current) {
    if (isAny(current, types)) return current
    current = current.parent
  }
  return null
}

/** Aufgeklappt? Gilt für Teilprozesse, Pools und Aufrufaktivitäten. */
export function isExpanded(element: DiagramElement, di?: ModdleElement): boolean {
  if (is(element, 'bpmn:CallActivity')) return false
  if (is(element, 'bpmn:SubProcess')) {
    di = di || getDi(element)
    if (di && is(di, 'bpmndi:BPMNPlane')) return true
    return !!di && !!di.isExpanded
  }
  if (is(element, 'bpmn:Participant')) {
    return !!getBusinessObject(element).processRef
  }
  return true
}

/** Waagerechte Ausrichtung eines Pools bzw. einer Bahn (Standard: ja). */
export function isHorizontal(element: DiagramElement): boolean {
  if (!isAny(element, ['bpmn:Participant', 'bpmn:Lane'])) return true
  const di = getDi(element)
  if (!di) return true
  const value = di.get ? di.get('isHorizontal') : di.isHorizontal
  return value === undefined ? true : !!value
}

export function isEventSubProcess(element: DiagramElement): boolean {
  return is(element, 'bpmn:SubProcess') && !!getBusinessObject(element).triggeredByEvent
}

/** Unterbrechend? Randereignisse über `cancelActivity`, Startereignisse über `isInterrupting`. */
export function isInterrupting(element: DiagramElement): boolean {
  const bo = getBusinessObject(element)
  if (is(bo, 'bpmn:BoundaryEvent')) return bo.cancelActivity !== false
  if (is(bo, 'bpmn:StartEvent')) return bo.isInterrupting !== false
  return true
}

export function getEventDefinitions(element: DiagramElement): ModdleElement[] {
  const bo = getBusinessObject(element)
  return (bo && bo.eventDefinitions) || []
}

export function getEventDefinition(element: DiagramElement, type?: string): ModdleElement | undefined {
  const definitions = getEventDefinitions(element)
  if (!type) return definitions[0]
  return definitions.find((definition: ModdleElement) => is(definition, type))
}

export function hasEventDefinition(element: DiagramElement, type: string): boolean {
  return !!getEventDefinition(element, type)
}

export function isEvent(element: DiagramElement): boolean {
  return is(element, 'bpmn:Event')
}

export function isLabel(element: DiagramElement): boolean {
  return !!element && !!element.labelTarget
}

export function isConnection(element: DiagramElement): boolean {
  return !!element && !!element.waypoints
}

/**
 * Diagrammwurzel? Wurzeln haben weder Elternteil noch Lage (keine Breite);
 * neu erzeugte, noch nicht eingefügte Formen dagegen schon.
 */
export function isRoot(element: DiagramElement): boolean {
  return (
    !!element &&
    !element.parent &&
    !element.labelTarget &&
    !element.waypoints &&
    typeof element.width !== 'number'
  )
}

/** Mehrfachinstanz- oder Schleifencharakteristik. */
export function getLoopType(element: DiagramElement): 'loop' | 'parallel' | 'sequential' | null {
  const loop = getBusinessObject(element)?.loopCharacteristics
  if (!loop) return null
  if (is(loop, 'bpmn:StandardLoopCharacteristics')) return 'loop'
  if (is(loop, 'bpmn:MultiInstanceLoopCharacteristics')) {
    return loop.isSequential ? 'sequential' : 'parallel'
  }
  return null
}

/** Wurzel-Definitionen eines moddle-Elements. */
export function getDefinitions(bo: ModdleElement): ModdleElement {
  let current = bo
  while (current && !is(current, 'bpmn:Definitions')) {
    current = current.$parent
  }
  return current
}

/** Fügt ein Element idempotent in eine Liste ein. */
export function addToList(list: unknown[], item: unknown, index?: number): void {
  if (list.indexOf(item) !== -1) return
  if (typeof index === 'number' && index >= 0 && index <= list.length) {
    list.splice(index, 0, item)
  } else {
    list.push(item)
  }
}

/** Entfernt ein Element aus einer Liste und liefert den bisherigen Index. */
export function removeFromList(list: unknown[] | undefined, item: unknown): number {
  if (!list) return -1
  const index = list.indexOf(item)
  if (index !== -1) list.splice(index, 1)
  return index
}
