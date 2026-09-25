/**
 * Zeichenreihenfolge (z-Ordnung) innerhalb eines Containers: Pools und
 * Bahnen hinten, Knoten davor, Randereignisse über ihrem Wirt, Kanten und
 * Beschriftungen vorne.
 */

import OrderingProvider from 'diagram-js/lib/features/ordering/OrderingProvider'

import { is, isAny } from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

function level(element: any): number {
  if (element.labelTarget) return 20
  if (is(element, 'bpmn:Participant')) return -2
  if (is(element, 'bpmn:Lane')) return -1
  if (is(element, 'bpmn:MessageFlow')) return 16
  if (isAny(element, ['bpmn:Association', 'bpmn:DataInputAssociation', 'bpmn:DataOutputAssociation'])) return 15
  if (is(element, 'bpmn:SequenceFlow')) return 14
  if (is(element, 'bpmn:Group')) return 12
  if (is(element, 'bpmn:BoundaryEvent')) return 8
  if (is(element, 'bpmn:SubProcess')) return 2
  return 5
}

export default class BpmnOrderingProvider extends (OrderingProvider as any) {
  static $inject = ['eventBus']

  constructor(eventBus: any) {
    super(eventBus)
  }

  getOrdering(element: any, newParent: any): { index: number; parent?: any } | null {
    if (!newParent) return null
    const own = level(element)
    const siblings: any[] = (newParent.children || []).filter((child: any) => child !== element)
    let index: number = siblings.findIndex((child: any) => level(child) > own)
    if (index === -1) index = siblings.length
    // Der Index bezieht sich auf die Kinderliste ohne das Element selbst.
    return { index }
  }
}
