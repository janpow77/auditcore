/**
 * Citation forms of a legal basis.
 *
 * The canonical form is the **long form** („Artikel 73 Absatz 2 Buchstabe b
 * der Verordnung (EU) 2021/1060“) because audit authority texts cite this
 * way (177 long to 59 short citations in the analysed diagrams). The short
 * form („Art. 73 Abs. 2 Buchst. b VO (EU) 2021/1060“) is for display.
 * Same rules as `Rechtsgrundlage.zitat()` in `auditcore_bpmn`.
 */

import type { LegalBasis } from '../schema/types'

const ACT_LONG: [RegExp, string][] = [
  [/^Delegierte\s+VO\b/, 'Delegierte Verordnung'],
  [/^Durchführungs-?VO\b/, 'Durchführungsverordnung'],
  [/^DVO\b/, 'Durchführungsverordnung'],
  [/^VO\b/, 'Verordnung'],
  [/^RL\b/, 'Richtlinie'],
]
const ACT_SHORT: [string, string][] = [
  ['Delegierte Verordnung', 'Delegierte VO'],
  ['Durchführungsverordnung', 'Durchführungs-VO'],
  ['Verordnung', 'VO'],
  ['Richtlinie', 'RL'],
]
const GENITIVE: [string, string][] = [
  ['Delegierte Verordnung', 'der Delegierten Verordnung'],
  ['Durchführungsverordnung', 'der Durchführungsverordnung'],
  ['Verordnung', 'der Verordnung'],
  ['Richtlinie', 'der Richtlinie'],
  ['Beschluss', 'des Beschlusses'],
  ['Entscheidung', 'der Entscheidung'],
]

/** Parts after the article, with short and long labels. */
const SUB_PARTS: [keyof LegalBasis, string, string][] = [
  ['paragraph', 'Abs.', 'Absatz'],
  ['subparagraph', 'UAbs.', 'Unterabsatz'],
  ['sentence', 'S.', 'Satz'],
  ['point', 'Buchst.', 'Buchstabe'],
  ['number', 'Nr.', 'Nummer'],
]

export const STRUCTURE_FIELDS = ['act', 'article', 'section', 'annex', 'paragraph', 'subparagraph', 'sentence', 'point', 'number'] as const

/** Long canonical form of an act name (`VO` → `Verordnung`). */
export function actLong(act: string): string {
  const value = act.split(/\s+/).filter(Boolean).join(' ')
  const rule = ACT_LONG.find(([pattern]) => pattern.test(value))
  return rule ? value.replace(rule[0], rule[1]) : value
}

/** Short form of an act name for display (`Verordnung` → `VO`). */
export function actShort(act: string): string {
  const value = actLong(act)
  const rule = ACT_SHORT.find(([long]) => value.startsWith(long))
  return rule ? rule[1] + value.slice(rule[0].length) : value
}

function actGenitive(act: string): string {
  const value = actLong(act)
  const rule = GENITIVE.find(([head]) => value === head || value.startsWith(`${head} `))
  return rule ? rule[1] + value.slice(rule[0].length) : value
}

export function isStructured(basis: LegalBasis): boolean {
  return STRUCTURE_FIELDS.some((field) => Boolean(basis[field]))
}

function head(basis: LegalBasis, short: boolean): string[] {
  if (basis.article) return [`${short ? 'Art.' : 'Artikel'} ${basis.article}`]
  if (basis.section) return [`§ ${basis.section}`]
  if (basis.annex) return [`Anhang ${basis.annex}`]
  return []
}

function parts(basis: LegalBasis, short: boolean): string[] {
  const tail = SUB_PARTS.filter(([field]) => basis[field]).map(([field, s, l]) => `${short ? s : l} ${String(basis[field])}`)
  return [...head(basis, short), ...tail]
}

/** `VV zu § 44 LHO` with number → „VV Nummer 4.2 zu § 44 LHO“. */
function administrativeRule(basis: LegalBasis, short: boolean): string | null {
  if (basis.act?.startsWith('VV zu ') && basis.number && !(basis.article || basis.section || basis.annex)) {
    return `VV ${short ? 'Nr.' : 'Nummer'} ${basis.number} ${basis.act.slice(3)}`
  }
  return null
}

/** Long citation, e.g. „Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060“. */
export function citation(basis: LegalBasis): string {
  if (!isStructured(basis)) return (basis.text ?? '').trim()
  const rule = administrativeRule(basis, false)
  if (rule) return rule
  const result = parts(basis, false)
  if (basis.act) {
    const genitive = Boolean(basis.article || basis.annex) && result.length > 0
    result.push(genitive ? actGenitive(basis.act) : actLong(basis.act))
  }
  return result.join(' ')
}

/** Short citation for display, e.g. „Art. 73 Abs. 2 Buchst. b VO (EU) 2021/1060“. */
export function shortCitation(basis: LegalBasis): string {
  if (!isStructured(basis)) return (basis.text ?? '').trim()
  const rule = administrativeRule(basis, true)
  if (rule) return rule
  const result = parts(basis, true)
  if (basis.act) result.push(actShort(basis.act))
  return result.join(' ')
}

/** Readable text: free text, otherwise short citation. */
export function displayText(basis: LegalBasis): string {
  return (basis.text ?? '').trim() || shortCitation(basis)
}

/** Act in long form and text content as long citation. */
export function normalized(basis: LegalBasis): LegalBasis {
  if (!isStructured(basis)) return basis
  const result: LegalBasis = { ...basis }
  if (basis.act) result.act = actLong(basis.act)
  result.text = citation(result)
  return result
}

/**
 * Prepares a legal basis for writing: text content is mandatory (1.0 readers
 * show it). Existing free text is never overwritten.
 */
export function forWriting(basis: LegalBasis): LegalBasis {
  if (basis.text?.trim()) return basis
  return isStructured(basis) ? { ...basis, text: citation(basis) } : basis
}

/** Splits a 1.0 free text with several acts („§ 55 BHO; Art. 74 VO (EU) 2021/1060“). */
export function splitFreeText(text: string): string[] {
  return text
    .split(/\s*[;\n]\s*/)
    .map((part) => part.trim())
    .filter(Boolean)
}

/** Key for duplicate detection (structured fields or text). */
export function legalBasisKey(basis: LegalBasis): string {
  if (!isStructured(basis)) return (basis.text ?? '').trim().toLowerCase().replace(/\s+/g, ' ')
  return STRUCTURE_FIELDS.map((field) => (field === 'act' && basis.act ? actLong(basis.act) : basis[field] ?? ''))
    .join('|')
    .toLowerCase()
}
