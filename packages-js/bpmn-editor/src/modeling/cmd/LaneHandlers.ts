/**
 * Befehle für Bahnen: anlegen (oberhalb/unterhalb bzw. links/rechts),
 * teilen, Größe ändern und Bahnzugehörigkeit (`flowNodeRef`) pflegen.
 */

import { getBusinessObject, is, isHorizontal } from '../../util/ModelUtil'
import {
  DEFAULT_LANE_SIZE,
  boundsEqual,
  getAllLanes,
  getAxis,
  getChildLanes,
  getContentBounds,
  getLaneParent,
  getParticipant,
  moveEdge,
  toBounds,
  type Axis,
  type Bounds,
} from '../LaneUtil'
import type { BpmnElement, Canvas, ElementRegistry, ModdleElement } from '../../types'
import type BpmnFactory from '../BpmnFactory'
import type ElementFactory from '../ElementFactory'
import type Modeling from '../Modeling'

export type LaneLocation = 'top' | 'bottom' | 'left' | 'right'

interface AddLaneContext {
  shape: BpmnElement
  location?: LaneLocation
  laneSize?: number
  newLane?: BpmnElement
}

interface SplitLaneContext {
  shape: BpmnElement
  count?: number
  createdLaneSet?: ModdleElement
  newLanes?: BpmnElement[]
}

interface ResizeLaneContext {
  shape: BpmnElement
  newBounds: Bounds
}

export interface LaneRefUpdate {
  lane: ModdleElement
  oldRefs: ModdleElement[]
  newRefs: ModdleElement[]
}

function isStart(location: LaneLocation): boolean {
  return location === 'top' || location === 'left'
}

/** Pool und alle übergeordneten Bahnen einer Bahn. */
function ancestorsOf(lane: BpmnElement, participant: BpmnElement): BpmnElement[] {
  const result: BpmnElement[] = [participant]
  let parent = getLaneParent(lane)
  while (parent && is(parent, 'bpmn:Lane')) {
    result.push(parent)
    parent = getLaneParent(parent)
  }
  return result
}

/** Legt eine Bahnform an und reiht sie semantisch in die Bahnmenge ein. */
function createLane(
  services: { modeling: Modeling; elementFactory: ElementFactory; bpmnFactory: BpmnFactory },
  participant: BpmnElement,
  bounds: Bounds,
  laneSet: ModdleElement | undefined,
  index: number,
): BpmnElement {
  const bo = services.bpmnFactory.create('bpmn:Lane')
  if (laneSet) {
    bo.$parent = laneSet
    const lanes = laneSet.get<ModdleElement[]>('lanes')
    lanes.splice(Math.min(index, lanes.length), 0, bo)
  }
  const shape = services.elementFactory.createShape({ type: 'bpmn:Lane', businessObject: bo, isHorizontal: isHorizontal(participant) })
  return services.modeling.createShape(shape as never, bounds, participant as never) as unknown as BpmnElement
}

export class AddLaneHandler {
  static $inject = ['modeling', 'elementFactory', 'bpmnFactory', 'canvas', 'elementRegistry']

  constructor(
    readonly modeling: Modeling,
    readonly elementFactory: ElementFactory,
    readonly bpmnFactory: BpmnFactory,
    private readonly canvas: Canvas,
    private readonly elementRegistry: ElementRegistry,
  ) {}

  preExecute(context: AddLaneContext): void {
    const participant = is(context.shape, 'bpmn:Participant') ? context.shape : getParticipant(context.shape)
    if (!participant) throw new Error('Bahnen setzen einen Pool voraus')
    const axis = getAxis(participant)
    const atStart = isStart(context.location || 'bottom')
    const target = this.resolveTarget(context.shape, participant, axis, atStart)
    const laneSize = context.laneSize || DEFAULT_LANE_SIZE
    const line = atStart ? target[axis.main] : target[axis.main] + target[axis.mainSize]
    this.makeSpace(participant, target, axis, atStart, line, laneSize)

    const parentBounds = getContentBounds(getLaneParent(target) || participant, axis)
    const bounds = { ...parentBounds, [axis.main]: atStart ? line - laneSize : line, [axis.mainSize]: laneSize }
    const laneSet = getBusinessObject(target).$parent || undefined
    const index = (laneSet?.get<ModdleElement[]>('lanes').indexOf(getBusinessObject(target)) ?? 0) + (atStart ? 0 : 1)
    context.newLane = createLane(this, participant, bounds, laneSet, index)
  }

  postExecute(context: AddLaneContext): void {
    const participant = getParticipant(context.newLane)
    if (participant) this.modeling.updateLaneRefs(participant)
  }

