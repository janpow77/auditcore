/**
 * Ersetzungsziele für Gateways, Aktivitäten, Daten und Pools
 * (deklarative Tabellen).
 */

import * as Icons from '../../icons/Icons'
import type { ReplaceOption } from './types'

export const GATEWAY_OPTIONS: ReplaceOption[] = [
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

const TASK_KINDS: [string, string, Icons.TaskKind][] = [
  ['bpmn:Task', 'Task', 'task'],
  ['bpmn:UserTask', 'User task', 'user'],
  ['bpmn:ManualTask', 'Manual task', 'manual'],
  ['bpmn:ServiceTask', 'Service task', 'service'],
  ['bpmn:ScriptTask', 'Script task', 'script'],
  ['bpmn:BusinessRuleTask', 'Business rule task', 'business-rule'],
  ['bpmn:SendTask', 'Send task', 'send'],
  ['bpmn:ReceiveTask', 'Receive task', 'receive'],
]

export const TASK_OPTIONS: ReplaceOption[] = [
  ...TASK_KINDS.map(([type, label, icon]) => ({
    id: `replace-${type.replace('bpmn:', '').replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()}`,
    label,
    icon: Icons.taskIcon(icon),
    target: { type },
  })),
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

export const EXPANDED_SUBPROCESS_OPTIONS: ReplaceOption[] = [
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
  { id: 'replace-transaction', label: 'Transaction', icon: Icons.subProcessIcon('transaction'), target: { type: 'bpmn:Transaction', isExpanded: true } },
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

export const DATA_OPTIONS: ReplaceOption[] = [
  { id: 'replace-data-object', label: 'Data object reference', icon: Icons.dataObjectIcon(), target: { type: 'bpmn:DataObjectReference' } },
  { id: 'replace-data-store', label: 'Data store reference', icon: Icons.dataStoreIcon(), target: { type: 'bpmn:DataStoreReference' } },
]

export const PARTICIPANT_OPTIONS: ReplaceOption[] = [
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
