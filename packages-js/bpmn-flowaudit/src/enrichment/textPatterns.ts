/**
 * Patterns for domain keys in free text (same as `auditcore_bpmn`
 * enrichment): assessment criteria, finding references („T15 F1“),
 * checklist items, audit file registers and manual references.
 */

import type { AuditReference, CrossReference, Source } from '../schema/types'

const WORD = String.raw`[\p{L}\p{N}_]`

export const CRITERIA = /Bewertungskriteri(?:um|en)\s+(?<liste>\d+\.\d+(?:\s*(?:,|und|sowie)\s*\d+\.\d+)*)/gu
export const CRITERION_SHORT = /\bBK\s+(?<bk>\d+\.\d+)/gu
export const FINDINGS = /Feststellung(?:en)?\s+(?<liste>T\d+\s+F\d+(?:\s*(?:,|und)\s*T\d+\s+F\d+)*)/gu
export const CHECKLIST_ITEM = new RegExp(
  String.raw`(?:(?<dok>[A-ZÄÖÜ](?:${WORD}|[\- ])*?[Cc]heckliste(?:\s+[\p{L}\p{N}_.]+)*?(?:\s+V\s?[\d.]+)?),\s*)?Prüffeld(?:er)?\s+(?<nr>\d+(?:\.\d+)+)`,
  'gu',
)
export const REGISTER = /\[(?<liste>[A-Z]\d{1,2}(?:\s*,\s*[A-Z]\d{1,2})*)\]/gu
export const MANUAL_REFERENCE = new RegExp(
  String.raw`(?<dok>[A-ZÄÖÜ](?:${WORD}|[+\-])*(?:handbuch|richtlinie|leitfaden|Merkblatt|merkblatt)(?:${WORD}|[+\-])*(?:\s+(?:V\s?)?[\d.+]+)*)` +
    String.raw`(?:,\s*|\s+)(?<stelle>(?:Kapitel|Abschnitt|Teil|Nummer|Anlage)\s+[\p{L}\p{N}_.]+(?:\s+(?:Nummer|Satz|Kapitel)\s+[\p{L}\p{N}_.]+)*)` +
    String.raw`(?:\s*\((?<seiten>(?:PDF-)?Seiten?\s+[^)]{1,30})\))?`,
  'gu',
)
/** Role prefix of a task label („Stelle: Antrag prüfen“). */
export const ROLE_PREFIX = /^(?<praefix>[^:\n]{2,60}):\s+\S/u

export function splitList(list: string): string[] {
  return list
    .split(/\s*(?:,|und|sowie)\s*/u)
    .map((part) => part.trim())
    .filter(Boolean)
}

export interface TextHit<T> {
  value: T
  excerpt: string
}

function hits<T>(text: string, pattern: RegExp, build: (groups: Record<string, string>) => T[]): TextHit<T>[] {
  return [...text.matchAll(pattern)].flatMap((match) =>
    build((match.groups ?? {}) as Record<string, string>).map((value) => ({ value, excerpt: match[0] })),
  )
}

export function auditReferencesIn(text: string): TextHit<AuditReference>[] {
  const toReference = (bk: string): AuditReference => ({ keyRequirement: bk.split('.')[0], assessmentCriterion: bk })
  return [
    ...hits(text, CRITERIA, (g) => splitList(g.liste).map(toReference)),
    ...hits(text, CRITERION_SHORT, (g) => [toReference(g.bk)]),
  ]
}

export function crossReferencesIn(text: string): TextHit<CrossReference>[] {
  return [
    ...hits(text, FINDINGS, (g) => splitList(g.liste).map((ref) => ({ kind: 'feststellung_ref', key: ref.split(/\s+/).join(' ') }))),
    ...hits(text, CHECKLIST_ITEM, (g) => [
      { kind: 'prueffeld', key: g.nr, ...(g.dok ? { document: g.dok.split(/\s+/).join(' ') } : {}) },
    ]),
    ...hits(text, REGISTER, (g) => splitList(g.liste).map((key) => ({ kind: 'register', key }))),
  ]
}

export function sourcesIn(text: string): TextHit<Source>[] {
  return hits(text, MANUAL_REFERENCE, (g) => {
    const place = g.stelle + (g.seiten ? ` (${g.seiten})` : '')
    return [{ sourceType: 'verfahrenshandbuch', location: `${g.dok}, ${place}` }]
  })
}

/** „Stelle: Antrag prüfen“ → „Antrag prüfen“. */
export function removeRolePrefix(name: string): string {
  const trimmed = name.trim()
  const match = ROLE_PREFIX.exec(trimmed)
  return match?.groups ? trimmed.slice(match.groups.praefix.length + 1).trim() : name
}
