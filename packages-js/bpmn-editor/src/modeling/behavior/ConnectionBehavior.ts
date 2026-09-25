/**
 * Kanten:
 * - Nach dem Verschieben werden Kanten geprüft: ungültige entfallen, der
 *   Typ wird bei Bedarf gewechselt (Sequenz- ↔ Nachrichtenfluss), die
 *   Elternform wird korrigiert.
 * - Standardfluss (`default`) wird beim Löschen/Umhängen bereinigt.
 * - Beim Löschen eines Knotens mit genau einem ein- und ausgehenden
 *   Sequenzfluss werden Vorgänger und Nachfolger verbunden.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'
import { getMid } from 'diagram-js/lib/layout/LayoutUtil'

import { getBusinessObject, is, isAny } from '../../util/ModelUtil'
import { getConnectionParent, type ConnectRules } from '../Modeling'
import type { BpmnElement, CommandEvent, EventBus, Point } from '../../types'
import type Modeling from '../Modeling'

const FLOW_TYPES = ['bpmn:SequenceFlow', 'bpmn:MessageFlow']

interface MoveContext {
  shapes?: BpmnElement[]
  closure?: { allShapes?: Record<string, BpmnElement> }
}

interface ConnectionContext {
  connection: BpmnElement
  newSource?: BpmnElement
}

interface DeleteContext {
  shape: BpmnElement
  hints?: { reconnect?: boolean }
}

function collectConnections(shapes: BpmnElement[]): Set<BpmnElement> {
  const connections = new Set<BpmnElement>()
  const visit = (shape: BpmnElement) => {
    for (const connection of [...(shape.incoming || []), ...(shape.outgoing || [])]) connections.add(connection as BpmnElement)
    ;((shape.attachers || []) as BpmnElement[]).forEach(visit)
    ;((shape.children || []) as BpmnElement[]).filter((child) => !child.waypoints).forEach(visit)
  }
  shapes.forEach(visit)
  return connections
}

function sequenceFlows(list: unknown[] | undefined): BpmnElement[] {
  return ((list || []) as BpmnElement[]).filter((connection) => is(connection, 'bpmn:SequenceFlow'))
}

/** Genau ein eingehender und ein ausgehender Sequenzfluss? Dann Brücke vom Vorgänger zum Nachfolger. */
function singleBridge(shape: BpmnElement): { inFlow: BpmnElement; target: BpmnElement } | null {
  const incoming = sequenceFlows(shape.incoming)
  const outgoing = sequenceFlows(shape.outgoing)
  if (incoming.length !== 1 || outgoing.length !== 1) return null
  const inFlow = incoming[0] as BpmnElement
  const target = (outgoing[0] as BpmnElement).target as BpmnElement | undefined
  if (!target || target === shape || inFlow.source === target) return null
  return { inFlow, target }
}

export default class ConnectionBehavior extends CommandInterceptor {
  static $inject = ['eventBus', 'modeling', 'bpmnRules']

  constructor(
    eventBus: EventBus,
    private readonly modeling: Modeling,
    private readonly rules: ConnectRules,
  ) {
    super(eventBus)
    this.postExecuted('elements.move', 400, (event: CommandEvent<MoveContext>) => {
      const closure = event.context.closure
      const shapes = closure?.allShapes ? Object.values(closure.allShapes) : event.context.shapes || []
      for (const connection of collectConnections(shapes)) this.checkConnection(connection)
    })
    this.preExecute('connection.delete', (event: CommandEvent<ConnectionContext>) => {
      const connection = event.context.connection
      const source = connection.source as BpmnElement | undefined
      if (source?.parent) this.clearDefault(source, connection)
    })
    this.preExecute('connection.reconnect', (event: CommandEvent<ConnectionContext>) => {
      const { connection, newSource } = event.context
      const oldSource = connection.source as BpmnElement | undefined
      if (newSource && oldSource && newSource !== oldSource) this.clearDefault(oldSource, connection)
    })
    this.preExecute('shape.delete', (event: CommandEvent<DeleteContext>) => this.bridgeGap(event.context))
  }

  private clearDefault(source: BpmnElement, connection: BpmnElement): void {
    if (getBusinessObject(source).default === getBusinessObject(connection)) {
      this.modeling.updateProperties(source, { default: undefined })
    }
  }

  /** Prüft eine Kante nach dem Verschieben ihrer Enden. */
  private checkConnection(connection: BpmnElement): void {
    const source = connection.source as BpmnElement | undefined
    const target = connection.target as BpmnElement | undefined
    if (!connection.parent || !source || !target) return
    const allowed = this.rules.canConnect(source, target, null)
    const type = String(connection.type || getBusinessObject(connection).$type)
    const isFlow = isAny(connection, FLOW_TYPES)
    if (!allowed) {
      // Nur Flüsse, deren Art sich aus der Lage ergibt, entfallen.
      if (isFlow) this.modeling.removeConnection(connection as never)
      return
    }
    const allowedType = String((allowed as { type?: string }).type)
    if (isFlow && allowedType !== type && FLOW_TYPES.includes(allowedType)) {
      this.retype(connection, source, target, allowedType)
      return
    }
    const expected = getConnectionParent(source, target, type)
    if (connection.parent !== expected) this.modeling.moveConnection(connection as never, { x: 0, y: 0 }, expected as never)
  }

  private retype(connection: BpmnElement, source: BpmnElement, target: BpmnElement, type: string): void {
    const name = getBusinessObject(connection).name
    const waypoints = (connection.waypoints as Point[]).map((point) => ({ x: point.x, y: point.y }))
    this.modeling.removeConnection(connection as never)
    const created = this.modeling.connect(source, target, { type, waypoints })
    if (created && name) this.modeling.updateProperties(created, { name })
  }

  /** Knoten löschen und Vorgänger mit Nachfolger verbinden. */
  private bridgeGap(context: DeleteContext): void {
    const shape = context.shape
    if (context.hints?.reconnect === false || !is(shape, 'bpmn:FlowNode') || shape.labelTarget) return
    const bridge = singleBridge(shape)
    if (!bridge || !this.rules.canConnect(bridge.inFlow.source as BpmnElement, bridge.target, bridge.inFlow)) return
    this.modeling.reconnectEnd(bridge.inFlow as never, bridge.target as never, getMid(bridge.target as never))
  }
}
