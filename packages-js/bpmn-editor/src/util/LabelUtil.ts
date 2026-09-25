/**
 * Beschriftungen: welches Element trägt eine externe Beschriftung, wo liegt
 * sie standardmäßig, und wie wird der Text gelesen bzw. geschrieben.
 */

import { layoutText, DEFAULT_TEXT_STYLE } from '../draw/TextLayout'
import { getBusinessObject, is, isAny, type DiagramElement, type ModdleElement } from './ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

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

/** Hat das Element eine eigenständig verschiebbare (externe) Beschriftung? */
export function isLabelExternal(semantic: DiagramElement): boolean {
  return isAny(semantic, EXTERNAL_LABEL_TYPES)
}

/** Hat das Element tatsächlich eine externe Beschriftung (mit Inhalt)? */
export function hasExternalLabel(element: DiagramElement): boolean {
  return isLabelExternal(element)
}

/** Name bzw. Text der Beschriftung. */
export function getLabel(element: DiagramElement): string | undefined {
  const semantic = getBusinessObject(element)
  if (!semantic) return undefined
  if (is(semantic, 'bpmn:TextAnnotation')) return semantic.text
  if (is(semantic, 'bpmn:Group')) return semantic.categoryValueRef?.value
  return semantic.name
}

/** Setzt den Beschriftungstext direkt am moddle-Objekt (ohne Befehlsstapel). */
export function setLabel(element: DiagramElement, text: string | undefined | null): void {
  const semantic = getBusinessObject(element)
  const value = text === null || text === undefined || text === '' ? undefined : text
  if (is(semantic, 'bpmn:TextAnnotation')) {
    semantic.text = value
  } else if (is(semantic, 'bpmn:Group')) {
    if (semantic.categoryValueRef) semantic.categoryValueRef.value = value
  } else {
    semantic.name = value
  }
}

function flowLabelPosition(waypoints: { x: number; y: number }[]) {
  // Mittelpunkt entlang der Streckenlänge.
  let total = 0
  const lengths: number[] = []
  for (let i = 1; i < waypoints.length; i++) {
    const length = Math.hypot(waypoints[i].x - waypoints[i - 1].x, waypoints[i].y - waypoints[i - 1].y)
    lengths.push(length)
    total += length
  }
  let remaining = total / 2
  for (let i = 1; i < waypoints.length; i++) {
    const length = lengths[i - 1]
    if (remaining <= length && length > 0) {
      const ratio = remaining / length
      return {
        x: waypoints[i - 1].x + (waypoints[i].x - waypoints[i - 1].x) * ratio,
        y: waypoints[i - 1].y + (waypoints[i].y - waypoints[i - 1].y) * ratio,
      }
    }
    remaining -= length
  }
  return { ...waypoints[0] }
}

/** Standardmittelpunkt einer externen Beschriftung. */
export function getExternalLabelMid(element: DiagramElement): { x: number; y: number } {
  if (element.waypoints) {
    const mid = flowLabelPosition(element.waypoints)
    return { x: mid.x, y: mid.y - FLOW_LABEL_INDENT }
  }
  if (is(element, 'bpmn:Group')) {
    return { x: element.x + element.width / 2, y: element.y + DEFAULT_LABEL_SIZE.height / 2 + 4 }
  }
  return {
    x: element.x + element.width / 2,
    y: element.y + element.height + DEFAULT_LABEL_SIZE.height / 2 + 4,
  }
}

/** Abmessungen einer externen Beschriftung für den gegebenen Text. */
export function getExternalLabelSize(text: string | undefined): { width: number; height: number } {
  if (!text) return { ...DEFAULT_LABEL_SIZE }
  const layout = layoutText(text, {
    box: { width: DEFAULT_LABEL_SIZE.width, height: 1000 },
    style: { ...DEFAULT_TEXT_STYLE, fontSize: EXTERNAL_LABEL_FONT_SIZE },
  })
  return {
    width: Math.max(Math.ceil(layout.width), 10),
    height: Math.max(Math.ceil(layout.height), 14),
  }
}

/** Bounds einer externen Beschriftung aus DI oder Standardlage. */
export function getExternalLabelBounds(di: ModdleElement, element: DiagramElement): {
  x: number
  y: number
  width: number
  height: number
} {
  const label = di && di.label
  if (label && label.bounds) {
    const bounds = label.bounds
    return {
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
    }
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

/** Liegt eine (nicht leere) Beschriftung vor? */
export function hasLabelText(element: DiagramElement): boolean {
  const text = getLabel(element)
  return typeof text === 'string' && text.trim().length > 0
}

export function isAnyLabelEditable(element: DiagramElement): boolean {
  return isAny(element, [
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
  ])
}

export { getBusinessObject }