  /** Ziel ist die Bahn am gewählten Rand; ein Pool ohne Bahnen erhält zuerst eine. */
  private resolveTarget(shape: BpmnElement, participant: BpmnElement, axis: Axis, atStart: boolean): BpmnElement {
    if (!is(shape, 'bpmn:Participant')) return shape
    const lanes = getChildLanes(participant).sort((a, b) => a[axis.main] - b[axis.main])
    if (lanes.length === 0) return createLane(this, participant, getContentBounds(participant, axis), undefined, 0)
    return (atStart ? lanes[0] : lanes[lanes.length - 1]) as BpmnElement
  }

  /** Schafft Platz für die neue Bahn (Raumwerkzeug-Befehl). */
  private makeSpace(participant: BpmnElement, target: BpmnElement, axis: Axis, atStart: boolean, line: number, size: number): void {
    const resizing = ancestorsOf(target, participant)
    const root = this.canvas.findRoot(participant as never)
    const moving = this.elementRegistry.filter((element) => {
      if (element.waypoints || !element.parent || resizing.includes(element)) return false
      if (this.canvas.findRoot(element as never) !== root) return false
      if (element.labelTarget && resizing.includes(element.labelTarget as BpmnElement)) return false
      const bounds = toBounds(element)
      return atStart ? bounds[axis.main] + bounds[axis.mainSize] <= line : bounds[axis.main] >= line
    })
    const delta = { x: 0, y: 0, [axis.main]: atStart ? -size : size }
    const horizontal = axis.main === 'y'
    const direction = horizontal ? (atStart ? 'n' : 's') : atStart ? 'w' : 'e'
    this.modeling.createSpace(moving as never, resizing as never, delta, direction, line)
  }
}

export class SplitLaneHandler {
  static $inject = ['modeling', 'elementFactory', 'bpmnFactory']

  constructor(
    readonly modeling: Modeling,
    readonly elementFactory: ElementFactory,
    readonly bpmnFactory: BpmnFactory,
  ) {}

  execute(context: SplitLaneContext): BpmnElement[] {
    const bo = getBusinessObject(context.shape)
    if (is(bo, 'bpmn:Lane') && !bo.childLaneSet) {
      const laneSet = this.bpmnFactory.create('bpmn:LaneSet')
      laneSet.$parent = bo
      bo.childLaneSet = laneSet
      context.createdLaneSet = laneSet
    }
    return [context.shape]
  }

  revert(context: SplitLaneContext): BpmnElement[] {
    if (context.createdLaneSet) getBusinessObject(context.shape).childLaneSet = undefined
    return [context.shape]
  }

  postExecute(context: SplitLaneContext): void {
    const shape = context.shape
    const participant = is(shape, 'bpmn:Participant') ? shape : getParticipant(shape)
    if (!participant || getChildLanes(shape).length > 0) return
    const laneSet = this.targetLaneSet(shape)
    if (!laneSet) return
    const axis = getAxis(participant)
    const content = getContentBounds(shape, axis)
    const count = Math.max(2, context.count || 2)
    const size = Math.floor(content[axis.mainSize] / count)
    context.newLanes = Array.from({ length: count }, (_, index) => {
      const bounds = {
        ...content,
        [axis.main]: content[axis.main] + index * size,
        [axis.mainSize]: index === count - 1 ? content[axis.mainSize] - index * size : size,
      }
      return createLane(this, participant, bounds, laneSet, index)
    })
    this.modeling.updateLaneRefs(participant)
  }

  private targetLaneSet(shape: BpmnElement): ModdleElement | undefined {
    const bo = getBusinessObject(shape)
    if (!is(bo, 'bpmn:Participant')) return bo.childLaneSet
    const process = bo.processRef
    if (!process) return undefined
    const laneSets = process.get<ModdleElement[]>('laneSets')
    if (laneSets[0]) return laneSets[0]
    const laneSet = this.bpmnFactory.create('bpmn:LaneSet')
    laneSet.$parent = process
    laneSets.push(laneSet)
    return laneSet
  }
}

/**
 * Größenänderung einer Bahn: angrenzende Bahnen und – an Außenkanten – der
 * Pool passen sich an, damit keine Lücken oder Überlappungen entstehen.
 */
export class ResizeLaneHandler {
  static $inject = ['modeling']

  constructor(private readonly modeling: Modeling) {}

