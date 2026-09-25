/**
 * FlowStat task fields (duration, cost, resource, frequency, personnel) as
 * unqualified attributes on activities.
 *
 * Ported from `useBpmnEditor.ts` of the audit_designer: all known aliases
 * are read, only the canonical form is written (aliases are removed). Two
 * ways: on the XML text (as before) and through `modeling.updateProperties`
 * in a running editor.
 */

import type { DiagramElement, ModdleElement, Modeling } from '../diagram/services'
import { elementsByNs, parseXml, serializeXml } from './xmlDom'

export interface FlowstatTask {
  id: string
  name: string
  duration_minutes: number | null
  cost: number | null
  resource: string | null
  frequency: number | null
  personnel_count: number | null
}

export type FlowstatField = 'duration_minutes' | 'cost' | 'resource' | 'frequency' | 'personnel_count'

const BPMN_NAMESPACE = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
const ACTIVITY_NAMES = new Set(['task', 'userTask', 'serviceTask', 'manualTask', 'scriptTask', 'businessRuleTask', 'sendTask', 'receiveTask', 'subProcess'])

/** Canonical attribute and aliases (read, removed on write). */
export const FLOWSTAT_FIELDS: Record<FlowstatField, { canonical: string; aliases: string[]; numeric: boolean }> = {
  duration_minutes: { canonical: 'durationEstimated', aliases: ['duration', 'durationMinutes', 'bva:duration'], numeric: true },
  cost: { canonical: 'costEstimate', aliases: ['cost', 'bva:cost'], numeric: true },
  resource: { canonical: 'resourcesPersonnel', aliases: ['resource', 'bva:resource'], numeric: false },
  frequency: { canonical: 'frequency', aliases: ['frequencyPerYear'], numeric: true },
  personnel_count: { canonical: 'personnelCount', aliases: ['personnel_count', 'personnel'], numeric: true },
}

const FIELD_NAMES = Object.keys(FLOWSTAT_FIELDS) as FlowstatField[]

function toNumber(value: string | null): number | null {
  if (value === null || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function readField(read: (name: string) => string | null | undefined, field: FlowstatField): string | null {
  const { canonical, aliases } = FLOWSTAT_FIELDS[field]
  for (const name of [canonical, ...aliases]) {
    const value = read(name)
    if (value !== null && value !== undefined && value !== '') return value
  }
  return null
}

function taskFrom(id: string, name: string, read: (name: string) => string | null | undefined): FlowstatTask {
  const task = { id, name } as FlowstatTask
  const target = task as unknown as Record<string, unknown>
  for (const field of FIELD_NAMES) {
    const raw = readField(read, field)
    target[field] = FLOWSTAT_FIELDS[field].numeric ? toNumber(raw) : raw
  }
  return task
}

// ----- XML text (as `parseTasks`/`updateTaskProperties`) ------------------

const parse = parseXml

function activitiesIn(document: XMLDocument): Element[] {
  return elementsByNs(document, BPMN_NAMESPACE).filter((el) => ACTIVITY_NAMES.has(el.localName))
}

export function readTasksFromXml(xml: string): FlowstatTask[] {
  const document = parse(xml)
  if (!document) return []
  return activitiesIn(document).flatMap((el) => {
    const id = el.getAttribute('id')
    return id ? [taskFrom(id, el.getAttribute('name') ?? '', (n) => el.getAttribute(n))] : []
  })
}

function writeCanonical(el: Element, canonical: string, aliases: string[], value: unknown): void {
  for (const alias of aliases) el.removeAttribute(alias)
  if (value === null || value === undefined || value === '') el.removeAttribute(canonical)
  else el.setAttribute(canonical, String(value))
}

/** Writes one task back; returns the new XML, or the old one if nothing matches. */
export function writeTaskToXml(xml: string, task: FlowstatTask): string {
  const document = parse(xml)
  const el = document ? activitiesIn(document).find((candidate) => candidate.getAttribute('id') === task.id) : undefined
  if (!document || !el) return xml
  writeCanonical(el, 'name', [], task.name)
  for (const field of FIELD_NAMES) {
    writeCanonical(el, FLOWSTAT_FIELDS[field].canonical, FLOWSTAT_FIELDS[field].aliases, task[field])
  }
  writeCanonical(el, 'durationUnit', [], task.duration_minutes === null ? null : 'Minuten')
  return serializeXml(document)
}

// ----- Editor ----------------------------------------------------------------

export function readFlowstatValues(bo: ModdleElement): FlowstatTask {
  const attrs = bo.$attrs ?? {}
  return taskFrom(String(bo.id ?? ''), String(bo.get('name') ?? ''), (n) => attrs[n])
}

/** Writes FlowStat fields canonically through `modeling.updateProperties`. */
export function writeFlowstatValues(
  element: DiagramElement,
  values: Partial<Record<FlowstatField, number | string | null>>,
  modeling: Pick<Modeling, 'updateProperties'>,
): void {
  const props: Record<string, unknown> = {}
  const present = element.businessObject.$attrs ?? {}
  for (const field of Object.keys(values) as FlowstatField[]) {
    const { canonical, aliases } = FLOWSTAT_FIELDS[field]
    for (const alias of aliases.filter((name) => name in present)) props[alias] = undefined
    const value = values[field]
    props[canonical] = value === null || value === undefined || value === '' ? undefined : String(value)
    if (field === 'duration_minutes') props.durationUnit = props[canonical] === undefined ? undefined : 'Minuten'
  }
  if (Object.keys(props).length) modeling.updateProperties(element, props)
}
