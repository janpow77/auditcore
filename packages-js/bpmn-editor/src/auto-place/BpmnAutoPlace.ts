/**
 * Lage neu angehängter Elemente (Kontextpad „Anhängen“): Flussknoten
 * rechts vom Quellelement, Daten darunter, Anmerkungen darüber; belegte
 * Plätze werden übersprungen.
 */

import {
  findFreePosition,
  generateGetNextPosition,
  getConnectedDistance,
} from 'diagram-js/lib/features/auto-place/AutoPlaceUtil'
import type { Shape } from 'diagram-js/lib/model/Types'

import { is, isAny } from '../util/ModelUtil'
import type { EventBus, Point } from '../types'

const HORIZONTAL_GAP = 80
const VERTICAL_GAP = 80

function mid(shape: Shape): Point {
  return { x: shape.x + shape.width / 2, y: shape.y + shape.height / 2 }
}

export function getFlowNodePosition(source: Shape, element: Shape): Point {
  const sourceMid = mid(source)
  const distance = getConnectedDistance(source, {
    defaultDistance: HORIZONTAL_GAP,
    filter: (connection) => is(connection, 'bpmn:SequenceFlow'),
  })
  const reference = is(source, 'bpmn:BoundaryEvent') && source.host ? source.host : source
  const position: Point = is(source, 'bpmn:BoundaryEvent')
    ? { x: sourceMid.x + element.width / 2 + 20, y: reference.y + reference.height + VERTICAL_GAP + element.height / 2 }
    : { x: source.x + source.width + distance + element.width / 2, y: sourceMid.y }
  const next = generateGetNextPosition({ y: { margin: 30, minDistance: 20 } })
  return findFreePosition(source, element, position, next)
}

export function getDataPosition(source: Shape, element: Shape): Point {
  const position = { x: source.x + source.width / 2 + 30, y: source.y + source.height + VERTICAL_GAP + element.height / 2 }
  const next = generateGetNextPosition({ x: { margin: 30, minDistance: 20 } })
  return findFreePosition(source, element, position, next)
}

export function getAnnotationPosition(source: Shape, element: Shape): Point {
  const position = {
    x: source.x + source.width + element.width / 2 + 30,
    y: source.y - 50 - element.height / 2,
  }
  const next = generateGetNextPosition({ y: { margin: -30, minDistance: 20 } })
  return findFreePosition(source, element, position, next)
}

export function getNewShapePosition(source: Shape, element: Shape): Point {
  if (is(element, 'bpmn:TextAnnotation')) return getAnnotationPosition(source, element)
  if (isAny(element, ['bpmn:DataObjectReference', 'bpmn:DataStoreReference'])) return getDataPosition(source, element)
  if (is(element, 'bpmn:FlowNode')) return getFlowNodePosition(source, element)
  return { x: source.x + source.width + HORIZONTAL_GAP + element.width / 2, y: mid(source).y }
}

export default class BpmnAutoPlace {
  static $inject = ['eventBus']

  constructor(eventBus: EventBus) {
    eventBus.on('autoPlace', 1500, (event: { shape: Shape; source: Shape }) => getNewShapePosition(event.source, event.shape))
  }
}