  preExecute(context: ResizeLaneContext): void {
    const lane = context.shape
    const participant = getParticipant(lane)
    if (!participant) return
    const shapes = [participant, ...getAllLanes(participant)]
    const axis = getAxis(participant)
    const planned = new Map<BpmnElement, Bounds>()
    const old = toBounds(lane)
    const next = context.newBounds
    const oldEnd = old[axis.main] + old[axis.mainSize]
    const newEnd = next[axis.main] + next[axis.mainSize]
    if (next[axis.main] !== old[axis.main]) moveEdge(shapes, axis.main, old[axis.main], next[axis.main] - old[axis.main], planned)
    if (newEnd !== oldEnd) moveEdge(shapes, axis.main, oldEnd, newEnd - oldEnd, planned)
    this.planCrossAxis(shapes, participant, axis, old, next, planned)
    const ordered = [...planned.entries()].sort(([a]) => (a === participant ? -1 : 1))
    for (const [shape, bounds] of ordered) {
      if (!boundsEqual(bounds, toBounds(shape))) {
        this.modeling.resizeShape(shape as never, bounds, undefined, { skipLaneLayout: true } as never)
      }
    }
  }

  /** Querachse: rechte Kante betrifft alle, linke Kante verschiebt Pool und Bahnen. */
  private planCrossAxis(shapes: BpmnElement[], participant: BpmnElement, axis: Axis, old: Bounds, next: Bounds, planned: Map<BpmnElement, Bounds>): void {
    const oldEnd = old[axis.cross] + old[axis.crossSize]
    const newEnd = next[axis.cross] + next[axis.crossSize]
    if (newEnd !== oldEnd) {
      const participantEnd = toBounds(participant)[axis.cross] + toBounds(participant)[axis.crossSize]
      moveEdge(shapes, axis.cross, participantEnd, newEnd - oldEnd, planned)
    }
    const delta = next[axis.cross] - old[axis.cross]
    if (delta === 0) return
    for (const shape of shapes) {
      const bounds = planned.get(shape) || toBounds(shape)
      planned.set(shape, { ...bounds, [axis.cross]: bounds[axis.cross] + delta, [axis.crossSize]: bounds[axis.crossSize] - delta })
    }
  }

  postExecute(context: ResizeLaneContext): void {
    const participant = getParticipant(context.shape)
    if (participant) this.modeling.updateLaneRefs(participant)
  }
}

/** Pflegt `flowNodeRef` aller Bahnen eines Pools anhand der Lage der Knoten. */
export class UpdateFlowNodeRefsHandler {
  execute(context: { updates: LaneRefUpdate[] }): BpmnElement[] {
    for (const update of context.updates) replaceList(update.lane.get<ModdleElement[]>('flowNodeRef'), update.newRefs)
    return []
  }

  revert(context: { updates: LaneRefUpdate[] }): BpmnElement[] {
    for (const update of context.updates) replaceList(update.lane.get<ModdleElement[]>('flowNodeRef'), update.oldRefs)
    return []
  }
}

function replaceList<T>(list: T[], values: T[]): void {
  list.length = 0
  list.push(...values)
}

function containsCenter(lane: Bounds, node: Bounds): boolean {
  const cx = node.x + node.width / 2
  const cy = node.y + node.height / 2
  return cx >= lane.x && cx <= lane.x + lane.width && cy >= lane.y && cy <= lane.y + lane.height
}

/** Berechnet die Soll-Referenzen; liefert nur tatsächliche Änderungen. */
export function computeLaneRefUpdates(participant: BpmnElement): LaneRefUpdate[] {
  const lanes = getAllLanes(participant)
  if (lanes.length === 0) return []
  const nodes = ((participant.children || []) as BpmnElement[]).filter(
    (child) => is(child, 'bpmn:FlowNode') && !child.labelTarget && !child.waypoints,
  )
  const shown = new Set(nodes.map((node) => getBusinessObject(node)))
  const updates: LaneRefUpdate[] = []
  for (const laneShape of lanes) {
    const lane = getBusinessObject(laneShape)
    const oldRefs = [...lane.get<ModdleElement[]>('flowNodeRef')]
    const contained = nodes.filter((node) => containsCenter(toBounds(laneShape), toBounds(node))).map((node) => getBusinessObject(node))
    // Referenzen auf nicht dargestellte Knoten bleiben erhalten, Reihenfolge ebenso.
    const newRefs = [
      ...oldRefs.filter((ref) => !shown.has(ref) || contained.includes(ref)),
      ...contained.filter((ref) => !oldRefs.includes(ref)),
    ]
    const same = newRefs.length === oldRefs.length && newRefs.every((ref, index) => ref === oldRefs[index])
    if (!same) updates.push({ lane, oldRefs, newRefs })
  }
  return updates
}
