/**
 * Ersetzungsziele je Elementart (Ersetzen-Menü, „Morphen“).
 */

import * as Icons from '../icons/Icons'
import {
  getBusinessObject,
  getEventDefinition,
  is,
  isEventSubProcess,
  isExpanded,
  isInterrupting,
  type DiagramElement,
} from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface ReplaceTarget {
  type: string
  eventDefinitionType?: string
  isExpanded?: boolean
  triggeredByEvent?: boolean
  isInterrupting?: boolean
  cancelActivity?: boolean
  eventGatewayType?: 'Exclusive' | 'Parallel'
  instantiate?: boolean
}

export interface ReplaceOption {
  id: string
  label: string
  icon: string
  target: ReplaceTarget
  group?: string
}

const DEF = {
  message: 'bpmn:MessageEventDefinition',
  timer: 'bpmn:TimerEventDefinition',
  escalation: 'bpmn:EscalationEventDefinition',
  conditional: 'bpmn:ConditionalEventDefinition',
  link: 'bpmn:LinkEventDefinition',
  error: 'bpmn:ErrorEventDefinition',
  cancel: 'bpmn:CancelEventDefinition',
  compensation: 'bpmn:CompensateEventDefinition',
  signal: 'bpmn:SignalEventDefinition',
  terminate: 'bpmn:TerminateEventDefinition',
} as const

type DefKey = keyof typeof DEF

const DEF_LABEL: Record<DefKey, string> = {
  message: 'Message',
  timer: 'Timer',
  escalation: 'Escalation',
  conditional: 'Conditional',
  link: 'Link',
  error: 'Error',
  cancel: 'Cancel',
  compensation: 'Compensation',
  signal: 'Signal',
  terminate: 'Terminate',
}

function startOption(def?: DefKey, nonInterrupting = false): ReplaceOption {
  const label = def ? `${DEF_LABEL[def]} start event` : 'Start event'
  return {
    id: `replace-start-${def || 'none'}${nonInterrupting ? '-non-interrupting' : ''}`,
    label: nonInterrupting ? `${label} (non-interrupting)` : label,
    icon: Icons.eventIcon('start', (def || 'none') as any, nonInterrupting),
    target: {
      type: 'bpmn:StartEvent',
      ...(def ? { eventDefinitionType: DEF[def] } : {}),
      ...(nonInterrupting ? { isInterrupting: false } : {}),
    },
    group: 'start',
  }
}

function intermediateOption(def: DefKey | undefined, isThrow: boolean): ReplaceOption {
  const type = isThrow ? 'bpmn:IntermediateThrowEvent' : 'bpmn:IntermediateCatchEvent'
  const base = def ? `${DEF_LABEL[def]} intermediate ${isThrow ? 'throw' : 'catch'} event` : 'Intermediate throw event'
  return {
    id: `replace-intermediate-${isThrow ? 'throw' : 'catch'}-${def || 'none'}`,
    label: base,
    icon: Icons.eventIcon(isThrow ? 'intermediate-throw' : 'intermediate-catch', (def || 'none') as any),
    target: { type, ...(def ? { eventDefinitionType: DEF[def] } : {}) },
    group: 'intermediate',
  }
}

function endOption(def?: DefKey): ReplaceOption {
  return {
    id: `replace-end-${def || 'none'}`,
    label: def ? `${DEF_LABEL[def]} end event` : 'End event',
    icon: Icons.eventIcon('end', (def || 'none') as any),
    target: { type: 'bpmn:EndEvent', ...(def ? { eventDefinitionType: DEF[def] } : {}) },
    group: 'end',
  }
}

function boundaryOption(def: DefKey, nonInterrupting = false): ReplaceOption {
  const label = `${DEF_LABEL[def]} boundary event`
  return {
    id: `replace-boundary-${def}${nonInterrupting ? '-non-interrupting' : ''}`,
    label: nonInterrupting ? `${label} (non-interrupting)` : label,
    icon: Icons.eventIcon('boundary', def as any, nonInterrupting),
    target: {
      type: 'bpmn:BoundaryEvent',
      eventDefinitionType: DEF[def],
      ...(nonInterrupting ? { cancelActivity: false } : {}),
    },
    group: 'boundary',
  }
}

