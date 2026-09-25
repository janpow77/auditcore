/**
 * Kantenführung: Sequenz- und Nachrichtenflüsse rechtwinklig (Manhattan),
 * Assoziationen und Datenassoziationen gerade. Anfang und Ende werden am
 * tatsächlichen Umriss der Form abgeschnitten (Andockpunkte).
 */

import BaseLayouter from 'diagram-js/lib/layout/BaseLayouter'
import { getMid, getOrientation } from 'diagram-js/lib/layout/LayoutUtil'
import { repairConnection, withoutRedundantPoints } from 'diagram-js/lib/layout/ManhattanLayout'
import type { Connection, Element, Shape } from 'diagram-js/lib/model/Types'

import { getBusinessObject, is } from '../util/ModelUtil'
import type { Point } from '../types'

interface LayoutHints {
  source?: Shape
  target?: Shape
  waypoints?: Point[]
  connectionStart?: Point
  connectionEnd?: Point
  type?: string
  [key: string]: unknown
}

interface Docking {
  getCroppedWaypoints(connection: { waypoints: Point[]; source: Element; target: Element }, source: Element, target: Element): Point[]
}

const MANHATTAN_TYPES = ['bpmn:SequenceFlow', 'bpmn:MessageFlow']

function dockingOf(point: Point | undefined, shape: Shape): Point {
  return point?.original || getMid(shape)
}

function connectionType(connection: Connection, hints: LayoutHints): string {
  return String(connection.type || getBusinessObject(connection)?.$type || hints.type || '')
}

/** Bevorzugte Führung je Situation (Richtung am Start : am Ende). */
export function preferredLayouts(type: string, source: Shape, target: Shape): string[] {
  if (type === 'bpmn:MessageFlow') return ['straight', 'v:v']
  if (is(source, 'bpmn:BoundaryEvent') && source.host) {
    const mid = getMid(source)
    const orientation = getOrientation({ ...mid, width: 0, height: 0 }, source.host, -10)
    return /top|bottom/.test(orientation) ? ['v:h'] : ['h:v']
  }
  const aligned = Math.abs(getMid(source).y - getMid(target).y) < 5
  if (is(source, 'bpmn:Gateway') && !aligned) return ['v:h']
  if (is(target, 'bpmn:Gateway') && !aligned) return ['h:v']
  return ['h:h']
}

export default class BpmnLayouter extends BaseLayouter {
  static $inject = ['connectionDocking']

  constructor(private readonly docking: Docking | undefined) {
    super()
  }

  layoutConnection(connection: Connection, hints: LayoutHints = {}): Point[] {
    const source = (hints.source || connection.source) as Shape | undefined
    const target = (hints.target || connection.target) as Shape | undefined
    const waypoints = (hints.waypoints || connection.waypoints) as Point[] | undefined
    if (!source || !target) return waypoints || []
    return this.layoutBetween(connection, source, target, waypoints, hints)
  }

  private layoutBetween(connection: Connection, source: Shape, target: Shape, waypoints: Point[] | undefined, hints: LayoutHints): Point[] {
    const start = hints.connectionStart || dockingOf(waypoints?.[0], source)
    const end = hints.connectionEnd || dockingOf(waypoints?.[waypoints.length - 1], target)
    const type = connectionType(connection, hints)
    let result: Point[] = [start, end]
    if (MANHATTAN_TYPES.includes(type)) {
      // diagram-js typisiert connectionStart/-End hier als Schalter; es werden aber Punkte übergeben.
      const layoutHints = { preferredLayouts: preferredLayouts(type, source, target), ...hints } as Parameters<typeof repairConnection>[5]
      result = repairConnection(source, target, start, end, waypoints, layoutHints) || result
    }
    return this.crop(withoutRedundantPoints(result), source, target)
  }

  private crop(points: Point[], source: Shape, target: Shape): Point[] {
    if (!this.docking || points.length < 2) return points
    try {
      const temp = { waypoints: points.map((point) => ({ x: point.x, y: point.y })), source, target }
      return this.docking.getCroppedWaypoints(temp, source, target).map((point) => ({
        x: Math.round(point.x),
        y: Math.round(point.y),
        ...(point.original ? { original: { x: Math.round(point.original.x), y: Math.round(point.original.y) } } : {}),
      }))
    } catch {
      return points
    }
  }
}
