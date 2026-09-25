/**
 * BPMN-Modellierungsdienst. Erweitert den diagram-js-Dienst um fachliche
 * Befehle; Namen und Bedeutung entsprechen der verbreiteten
 * Modellierungs-API (`updateProperties`, `updateModdleProperties`,
 * `setColor`, `updateLabel`, `addLane`, `splitLane`, …).
 */

import BaseModeling from 'diagram-js/lib/features/modeling/Modeling'
import type { Connection, Element, Shape } from 'diagram-js/lib/model/Types'

import {
  AddLaneHandler,
  ResizeLaneHandler,
  SplitLaneHandler,
  UpdateFlowNodeRefsHandler,
  computeLaneRefUpdates,
  type LaneLocation,
} from './cmd/LaneHandlers'
import {
  IdClaimHandler,
  SetColorHandler,
  UpdateCanvasRootHandler,
  UpdateModdlePropertiesHandler,
  UpdatePropertiesHandler,
} from './cmd/PropertyHandlers'
import UpdateLabelHandler from './cmd/UpdateLabelHandler'
import { getParticipant } from './LaneUtil'
import { is } from '../util/ModelUtil'
import type { BpmnElement, Bounds, Canvas, CommandStack, EventBus, ModdleElement } from '../types'
import type BpmnFactory from './BpmnFactory'
import type ElementFactory from './ElementFactory'

/** Regeldienst, soweit die Modellierung ihn braucht. */
export interface ConnectRules {
  canConnect(source: Element, target: Element, connection?: Element | null): false | null | { type: string } | Record<string, unknown>
}

type Attrs = Record<string, unknown>

/** Bündelt verschachtelte Befehle zu einem Schritt. */
class CompoundHandler {
  preExecute(context: { run: () => void }): void {
    context.run()
  }

  execute(): Element[] {
    return []
  }

  revert(): Element[] {
    return []
  }
}