const GATEWAY_OPTIONS: ReplaceOption[] = [
  { id: 'replace-exclusive-gateway', label: 'Exclusive gateway', icon: Icons.gatewayIcon('exclusive'), target: { type: 'bpmn:ExclusiveGateway' } },
  { id: 'replace-parallel-gateway', label: 'Parallel gateway', icon: Icons.gatewayIcon('parallel'), target: { type: 'bpmn:ParallelGateway' } },
  { id: 'replace-inclusive-gateway', label: 'Inclusive gateway', icon: Icons.gatewayIcon('inclusive'), target: { type: 'bpmn:InclusiveGateway' } },
  { id: 'replace-complex-gateway', label: 'Complex gateway', icon: Icons.gatewayIcon('complex'), target: { type: 'bpmn:ComplexGateway' } },
  {
    id: 'replace-event-based-gateway',
    label: 'Event-based gateway',
    icon: Icons.gatewayIcon('event-based'),
    target: { type: 'bpmn:EventBasedGateway', eventGatewayType: 'Exclusive', instantiate: false },
  },
  {
    id: 'replace-event-based-gateway-instantiate',
    label: 'Event-based gateway (instantiating)',
    icon: Icons.gatewayIcon('event-based-instantiate'),
    target: { type: 'bpmn:EventBasedGateway', eventGatewayType: 'Exclusive', instantiate: true },
  },
  {
    id: 'replace-parallel-event-based-gateway',
    label: 'Parallel event-based gateway',
    icon: Icons.gatewayIcon('event-based-parallel'),
    target: { type: 'bpmn:EventBasedGateway', eventGatewayType: 'Parallel', instantiate: true },
  },
]

const TASK_OPTIONS: ReplaceOption[] = [
  { id: 'replace-task', label: 'Task', icon: Icons.taskIcon('task'), target: { type: 'bpmn:Task' } },
  { id: 'replace-user-task', label: 'User task', icon: Icons.taskIcon('user'), target: { type: 'bpmn:UserTask' } },
  { id: 'replace-manual-task', label: 'Manual task', icon: Icons.taskIcon('manual'), target: { type: 'bpmn:ManualTask' } },
  { id: 'replace-service-task', label: 'Service task', icon: Icons.taskIcon('service'), target: { type: 'bpmn:ServiceTask' } },
  { id: 'replace-script-task', label: 'Script task', icon: Icons.taskIcon('script'), target: { type: 'bpmn:ScriptTask' } },
  { id: 'replace-business-rule-task', label: 'Business rule task', icon: Icons.taskIcon('business-rule'), target: { type: 'bpmn:BusinessRuleTask' } },
  { id: 'replace-send-task', label: 'Send task', icon: Icons.taskIcon('send'), target: { type: 'bpmn:SendTask' } },
  { id: 'replace-receive-task', label: 'Receive task', icon: Icons.taskIcon('receive'), target: { type: 'bpmn:ReceiveTask' } },
  { id: 'replace-call-activity', label: 'Call activity', icon: Icons.callActivityIcon(), target: { type: 'bpmn:CallActivity' } },
  {
    id: 'replace-collapsed-subprocess',
    label: 'Sub-process (collapsed)',
    icon: Icons.subProcessIcon('collapsed'),
    target: { type: 'bpmn:SubProcess', isExpanded: false },
  },
  {
    id: 'replace-expanded-subprocess',
    label: 'Sub-process (expanded)',
    icon: Icons.subProcessIcon('expanded'),
    target: { type: 'bpmn:SubProcess', isExpanded: true },
  },
  {
    id: 'replace-collapsed-transaction',
    label: 'Transaction (collapsed)',
    icon: Icons.subProcessIcon('transaction'),
    target: { type: 'bpmn:Transaction', isExpanded: false },
  },
  {
    id: 'replace-collapsed-adhoc',
    label: 'Ad-hoc sub-process (collapsed)',
    icon: Icons.subProcessIcon('adhoc'),
    target: { type: 'bpmn:AdHocSubProcess', isExpanded: false },
  },
]

