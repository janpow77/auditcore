/**
 * Ersetzungsziele je Elementart (Ersetzen-Menü, „Morphen“) und Varianten
 * des Sequenzflusses.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import * as Icons from '../icons/Icons'
import { getBusinessObject, getEventDefinition, is, isAny, isEventSubProcess, isExpanded, isInterrupting } from '../util/ModelUtil'
import { DATA_OPTIONS, EXPANDED_SUBPROCESS_OPTIONS, GATEWAY_OPTIONS, PARTICIPANT_OPTIONS, TASK_OPTIONS } from './options/elementOptions'
import { boundaryEventOptions, endEventOptions, intermediateEventOptions, startEventOptions } from './options/eventOptions'
import type { ReplaceOption, ReplaceTarget } from './options/types'

export type { ReplaceOption, ReplaceTarget }

function isInsideTransaction(element: Element): boolean {
  for (let current = element.host ? (element.host as Element) : element.parent; current; current = current.parent) {
    if (is(current, 'bpmn:Transaction')) return true
  }
  return false
}

type OptionSource = [(element: Element) => boolean, (element: Element) => ReplaceOption[]]

/** Ersetzungsziele je Elementart (erste passende gewinnt). */
const OPTION_SOURCES: OptionSource[] = [
  [(element) => is(element, 'bpmn:StartEvent'), (element) => startEventOptions(isEventSubProcess(element.parent))],
  [(element) => is(element, 'bpmn:BoundaryEvent'), (element) => boundaryEventOptions(!!element.host && is(element.host, 'bpmn:Transaction'))],
  [(element) => isAny(element, ['bpmn:IntermediateCatchEvent', 'bpmn:IntermediateThrowEvent']), () => intermediateEventOptions()],
  [(element) => is(element, 'bpmn:EndEvent'), (element) => endEventOptions(isInsideTransaction(element))],
  [(element) => is(element, 'bpmn:Gateway'), () => GATEWAY_OPTIONS],
  [
    (element) => is(element, 'bpmn:SubProcess') && isExpanded(element),
    (element) =>
      isEventSubProcess(element)
        ? EXPANDED_SUBPROCESS_OPTIONS.filter((option) => option.id !== 'replace-collapsed-subprocess')
        : EXPANDED_SUBPROCESS_OPTIONS,
  ],
  [(element) => is(element, 'bpmn:Activity'), (element) => (isEventSubProcess(element) ? [] : TASK_OPTIONS)],
  [(element) => isAny(element, ['bpmn:DataObjectReference', 'bpmn:DataStoreReference']), () => DATA_OPTIONS],
  [(element) => is(element, 'bpmn:Participant'), () => PARTICIPANT_OPTIONS],
]

/** Beschreibt den aktuellen Zustand des Elements in Zielform. */
export function describe(element: Element): ReplaceTarget {
  const bo = getBusinessObject(element)
  const definition = getEventDefinition(element)
  const target: ReplaceTarget = { type: bo.$type }
  if (definition) target.eventDefinitionType = definition.$type
  if (isAny(bo, ['bpmn:SubProcess', 'bpmn:Participant'])) target.isExpanded = isExpanded(element)
  if (is(bo, 'bpmn:SubProcess') && bo.triggeredByEvent) target.triggeredByEvent = true
  if (is(bo, 'bpmn:StartEvent') && !isInterrupting(element)) target.isInterrupting = false
  if (is(bo, 'bpmn:BoundaryEvent') && !isInterrupting(element)) target.cancelActivity = false
  if (is(bo, 'bpmn:EventBasedGateway')) {
    target.eventGatewayType = bo.eventGatewayType === 'Parallel' ? 'Parallel' : 'Exclusive'
    target.instantiate = !!bo.instantiate
  }
  return target
}

function sameGatewayKind(a: ReplaceTarget, b: ReplaceTarget): boolean {
  if (a.type !== 'bpmn:EventBasedGateway') return true
  return (a.eventGatewayType || 'Exclusive') === (b.eventGatewayType || 'Exclusive') && !!a.instantiate === !!b.instantiate
}

/** Vergleichsmerkmale zweier Ziele (jeweils normalisiert). */
const TARGET_KEYS: ((target: ReplaceTarget) => unknown)[] = [
  (target) => target.type,
  (target) => target.eventDefinitionType || null,
  (target) => !!target.triggeredByEvent,
  (target) => target.isInterrupting ?? true,
  (target) => target.cancelActivity ?? true,
]

export function isSameTarget(a: ReplaceTarget, b: ReplaceTarget): boolean {
  const sameExpansion = a.isExpanded === undefined || b.isExpanded === undefined || a.isExpanded === b.isExpanded
  return sameExpansion && TARGET_KEYS.every((key) => key(a) === key(b)) && sameGatewayKind(a, b)
}

/** Alle Ersetzungsziele für ein Element (ohne den aktuellen Zustand). */
export function getReplaceOptions(element: Element): ReplaceOption[] {
  const source = OPTION_SOURCES.find(([matches]) => matches(element))
  if (!source) return []
  const current = describe(element)
  return source[1](element).filter((option) => !isSameTarget(option.target, current))
}

export interface FlowOption {
  id: string
  label: string
  icon: string
  kind: 'sequence' | 'default' | 'conditional'
}

const DEFAULT_SOURCES = ['bpmn:ExclusiveGateway', 'bpmn:InclusiveGateway', 'bpmn:ComplexGateway', 'bpmn:Activity']
const NO_CONDITION_SOURCES = ['bpmn:ParallelGateway', 'bpmn:EventBasedGateway', 'bpmn:Event']

/** Varianten eines Sequenzflusses (Standard, Default, bedingt). */
export function getFlowOptions(connection: Element): FlowOption[] {
  const bo = getBusinessObject(connection)
  if (!is(bo, 'bpmn:SequenceFlow')) return []
  const source = bo.sourceRef
  const isDefault = !!source && source.default === bo
  const isConditional = !!bo.conditionExpression
  const options: FlowOption[] = []
  if (isDefault || isConditional) {
    options.push({ id: 'replace-sequence-flow', label: 'Sequence flow', icon: Icons.toolIcons.sequenceFlow, kind: 'sequence' })
  }
  if (!isDefault && isAny(source, DEFAULT_SOURCES)) {
    options.push({ id: 'replace-default-flow', label: 'Default flow', icon: Icons.toolIcons.defaultFlow, kind: 'default' })
  }
  if (!isConditional && !isAny(source, NO_CONDITION_SOURCES)) {
    options.push({ id: 'replace-conditional-flow', label: 'Conditional flow', icon: Icons.toolIcons.conditionalFlow, kind: 'conditional' })
  }
  return options
}
