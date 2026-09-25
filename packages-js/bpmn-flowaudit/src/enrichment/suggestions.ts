/**
 * Enriching existing diagrams: suggestions from labels, documentation and
 * colours (same logic as `auditcore_bpmn` enrichment).
 *
 * Many existing diagrams carry their domain data as free text in
 * `bpmn:documentation` and in labels („Stelle: …“), findings as colour.
 * `collectSuggestions` derives **suggestions** – legal bases (long form),
 * manual references, audit references from assessment criteria, finding
 * references („T15 F1“), checklist items, registers, actor roles and
 * markers from colours. `applySuggestions` takes over only the accepted
 * suggestions and adds to existing data without overwriting it.
 */

import { citation } from '../model/legalBasis'
import type { ModelAccess } from '../model/access'
import { isActivity, type ModelElement, type ProcessModel } from '../model/processModel'
import { roleFromText, type ProfileData, type RoleAlias } from '../profile/profile'
import type { Actor, AuditReference, CrossReference, Extensions, LegalBasis, Marker, Source } from '../schema/types'
import { findCitations } from './citations'
import { ROLE_PREFIX, auditReferencesIn, crossReferencesIn, removeRolePrefix, sourcesIn, type TextHit } from './textPatterns'

export type SuggestionKind = 'legalBasis' | 'auditReference' | 'crossReference' | 'source' | 'actor' | 'rolePrefix' | 'marker'
export type SuggestionOrigin = 'documentation' | 'name' | 'color' | 'annotation'

export interface Suggestion {
  id: string
  elementId: string
  kind: SuggestionKind
  value: LegalBasis | AuditReference | CrossReference | Source | Actor | Marker | string
  /** Text passage the suggestion was taken from. */
  excerpt: string
  origin: SuggestionOrigin
}

/** Colour pair (fill, stroke) → marker suggestion. */
export const COLOR_MARKERS: Record<string, string> = {
  '#fce8e6|#b3261e': 'feststellung',
  '#ffcdd2|#b71c1c': 'feststellung',
  '#ffe0e0|#cc0000': 'soll_ohne_regelung',
  '#c8e6c9|#1b5e20': 'ohne_befund',
  '#bbdefb|#0d47a1': 'offener_nachweis',
}

/** Annotation prefixes that mark a gap in the rules („Lücke:“). */
const GAP_PREFIXES = /^(?:Lücke|Nicht geregelt|Regelungslücke|Nicht vorgesehen)\s*:/iu

export interface SuggestionOptions {
  profile?: ProfileData | null
  /** Additional aliases supplied by the application (e.g. names of bodies). */
  roleAliases?: RoleAlias[]
}

type Draft = Omit<Suggestion, 'id'>

function fromHits<T extends Suggestion['value']>(elementId: string, kind: SuggestionKind, origin: SuggestionOrigin, list: TextHit<T>[]): Draft[] {
  return list.map((hit) => ({ elementId, kind, value: hit.value, excerpt: hit.excerpt, origin }))
}

export function textSuggestions(elementId: string, text: string, origin: SuggestionOrigin): Draft[] {
  return [
    ...findCitations(text).map((hit): Draft => ({ elementId, kind: 'legalBasis', value: hit.legalBasis, excerpt: hit.text, origin })),
    ...fromHits(elementId, 'auditReference', origin, auditReferencesIn(text)),
    ...fromHits(elementId, 'crossReference', origin, crossReferencesIn(text)),
    ...fromHits(elementId, 'source', origin, sourcesIn(text)),
  ]
}

function isContainer(element: ModelElement): boolean {
  return element.type === 'bpmn:Participant' || element.type === 'bpmn:Lane'
}

function actorSuggestion(element: ModelElement, options: SuggestionOptions): Draft[] {
  const role = roleFromText(options.profile, element.name, options.roleAliases ?? [])
  const actor: Actor = { role, ...(element.name ? { displayName: element.name } : {}) }
  return role ? [{ elementId: element.id, kind: 'actor', value: actor, excerpt: element.name, origin: 'name' }] : []
}

function rolePrefixSuggestion(element: ModelElement, options: SuggestionOptions): Draft[] {
  const prefix = isActivity(element.type) && element.name ? ROLE_PREFIX.exec(element.name.trim())?.groups?.praefix : undefined
  const role = prefix ? roleFromText(options.profile, prefix, options.roleAliases ?? []) : undefined
  return role && prefix ? [{ elementId: element.id, kind: 'rolePrefix', value: role, excerpt: prefix, origin: 'name' }] : []
}

function roleSuggestions(element: ModelElement, options: SuggestionOptions): Draft[] {
  if (isContainer(element) && !element.extensions.actor) return actorSuggestion(element, options)
  return rolePrefixSuggestion(element, options)
}

