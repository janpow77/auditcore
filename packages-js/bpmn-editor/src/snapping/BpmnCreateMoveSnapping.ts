/**
 * Einrasten und Hilfslinien beim Anlegen/Verschieben:
 * - Mittelpunkte der Nachbarn (auch durch Bahnen hindurch, d. h. im Pool),
 * - Randereignisse rasten auf der Kante der Aktivität ein.
 */

import CreateMoveSnapping from 'diagram-js/lib/features/snapping/CreateMoveSnapping'
import type { Element, Shape } from 'diagram-js/lib/model/Types'

import { is } from '../util/ModelUtil'
import type { EventBus } from '../types'

interface SnapEvent {
  x: number
  y: number
  shape?: Shape
  context: { shape?: Shape; target?: Shape; canExecute?: unknown }
}

/** Nächster Punkt auf dem Rand eines Rechtecks. */
export function snapToBorder(point: { x: number; y: number }, host: Shape): { x: number; y: number } {
  const left = host.x
  const right = host.x + host.width
  const top = host.y
  const bottom = host.y + host.height
  const clampedX = Math.min(Math.max(point.x, left), right)
  const clampedY = Math.min(Math.max(point.y, top), bottom)
  const distances = [
    { edge: 'left', d: Math.abs(point.x - left) },
    { edge: 'right', d: Math.abs(point.x - right) },
    { edge: 'top', d: Math.abs(point.y - top) },
    { edge: 'bottom', d: Math.abs(point.y - bottom) },
  ].sort((a, b) => a.d - b.d)
  switch (distances[0]?.edge) {
    case 'left':
      return { x: left, y: clampedY }
    case 'right':
      return { x: right, y: clampedY }
    case 'top':
      return { x: clampedX, y: top }
    default:
      return { x: clampedX, y: bottom }
  }
}

export default class BpmnCreateMoveSnapping extends CreateMoveSnapping {
  static $inject = ['elementRegistry', 'eventBus', 'snapping']

  constructor(elementRegistry: unknown, eventBus: EventBus, snapping: unknown) {
    super(elementRegistry as never, eventBus, snapping as never)
    eventBus.on(['create.move', 'shape.move.move'], 1100, (event: SnapEvent) => {
      const context = event.context
      const shape = context.shape
      const target = context.target
      if (!shape || !target || !context.canExecute) return
      if (context.canExecute !== 'attach' || !is(shape, 'bpmn:Event')) return
      const point = snapToBorder({ x: event.x, y: event.y }, target)
      event.x = point.x
      event.y = point.y
    })
  }

  getSnapTargets(shape: Shape, target: Element): Shape[] {
    const container = is(target, 'bpmn:Lane') ? findParticipant(target) || target : target
    return ((container.children || []) as Shape[]).filter(
      (child) => !child.hidden && !child.labelTarget && !(child as { waypoints?: unknown }).waypoints && child !== shape && !is(child, 'bpmn:Lane'),
    )
  }
}

function findParticipant(element: Element): Element | null {
  let current: Element | undefined = element
  while (current && !is(current, 'bpmn:Participant')) current = current.parent
  return current || null
}
