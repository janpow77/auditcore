/**
 * Lesbare Typbezeichnungen (englische Vorlage, übersetzt über `translate`).
 */

import { getBusinessObject, type BpmnLike } from '../util/ModelUtil'
import type { Translate } from '../types'

const TYPE_LABELS: Record<string, string> = {
  'bpmn:Task': 'Task',
  'bpmn:UserTask': 'User task',
  'bpmn:ManualTask': 'Manual task',
  'bpmn:ServiceTask': 'Service task',
  'bpmn:ScriptTask': 'Script task',
  'bpmn:BusinessRuleTask': 'Business rule task',
  'bpmn:SendTask': 'Send task',
  'bpmn:ReceiveTask': 'Receive task',
  'bpmn:CallActivity': 'Call activity',
  'bpmn:SubProcess': 'Sub-process',
  'bpmn:Transaction': 'Transaction',
  'bpmn:AdHocSubProcess': 'Ad-hoc sub-process',
  'bpmn:StartEvent': 'Start event',
  'bpmn:IntermediateCatchEvent': 'Intermediate catch event',
  'bpmn:IntermediateThrowEvent': 'Intermediate throw event',
  'bpmn:EndEvent': 'End event',
  'bpmn:BoundaryEvent': 'Boundary event',
  'bpmn:ExclusiveGateway': 'Exclusive gateway',
  'bpmn:ParallelGateway': 'Parallel gateway',
  'bpmn:InclusiveGateway': 'Inclusive gateway',
  'bpmn:ComplexGateway': 'Complex gateway',
  'bpmn:EventBasedGateway': 'Event-based gateway',
  'bpmn:DataObjectReference': 'Data object reference',
  'bpmn:DataStoreReference': 'Data store reference',
  'bpmn:DataInput': 'Data input',
  'bpmn:DataOutput': 'Data output',
  'bpmn:Participant': 'Pool/participant',
  'bpmn:Lane': 'Lane',
  'bpmn:TextAnnotation': 'Text annotation',
  'bpmn:Group': 'Group',
  'bpmn:SequenceFlow': 'Sequence flow',
  'bpmn:MessageFlow': 'Message flow',
  'bpmn:Association': 'Association',
  'bpmn:DataInputAssociation': 'Data association',
  'bpmn:DataOutputAssociation': 'Data association',
  'bpmn:Process': 'Process',
  'bpmn:Collaboration': 'Collaboration',
}

/** Bezeichnung des BPMN-Typs eines Elements in der Oberflächensprache. */
export function getTypeLabel(element: BpmnLike, translate: Translate): string {
  const type = getBusinessObject(element).$type
  const label = TYPE_LABELS[type]
  return label ? translate(label) : type.replace(/^[a-z]+:/, '')
}

export { TYPE_LABELS }