const EXPANDED_SUBPROCESS_OPTIONS: ReplaceOption[] = [
  {
    id: 'replace-expanded-subprocess',
    label: 'Sub-process (expanded)',
    icon: Icons.subProcessIcon('expanded'),
    target: { type: 'bpmn:SubProcess', isExpanded: true },
  },
  {
    id: 'replace-collapsed-subprocess',
    label: 'Sub-process (collapsed)',
    icon: Icons.subProcessIcon('collapsed'),
    target: { type: 'bpmn:SubProcess', isExpanded: false },
  },
  {
    id: 'replace-transaction',
    label: 'Transaction',
    icon: Icons.subProcessIcon('transaction'),
    target: { type: 'bpmn:Transaction', isExpanded: true },
  },
  {
    id: 'replace-event-subprocess',
    label: 'Event sub-process',
    icon: Icons.subProcessIcon('event'),
    target: { type: 'bpmn:SubProcess', isExpanded: true, triggeredByEvent: true },
  },
  {
    id: 'replace-adhoc-subprocess',
    label: 'Ad-hoc sub-process',
    icon: Icons.subProcessIcon('adhoc'),
    target: { type: 'bpmn:AdHocSubProcess', isExpanded: true },
  },
]

const DATA_OPTIONS: ReplaceOption[] = [
  { id: 'replace-data-object', label: 'Data object reference', icon: Icons.dataObjectIcon(), target: { type: 'bpmn:DataObjectReference' } },
  { id: 'replace-data-store', label: 'Data store reference', icon: Icons.dataStoreIcon(), target: { type: 'bpmn:DataStoreReference' } },
]

const PARTICIPANT_OPTIONS: ReplaceOption[] = [
  {
    id: 'replace-expanded-pool',
    label: 'Expanded pool/participant',
    icon: Icons.participantIcon('expanded'),
    target: { type: 'bpmn:Participant', isExpanded: true },
  },
  {
    id: 'replace-empty-pool',
    label: 'Empty pool/participant',
    icon: Icons.participantIcon('collapsed'),
    target: { type: 'bpmn:Participant', isExpanded: false },
  },
]

function isInsideTransaction(element: DiagramElement): boolean {
  let current = element.host ? element.host : element.parent
  while (current) {
    if (is(current, 'bpmn:Transaction')) return true
    current = current.parent
  }
  return false
}

/** Beschreibt den aktuellen Zustand des Elements in Zielform. */
export function describe(element: DiagramElement): ReplaceTarget {
  const bo = getBusinessObject(element)
  const definition = getEventDefinition(element)
  const target: ReplaceTarget = { type: bo.$type }
  if (definition) target.eventDefinitionType = definition.$type
  if (is(bo, 'bpmn:SubProcess')) {
    target.isExpanded = isExpanded(element)
    if (bo.triggeredByEvent) target.triggeredByEvent = true
  }
  if (is(bo, 'bpmn:Participant')) target.isExpanded = isExpanded(element)
  if (is(bo, 'bpmn:StartEvent') && !isInterrupting(element)) target.isInterrupting = false
  if (is(bo, 'bpmn:BoundaryEvent') && !isInterrupting(element)) target.cancelActivity = false
  if (is(bo, 'bpmn:EventBasedGateway')) {
    target.eventGatewayType = bo.eventGatewayType === 'Parallel' ? 'Parallel' : 'Exclusive'
    target.instantiate = !!bo.instantiate
  }
  return target
}

export function isSameTarget(a: ReplaceTarget, b: ReplaceTarget): boolean {
  return (
    a.type === b.type &&
    (a.eventDefinitionType || null) === (b.eventDefinitionType || null) &&
    (a.isExpanded === undefined || b.isExpanded === undefined || a.isExpanded === b.isExpanded) &&
    !!a.triggeredByEvent === !!b.triggeredByEvent &&
    (a.isInterrupting ?? true) === (b.isInterrupting ?? true) &&
    (a.cancelActivity ?? true) === (b.cancelActivity ?? true) &&
    (a.type !== 'bpmn:EventBasedGateway' ||
      ((a.eventGatewayType || 'Exclusive') === (b.eventGatewayType || 'Exclusive') && !!a.instantiate === !!b.instantiate))
  )
}

