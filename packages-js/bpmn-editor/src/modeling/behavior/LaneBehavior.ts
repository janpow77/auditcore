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
  getSiblingLanes,
  moveEdge,
  type Bounds,
} from '../LaneUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

function laneContainer(target: any): any {
  let current = target
  while (current && is(current, 'bpmn:Lane')) current = current.parent
  return current
}

export default class LaneBehavior extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'modeling', 'elementRegistry']

  constructor(eventBus: any, modeling: any, elementRegistry: any) {
    super(eventBus)


    // (1) Ziel „Bahn“ → Pool
    this.preExecute(['shape.create', 'elements.create'], 1500, (event: any) => {
      const context = event.context
      const shape = context.shape
      if (shape && is(shape, 'bpmn:Lane')) return
      if (context.parent && is(context.parent, 'bpmn:Lane')) context.parent = laneContainer(context.parent)
    })
    this.preExecute(['elements.move'], 1500, (event: any) => {
      const context = event.context
      const shapes: any[] = context.shapes || []
      if (shapes.some((shape) => is(shape, 'bpmn:Lane'))) return
      if (context.newParent && is(context.newParent, 'bpmn:Lane')) context.newParent = laneContainer(context.newParent)
    })
    this.preExecute(['shape.move'], 1500, (event: any) => {
      const context = event.context
      if (is(context.shape, 'bpmn:Lane')) return
      if (context.newParent && is(context.newParent, 'bpmn:Lane')) context.newParent = laneContainer(context.newParent)
    })

    // (2) Pool-Größe → Bahnen anordnen (nicht beim Raumwerkzeug: dort
    // werden Bahnen, die die Linie kreuzen, bereits mit angepasst).
    let spaceToolDepth = 0
    this.preExecute('spaceTool', () => {
      spaceToolDepth++
    })
    this.postExecute('spaceTool', () => {
      spaceToolDepth--
    })
    this.postExecute('shape.resize', (event: any) => {
      const context = event.context
      const shape = context.shape
      const hints = context.hints || {}
      if (!is(shape, 'bpmn:Participant') || hints.skipLaneLayout || spaceToolDepth > 0) return
      if (getAllLanes(shape).length === 0) return
      const axis = getAxis(shape)
      const oldBounds: Bounds = context.oldBounds
      const absorbAtStart = oldBounds[axis.main] !== shape[axis.main]
      const layout = computeLanesLayout(shape, { x: shape.x, y: shape.y, width: shape.width, height: shape.height }, absorbAtStart)
      for (const [lane, bounds] of layout) {
        if (!boundsEqual(bounds, lane)) modeling.resizeShape(lane, bounds, null, { skipLaneLayout: true, attachSupport: false })
      }
      modeling.updateLaneRefs(shape)
    })

    // (3) Löschen einer Bahn
    this.preExecute('shape.delete', (event: any) => {
      const context = event.context
      const shape = context.shape
      if (!is(shape, 'bpmn:Lane') || (context.hints && context.hints.laneChild)) return
      const participant = getParticipant(shape)
      if (!participant) return
      context.laneParticipant = participant
      context.laneBounds = { x: shape.x, y: shape.y, width: shape.width, height: shape.height }
      for (const child of getDescendantLanes(shape).reverse()) {
        if (child.parent) modeling.removeShape(child, { laneChild: true })
      }
    })
    this.postExecute('shape.delete', (event: any) => {
      const context = event.context
      const shape = context.shape
      if (!is(shape, 'bpmn:Lane') || !context.laneParticipant || (context.hints && context.hints.laneChild)) return
      const participant = context.laneParticipant
      if (!participant.parent) return
      const removed: Bounds = context.laneBounds
      const axis = getAxis(participant)
      const lanes = getAllLanes(participant)
      if (lanes.length === 0) return
      const planned = new Map<any, Bounds>()
      const start = removed[axis.main]
      const end = removed[axis.main] + removed[axis.mainSize]
      const size = removed[axis.mainSize]
      // Vorgängerbahnen wachsen nach hinten; gibt es keine, wachsen die Nachfolger nach vorn.
      const before = lanes.some((lane: any) => Math.abs(lane[axis.main] + lane[axis.mainSize] - start) < 1)
      if (before) moveEdge(lanes, axis.main, start, size, planned)
      else moveEdge(lanes, axis.main, end, -size, planned)
      for (const [lane, bounds] of planned) {
        if (!boundsEqual(bounds, lane)) modeling.resizeShape(lane, bounds, null, { skipLaneLayout: true, attachSupport: false })
      }
      modeling.updateLaneRefs(participant)
    })

    // (4) Bahnzugehörigkeit nachführen
    this.postExecuted(
      ['elements.create', 'elements.move', 'shape.create', 'shape.resize', 'spaceTool', 'shape.replace', 'elements.delete'],
      500,
      (event: any) => {
        const context = event.context
        const shapes: any[] = [
          ...(context.elements || []),
          ...(context.shapes || []),
          ...(context.shape ? [context.shape] : []),
          ...(context.newShape ? [context.newShape] : []),
          ...(context.movingShapes || []),
          ...(context.resizingShapes || []),
        ]
        const participants = new Set<any>()
        for (const shape of shapes) {
          const participant = is(shape, 'bpmn:Participant') ? shape : getParticipant(shape)
          if (participant && participant.parent) participants.add(participant)
        }
        if (context.newParent && getParticipant(context.newParent)) participants.add(getParticipant(context.newParent))
        if (context.oldParent && getParticipant(context.oldParent)) participants.add(getParticipant(context.oldParent))
        for (const participant of participants) modeling.updateLaneRefs(participant)
      },
    )

    // (5) Interaktive Größenänderung einer Bahn über lane.resize
    eventBus.on('resize.end', 2000, (event: any) => {
      const context = event.context
      const shape = context.shape
      if (!is(shape, 'bpmn:Lane')) return
      const newBounds = context.newBounds
      if (!newBounds || !context.canExecute) return
      modeling.resizeLane(shape, {
        x: Math.round(newBounds.x),
        y: Math.round(newBounds.y),
        width: Math.round(newBounds.width),
        height: Math.round(newBounds.height),
      })
      return false
    })

    void elementRegistry
    void getSiblingLanes
  }
}
