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

import { getBusinessObject, is } from '../../util/ModelUtil'
import { getConnectionParent } from '../Modeling'

/* eslint-disable @typescript-eslint/no-explicit-any */

export default class ConnectionBehavior extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'modeling', 'bpmnRules']

  constructor(eventBus: any, modeling: any, bpmnRules: any) {
    super(eventBus)

    const checkConnections = (shapes: any[]) => {
      const connections = new Set<any>()
      const visit = (shape: any) => {
        ;(shape.incoming || []).forEach((connection: any) => connections.add(connection))
        ;(shape.outgoing || []).forEach((connection: any) => connections.add(connection))
        ;(shape.attachers || []).forEach(visit)
        ;(shape.children || []).forEach((child: any) => {
          if (!child.waypoints) visit(child)
        })
      }
      shapes.forEach(visit)

      for (const connection of connections) {
        if (!connection.parent || !connection.source || !connection.target) continue
        const allowed = bpmnRules.canConnect(connection.source, connection.target, null)
        const type = connection.type || getBusinessObject(connection).$type
        if (!allowed) {
          // Nur Flüsse prüfen, deren Art sich aus der Lage ergibt.
          if (is(connection, 'bpmn:SequenceFlow') || is(connection, 'bpmn:MessageFlow')) modeling.removeConnection(connection)
          continue
        }
        if (
          (is(connection, 'bpmn:SequenceFlow') || is(connection, 'bpmn:MessageFlow')) &&
          allowed.type !== type &&
          (allowed.type === 'bpmn:SequenceFlow' || allowed.type === 'bpmn:MessageFlow')
        ) {
          const bo = getBusinessObject(connection)
          const { source, target } = connection
          const waypoints = connection.waypoints.map((point: any) => ({ x: point.x, y: point.y }))
          modeling.removeConnection(connection)
          const created = modeling.connect(source, target, { type: allowed.type, waypoints })
          if (created && bo.name) modeling.updateProperties(created, { name: bo.name })
          continue
        }
        const expected = getConnectionParent(connection.source, connection.target, type)
        if (expected && connection.parent !== expected) {
          modeling.moveConnection(connection, { x: 0, y: 0 }, expected)
        }
      }
    }

    this.postExecuted('elements.move', 400, (event: any) => {
      const closure = event.context.closure
      checkConnections(closure && closure.allShapes ? Object.values(closure.allShapes) : event.context.shapes || [])
    })

    // Standardfluss bereinigen
    this.preExecute('connection.delete', (event: any) => {
      const connection = event.context.connection
      const source = connection.source
      if (source && source.parent && getBusinessObject(source).default === getBusinessObject(connection)) {
        modeling.updateProperties(source, { default: undefined })
      }
    })
    this.preExecute('connection.reconnect', (event: any) => {
      const context = event.context
      const connection = context.connection
      const oldSource = connection.source
      if (context.newSource && oldSource && context.newSource !== oldSource) {
        if (getBusinessObject(oldSource).default === getBusinessObject(connection)) {
          modeling.updateProperties(oldSource, { default: undefined })
        }
      }
    })

    // Knoten löschen und Vorgänger mit Nachfolger verbinden
    this.preExecute('shape.delete', (event: any) => {
      const context = event.context
      const shape = context.shape
      const hints = context.hints || {}
      if (hints.reconnect === false || !is(shape, 'bpmn:FlowNode') || shape.labelTarget) return
      const incoming = (shape.incoming || []).filter((connection: any) => is(connection, 'bpmn:SequenceFlow'))
      const outgoing = (shape.outgoing || []).filter((connection: any) => is(connection, 'bpmn:SequenceFlow'))
      if (incoming.length !== 1 || outgoing.length !== 1) return
      const inFlow = incoming[0]
      const outFlow = outgoing[0]
      const target = outFlow.target
      if (!target || target === shape || inFlow.source === target) return
      if (!bpmnRules.canConnect(inFlow.source, target, inFlow)) return
      modeling.reconnectEnd(inFlow, target, getMid(target))
    })
  }
}
