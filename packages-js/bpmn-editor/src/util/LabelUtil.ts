/**
 * Beschriftungen: welches Element trägt eine externe Beschriftung, wo liegt
 * sie standardmäßig, und wie wird der Text gelesen bzw. geschrieben.
 */

import { layoutText, DEFAULT_TEXT_STYLE } from '../draw/TextLayout'
import type { Element as DjsElement } from 'diagram-js/lib/model/Types'

import type { Bounds, ModdleElement, Point } from '../types'
import { getBusinessObject, is, isAny, type BpmnLike } from './ModelUtil'

export const DEFAULT_LABEL_SIZE = { width: 90, height: 20 }
export const EXTERNAL_LABEL_FONT_SIZE = 11
export const FLOW_LABEL_INDENT = 15

const EXTERNAL_LABEL_TYPES = [
  'bpmn:Event',
  'bpmn:Gateway',
  'bpmn:DataStoreReference',
  'bpmn:DataObjectReference',
  'bpmn:DataInput',
  'bpmn:DataOutput',
  'bpmn:SequenceFlow',
  'bpmn:MessageFlow',
  'bpmn:Group',
]

const EDITABLE_TYPES = [
  'bpmn:FlowNode',
  'bpmn:Participant',
  'bpmn:Lane',
  'bpmn:SequenceFlow',
  'bpmn:MessageFlow',
  'bpmn:DataObjectReference',
  'bpmn:DataStoreReference',
  'bpmn:DataInput',
  'bpmn:DataOutput',
  'bpmn:TextAnnotation',
  'bpmn:Group',
]

/** Hat das Element eine eigenständig verschiebbare (externe) Beschriftung? */
export function isLabelExternal(semantic: BpmnLike | null | undefined): boolean {
  return isAny(semantic, EXTERNAL_LABEL_TYPES)
}

/** Kann die Beschriftung direkt bearbeitet werden? */
export function isAnyLabelEditable(element: BpmnLike | null | undefined): boolean {
  return isAny(element, EDITABLE_TYPES)
}

/** Name bzw. Text der Beschriftung. */
export function getLabel(element: BpmnLike | null | undefined): string | undefined {
  const semantic = getBusinessObject(element)
  if (!semantic) return undefined
  if (is(semantic, 'bpmn:TextAnnotation')) return semantic.text
  if (is(semantic, 'bpmn:Group')) return semantic.categoryValueRef?.value
  return semantic.name
}

/** Setzt den Beschriftungstext direkt am moddle-Objekt (ohne Befehlsstapel). */
export function setLabel(element: BpmnLike, text: string | undefined | null): void {
  const semantic: ModdleElement = getBusinessObject(element)
  const value = text === null || text === undefined || text === '' ? undefined : text
  if (is(semantic, 'bpmn:TextAnnotation')) semantic.text = value
  else if (is(semantic, 'bpmn:Group')) {
    if (semantic.categoryValueRef) semantic.categoryValueRef.value = value
  } else semantic.name = value
}

/** Punkt in der Mitte eines Kantenzugs (nach Streckenlänge). */
export function getPathMid(points: readonly Point[]): Point {
  const first = points[0]
  if (!first) return { x: 0, y: 0 }
  const lengths = points.slice(1).map((point, index) => {
    const previous = points[index] as Point
    return Math.hypot(point.x - previous.x, point.y - previous.y)
  })
  let remaining = lengths.reduce((sum, length) => sum + length, 0) / 2
  for (let i = 1; i < points.length; i++) {
    const length = lengths[i - 1] ?? 0
    const a = points[i - 1] as Point
    const b = points[i] as Point
    if (remaining <= length && length > 0) {
      const ratio = remaining / length
      return { x: a.x + (b.x - a.x) * ratio, y: a.y + (b.y - a.y) * ratio }
    }
    remaining -= length
  }
  return { x: first.x, y: first.y }
}

/** Standardmittelpunkt einer externen Beschriftung. */
export function getExternalLabelMid(element: DjsElement): Point {
  if (element.waypoints) {
    const mid = getPathMid(element.waypoints as Point[])
    return { x: mid.x, y: mid.y - FLOW_LABEL_INDENT }
  }
  const shape = element as unknown as Bounds
  if (is(element, 'bpmn:Group')) {
    return { x: shape.x + shape.width / 2, y: shape.y + DEFAULT_LABEL_SIZE.height / 2 + 4 }
  }
  return { x: shape.x + shape.width / 2, y: shape.y + shape.height + DEFAULT_LABEL_SIZE.height / 2 + 4 }
}

/** Abmessungen einer externen Beschriftung für den gegebenen Text. */
export function getExternalLabelSize(text: string | undefined): { width: number; height: number } {
  if (!text) return { ...DEFAULT_LABEL_SIZE }
  const layout = layoutText(text, {
    box: { width: DEFAULT_LABEL_SIZE.width, height: 1000 },
    style: { ...DEFAULT_TEXT_STYLE, fontSize: EXTERNAL_LABEL_FONT_SIZE },
  })
  return { width: Math.max(Math.ceil(layout.width), 10), height: Math.max(Math.ceil(layout.height), 14) }
}

/** Bounds einer externen Beschriftung aus DI oder Standardlage. */
export function getExternalLabelBounds(di: ModdleElement | undefined, element: DjsElement): Bounds {
  const bounds = di?.label?.bounds
  if (bounds) {
    return { x: bounds.x ?? 0, y: bounds.y ?? 0, width: bounds.width ?? 0, height: bounds.height ?? 0 }
  }
  const mid = getExternalLabelMid(element)
  const size = getExternalLabelSize(getLabel(element))
  return {
    x: Math.round(mid.x - size.width / 2),
    y: Math.round(mid.y - DEFAULT_LABEL_SIZE.height / 2),
    width: size.width,
    height: size.height,
  }
}
