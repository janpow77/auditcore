/**
 * Kantenführung: Sequenz- und Nachrichtenflüsse rechtwinklig (Manhattan),
 * Assoziationen und Datenassoziationen gerade. Anfang und Ende werden am
 * tatsächlichen Umriss der Form abgeschnitten (Andockpunkte).
 */

import BaseLayouter from 'diagram-js/lib/layout/BaseLayouter'
import { getMid, getOrientation } from 'diagram-js/lib/layout/LayoutUtil'
import { repairConnection, withoutRedundantPoints } from 'diagram-js/lib/layout/ManhattanLayout'

import { is } from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

type Point = { x: number; y: number; original?: Point }

export default class BpmnLayouter extends (BaseLayouter as any) {
  static $inject = ['connectionDocking']

  constructor(private _connectionDocking: any) {
    super()
  }

  layoutConnection(connection: any, hints: any = {}): Point[] {
    const source = hints.source || connection.source
    const target = hints.target || connection.target
    const waypoints: Point[] | undefined = hints.waypoints || connection.waypoints
    let start: Point = hints.connectionStart
    let end: Point = hints.connectionEnd

    if (!start) start = dockingOf(waypoints && waypoints[0], source)
    if (!end) end = dockingOf(waypoints && waypoints[waypoints.length - 1], target)

    const type = connection.type || connection.businessObject?.$type || hints.type
    let result: Point[]

    if (!source || !target) return waypoints || []

    if (type === 'bpmn:SequenceFlow' || type === 'bpmn:MessageFlow') {
      const manhattanHints = this.getManhattanHints(type, source, target)
      result = repairConnection(source, target, start, end, waypoints, { ...manhattanHints, ...hints }) || [start, end]
    } else {
      result = [start, end]
    }

    result = withoutRedundantPoints(result)
    return this.crop(result, source, target)
  }

  getManhattanHints(type: string, source: any, target: any): { preferredLayouts: string[] } {
    if (type === 'bpmn:MessageFlow') return { preferredLayouts: ['straight', 'v:v'] }

    if (is(source, 'bpmn:BoundaryEvent') && source.host) {
      const mid = getMid(source)
      const orientation = getOrientation({ ...mid, width: 0, height: 0 }, source.host, -10)
      if (/top|bottom/.test(orientation)) return { preferredLayouts: ['v:h'] }
      return { preferredLayouts: ['h:v'] }
    }
    const aligned = Math.abs(getMid(source).y - getMid(target).y) < 5
    if (is(source, 'bpmn:Gateway') && !aligned) return { preferredLayouts: ['v:h'] }
    if (is(target, 'bpmn:Gateway') && !aligned) return { preferredLayouts: ['h:v'] }
    return { preferredLayouts: ['h:h'] }
  }

  private crop(points: Point[], source: any, target: any): Point[] {
    if (!this._connectionDocking || points.length < 2) return points
    try {
      const temp = { waypoints: points.map((p) => ({ x: p.x, y: p.y })), source, target }
      const cropped = this._connectionDocking.getCroppedWaypoints(temp, source, target)
      return cropped.map((p: Point) => ({
        x: Math.round(p.x),
        y: Math.round(p.y),
        ...(p.original ? { original: { x: Math.round(p.original.x), y: Math.round(p.original.y) } } : {}),
      }))
    } catch {
      return points
    }
  }
}

function dockingOf(point: Point | undefined, shape: any): Point {
  if (point && point.original) return point.original
  return getMid(shape)
}
