/**
 * BPMN-Modellierungsdienst. Erweitert den diagram-js-Dienst um fachliche
 * Befehle; Namen und Bedeutung entsprechen der verbreiteten
 * Modellierungs-API (`updateProperties`, `updateModdleProperties`,
 * `setColor`, `updateLabel`, `addLane`, `splitLane`, …).
 */

import BaseModeling from 'diagram-js/lib/features/modeling/Modeling'

import {
  AddLaneHandler,
  ResizeLaneHandler,
  SplitLaneHandler,
  UpdateFlowNodeRefsHandler,
  computeLaneRefUpdates,
} from './cmd/LaneHandlers'
import {
  IdClaimHandler,
  SetColorHandler,
  UpdateCanvasRootHandler,
  UpdateLabelHandler,
  UpdateModdlePropertiesHandler,
  UpdatePropertiesHandler,
} from './cmd/PropertyHandlers'
import { getParticipant } from './LaneUtil'
import { getBusinessObject, is } from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

export default class Modeling extends (BaseModeling as any) {
  static $inject = ['eventBus', 'elementFactory', 'commandStack', 'bpmnRules', 'bpmnFactory', 'canvas']

  _bpmnRules: any
  _bpmnFactory: any
  _canvas: any

  constructor(eventBus: any, elementFactory: any, commandStack: any, bpmnRules: any, bpmnFactory: any, canvas: any) {
    super(eventBus, elementFactory, commandStack)
    this._bpmnRules = bpmnRules
    this._bpmnFactory = bpmnFactory
    this._canvas = canvas
  }

  getHandlers(): Record<string, unknown> {
    const handlers = BaseModeling.prototype.getHandlers.call(this)
    return {
      ...handlers,
      'element.updateProperties': UpdatePropertiesHandler,
      'element.updateModdleProperties': UpdateModdlePropertiesHandler,
      'element.setColor': SetColorHandler,
      'element.updateLabel': UpdateLabelHandler,
      'canvas.updateRoot': UpdateCanvasRootHandler,
      'id.updateClaim': IdClaimHandler,
      'lane.add': AddLaneHandler,
      'lane.split': SplitLaneHandler,
      'lane.resize': ResizeLaneHandler,
      'lane.updateRefs': UpdateFlowNodeRefsHandler,
      'elements.compound': CompoundHandler,
    }
  }

  /** Führt mehrere Änderungen als einen rückgängig machbaren Schritt aus. */
  compound(run: () => void): void {
    this._commandStack.execute('elements.compound', { run })
  }

  updateLabel(element: any, newLabel: string | null, newBounds?: any, hints?: any): void {
    this._commandStack.execute('element.updateLabel', { element, newLabel, newBounds, hints: hints || {} })
  }

  /** Verbindet zwei Elemente; der Typ ergibt sich aus den Modellierungsregeln. */
  connect(source: any, target: any, attrs?: any, hints?: any): any {
    const bpmnRules = this._bpmnRules
    if (!attrs || !attrs.type) {
      const rule = bpmnRules.canConnect(source, target)
      if (!rule) return undefined
      attrs = { ...(attrs || {}), ...rule }
    }
    const parent = getConnectionParent(source, target, attrs.type)
    return this.createConnection(source, target, attrs, parent, hints)
  }

  updateProperties(element: any, properties: Record<string, unknown>): void {
    this._commandStack.execute('element.updateProperties', { element, properties })
  }

  updateModdleProperties(element: any, moddleElement: any, properties: Record<string, unknown>): void {
    this._commandStack.execute('element.updateModdleProperties', { element, moddleElement, properties })
  }

  setColor(elements: any | any[], colors: { fill?: string | null; stroke?: string | null } = {}): void {
    const list = Array.isArray(elements) ? elements : [elements]
    this._commandStack.execute('element.setColor', { elements: list, colors })
  }

  addLane(targetLaneShape: any, location: 'top' | 'bottom' | 'left' | 'right' = 'bottom'): any {
    const context: any = { shape: targetLaneShape, location }
    this._commandStack.execute('lane.add', context)
    return context.newLane
  }

  splitLane(targetLane: any, count: number): any[] {
    const context: any = { shape: targetLane, count }
    this._commandStack.execute('lane.split', context)
    return context.newLanes || []
  }

  resizeLane(laneShape: any, newBounds: any, balanced?: boolean): void {
    this._commandStack.execute('lane.resize', { shape: laneShape, newBounds, balanced })
  }

  /** Aktualisiert `flowNodeRef` aller Bahnen des Pools (nur bei Änderungen). */
  updateLaneRefs(participantOrElement: any): void {
    const participant = is(participantOrElement, 'bpmn:Participant')
      ? participantOrElement
      : getParticipant(participantOrElement)
    if (!participant) return
    const updates = computeLaneRefUpdates(participant)
    if (updates.length === 0) return
    this._commandStack.execute('lane.updateRefs', { updates })
  }

  /** Macht aus der Prozesswurzel eine Kollaboration (Prozess bleibt erhalten). */
  makeCollaboration(): any {
    const collaboration = this._bpmnFactory.create('bpmn:Collaboration')
    this._commandStack.execute('canvas.updateRoot', { newBusinessObject: collaboration, keepOld: true })
    return this._canvas.getRootElement()
  }

  /** Macht aus der Kollaborationswurzel wieder einen Prozess. */
  makeProcess(): any {
    const process = this._bpmnFactory.create('bpmn:Process', { isExecutable: false })
    this._commandStack.execute('canvas.updateRoot', { newBusinessObject: process, keepOld: false })
    return this._canvas.getRootElement()
  }

  claimId(id: string, moddleElement: any): void {
    this._commandStack.execute('id.updateClaim', { id, element: moddleElement, claiming: true })
  }

  unclaimId(id: string, moddleElement: any): void {
    this._commandStack.execute('id.updateClaim', { id, element: moddleElement, claiming: false })
  }

  /** Blendet den Inhalt eines Teilprozesses ein bzw. aus. */
  toggleCollapse(shape: any, hints?: any): void {
    BaseModeling.prototype.toggleCollapse.call(this, shape, hints)
  }
}

/** Bündelt verschachtelte Befehle zu einem Schritt. */
class CompoundHandler {
  preExecute(context: any): void {
    context.run()
  }

  execute(): any[] {
    return []
  }

  revert(): any[] {
    return []
  }
}

/** Diagramm-Elternform einer neuen Kante. */
export function getConnectionParent(source: any, target: any, type: string): any {
  const rootOf = (element: any) => {
    let current = element
    while (current.parent) current = current.parent
    return current
  }
  if (type === 'bpmn:MessageFlow') {
    return rootOf(source)
  }
  if (type === 'bpmn:Association' || type === 'bpmn:DataInputAssociation' || type === 'bpmn:DataOutputAssociation') {
    return commonParent(source, target) || rootOf(source)
  }
  // Sequenzfluss: Container des Quellknotens (Randereignisse: Container des Wirts).
  const base = source.host || source
  let parent = base.parent
  while (parent && is(parent, 'bpmn:Lane')) parent = parent.parent
  return parent || rootOf(source)
}

function commonParent(a: any, b: any): any {
  const ancestors = new Set<any>()
  let current = a.parent
  while (current) {
    ancestors.add(current)
    current = current.parent
  }
  current = b.parent
  while (current) {
    if (ancestors.has(current) && !is(current, 'bpmn:Lane')) return current
    current = current.parent
  }
  return null
}

export { getBusinessObject }
