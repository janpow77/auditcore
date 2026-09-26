/**
 * Editing of legal bases: structured fields, duplicate check, regeneration
 * of the citation text, splitting legacy free text, typed citations and
 * search hits without display fields.
 */

import { citation, completeEuAct, findCitations, forWriting, isStructured, legalBasisKey, parseCitation, splitFreeText, type LegalBasis, type LegalSearchHit } from '../index'
import type { FieldDescriptor } from './descriptors'

const legal = (key: string, extra: Partial<FieldDescriptor> = {}): FieldDescriptor => ({ key, label: `legal.${key}`, kind: 'text', ...extra })

export const LEGAL_FIELDS: FieldDescriptor[] = [
  legal('act', { wide: true, placeholder: 'Verordnung (EU) 2021/1060' }),
  legal('article'),
  legal('section'),
  legal('annex'),
  legal('paragraph'),
  legal('subparagraph'),
  legal('sentence'),
  legal('point'),
  legal('number'),
  legal('version', { wide: true }),
  legal('celex'),
  legal('eli'),
  legal('url', { wide: true }),
  legal('shortTitle', { wide: true }),
  legal('note', { wide: true }),
  { key: 'confidential', label: 'field.confidential', kind: 'checkbox', wide: true },
]

const prepare = (items: LegalBasis[]) => items.map(forWriting)

/** List with the new entry, or `null` for a duplicate. */
export function addLegalBasis(items: LegalBasis[], value: LegalBasis): LegalBasis[] | null {
  if (items.some((item) => legalBasisKey(item) === legalBasisKey(value))) return null
  return prepare([...items, value])
}

/** Structured edits regenerate the text; free text of the legacy form stays. */
export function updateLegalBasis(items: LegalBasis[], index: number, value: LegalBasis): LegalBasis[] {
  const previous = items[index]
  const regenerated = isStructured(value) && previous && previous.text === citation(previous) ? { ...value, text: undefined } : value
  return prepare(items.map((item, i) => (i === index ? regenerated : item)))
}

export const removeLegalBasis = (items: LegalBasis[], index: number): LegalBasis[] => prepare(items.filter((_, i) => i !== index))

/** Splits a legacy free text into structured entries (unrecognised parts stay text). */
export function structureLegalBasis(items: LegalBasis[], index: number): LegalBasis[] | null {
  const legacy = items[index]
  if (!legacy) return null
  const parts = splitFreeText(legacy.text ?? '').flatMap((part) => {
    const hits = findCitations(part)
    return hits.length ? hits.map((hit) => hit.legalBasis) : [{ text: part }]
  })
  return prepare([...items.slice(0, index), ...parts, ...items.slice(index + 1)])
}

/** Citation typed into the search field (or `null`). */
export function typedCitation(query: string): LegalBasis | null {
  const parsed = parseCitation(query)
  return parsed.act || parsed.text ? completeEuAct(parsed) : null
}

const DISPLAY = new Set(['title', 'excerpt', 'origin'])

/** Search hits carry display helpers (title, excerpt, origin) that are not stored. */
export function withoutDisplayFields(value: LegalBasis | LegalSearchHit): LegalBasis {
  return Object.fromEntries(Object.entries(value).filter(([key]) => !DISPLAY.has(key))) as LegalBasis
}

export const hitHint = (hit: LegalSearchHit): string => [hit.title, hit.origin].filter(Boolean).join(' · ')
