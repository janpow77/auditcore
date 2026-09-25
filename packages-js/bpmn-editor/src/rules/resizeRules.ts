/**
 * Größenänderung: welche Formen dürfen verändert werden und wie klein sie
 * mindestens bleiben.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import { is, isAny, isExpanded } from '../util/ModelUtil'
import type { Bounds } from '../types'

type Size = { width: number; height: number }

/** Mindestmaße je Typ (erste passende gewinnt). */
const MIN_SIZES: [(element: Element) => boolean, Size][] = [
  [(element) => is(element, 'bpmn:SubProcess') && !isExpanded(element), { width: 60, height: 50 }],
  [(element) => is(element, 'bpmn:SubProcess'), { width: 100, height: 80 }],
  [(element) => is(element, 'bpmn:Lane'), { width: 60, height: 60 }],
  [(element) => is(element, 'bpmn:Participant'), { width: 250, height: 50 }],
  [(element) => is(element, 'bpmn:TextAnnotation'), { width: 50, height: 30 }],
  [(element) => is(element, 'bpmn:Group'), { width: 60, height: 60 }],
  [(element) => isAny(element, ['bpmn:Task', 'bpmn:CallActivity']), { width: 60, height: 50 }],
]

export function canResize(shape: Element, newBounds?: Bounds): boolean {
  const entry = MIN_SIZES.find(([matches]) => matches(shape))
  if (!entry) return false
  if (!newBounds) return true
  return newBounds.width >= entry[1].width && newBounds.height >= entry[1].height
}