/** Alle Ersetzungsziele für ein Element (ohne den aktuellen Zustand). */
export function getReplaceOptions(element: DiagramElement): ReplaceOption[] {
  const bo = getBusinessObject(element)
  let options: ReplaceOption[] = []

  if (is(bo, 'bpmn:StartEvent')) {
    if (isEventSubProcess(element.parent)) {
      const defs: DefKey[] = ['message', 'timer', 'conditional', 'signal', 'error', 'escalation', 'compensation']
      options = [
        startOption(),
        ...defs.map((def) => startOption(def)),
        ...(['message', 'timer', 'conditional', 'signal', 'escalation'] as DefKey[]).map((def) => startOption(def, true)),
      ]
    } else {
      options = [
        startOption(),
        ...(['message', 'timer', 'conditional', 'signal'] as DefKey[]).map((def) => startOption(def)),
        intermediateOption(undefined, true),
        endOption(),
      ]
    }
  } else if (is(bo, 'bpmn:BoundaryEvent')) {
    const defs: DefKey[] = ['message', 'timer', 'escalation', 'conditional', 'error', 'signal', 'compensation']
    if (element.host && is(element.host, 'bpmn:Transaction')) defs.splice(5, 0, 'cancel')
    options = [
      ...defs.map((def) => boundaryOption(def)),
      ...(['message', 'timer', 'escalation', 'conditional', 'signal'] as DefKey[]).map((def) => boundaryOption(def, true)),
    ]
  } else if (is(bo, 'bpmn:IntermediateCatchEvent') || is(bo, 'bpmn:IntermediateThrowEvent')) {
    options = [
      startOption(),
      intermediateOption(undefined, true),
      intermediateOption('message', false),
      intermediateOption('message', true),
      intermediateOption('timer', false),
      intermediateOption('escalation', true),
      intermediateOption('conditional', false),
      intermediateOption('link', false),
      intermediateOption('link', true),
      intermediateOption('compensation', true),
      intermediateOption('signal', false),
      intermediateOption('signal', true),
      endOption(),
    ]
  } else if (is(bo, 'bpmn:EndEvent')) {
    const defs: DefKey[] = ['message', 'escalation', 'error', 'compensation', 'signal', 'terminate']
    if (isInsideTransaction(element)) defs.splice(3, 0, 'cancel')
    options = [startOption(), intermediateOption(undefined, true), endOption(), ...defs.map((def) => endOption(def))]
  } else if (is(bo, 'bpmn:Gateway')) {
    options = GATEWAY_OPTIONS
  } else if (is(bo, 'bpmn:SubProcess') && isExpanded(element)) {
    options = EXPANDED_SUBPROCESS_OPTIONS
    if (isEventSubProcess(element)) {
      options = options.filter((option) => option.id !== 'replace-collapsed-subprocess')
    }
  } else if (is(bo, 'bpmn:Activity')) {
    options = TASK_OPTIONS
    if (isEventSubProcess(element)) options = []
  } else if (is(bo, 'bpmn:DataObjectReference') || is(bo, 'bpmn:DataStoreReference')) {
    options = DATA_OPTIONS
  } else if (is(bo, 'bpmn:Participant')) {
    options = PARTICIPANT_OPTIONS
  }

  const current = describe(element)
  return options.filter((option) => !isSameTarget(option.target, current))
}

export interface FlowOption {
  id: string
  label: string
  icon: string
  kind: 'sequence' | 'default' | 'conditional'
}

/** Varianten eines Sequenzflusses (Standard, Default, bedingt). */
export function getFlowOptions(connection: DiagramElement): FlowOption[] {
  const bo = getBusinessObject(connection)
  if (!is(bo, 'bpmn:SequenceFlow')) return []
  const source = bo.sourceRef
  const isDefault = !!source && source.default === bo
  const isConditional = !!bo.conditionExpression
  const options: FlowOption[] = []
  if (isDefault || isConditional) {
    options.push({ id: 'replace-sequence-flow', label: 'Sequence flow', icon: Icons.toolIcons.sequenceFlow, kind: 'sequence' })
  }
  const canHaveDefault = is(source, 'bpmn:ExclusiveGateway') || is(source, 'bpmn:InclusiveGateway') || is(source, 'bpmn:ComplexGateway') || is(source, 'bpmn:Activity')
  if (!isDefault && canHaveDefault) {
    options.push({ id: 'replace-default-flow', label: 'Default flow', icon: Icons.toolIcons.defaultFlow, kind: 'default' })
  }
  const canHaveCondition = !is(source, 'bpmn:ParallelGateway') && !is(source, 'bpmn:EventBasedGateway') && !is(source, 'bpmn:Event')
  if (!isConditional && canHaveCondition) {
    options.push({ id: 'replace-conditional-flow', label: 'Conditional flow', icon: Icons.toolIcons.conditionalFlow, kind: 'conditional' })
  }
  return options
}
