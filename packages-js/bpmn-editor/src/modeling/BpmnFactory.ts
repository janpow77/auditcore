/**
 * Erzeugt semantische (moddle-)Elemente und die zugehörige DI.
 */

import { getIds } from '../util/Ids'
import { is } from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

const ID_PREFIXES: [string, string][] = [
  ['bpmn:Definitions', 'Definitions_'],
  ['bpmn:Process', 'Process_'],
  ['bpmn:Collaboration', 'Collaboration_'],
  ['bpmn:Participant', 'Participant_'],
  ['bpmn:Lane', 'Lane_'],
  ['bpmn:LaneSet', 'LaneSet_'],
  ['bpmn:SequenceFlow', 'Flow_'],
  ['bpmn:MessageFlow', 'MessageFlow_'],
  ['bpmn:DataInputAssociation', 'DataInputAssociation_'],
  ['bpmn:DataOutputAssociation', 'DataOutputAssociation_'],
  ['bpmn:Association', 'Association_'],
  ['bpmn:BoundaryEvent', 'Event_'],
  ['bpmn:Event', 'Event_'],
  ['bpmn:Gateway', 'Gateway_'],
  ['bpmn:SubProcess', 'SubProcess_'],
  ['bpmn:CallActivity', 'CallActivity_'],
  ['bpmn:Task', 'Activity_'],
  ['bpmn:DataObjectReference', 'DataObjectReference_'],
  ['bpmn:DataObject', 'DataObject_'],
  ['bpmn:DataStoreReference', 'DataStoreReference_'],
  ['bpmn:DataStore', 'DataStore_'],
  ['bpmn:DataInput', 'DataInput_'],
  ['bpmn:DataOutput', 'DataOutput_'],
  ['bpmn:TextAnnotation', 'TextAnnotation_'],
  ['bpmn:Group', 'Group_'],
  ['bpmn:Category', 'Category_'],
  ['bpmn:CategoryValue', 'CategoryValue_'],
  ['bpmn:EventDefinition', 'EventDefinition_'],
  ['bpmn:FormalExpression', 'Expression_'],
  ['bpmn:Message', 'Message_'],
  ['bpmn:Signal', 'Signal_'],
  ['bpmn:Error', 'Error_'],
  ['bpmn:Escalation', 'Escalation_'],
  ['bpmndi:BPMNDiagram', 'BPMNDiagram_'],
  ['bpmndi:BPMNPlane', 'BPMNPlane_'],
]

export default class BpmnFactory {
  static $inject = ['moddle']

  _model: any

  constructor(moddle: any) {
    this._model = moddle
  }

  _needsId(element: any): boolean {
    return (
      is(element, 'bpmn:RootElement') ||
      is(element, 'bpmn:FlowElement') ||
      is(element, 'bpmn:MessageFlow') ||
      is(element, 'bpmn:DataAssociation') ||
      is(element, 'bpmn:Artifact') ||
      is(element, 'bpmn:Participant') ||
      is(element, 'bpmn:Lane') ||
      is(element, 'bpmn:LaneSet') ||
      is(element, 'bpmn:Process') ||
      is(element, 'bpmn:Collaboration') ||
      is(element, 'bpmn:EventDefinition') ||
      is(element, 'bpmn:ItemAwareElement') ||
      is(element, 'bpmn:InputOutputSpecification') ||
      is(element, 'bpmn:InputSet') ||
      is(element, 'bpmn:OutputSet') ||
      is(element, 'bpmn:CategoryValue') ||
      is(element, 'bpmn:Property') ||
      is(element, 'bpmndi:BPMNShape') ||
      is(element, 'bpmndi:BPMNEdge') ||
      is(element, 'bpmndi:BPMNDiagram') ||
      is(element, 'bpmndi:BPMNPlane')
    )
  }

  _prefix(element: any): string {
    for (const [type, prefix] of ID_PREFIXES) {
      if (is(element, type)) return prefix
    }
    const local = String(element.$type || 'Element').split(':').pop()
    return `${local}_`
  }

  _ensureId(element: any): void {
    if (element.id) {
      getIds(this._model).claim(element.id, element)
      return
    }
    if (!this._needsId(element)) return
    element.id = getIds(this._model).nextPrefixed(this._prefix(element), element)
  }

  create(type: string, attrs: Record<string, any> = {}): any {
    const element = this._model.create(type, attrs)
    this._ensureId(element)
    return element
  }

  createDiLabel(): any {
    return this.create('bpmndi:BPMNLabel', { bounds: this.createDiBounds() })
  }

  createDiShape(semantic: any, attrs: Record<string, any> = {}): any {
    return this.create('bpmndi:BPMNShape', {
      id: semantic.id ? `${semantic.id}_di` : undefined,
      bpmnElement: semantic,
      bounds: this.createDiBounds(),
      ...attrs,
    })
  }

  createDiBounds(bounds?: { x: number; y: number; width: number; height: number }): any {
    return this.create('dc:Bounds', bounds ? pick(bounds) : {})
  }

  createDiWaypoints(waypoints: { x: number; y: number }[]): any[] {
    return (waypoints || []).map((point) => this.createDiWaypoint(point))
  }

  createDiWaypoint(point: { x: number; y: number }): any {
    return this.create('dc:Point', { x: point.x, y: point.y })
  }

  createDiEdge(semantic: any, attrs: Record<string, any> = {}): any {
    return this.create('bpmndi:BPMNEdge', {
      id: semantic.id ? `${semantic.id}_di` : undefined,
      bpmnElement: semantic,
      waypoint: this.createDiWaypoints([]),
      ...attrs,
    })
  }

  createDiPlane(semantic: any, attrs: Record<string, any> = {}): any {
    return this.create('bpmndi:BPMNPlane', { bpmnElement: semantic, ...attrs })
  }

  createDiDiagram(plane: any): any {
    return this.create('bpmndi:BPMNDiagram', { plane })
  }
}

function pick(bounds: { x: number; y: number; width: number; height: number }) {
  return {
    x: Math.round(bounds.x),
    y: Math.round(bounds.y),
    width: Math.round(bounds.width),
    height: Math.round(bounds.height),
  }
}
