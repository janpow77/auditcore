/**
 * Befehle für Bahnen: anlegen (oberhalb/unterhalb bzw. links/rechts),
 * teilen, Größe ändern und Bahnzugehörigkeit (`flowNodeRef`) pflegen.
 */

import { getBusinessObject, is, isHorizontal } from '../../util/ModelUtil'
import {
  DEFAULT_LANE_SIZE,
  LANE_BAND,
  getAllLanes,
  getAxis,
  getChildLanes,
  getContentBounds,
  getLaneParent,
  getParticipant,
  moveEdge,
  boundsEqual,
  type Bounds,
} from '../LaneUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

type Location = 'top' | 'bottom' | 'left' | 'right'

function normalizeLocation(location: Location, horizontal: boolean): 'start' | 'end' {
  if (horizontal) return location === 'top' || location === 'left' ? 'start' : 'end'
  return location === 'left' || location === 'top' ? 'start' : 'end'
}

export class AddLaneHandler {
  static $inject = ['modeling', 'elementFactory', 'bpmnFactory', 'canvas', 'elementRegistry']

  constructor(
    private _modeling: any,
    private _elementFactory: any,
    private _bpmnFactory: any,
    private _canvas: any,
    private _elementRegistry: any,
  ) {}

  preExecute(context: any): void {
    let target = context.shape
    const participant = is(target, 'bpmn:Participant') ? target : getParticipant(target)
    if (!participant) throw new Error('Bahnen setzen einen Pool voraus')
    const horizontal = isHorizontal(participant)
    const axis = getAxis(participant)
    const where = normalizeLocation(context.location || 'bottom', horizontal)
    const laneSize = context.laneSize || DEFAULT_LANE_SIZE

    // Pool ohne Bahnen: erst eine Bahn über den ganzen Innenbereich anlegen.
    if (is(target, 'bpmn:Participant')) {
      const existing = getChildLanes(participant)
      if (existing.length === 0) {
        const first = this._createLane(participant, getContentBounds(participant), null, 0, horizontal)
        target = first
      } else {
        const sorted = existing.sort((a: any, b: any) => a[axis.main] - b[axis.main])
        target = where === 'start' ? sorted[0] : sorted[sorted.length - 1]
      }
    }

    const line = where === 'start' ? target[axis.main] : target[axis.main] + target[axis.mainSize]
    const delta = { x: 0, y: 0 }
    delta[axis.main] = where === 'start' ? -laneSize : laneSize
    const direction = horizontal ? (where === 'start' ? 'n' : 's') : where === 'start' ? 'w' : 'e'

    // Wachsen müssen Pool und alle übergeordneten Bahnen des Ziels.
    const resizing: any[] = [participant]
    let parent = getLaneParent(target)
    while (parent && is(parent, 'bpmn:Lane')) {
      resizing.push(parent)
      parent = getLaneParent(parent)
    }

    const root = this._canvas.findRoot(participant)
    const moving = this._elementRegistry.filter((element: any) => {
      if (element.waypoints || !element.parent || resizing.includes(element)) return false
      if (this._canvas.findRoot(element) !== root) return false
      if (element.labelTarget && resizing.includes(element.labelTarget)) return false
      if (where === 'start') return element[axis.main] + element[axis.mainSize] <= line
      return element[axis.main] >= line
    })

    this._modeling.createSpace(moving, resizing, delta, direction, line)

    // Neue Bahn in die Lücke setzen, gleiche Ebene wie das Ziel.
    const laneParent = getLaneParent(target)
    const parentBounds = is(laneParent, 'bpmn:Participant') ? getContentBounds(laneParent) : getContentBounds(laneParent)
    const bounds: Bounds = { x: 0, y: 0, width: 0, height: 0 }
    bounds[axis.main] = where === 'start' ? line - laneSize : line
    bounds[axis.mainSize] = laneSize
    bounds[axis.cross] = parentBounds[axis.cross]
    bounds[axis.crossSize] = parentBounds[axis.crossSize]
    const laneSet = getBusinessObject(target).$parent
    const index = laneSet.get('lanes').indexOf(getBusinessObject(target)) + (where === 'start' ? 0 : 1)
    context.newLane = this._createLane(participant, bounds, laneSet, index, horizontal)
  }

