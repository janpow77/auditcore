/**
 * Element matching and comparable features of two diagram versions
 * (same rules as `auditcore_bpmn` comparison): first by id, then by type and
 * normalised name (unique pairs only).
 */

import { displayName, isActivity, isEvent, isGateway, localType, type ModelElement, type ProcessModel } from '../model/processModel'
import type { Extensions } from '../schema/types'

const DATA_TYPES = new Set(['dataObject', 'dataObjectReference', 'dataStore', 'dataStoreReference', 'dataInput', 'dataOutput'])
const CONTAINER_TYPES = new Set(['process', 'collaboration', 'participant', 'lane'])

export function category(type: string): string {
  if (isActivity(type)) return 'aktivitaet'
  if (isEvent(type)) return 'ereignis'
  if (isGateway(type)) return 'gateway'
  if (DATA_TYPES.has(localType(type))) return 'daten'
  return CONTAINER_TYPES.has(localType(type)) ? 'container' : 'sonstige'
}

export function comparable(model: ProcessModel): ModelElement[] {
  return model.elements.filter((element) => category(element.type) !== 'sonstige')
}

export function normalName(name: string | undefined): string {
  return (name ?? '').trim().replace(/\s+/g, ' ').toLocaleLowerCase('de')
}

function groupByTypeAndName(elements: ModelElement[], skip: Set<string>): Map<string, string[]> {
  const groups = new Map<string, string[]>()
  for (const element of elements) {
    if (skip.has(element.id) || !normalName(element.name)) continue
    const key = `${element.type}|${normalName(element.name)}`
    groups.set(key, [...(groups.get(key) ?? []), element.id])
  }
  return groups
}

/** Element id old → element id new. */
export function matchElements(before: ProcessModel, after: ProcessModel): Map<string, string> {
  const oldElements = comparable(before)
  const newElements = new Map(comparable(after).map((element) => [element.id, element]))
  const mapping = new Map<string, string>()
  for (const element of oldElements) {
    const partner = newElements.get(element.id)
    if (partner && category(partner.type) === category(element.type)) mapping.set(element.id, partner.id)
  }
  const restOld = groupByTypeAndName(oldElements, new Set(mapping.keys()))
  const restNew = groupByTypeAndName([...newElements.values()], new Set(mapping.values()))
  for (const [key, ids] of restOld) {
    const partners = restNew.get(key) ?? []
    if (ids.length === 1 && partners.length === 1) mapping.set(ids[0], partners[0])
  }
  return mapping
}

/** Body of an element for display: role (display name), otherwise lane/pool. */
export function bodyLabel(element: ModelElement): string | null {
  const actor = element.actor
  if (actor?.role) return actor.role + (actor.displayName ? ` (${actor.displayName})` : '')
  return actor?.sourceName || null
}

export function neighbours(model: ProcessModel, element: ModelElement, direction: 'out' | 'in'): string[] {
  const flows = model.elements.filter((el) => el.type === 'bpmn:SequenceFlow' && (direction === 'out' ? el.sourceId : el.targetId) === element.id)
  return flows
    .map((flow) => model.byId.get((direction === 'out' ? flow.targetId : flow.sourceId) ?? ''))
    .filter((other): other is ModelElement => Boolean(other))
    .map((other) => normalName(other.name) || localType(other.type))
    .sort()
}

function compactExtensions(extensions: Extensions): Record<string, unknown> {
  return Object.fromEntries(Object.entries(extensions).filter(([, value]) => value !== undefined && !(Array.isArray(value) && !value.length)))
}

export interface Features {
  typ: string
  name: string
  stelle: string | null
  nachfolger: string[]
  vorgaenger: string[]
  dokumentation: string
  erweiterungen: Record<string, unknown>
}

export function features(model: ProcessModel, element: ModelElement): Features {
  return {
    typ: localType(element.type),
    name: element.name.trim(),
    stelle: bodyLabel(element),
    nachfolger: neighbours(model, element, 'out'),
    vorgaenger: neighbours(model, element, 'in'),
    dokumentation: element.documentation,
    erweiterungen: compactExtensions(element.extensions),
  }
}

export { displayName }