const BPMN_HANDLERS: Record<string, unknown> = {
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

export default class Modeling extends BaseModeling {
  static $inject = ['eventBus', 'elementFactory', 'commandStack', 'bpmnRules', 'bpmnFactory', 'canvas']

  private readonly commands: CommandStack

  constructor(
    eventBus: EventBus,
    elementFactory: ElementFactory,
    commandStack: CommandStack,
    private readonly bpmnRules: ConnectRules,
    private readonly bpmnFactory: BpmnFactory,
    private readonly canvas: Canvas,
  ) {
    super(eventBus, elementFactory as never, commandStack)
    this.commands = commandStack
  }

  getHandlers(): ReturnType<BaseModeling['getHandlers']> {
    const base = super.getHandlers() as unknown as Record<string, unknown>
    return { ...base, ...BPMN_HANDLERS } as unknown as ReturnType<BaseModeling['getHandlers']>
  }

  private run(command: string, context: object): void {
    this.commands.execute(command, context as never)
  }

  /** Führt mehrere Änderungen als einen rückgängig machbaren Schritt aus. */
  compound(run: () => void): void {
    this.run('elements.compound', { run })
  }

  updateLabel(element: Element, newLabel: string | null, newBounds?: Bounds, hints?: Attrs): void {
    this.run('element.updateLabel', { element, newLabel, newBounds, hints: hints || {} })
  }

  /** Verbindet zwei Elemente; der Typ ergibt sich aus den Modellierungsregeln. */
  connect(source: Element, target: Element, attrs?: Attrs, hints?: Attrs): Connection {
    let connectionAttrs = attrs
    if (!connectionAttrs || !connectionAttrs.type) {
      const rule = this.bpmnRules.canConnect(source, target)
      if (!rule) return undefined as unknown as Connection
      connectionAttrs = { ...(connectionAttrs || {}), ...rule }
    }
    const parent = getConnectionParent(source as BpmnElement, target as BpmnElement, String(connectionAttrs.type))
    return this.createConnection(source, target, connectionAttrs as never, parent as never, hints)
  }

  updateProperties(element: Element, properties: Attrs): void {
    this.run('element.updateProperties', { element, properties })
  }

  updateModdleProperties(element: Element, moddleElement: ModdleElement, properties: Attrs): void {
    this.run('element.updateModdleProperties', { element, moddleElement, properties })
  }

  setColor(elements: Element | Element[], colors: { fill?: string | null; stroke?: string | null } = {}): void {
    this.run('element.setColor', { elements: Array.isArray(elements) ? elements : [elements], colors })
  }

  addLane(targetLaneShape: Element, location: LaneLocation = 'bottom'): BpmnElement {
    const context: { shape: Element; location: LaneLocation; newLane?: BpmnElement } = { shape: targetLaneShape, location }
    this.run('lane.add', context)
    return context.newLane as BpmnElement
  }

  splitLane(targetLane: Element, count: number): BpmnElement[] {
    const context: { shape: Element; count: number; newLanes?: BpmnElement[] } = { shape: targetLane, count }
    this.run('lane.split', context)
    return context.newLanes || []
  }

  resizeLane(laneShape: Element, newBounds: Bounds, balanced?: boolean): void {
    this.run('lane.resize', { shape: laneShape, newBounds, balanced })
  }

  /** Aktualisiert `flowNodeRef` aller Bahnen des Pools (nur bei Änderungen). */
  updateLaneRefs(participantOrElement: Element): void {
    const element = participantOrElement as BpmnElement
    const participant = is(element, 'bpmn:Participant') ? element : getParticipant(element)
    if (!participant) return
    const updates = computeLaneRefUpdates(participant)
    if (updates.length) this.run('lane.updateRefs', { updates })
  }

  /** Macht aus der Prozesswurzel eine Kollaboration (Prozess bleibt erhalten). */
  makeCollaboration(): BpmnElement {
    this.run('canvas.updateRoot', { newBusinessObject: this.bpmnFactory.create('bpmn:Collaboration'), keepOld: true })
    return this.canvas.getRootElement() as unknown as BpmnElement
  }

  /** Macht aus der Kollaborationswurzel wieder einen Prozess. */
  makeProcess(): BpmnElement {
    const process = this.bpmnFactory.create('bpmn:Process', { isExecutable: false })
    this.run('canvas.updateRoot', { newBusinessObject: process, keepOld: false })
    return this.canvas.getRootElement() as unknown as BpmnElement
  }

  claimId(id: string, moddleElement: ModdleElement): void {
    this.run('id.updateClaim', { id, element: moddleElement, claiming: true })
  }

  unclaimId(id: string, moddleElement: ModdleElement): void {
    this.run('id.updateClaim', { id, element: moddleElement, claiming: false })
  }
}

function rootOf(element: BpmnElement): BpmnElement {
  let current = element
  while (current.parent) current = current.parent as BpmnElement
  return current
}

function commonParent(a: BpmnElement, b: BpmnElement): BpmnElement | null {
  const ancestors = new Set<unknown>()
  for (let current = a.parent; current; current = current.parent) ancestors.add(current)
  for (let current = b.parent as BpmnElement | undefined; current; current = current.parent as BpmnElement | undefined) {
    if (ancestors.has(current) && !is(current, 'bpmn:Lane')) return current
  }
  return null
}

/** Diagramm-Elternform einer neuen Kante. */
export function getConnectionParent(source: BpmnElement, target: BpmnElement, type: string): BpmnElement {
  if (type === 'bpmn:MessageFlow') return rootOf(source)
  if (['bpmn:Association', 'bpmn:DataInputAssociation', 'bpmn:DataOutputAssociation'].includes(type)) {
    return commonParent(source, target) || rootOf(source)
  }
  // Sequenzfluss: Container des Quellknotens (Randereignisse: Container des Wirts).
  const base = (source.host as BpmnElement | undefined) || source
  let parent = base.parent as BpmnElement | undefined
  while (parent && is(parent, 'bpmn:Lane')) parent = parent.parent as BpmnElement | undefined
  return parent || rootOf(source)
}

export type { Shape }
