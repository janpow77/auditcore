/**
 * Abgleich der Kanten-Semantik: Quelle/Ziel, `incoming`/`outgoing`,
 * Container (Prozess, Kollaboration, Aktivität bei Datenassoziationen).
 */

import { addToList, getBusinessObject, getList, getRootOf, is, removeFromList } from '../../util/ModelUtil'
import type { BpmnElement, ModdleElement } from '../../types'
import type BpmnFactory from '../BpmnFactory'
import type SemanticSync from './SemanticSync'

interface Ends {
  attached: boolean
  source: ModdleElement | undefined
  target: ModdleElement | undefined
}

export default class ConnectionSync {
  constructor(
    private readonly bpmnFactory: BpmnFactory,
    private readonly semantic: SemanticSync,
  ) {}

  update(connection: BpmnElement): void {
    const bo = getBusinessObject(connection)
    const ends: Ends = {
      attached: !!connection.parent,
      source: getBusinessObject(connection.source as BpmnElement | undefined),
      target: getBusinessObject(connection.target as BpmnElement | undefined),
    }
    if (is(bo, 'bpmn:DataInputAssociation') || is(bo, 'bpmn:DataOutputAssociation')) {
      this.updateDataAssociation(bo, ends)
      return
    }
    if (is(bo, 'bpmn:SequenceFlow')) this.updateSequenceFlowRefs(bo, ends)
    else if (ends.attached) {
      if (ends.source) bo.sourceRef = ends.source
      if (ends.target) bo.targetRef = ends.target
    }
    this.updateContainer(connection, bo, ends.attached)
  }

  private updateSequenceFlowRefs(bo: ModdleElement, { attached, source, target }: Ends): void {
    if (bo.sourceRef && (bo.sourceRef !== source || !attached)) removeFromList(bo.sourceRef.get<ModdleElement[]>('outgoing'), bo)
    if (bo.targetRef && (bo.targetRef !== target || !attached)) removeFromList(bo.targetRef.get<ModdleElement[]>('incoming'), bo)
    if (!attached) return
    if (source) {
      bo.sourceRef = source
      addToList(source.get<ModdleElement[]>('outgoing'), bo)
    }
    if (target) {
      bo.targetRef = target
      addToList(target.get<ModdleElement[]>('incoming'), bo)
    }
  }

  private updateContainer(connection: BpmnElement, bo: ModdleElement, attached: boolean): void {
    if (is(bo, 'bpmn:MessageFlow')) {
      const collaboration = attached ? getBusinessObject(getRootOf(connection)) : undefined
      if (bo.$parent && bo.$parent !== collaboration) removeFromList(getList(bo.$parent, 'messageFlows'), bo)
      if (collaboration && is(collaboration, 'bpmn:Collaboration')) {
        addToList(collaboration.get<ModdleElement[]>('messageFlows'), bo)
        bo.$parent = collaboration
      } else if (!attached) {
        bo.$parent = null
      }
      return
    }
    const property = is(bo, 'bpmn:SequenceFlow') ? 'flowElements' : is(bo, 'bpmn:Association') ? 'artifacts' : null
    if (!property) return
    const container = attached ? this.semantic.getContainer(connection.parent as BpmnElement, bo) : undefined
    this.semantic.moveTo(bo, container, property)
  }

  private updateDataAssociation(bo: ModdleElement, { attached, source, target }: Ends): void {
    const isInput = is(bo, 'bpmn:DataInputAssociation')
    const property = isInput ? 'dataInputAssociations' : 'dataOutputAssociations'
    const owner = attached ? (isInput ? target : source) : undefined
    const oldOwner = bo.$parent || undefined
    if (oldOwner && oldOwner !== owner) removeFromList(getList(oldOwner, property), bo)
    if (!owner) {
      bo.$parent = null
      return
    }
    addToList(owner.get<ModdleElement[]>(property), bo)
    bo.$parent = owner
    if (isInput) this.updateInputRefs(bo, owner, source)
    else bo.targetRef = target
  }

  private updateInputRefs(bo: ModdleElement, owner: ModdleElement, source: ModdleElement | undefined): void {
    const refs = bo.get<ModdleElement[]>('sourceRef')
    refs.length = 0
    if (source) refs.push(source)
    if (bo.targetRef || !is(owner, 'bpmn:Activity')) return
    // Ziel einer Dateneingangsassoziation ist ein Eingabeelement der Aktivität.
    const property = this.bpmnFactory.create('bpmn:Property')
    property.$parent = owner
    owner.get<ModdleElement[]>('properties').push(property)
    bo.targetRef = property
  }
}
