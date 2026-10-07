/**
 * Bahnen verschieben ihren Pool: Bahnen füllen einen Pool bis auf den
 * Titelstreifen aus und dürfen nicht allein verschoben werden
 * (`canMove`). Ohne diese Umleitung ließ sich ein Pool nur am schmalen
 * Titelstreifen greifen – ein Ziehen in der Fläche traf die Bahn und tat
 * nichts. Beim Start einer Verschiebung werden Bahnen deshalb durch ihren
 * Pool ersetzt, auch in einer Mehrfachauswahl. Ein Klick wählt weiterhin die
 * Bahn, Shift-Ziehen bleibt das Lasso.
 */

import type { Element, Shape } from 'diagram-js/lib/model/Types'

import { is } from '../util/ModelUtil'
import type { EventBus } from '../types'

/** Zwischen dem Aufbau des Kontexts (1500) und der Regelprüfung (1250) von diagram-js. */
const PRIORITY = 1400

interface MoveStartEvent {
  shape: Shape
  context: { shape?: Shape; shapes?: Shape[]; validatedShapes?: Shape[] }
}

/** Der Pool einer (ggf. verschachtelten) Bahn; andere Elemente unverändert. */
export function frameOf(element: Shape): Shape {
  let current: Element | undefined = element
  while (current && is(current, 'bpmn:Lane')) current = current.parent as Element | undefined
  return current && is(current, 'bpmn:Participant') ? (current as Shape) : element
}

function hasAncestorIn(shape: Shape, set: Set<Shape>): boolean {
  for (let parent = shape.parent as Shape | undefined; parent; parent = parent.parent as Shape | undefined) {
    if (set.has(parent)) return true
  }
  return false
}

/** Bahnen durch ihren Pool ersetzen, doppelte und verschachtelte Einträge entfernen. */
export function replaceLanes(shapes: readonly Shape[]): Shape[] {
  const set = new Set(shapes.map(frameOf))
  return [...set].filter((shape) => !hasAncestorIn(shape, set))
}

export default class LaneMove {
  static $inject = ['eventBus']

  constructor(eventBus: EventBus) {
    eventBus.on('shape.move.start', PRIORITY, (event: MoveStartEvent) => {
      const { context } = event
      const shapes = context.shapes ?? [event.shape]
      if (!shapes.some((shape) => is(shape, 'bpmn:Lane'))) return
      const replaced = replaceLanes(shapes)
      context.shapes = replaced
      context.validatedShapes = replaced
      if (context.shape) context.shape = frameOf(context.shape)
    })
  }
}
