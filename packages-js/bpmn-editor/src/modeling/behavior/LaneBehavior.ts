/**
 * Verhalten rund um Bahnen:
 * - Ablegen auf einer Bahn legt das Element in den Pool (Bahnen sind keine Container).
 * - Größenänderung eines Pools ordnet seine Bahnen neu an.
 * - Größenänderung einer Bahn passt Nachbarbahnen an (statt Lücken).
 * - Löschen einer Bahn entfernt Unterbahnen und schließt die Lücke.
 * - Nach Änderungen wird `flowNodeRef` nachgeführt.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { is } from '../../util/ModelUtil'
import {
  boundsEqual,
  computeLanesLayout,
  getAllLanes,
  getAxis,
  getDescendantLanes,
  getParticipant,
  moveEdge,
  toBounds,
  type Bounds,
} from '../LaneUtil'
import type { BpmnElement, CommandEvent, EventBus } from '../../types'
import type Modeling from '../Modeling'

type Context = {
  shape?: BpmnElement
  shapes?: BpmnElement[]
  elements?: BpmnElement[]
  newShape?: BpmnElement
  parent?: BpmnElement
  newParent?: BpmnElement
  oldParent?: BpmnElement
  movingShapes?: BpmnElement[]
  resizingShapes?: BpmnElement[]
  oldBounds?: Bounds
  hints?: { skipLaneLayout?: boolean; laneChild?: boolean }
  laneParticipant?: BpmnElement
  laneBounds?: Bounds
}

const REF_COMMANDS = ['elements.create', 'elements.move', 'shape.create', 'shape.resize', 'spaceTool', 'shape.replace', 'elements.delete']

function laneContainer(target: BpmnElement | undefined): BpmnElement | undefined {
  let current = target
  while (current && is(current, 'bpmn:Lane')) current = current.parent as BpmnElement | undefined
  return current
}

function affectedParticipants(context: Context): Set<BpmnElement> {
  const shapes = [
    ...(context.elements || []),
    ...(context.shapes || []),
    ...(context.movingShapes || []),
    ...(context.resizingShapes || []),
    ...[context.shape, context.newShape, context.newParent, context.oldParent].filter((shape): shape is BpmnElement => !!shape),
  ]
  const participants = new Set<BpmnElement>()
  for (const shape of shapes) {
    const participant = getParticipant(shape)
    if (participant && participant.parent) participants.add(participant)
  }
  return participants
}

export default class LaneBehavior extends CommandInterceptor {
  static $inject = ['eventBus', 'modeling']

  private spaceToolDepth = 0

  constructor(
    eventBus: EventBus,
    private readonly modeling: Modeling,
  ) {
    super(eventBus)
    this.registerRetargeting()
    this.preExecute('spaceTool', () => void this.spaceToolDepth++)
    this.postExecute('spaceTool', () => void this.spaceToolDepth--)
    this.postExecute('shape.resize', (event: CommandEvent<Context>) => this.layoutAfterResize(event.context))
    this.preExecute('shape.delete', (event: CommandEvent<Context>) => this.removeChildLanes(event.context))
    this.postExecute('shape.delete', (event: CommandEvent<Context>) => this.closeGap(event.context))
    this.postExecuted(REF_COMMANDS, 500, (event: CommandEvent<Context>) => {
      for (const participant of affectedParticipants(event.context)) this.modeling.updateLaneRefs(participant as never)
    })
    // Interaktive Größenänderung einer Bahn über lane.resize
    eventBus.on('resize.end', 2000, (event: { context: { shape: BpmnElement; newBounds?: Bounds; canExecute?: unknown } }) => {
      const { shape, newBounds, canExecute } = event.context
      if (!is(shape, 'bpmn:Lane') || !newBounds || !canExecute) return
      this.modeling.resizeLane(shape as never, {
        x: Math.round(newBounds.x),
        y: Math.round(newBounds.y),
        width: Math.round(newBounds.width),
        height: Math.round(newBounds.height),
      })
      return false
    })
  }

  /** Ziel „Bahn“ → Pool. */
  private registerRetargeting(): void {
    this.preExecute(['shape.create', 'elements.create'], 1500, (event: CommandEvent<Context>) => {
      const context = event.context
      if (context.shape && is(context.shape, 'bpmn:Lane')) return
      if (context.parent && is(context.parent, 'bpmn:Lane')) context.parent = laneContainer(context.parent)
    })
    this.preExecute(['elements.move', 'shape.move'], 1500, (event: CommandEvent<Context>) => {
      const context = event.context
      const moved = context.shapes || (context.shape ? [context.shape] : [])
      if (moved.some((shape) => is(shape, 'bpmn:Lane'))) return
      if (context.newParent && is(context.newParent, 'bpmn:Lane')) context.newParent = laneContainer(context.newParent)
    })
  }

  /** Pool-Größe → Bahnen anordnen (nicht beim Raumwerkzeug: dort passen sich Bahnen selbst an). */
  private layoutAfterResize(context: Context): void {
    const shape = context.shape
    if (!shape || !is(shape, 'bpmn:Participant') || context.hints?.skipLaneLayout || this.spaceToolDepth > 0) return
    if (getAllLanes(shape).length === 0 || !context.oldBounds) return
    const axis = getAxis(shape)
    const absorbAtStart = context.oldBounds[axis.main] !== toBounds(shape)[axis.main]
    for (const [lane, bounds] of computeLanesLayout(shape, toBounds(shape), absorbAtStart)) {
      if (!boundsEqual(bounds, toBounds(lane))) this.resizeLane(lane, bounds)
    }
    this.modeling.updateLaneRefs(shape as never)
  }

  private resizeLane(lane: BpmnElement, bounds: Bounds): void {
    this.modeling.resizeShape(lane as never, bounds, undefined, { skipLaneLayout: true, attachSupport: false } as never)
  }

  private removeChildLanes(context: Context): void {
    const shape = context.shape
    if (!shape || !is(shape, 'bpmn:Lane') || context.hints?.laneChild) return
    const participant = getParticipant(shape)
    if (!participant) return
    context.laneParticipant = participant
    context.laneBounds = toBounds(shape)
    for (const child of getDescendantLanes(shape).reverse()) {
      if (child.parent) this.modeling.removeShape(child as never, { laneChild: true } as never)
    }
  }

  /** Vorgängerbahnen wachsen nach hinten; gibt es keine, wachsen die Nachfolger nach vorn. */
  private closeGap(context: Context): void {
    const participant = context.laneParticipant
    const removed = context.laneBounds
    if (!participant || !removed || !participant.parent || context.hints?.laneChild) return
    const lanes = getAllLanes(participant)
    if (lanes.length === 0) return
    const axis = getAxis(participant)
    const start = removed[axis.main]
    const size = removed[axis.mainSize]
    const planned = new Map<BpmnElement, Bounds>()
    const hasBefore = lanes.some((lane) => Math.abs(lane[axis.main] + lane[axis.mainSize] - start) < 1)
    if (hasBefore) moveEdge(lanes, axis.main, start, size, planned)
    else moveEdge(lanes, axis.main, start + size, -size, planned)
    for (const [lane, bounds] of planned) {
      if (!boundsEqual(bounds, toBounds(lane))) this.resizeLane(lane, bounds)
    }
    this.modeling.updateLaneRefs(participant as never)
  }
}