  postExecute(context: any): void {
    const participant = getParticipant(context.newLane)
    if (participant) this._modeling.updateLaneRefs(participant)
  }

  _createLane(participant: any, bounds: Bounds, laneSet: any, index: number, horizontal: boolean): any {
    const bo = this._bpmnFactory.create('bpmn:Lane')
    if (laneSet) {
      bo.$parent = laneSet
      const lanes = laneSet.get('lanes')
      lanes.splice(Math.min(index, lanes.length), 0, bo)
    }
    const shape = this._elementFactory.createShape({
      type: 'bpmn:Lane',
      businessObject: bo,
      isHorizontal: horizontal,
    })
    return this._modeling.createShape(shape, bounds, participant)
  }
}

export class SplitLaneHandler {
  static $inject = ['modeling', 'elementFactory', 'bpmnFactory']

  constructor(private _modeling: any, private _elementFactory: any, private _bpmnFactory: any) {}

  execute(context: any): any[] {
    const shape = context.shape
    const bo = getBusinessObject(shape)
    if (is(bo, 'bpmn:Lane') && !bo.childLaneSet) {
      const laneSet = this._bpmnFactory.create('bpmn:LaneSet')
      laneSet.$parent = bo
      bo.childLaneSet = laneSet
      context.createdLaneSet = laneSet
    }
    return [shape]
  }

  revert(context: any): any[] {
    if (context.createdLaneSet) getBusinessObject(context.shape).childLaneSet = undefined
    return [context.shape]
  }

  postExecute(context: any): void {
    const shape = context.shape
    const count = Math.max(2, context.count || 2)
    const participant = is(shape, 'bpmn:Participant') ? shape : getParticipant(shape)
    const horizontal = isHorizontal(participant)
    const axis = getAxis(participant)
    const existing = getChildLanes(shape)
    if (existing.length > 0) return

    const content = getContentBounds(shape)
    const bo = getBusinessObject(shape)
    let laneSet: any
    if (is(bo, 'bpmn:Participant')) {
      const process = bo.processRef
      laneSet = process.get('laneSets')[0]
      if (!laneSet) {
        laneSet = this._bpmnFactory.create('bpmn:LaneSet')
        laneSet.$parent = process
        process.get('laneSets').push(laneSet)
      }
    } else {
      laneSet = bo.childLaneSet
    }

    const size = Math.floor(content[axis.mainSize] / count)
    const created: any[] = []
    for (let i = 0; i < count; i++) {
      const bounds: Bounds = { ...content }
      bounds[axis.main] = content[axis.main] + i * size
      bounds[axis.mainSize] = i === count - 1 ? content[axis.mainSize] - i * size : size
      const laneBo = this._bpmnFactory.create('bpmn:Lane')
      laneBo.$parent = laneSet
      laneSet.get('lanes').push(laneBo)
      const laneShape = this._elementFactory.createShape({ type: 'bpmn:Lane', businessObject: laneBo, isHorizontal: horizontal })
      created.push(this._modeling.createShape(laneShape, bounds, participant))
    }
    context.newLanes = created
    this._modeling.updateLaneRefs(participant)
  }
}

/**
 * Größenänderung einer Bahn: angrenzende Bahnen und – an Außenkanten – der
 * Pool passen sich an, damit keine Lücken oder Überlappungen entstehen.
 */
export class ResizeLaneHandler {
  static $inject = ['modeling']

  constructor(private _modeling: any) {}

