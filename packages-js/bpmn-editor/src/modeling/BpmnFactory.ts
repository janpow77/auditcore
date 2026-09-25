/**
 * Erzeugt semantische (moddle-)Elemente und die zugehörige DI.
 */

import { getIds } from '../util/Ids'
import { is, isAny } from '../util/ModelUtil'
import type { Bounds, Moddle, ModdleElement, Point } from '../types'

/** Präfix neuer Kennungen je Typ (erster Treffer gewinnt). */
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
  ['bpmndi:BPMNDiagram', 'BPMNDiagram_'],
  ['bpmndi:BPMNPlane', 'BPMNPlane_'],
]

/** Typen, die eine Kennung erhalten. */
const NEEDS_ID = [
  'bpmn:RootElement',
  'bpmn:FlowElement',
  'bpmn:MessageFlow',
  'bpmn:DataAssociation',
  'bpmn:Artifact',
  'bpmn:Participant',
  'bpmn:Lane',
  'bpmn:LaneSet',
  'bpmn:EventDefinition',
  'bpmn:ItemAwareElement',
  'bpmn:InputOutputSpecification',
  'bpmn:InputSet',
  'bpmn:OutputSet',
  'bpmn:CategoryValue',
  'bpmn:Property',
  'bpmn:ParticipantMultiplicity',
  'bpmndi:BPMNShape',
  'bpmndi:BPMNEdge',
  'bpmndi:BPMNDiagram',
  'bpmndi:BPMNPlane',
]

function roundBounds(bounds: Bounds): Bounds {
  return {
    x: Math.round(bounds.x),
    y: Math.round(bounds.y),
    width: Math.round(bounds.width),
    height: Math.round(bounds.height),
  }
}

export default class BpmnFactory {
  static $inject = ['moddle']

  constructor(private readonly moddle: Moddle) {}

  private prefix(element: ModdleElement): string {
    const entry = ID_PREFIXES.find(([type]) => is(element, type))
    if (entry) return entry[1]
    return `${element.$type.split(':').pop() || 'Element'}_`
  }

  /** Vergibt bzw. beansprucht die Kennung eines Elements. */
  _ensureId(element: ModdleElement): void {
    const ids = getIds(this.moddle)
    if (element.id) {
      ids.claim(element.id, element)
      return
    }
    if (isAny(element, NEEDS_ID)) element.id = ids.nextPrefixed(this.prefix(element), element)
  }

  create(type: string, attrs: Record<string, unknown> = {}): ModdleElement {
    const element = this.moddle.create(type, attrs)
    this._ensureId(element)
    return element
  }

  createDiLabel(): ModdleElement {
    return this.create('bpmndi:BPMNLabel', { bounds: this.createDiBounds() })
  }

  createDiShape(semantic: ModdleElement, attrs: Record<string, unknown> = {}): ModdleElement {
    return this.create('bpmndi:BPMNShape', {
      id: semantic.id ? `${semantic.id}_di` : undefined,
      bpmnElement: semantic,
      bounds: this.createDiBounds(),
      ...attrs,
    })
  }

  createDiBounds(bounds?: Bounds): ModdleElement {
    return this.create('dc:Bounds', bounds ? { ...roundBounds(bounds) } : {})
  }

  createDiWaypoints(waypoints: readonly Point[]): ModdleElement[] {
    return waypoints.map((point) => this.createDiWaypoint(point))
  }

  createDiWaypoint(point: Point): ModdleElement {
    return this.create('dc:Point', { x: point.x, y: point.y })
  }

  createDiEdge(semantic: ModdleElement, attrs: Record<string, unknown> = {}): ModdleElement {
    return this.create('bpmndi:BPMNEdge', {
      id: semantic.id ? `${semantic.id}_di` : undefined,
      bpmnElement: semantic,
      waypoint: [],
      ...attrs,
    })
  }

  createDiPlane(semantic: ModdleElement, attrs: Record<string, unknown> = {}): ModdleElement {
    return this.create('bpmndi:BPMNPlane', { bpmnElement: semantic, ...attrs })
  }

  createDiDiagram(plane: ModdleElement): ModdleElement {
    return this.create('bpmndi:BPMNDiagram', { plane })
  }
}
