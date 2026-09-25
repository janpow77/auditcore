/**
 * Verbindungsregeln nach BPMN 2.0 (OMG BPMN 2.0.2, Kap. 7.5 und 10):
 * Sequenzfluss, Nachrichtenfluss, Assoziation, Datenassoziation.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import { getBusinessObject, hasEventDefinition, is, isAny, isEventSubProcess, isLabel, isRoot } from '../util/ModelUtil'

export type ConnectResult = false | null | { type: string; associationDirection?: string }

const DATA_TYPES = ['bpmn:DataObjectReference', 'bpmn:DataStoreReference', 'bpmn:DataInput', 'bpmn:DataOutput']
const EVENT_GATEWAY_TARGET_DEFINITIONS = [
  'bpmn:MessageEventDefinition',
  'bpmn:TimerEventDefinition',
  'bpmn:ConditionalEventDefinition',
  'bpmn:SignalEventDefinition',
]

function isConnection(element: Element): boolean {
  return !!element.waypoints
}

export function isParentOf(possibleParent: Element, element: Element): boolean {
  for (let current = element.parent; current; current = current.parent) {
    if (current === possibleParent) return true
  }
  return false
}

/** Sichtbarer Gültigkeitsbereich eines Flussknotens (Pool, Teilprozess, Wurzel). */
export function getScope(element: Element): Element | undefined {
  let current = element.host ? (element.host as Element).parent : element.parent
  while (current && is(current, 'bpmn:Lane')) current = current.parent
  return current
}

/** Pool, in dem das Element liegt (oder der Pool selbst). */
export function getOwnParticipant(element: Element): Element | null {
  for (let current: Element | undefined = element; current; current = current.parent) {
    if (is(current, 'bpmn:Participant')) return current
  }
  return null
}

function isForCompensation(element: Element): boolean {
  return !!getBusinessObject(element).isForCompensation
}

export function isCompensationBoundary(element: Element): boolean {
  return is(element, 'bpmn:BoundaryEvent') && hasEventDefinition(element, 'bpmn:CompensateEventDefinition')
}

function isLink(element: Element, type: string): boolean {
  return is(element, type) && hasEventDefinition(element, 'bpmn:LinkEventDefinition')
}

function isSequenceFlowSource(element: Element): boolean {
  if (!is(element, 'bpmn:FlowNode') || is(element, 'bpmn:EndEvent') || isEventSubProcess(element)) return false
  if (isForCompensation(element) || isCompensationBoundary(element)) return false
  return !isLink(element, 'bpmn:IntermediateThrowEvent')
}

function isSequenceFlowTarget(element: Element): boolean {
  if (!is(element, 'bpmn:FlowNode') || isAny(element, ['bpmn:StartEvent', 'bpmn:BoundaryEvent'])) return false
  if (isEventSubProcess(element) || isForCompensation(element)) return false
  return !isLink(element, 'bpmn:IntermediateCatchEvent')
}

function carriesMessage(element: Element): boolean {
  const definitions = getBusinessObject(element).eventDefinitions || []
  return definitions.length === 0 || hasEventDefinition(element, 'bpmn:MessageEventDefinition')
}

function isMessageFlowSource(element: Element): boolean {
  if (is(element, 'bpmn:Participant')) return true
  if (is(element, 'bpmn:Activity')) return !isEventSubProcess(element) && !is(element, 'bpmn:ReceiveTask')
  return isAny(element, ['bpmn:IntermediateThrowEvent', 'bpmn:EndEvent']) && carriesMessage(element)
}

function isMessageFlowTarget(element: Element): boolean {
  if (is(element, 'bpmn:Participant')) return true
  if (is(element, 'bpmn:Activity')) return !isEventSubProcess(element) && !is(element, 'bpmn:SendTask')
  if (!isAny(element, ['bpmn:StartEvent', 'bpmn:IntermediateCatchEvent', 'bpmn:BoundaryEvent'])) return false
  const scope = getScope(element)
  if (is(element, 'bpmn:StartEvent') && scope && is(scope, 'bpmn:SubProcess')) return false
  return carriesMessage(element)
}