function colorSuggestion(element: ModelElement): Draft[] {
  const key = `${element.color?.fill ?? ''}|${element.color?.stroke ?? ''}`
  const marker = COLOR_MARKERS[key]
  return marker ? [{ elementId: element.id, kind: 'marker', value: { type: marker }, excerpt: key.replace('|', '/'), origin: 'color' }] : []
}

function annotationSuggestions(model: ProcessModel, element: ModelElement): Draft[] {
  if (element.type !== 'bpmn:Association') return []
  const [source, target] = [model.byId.get(element.sourceId ?? ''), model.byId.get(element.targetId ?? '')]
  const annotation = [source, target].find((el) => el?.type === 'bpmn:TextAnnotation')
  const other = annotation === source ? target : source
  const text = annotation?.name ?? ''
  if (!annotation || !other || !GAP_PREFIXES.test(text)) return []
  return [{ elementId: other.id, kind: 'marker', value: { type: 'soll_ohne_regelung' }, excerpt: text.slice(0, 80), origin: 'annotation' }]
}

function suggestionsFor(model: ProcessModel, element: ModelElement, options: SuggestionOptions): Draft[] {
  return [
    ...(element.documentation ? textSuggestions(element.id, element.documentation, 'documentation') : []),
    ...(element.name && !isContainer(element) ? textSuggestions(element.id, element.name, 'name') : []),
    ...roleSuggestions(element, options),
    ...colorSuggestion(element),
    ...annotationSuggestions(model, element),
  ]
}

/** All suggestions for an unchanged diagram; duplicates per element are dropped. */
export function collectSuggestions(model: ProcessModel, options: SuggestionOptions = {}): Suggestion[] {
  const unique = new Map<string, Suggestion>()
  for (const element of model.elements) {
    for (const draft of suggestionsFor(model, element, options)) {
      const key = `${draft.elementId}|${draft.kind}|${JSON.stringify(draft.value)}`
      if (!unique.has(key)) unique.set(key, { ...draft, id: `S${unique.size + 1}` })
    }
  }
  return [...unique.values()]
}

// ---------------------------------------------------------------------------
// Applying suggestions
// ---------------------------------------------------------------------------

type Merger = (ext: Extensions, value: Suggestion['value']) => Partial<Extensions> | null

function addUnique<T>(list: T[], value: T, key: (item: T) => string): T[] | null {
  return list.some((item) => key(item) === key(value)) ? null : [...list, value]
}

const MERGERS: Record<Exclude<SuggestionKind, 'rolePrefix'>, Merger> = {
  legalBasis: (ext, value) => wrap('legalBases', addUnique(ext.legalBases, value as LegalBasis, citation)),
  auditReference: (ext, value) =>
    wrap('auditReferences', addUnique(ext.auditReferences, value as AuditReference, (r) => `${r.keyRequirement}|${r.assessmentCriterion ?? ''}`)),
  crossReference: (ext, value) => wrap('crossReferences', addUnique(ext.crossReferences, value as CrossReference, (r) => `${r.kind}|${r.key}`)),
  source: (ext, value) => wrap('sources', addUnique(ext.sources, value as Source, (s) => s.location ?? '')),
  marker: (ext, value) => wrap('markers', addUnique(ext.markers, value as Marker, (m) => m.type)),
  actor: (ext, value) => (ext.actor ? null : { actor: value as Actor }),
}

function wrap<K extends keyof Extensions>(key: K, value: Extensions[K] | null): Partial<Extensions> | null {
  return value === null ? null : ({ [key]: value } as Partial<Extensions>)
}

export interface ApplyOptions {
  /** Removes the role prefix from task labels for accepted `rolePrefix` suggestions. */
  removePrefixes?: boolean
}

/** Takes over accepted suggestions; existing data stays, duplicates are skipped. */
export function applySuggestions(access: ModelAccess, accepted: Suggestion[], options: ApplyOptions = {}): number {
  let changed = 0
  const byElement = new Map<string, Suggestion[]>()
  for (const item of accepted) byElement.set(item.elementId, [...(byElement.get(item.elementId) ?? []), item])
  for (const [elementId, items] of byElement) {
    if (!access.has(elementId)) continue
    const ext = access.read(elementId)
    const patch: Partial<Extensions> = {}
    for (const item of items) {
      if (item.kind === 'rolePrefix') continue
      const change = MERGERS[item.kind]({ ...ext, ...patch } as Extensions, item.value)
      if (change) Object.assign(patch, change)
    }
    if (Object.keys(patch).length) {
      access.write(elementId, patch)
      changed += 1
    }
    if (options.removePrefixes && items.some((item) => item.kind === 'rolePrefix')) {
      access.rename(elementId, removeRolePrefix(access.name(elementId)))
      changed += 1
    }
  }
  return changed
}