  preExecute(context: any): void {
    const lane = context.shape
    const newBounds: Bounds = context.newBounds
    const participant = getParticipant(lane)
    const lanes = getAllLanes(participant)
    const shapes = [participant, ...lanes]
    const axis = getAxis(participant)
    const planned = new Map<any, Bounds>()

    const oldStart = lane[axis.main]
    const oldEnd = lane[axis.main] + lane[axis.mainSize]
    const newStart = newBounds[axis.main]
    const newEnd = newBounds[axis.main] + newBounds[axis.mainSize]
    if (newStart !== oldStart) moveEdge(shapes, axis.main, oldStart, newStart - oldStart, planned)
    if (newEnd !== oldEnd) moveEdge(shapes, axis.main, oldEnd, newEnd - oldEnd, planned)

    // Querachse: Pool und alle Bahnen gemeinsam.
    const crossStart = lane[axis.cross]
    const crossEnd = lane[axis.cross] + lane[axis.crossSize]
    const newCrossStart = newBounds[axis.cross]
    const newCrossEnd = newBounds[axis.cross] + newBounds[axis.crossSize]
    if (newCrossEnd !== crossEnd) {
      const participantEnd = participant[axis.cross] + participant[axis.crossSize]
      moveEdge(shapes, axis.cross, participantEnd, newCrossEnd - crossEnd, planned)
    }
    if (newCrossStart !== crossStart) {
      // Linke Kante: der ganze Pool wächst bzw. schrumpft, Bahnen folgen.
      const delta = newCrossStart - crossStart
      for (const shape of shapes) {
        const bounds = planned.get(shape) || { x: shape.x, y: shape.y, width: shape.width, height: shape.height }
        bounds[axis.cross] += delta
        bounds[axis.crossSize] -= delta
        planned.set(shape, bounds)
      }
    }

    // Pool zuerst, damit Kinder innerhalb bleiben.
    const ordered = [...planned.entries()].sort(([a], [b]) => (a === participant ? -1 : b === participant ? 1 : 0))
    for (const [shape, bounds] of ordered) {
      if (!boundsEqual(bounds, shape)) {
        this._modeling.resizeShape(shape, bounds, null, { skipLaneLayout: true })
      }
    }
  }

  postExecute(context: any): void {
    const participant = getParticipant(context.shape)
    if (participant) this._modeling.updateLaneRefs(participant)
  }
}

/** Pflegt `flowNodeRef` aller Bahnen eines Pools anhand der Lage der Knoten. */
export class UpdateFlowNodeRefsHandler {
  execute(context: any): any[] {
    const updates: { lane: any; oldRefs: any[]; newRefs: any[] }[] = context.updates
    for (const update of updates) {
      const refs = update.lane.get('flowNodeRef')
      refs.length = 0
      refs.push(...update.newRefs)
    }
    return []
  }

  revert(context: any): any[] {
    for (const update of context.updates) {
      const refs = update.lane.get('flowNodeRef')
      refs.length = 0
      refs.push(...update.oldRefs)
    }
    return []
  }
}

/** Berechnet die Soll-Referenzen; liefert nur tatsächliche Änderungen. */
export function computeLaneRefUpdates(participant: any): { lane: any; oldRefs: any[]; newRefs: any[] }[] {
  const lanes = getAllLanes(participant)
  if (lanes.length === 0) return []
  const nodes = (participant.children || []).filter(
    (child: any) => is(child, 'bpmn:FlowNode') && !child.labelTarget && !child.waypoints,
  )
  const shownNodes = new Set(nodes.map((node: any) => getBusinessObject(node)))
  const updates: { lane: any; oldRefs: any[]; newRefs: any[] }[] = []
  for (const laneShape of lanes) {
    const lane = getBusinessObject(laneShape)
    const oldRefs = [...lane.get('flowNodeRef')]
    const contained = nodes
      .filter((node: any) => {
        const cx = node.x + node.width / 2
        const cy = node.y + node.height / 2
        return cx >= laneShape.x && cx <= laneShape.x + laneShape.width && cy >= laneShape.y && cy <= laneShape.y + laneShape.height
      })
      .map((node: any) => getBusinessObject(node))
    // Referenzen auf nicht dargestellte Knoten bleiben erhalten, Reihenfolge ebenso.
    const newRefs = [
      ...oldRefs.filter((ref: any) => !shownNodes.has(ref) || contained.includes(ref)),
      ...contained.filter((ref: any) => !oldRefs.includes(ref)),
    ]
    const same = newRefs.length === oldRefs.length && newRefs.every((ref, index) => ref === oldRefs[index])
    if (!same) updates.push({ lane, oldRefs, newRefs })
  }
  return updates
}

export { LANE_BAND }