export function canConnectSequenceFlow(source: Element, target: Element): boolean {
  if (source === target || !isSequenceFlowSource(source) || !isSequenceFlowTarget(target)) return false
  if (getScope(source) !== getScope(target)) return false
  if (!is(source, 'bpmn:EventBasedGateway')) return true
  return (
    is(target, 'bpmn:ReceiveTask') ||
    (is(target, 'bpmn:IntermediateCatchEvent') && EVENT_GATEWAY_TARGET_DEFINITIONS.some((type) => hasEventDefinition(target, type)))
  )
}

export function canConnectMessageFlow(source: Element, target: Element): boolean {
  if (source === target || isLabel(source) || isLabel(target)) return false
  const sourceParticipant = getOwnParticipant(source)
  const targetParticipant = getOwnParticipant(target)
  if (!sourceParticipant || !targetParticipant || sourceParticipant === targetParticipant) return false
  return isMessageFlowSource(source) && isMessageFlowTarget(target)
}

export function canConnectAssociation(source: Element, target: Element): boolean {
  if (source === target || is(source, 'bpmn:Group') || is(target, 'bpmn:Group')) return false
  const sourceIsNote = is(source, 'bpmn:TextAnnotation')
  const targetIsNote = is(target, 'bpmn:TextAnnotation')
  if (sourceIsNote || targetIsNote) return !(sourceIsNote && targetIsNote) && !isParentOf(source, target) && !isParentOf(target, source)
  return isCompensationBoundary(source) && isForCompensation(target)
}

export function canConnectDataAssociation(source: Element, target: Element): ConnectResult {
  if (isAny(source, DATA_TYPES) && isAny(target, ['bpmn:Activity', 'bpmn:ThrowEvent'])) {
    return is(source, 'bpmn:DataOutput') ? false : { type: 'bpmn:DataInputAssociation' }
  }
  if (isAny(target, DATA_TYPES) && isAny(source, ['bpmn:Activity', 'bpmn:CatchEvent'])) {
    return is(target, 'bpmn:DataInput') ? false : { type: 'bpmn:DataOutputAssociation' }
  }
  return false
}

/** Prüfung für eine bestehende Kante eines bestimmten Typs. */
function canReconnect(source: Element, target: Element, connection: Element): ConnectResult {
  if (isAny(connection, ['bpmn:DataInputAssociation', 'bpmn:DataOutputAssociation'])) return canConnectDataAssociation(source, target)
  if (is(connection, 'bpmn:Association')) return canConnectAssociation(source, target) ? { type: 'bpmn:Association' } : false
  if (is(connection, 'bpmn:MessageFlow')) return canConnectMessageFlow(source, target) ? { type: 'bpmn:MessageFlow' } : false
  if (is(connection, 'bpmn:SequenceFlow')) return canConnectSequenceFlow(source, target) ? { type: 'bpmn:SequenceFlow' } : false
  return false
}

/** Ermittelt die zulässige Verbindungsart zwischen zwei Elementen. */
export function canConnect(source: Element | undefined, target: Element | undefined, connection?: Element | null): ConnectResult {
  if (!source || !target || isLabel(source) || isLabel(target)) return null
  if ([source, target].some((element) => isRoot(element) || isConnection(element))) return false
  return connection ? canReconnect(source, target, connection) : detectConnection(source, target)
}

/** Verbindungsart für eine neue Kante (Vorrang: Nachricht, Sequenz, Daten, Assoziation). */
function detectConnection(source: Element, target: Element): ConnectResult {
  if (canConnectMessageFlow(source, target)) return { type: 'bpmn:MessageFlow' }
  if (canConnectSequenceFlow(source, target)) return { type: 'bpmn:SequenceFlow' }
  const data = canConnectDataAssociation(source, target)
  if (data) return data
  if (isCompensationBoundary(source) && isForCompensation(target)) return { type: 'bpmn:Association', associationDirection: 'One' }
  if (canConnectAssociation(source, target)) return { type: 'bpmn:Association', associationDirection: 'None' }
  return false
}

/** Darf von hier aus eine Verbindung begonnen werden? */
export function canStartConnection(element: Element | undefined): boolean {
  if (!element || isLabel(element) || isRoot(element) || isConnection(element)) return false
  return isAny(element, ['bpmn:FlowNode', 'bpmn:InteractionNode', 'bpmn:TextAnnotation', ...DATA_TYPES, 'bpmn:Participant'])
}
