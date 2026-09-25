/**
 * Ersetzungsziele für Ereignisse (Start, Zwischen, Ende, Rand).
 */

import * as Icons from '../../icons/Icons'
import type { ReplaceOption } from './types'

export type DefinitionKey =
  | 'message'
  | 'timer'
  | 'escalation'
  | 'conditional'
  | 'link'
  | 'error'
  | 'cancel'
  | 'compensation'
  | 'signal'
  | 'terminate'

const DEFINITIONS: Record<DefinitionKey, { type: string; label: string }> = {
  message: { type: 'bpmn:MessageEventDefinition', label: 'Message' },
  timer: { type: 'bpmn:TimerEventDefinition', label: 'Timer' },
  escalation: { type: 'bpmn:EscalationEventDefinition', label: 'Escalation' },
  conditional: { type: 'bpmn:ConditionalEventDefinition', label: 'Conditional' },
  link: { type: 'bpmn:LinkEventDefinition', label: 'Link' },
  error: { type: 'bpmn:ErrorEventDefinition', label: 'Error' },
  cancel: { type: 'bpmn:CancelEventDefinition', label: 'Cancel' },
  compensation: { type: 'bpmn:CompensateEventDefinition', label: 'Compensation' },
  signal: { type: 'bpmn:SignalEventDefinition', label: 'Signal' },
  terminate: { type: 'bpmn:TerminateEventDefinition', label: 'Terminate' },
}

function definitionAttrs(definition?: DefinitionKey): { eventDefinitionType?: string } {
  return definition ? { eventDefinitionType: DEFINITIONS[definition].type } : {}
}

export function startOption(definition?: DefinitionKey, nonInterrupting = false): ReplaceOption {
  const base = definition ? `${DEFINITIONS[definition].label} start event` : 'Start event'
  return {
    id: `replace-start-${definition || 'none'}${nonInterrupting ? '-non-interrupting' : ''}`,
    label: nonInterrupting ? `${base} (non-interrupting)` : base,
    icon: Icons.eventIcon('start', definition || 'none', nonInterrupting),
    target: { type: 'bpmn:StartEvent', ...definitionAttrs(definition), ...(nonInterrupting ? { isInterrupting: false } : {}) },
    group: 'start',
  }
}

export function intermediateOption(definition: DefinitionKey | undefined, isThrow: boolean): ReplaceOption {
  const direction = isThrow ? 'throw' : 'catch'
  return {
    id: `replace-intermediate-${direction}-${definition || 'none'}`,
    label: definition ? `${DEFINITIONS[definition].label} intermediate ${direction} event` : 'Intermediate throw event',
    icon: Icons.eventIcon(isThrow ? 'intermediate-throw' : 'intermediate-catch', definition || 'none'),
    target: { type: isThrow ? 'bpmn:IntermediateThrowEvent' : 'bpmn:IntermediateCatchEvent', ...definitionAttrs(definition) },
    group: 'intermediate',
  }
}

export function endOption(definition?: DefinitionKey): ReplaceOption {
  return {
    id: `replace-end-${definition || 'none'}`,
    label: definition ? `${DEFINITIONS[definition].label} end event` : 'End event',
    icon: Icons.eventIcon('end', definition || 'none'),
    target: { type: 'bpmn:EndEvent', ...definitionAttrs(definition) },
    group: 'end',
  }
}

export function boundaryOption(definition: DefinitionKey, nonInterrupting = false): ReplaceOption {
  const base = `${DEFINITIONS[definition].label} boundary event`
  return {
    id: `replace-boundary-${definition}${nonInterrupting ? '-non-interrupting' : ''}`,
    label: nonInterrupting ? `${base} (non-interrupting)` : base,
    icon: Icons.eventIcon('boundary', definition, nonInterrupting),
    target: { type: 'bpmn:BoundaryEvent', ...definitionAttrs(definition), ...(nonInterrupting ? { cancelActivity: false } : {}) },
    group: 'boundary',
  }
}

const NON_INTERRUPTING: DefinitionKey[] = ['message', 'timer', 'escalation', 'conditional', 'signal']

export function startEventOptions(inEventSubProcess: boolean): ReplaceOption[] {
  if (!inEventSubProcess) {
    const definitions: DefinitionKey[] = ['message', 'timer', 'conditional', 'signal']
    return [startOption(), ...definitions.map((definition) => startOption(definition)), intermediateOption(undefined, true), endOption()]
  }
  const definitions: DefinitionKey[] = ['message', 'timer', 'conditional', 'signal', 'error', 'escalation', 'compensation']
  return [
    startOption(),
    ...definitions.map((definition) => startOption(definition)),
    ...NON_INTERRUPTING.map((definition) => startOption(definition, true)),
  ]
}

export function boundaryEventOptions(hostIsTransaction: boolean): ReplaceOption[] {
  const definitions: DefinitionKey[] = ['message', 'timer', 'escalation', 'conditional', 'error', 'signal', 'compensation']
  if (hostIsTransaction) definitions.splice(5, 0, 'cancel')
  return [
    ...definitions.map((definition) => boundaryOption(definition)),
    ...NON_INTERRUPTING.map((definition) => boundaryOption(definition, true)),
  ]
}

/** Zwischenereignisse: [Definition, werfend?]. */
const INTERMEDIATE: [DefinitionKey | undefined, boolean][] = [
  [undefined, true],
  ['message', false],
  ['message', true],
  ['timer', false],
  ['escalation', true],
  ['conditional', false],
  ['link', false],
  ['link', true],
  ['compensation', true],
  ['signal', false],
  ['signal', true],
]

export function intermediateEventOptions(): ReplaceOption[] {
  return [startOption(), ...INTERMEDIATE.map(([definition, isThrow]) => intermediateOption(definition, isThrow)), endOption()]
}

export function endEventOptions(insideTransaction: boolean): ReplaceOption[] {
  const definitions: DefinitionKey[] = ['message', 'escalation', 'error', 'compensation', 'signal', 'terminate']
  if (insideTransaction) definitions.splice(3, 0, 'cancel')
  return [startOption(), intermediateOption(undefined, true), endOption(), ...definitions.map((definition) => endOption(definition))]
}
