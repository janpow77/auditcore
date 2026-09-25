/**
 * Ereignisse:
 * - Anheften an eine Aktivität macht aus einem Zwischenereignis ein
 *   Randereignis; Lösen macht daraus wieder ein fangendes Zwischenereignis.
 * - Neu erzeugte, direkt angeheftete Ereignisse werden gleich als
 *   Randereignis angelegt.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { getBusinessObject, getEventDefinition, is } from '../../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

export default class EventBehavior extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'bpmnReplace', 'bpmnFactory', 'injector']

  constructor(eventBus: any, private _bpmnReplace: any, bpmnFactory: any, injector: any) {
    super(eventBus)

    // Beim Anlegen mit Anheften: semantisch direkt Randereignis.
    const toBoundary = (shape: any) => {
      if (!shape || !is(shape, 'bpmn:Event') || is(shape, 'bpmn:BoundaryEvent')) return
      const oldBo = getBusinessObject(shape)
      const newBo = bpmnFactory.create('bpmn:BoundaryEvent')
      const definition = getEventDefinition(shape)
      if (definition) {
        definition.$parent = newBo
        newBo.get('eventDefinitions').push(definition)
      }
      if (oldBo.name) newBo.name = oldBo.name
      shape.businessObject = newBo
      if (shape.di) shape.di.bpmnElement = newBo
      shape.id = newBo.id
      shape.type = 'bpmn:BoundaryEvent'
    }

    this.preExecute('elements.create', 1500, (event: any) => {
      const context = event.context
      const hints = context.hints || {}
      if (!hints.attach) return
      const shapes = (context.elements || []).filter((element: any) => !element.waypoints && !element.labelTarget)
      if (shapes.length === 1) toBoundary(shapes[0])
    })

    this.preExecute('shape.create', 1500, (event: any) => {
      const context = event.context
      if (context.host) toBoundary(context.shape)
    })

    // Verschieben mit Anheften / Lösen
    this.postExecuted('elements.move', 500, (event: any) => {
      const context = event.context
      const shapes: any[] = context.shapes || []
      const newHost = context.newHost
      if (newHost && shapes.length === 1) {
        const shape = shapes[0]
        if (is(shape, 'bpmn:Event') && !is(shape, 'bpmn:BoundaryEvent') && shape.parent) {
          const definition = getEventDefinition(shape)
          this._bpmnReplace.replaceElement(
            shape,
            { type: 'bpmn:BoundaryEvent', ...(definition ? { eventDefinitionType: definition.$type } : {}) },
            { select: false },
          )
        }
        return
      }
      for (const shape of shapes) {
        if (is(shape, 'bpmn:BoundaryEvent') && !shape.host && shape.parent) {
          const definition = getEventDefinition(shape)
          const keep =
            definition &&
            ['bpmn:MessageEventDefinition', 'bpmn:TimerEventDefinition', 'bpmn:SignalEventDefinition', 'bpmn:ConditionalEventDefinition'].some(
              (type) => is(definition, type),
            )
          this._bpmnReplace.replaceElement(
            shape,
            { type: 'bpmn:IntermediateCatchEvent', ...(keep ? { eventDefinitionType: definition.$type } : {}) },
            { select: false },
          )
        }
      }
    })

    void injector
  }
}
