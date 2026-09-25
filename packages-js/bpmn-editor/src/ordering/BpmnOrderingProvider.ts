/**
 * Zeichenreihenfolge (z-Ordnung) innerhalb eines Containers: Pools und
 * Bahnen hinten, Knoten davor, Randereignisse über ihrem Wirt, Kanten und
 * Beschriftungen vorne.
 */

import OrderingProvider from 'diagram-js/lib/features/ordering/OrderingProvider'
import type { Element, ShapeLike } from 'diagram-js/lib/model/Types'

import { isAny } from '../util/ModelUtil'
import type { EventBus } from '../types'

/** Ebene je Typ (erste passende gewinnt; höher = weiter vorn). */
const LEVELS: [string[], number][] = [
  [['bpmn:Participant'], -2],
  [['bpmn:Lane'], -1],
  [['bpmn:MessageFlow'], 16],
  [['bpmn:Association', 'bpmn:DataInputAssociation', 'bpmn:DataOutputAssociation'], 15],
  [['bpmn:SequenceFlow'], 14],
  [['bpmn:Group'], 12],
  [['bpmn:BoundaryEvent'], 8],
  [['bpmn:SubProcess'], 2],
]

export function level(element: Element): number {
  if (element.labelTarget) return 20
  return LEVELS.find(([types]) => isAny(element, types))?.[1] ?? 5
}

export default class BpmnOrderingProvider extends OrderingProvider {
  static $inject = ['eventBus']

  constructor(eventBus: EventBus) {
    super(eventBus)
  }

  /** Index bezogen auf die Kinderliste ohne das Element selbst. */
  getOrdering(element: Element, newParent: ShapeLike): { index: number } {
    const own = level(element)
    const children = (newParent as unknown as { children?: Element[] } | undefined)?.children || []
    const siblings = children.filter((child) => child !== element)
    const index = siblings.findIndex((child) => level(child) > own)
    return { index: index === -1 ? siblings.length : index }
  }
}
