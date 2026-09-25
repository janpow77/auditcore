/**
 * Ereignisse:
 * - Anheften an eine Aktivität macht aus einem Zwischenereignis ein
 *   Randereignis; Lösen macht daraus wieder ein fangendes Zwischenereignis.
 * - Neu erzeugte, direkt angeheftete Ereignisse werden gleich als
 *   Randereignis angelegt.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { getBusinessObject, getEventDefinition, is, isAny } from '../../util/ModelUtil'
import type { BpmnElement, CommandEvent, EventBus, ModdleElement } from '../../types'
import type BpmnFactory from '../BpmnFactory'
import type BpmnReplace from '../../replace/BpmnReplace'

/** Ereignisdefinitionen, die ein gelöstes Randereignis als Zwischenereignis behält. */
const CATCH_DEFINITIONS = [
  'bpmn:MessageEventDefinition',
  'bpmn:TimerEventDefinition',
  'bpmn:SignalEventDefinition',
  'bpmn:ConditionalEventDefinition',
]

interface CreateContext {
  shape?: BpmnElement
  host?: BpmnElement
  elements?: BpmnElement[]
  hints?: { attach?: boolean }
}

interface MoveContext {
  shapes?: BpmnElement[]
  newHost?: BpmnElement
}

export default class EventBehavior extends CommandInterceptor {
  static $inject = ['eventBus', 'bpmnReplace', 'bpmnFactory']

  constructor(
    eventBus: EventBus,
    private readonly bpmnReplace: BpmnReplace,
    private readonly bpmnFactory: BpmnFactory,
  ) {
    super(eventBus)
    this.preExecute('elements.create', 1500, (event: CommandEvent<CreateContext>) => {
      const { context } = event
      if (!context.hints?.attach) return
      const shapes = (context.elements || []).filter((element) => !element.waypoints && !element.labelTarget)
      if (shapes.length === 1 && shapes[0]) this.toBoundary(shapes[0])
    })
    this.preExecute('shape.create', 1500, (event: CommandEvent<CreateContext>) => {
      if (event.context.host && event.context.shape) this.toBoundary(event.context.shape)
    })
    this.postExecuted('elements.move', 500, (event: CommandEvent<MoveContext>) => this.afterMove(event.context))
  }

  /** Neues Ereignis vor dem Anlegen semantisch zum Randereignis machen. */
  private toBoundary(shape: BpmnElement): void {
    if (!is(shape, 'bpmn:Event') || is(shape, 'bpmn:BoundaryEvent')) return
    const oldBo = getBusinessObject(shape)
    const newBo = this.bpmnFactory.create('bpmn:BoundaryEvent')
    const definition = getEventDefinition(shape)
    if (definition) {
      definition.$parent = newBo
      newBo.get<ModdleElement[]>('eventDefinitions').push(definition)
    }
    if (oldBo.name) newBo.name = oldBo.name
    shape.businessObject = newBo
    if (shape.di) shape.di.bpmnElement = newBo
    shape.id = newBo.id as string
    shape.type = 'bpmn:BoundaryEvent'
  }

  private afterMove(context: MoveContext): void {
    const shapes = context.shapes || []
    const [single] = shapes
    if (context.newHost && shapes.length === 1 && single) {
      this.attach(single)
      return
    }
    for (const shape of shapes) {
      if (is(shape, 'bpmn:BoundaryEvent') && !shape.host && shape.parent) this.detach(shape)
    }
  }

  private attach(shape: BpmnElement): void {
    if (!is(shape, 'bpmn:Event') || is(shape, 'bpmn:BoundaryEvent') || !shape.parent) return
    const definition = getEventDefinition(shape)
    this.bpmnReplace.replaceElement(
      shape,
      { type: 'bpmn:BoundaryEvent', ...(definition ? { eventDefinitionType: definition.$type } : {}) },
      { select: false },
    )
  }

  private detach(shape: BpmnElement): void {
    const definition = getEventDefinition(shape)
    const keep = !!definition && isAny(definition, CATCH_DEFINITIONS)
    this.bpmnReplace.replaceElement(
      shape,
      { type: 'bpmn:IntermediateCatchEvent', ...(keep && definition ? { eventDefinitionType: definition.$type } : {}) },
      { select: false },
    )
  }
}
