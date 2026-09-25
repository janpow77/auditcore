/**
 * Recognising legal citations in free text and resolving EU acts (CELEX,
 * ELI, EUR-Lex URL) – purely syntactic, no network access.
 *
 * Same patterns as `auditcore_bpmn.citations`: long form („Artikel 73
 * Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060“), short form („Art. 74
 * Abs. 2 UAbs. 2“), sections („§ 44 Absatz 1 LHO“, „§§ 23 und 44 LHO“),
 * administrative rules („VV Nummer 4.2 zu § 44 LHO“) and annexes.
 */

import { actLong, citation, normalized } from '../model/legalBasis'
import type { LegalBasis } from '../schema/types'

export type CitationForm = 'vv' | 'long' | 'short' | 'sections' | 'section'

export interface CitationHit {
  legalBasis: LegalBasis
  start: number
  end: number
  text: string
  form: CitationForm
}

const EU_ACT = String.raw`(?:(?:Delegierten|Durchführungs)\s*)?(?:Verordnung|Richtlinie|VO|RL)\s*\((?:EU|EG|EWG|EU,\s*Euratom|EG,\s*Euratom)\)\s*(?:Nr\.\s*)?\d{1,4}\/\d{1,4}`
const SUB_LONG = String.raw`(?:\s+Absatz\s+(?<abs>\d+[a-z]?))?(?:\s+Unterabsatz\s+(?<uabs>\d+))?(?:\s+Satz\s+(?<satz>\d+))?(?:\s+Buchstabe\s+(?<buchst>[a-z]{1,3}))?(?:\s+(?:Nummer|Ziffer)\s+(?<nr>[\divx.]+))?`
const SUB_SHORT = String.raw`(?:\s*Abs\.\s*(?<abs>\d+[a-z]?))?(?:\s*UAbs\.\s*(?<uabs>\d+))?(?:\s*(?:S\.|Satz)\s*(?<satz>\d+))?(?:\s*(?:Buchst\.|lit\.)\s*(?<buchst>[a-z]{1,3}))?(?:\s*(?:Nr\.|Ziff\.)\s*(?<nr>[\divx.]+))?`
const SUB_SECTION = String.raw`(?:\s+(?:Absatz|Abs\.)\s+(?<abs>\d+[a-z]?))?(?:\s+Unterabsatz\s+(?<uabs>\d+))?(?:\s+(?:Satz|S\.)\s+(?<satz>\d+))?(?:\s+Buchstabe\s+(?<buchst>[a-z]{1,3}))?(?:\s+(?:Nummer|Nr\.|Ziffer)\s+(?<nr>[\divx.]+))?`
const NATIONAL_ACT = String.raw`(?<norm>(?:[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]*|UVgO|VgV|GWB))(?![A-Za-zÄÖÜäöüß0-9_])`

const LONG = new RegExp(String.raw`(?<kopf>Artikel\s+(?<art>\d+[a-z]?)|Anhang\s+(?<anh>[IVXLC]+))${SUB_LONG}\s+(?:der|des)\s+(?<norm>${EU_ACT})`, 'g')
const SHORT = new RegExp(String.raw`Art\.\s*(?<art>\d+[a-z]?)${SUB_SHORT}(?:\s+(?<norm>${EU_ACT}|CPR|Dach-VO))?`, 'g')
const SECTION = new RegExp(String.raw`§\s*(?<par>\d+[a-z]?)${SUB_SECTION}\s+${NATIONAL_ACT}`, 'g')
const SECTIONS = new RegExp(String.raw`§§\s*(?<liste>\d+[a-z]?(?:\s*(?:,|und|bis)\s*\d+[a-z]?)+)\s+${NATIONAL_ACT}`, 'g')
const VV = new RegExp(String.raw`VV\s+(?:Nummer|Nr\.)\s*(?<nr>[\d.]+)\s+zu\s+§\s*(?<par>\d+[a-z]?)\s+${NATIONAL_ACT}`, 'g')

type Groups = Record<string, string | undefined>

function group(groups: Groups, name: string): string | undefined {
  const value = groups[name]?.trim()
  return value ? value : undefined
}

function subdivisions(groups: Groups): Partial<LegalBasis> {
  return {
    paragraph: group(groups, 'abs'),
    subparagraph: group(groups, 'uabs'),
    sentence: group(groups, 'satz'),
    point: group(groups, 'buchst'),
    number: group(groups, 'nr'),
  }
}

function compact(basis: LegalBasis): LegalBasis {
  return Object.fromEntries(Object.entries(basis).filter(([, value]) => value !== undefined)) as LegalBasis
}

interface Recogniser {
  pattern: RegExp
  form: CitationForm
  build: (groups: Groups) => LegalBasis[]
}

const RECOGNISERS: Recogniser[] = [
  { pattern: VV, form: 'vv', build: (g) => [{ act: `VV zu § ${g.par} ${g.norm}`, number: g.nr }] },
  {
    pattern: LONG,
    form: 'long',
    build: (g) => [{ act: g.norm, article: group(g, 'art'), annex: group(g, 'anh'), ...subdivisions(g) }],
  },
  { pattern: SHORT, form: 'short', build: (g) => [{ act: group(g, 'norm'), article: g.art, ...subdivisions(g) }] },
  {
    pattern: SECTIONS,
    form: 'sections',
    build: (g) => (g.liste?.match(/\d+[a-z]?/g) ?? []).map((section) => ({ act: g.norm, section })),
  },
  { pattern: SECTION, form: 'section', build: (g) => [{ act: g.norm, section: g.par, ...subdivisions(g) }] },
]

/** Finds legal citations in free text (e.g. `bpmn:documentation`), without overlaps. */
export function findCitations(text: string | null | undefined): CitationHit[] {
  if (!text) return []
  const hits: CitationHit[] = []
  const taken: [number, number][] = []
  const free = (start: number, end: number) => taken.every(([s, e]) => end <= s || start >= e)
  for (const { pattern, form, build } of RECOGNISERS) {
    for (const match of text.matchAll(pattern)) {
      const start = match.index ?? 0
      const end = start + match[0].length
      if (!free(start, end)) continue
      taken.push([start, end])
      for (const basis of build((match.groups ?? {}) as Groups)) {
        hits.push({ legalBasis: normalized(compact(basis)), start, end, text: match[0], form })
      }
    }
  }
  return hits.sort((a, b) => a.start - b.start || citation(a.legalBasis).localeCompare(citation(b.legalBasis)))
}

/** Reads a single citation; without a hit it stays free text. */
export function parseCitation(text: string): LegalBasis {
  const hits = findCitations(text)
  const [only] = hits
  if (hits.length === 1 && only && only.text.trim() === text.trim()) return only.legalBasis
  return text.trim() ? { text: text.trim() } : {}
}

// ---------------------------------------------------------------------------
// EU acts
// ---------------------------------------------------------------------------

const EU_ACT_PARTS = /(?<typ>Delegierte(?:n)? Verordnung|Durchführungsverordnung|Verordnung|Richtlinie|Beschluss|Entscheidung)\s*\((?<org>EU|EG|EWG|EU,\s*Euratom|EG,\s*Euratom)\)\s*(?<nr>Nr\.\s*)?(?<a>\d{1,4})\/(?<b>\d{1,4})/
const OLD_DIRECTIVE = /Richtlinie\s+(?<a>\d{4})\/(?<b>\d{1,4})\/(?<org>EU|EG|EWG)/
const ELI_KIND: Record<string, string> = {
  Verordnung: 'reg',
  'Delegierte Verordnung': 'reg_del',
  'Delegierten Verordnung': 'reg_del',
  Durchführungsverordnung: 'reg_impl',
  Richtlinie: 'dir',
  Beschluss: 'dec',
  Entscheidung: 'dec',
}
const CELEX_TYPE: Record<string, string> = { reg: 'R', reg_del: 'R', reg_impl: 'R', dir: 'L', dec: 'D' }

const isYear = (value: number) => value >= 1950 && value <= 2100

/** `[eliKind, year, number]` of an EU act, or `null`. */
export function euAct(act: string): [string, number, number] | null {
  const text = actLong(act)
  const match = EU_ACT_PARTS.exec(text)
  if (match?.groups) {
    const kind = ELI_KIND[match.groups.typ ?? '']
    if (!kind) return null
    const first = Number(match.groups.a)
    const second = Number(match.groups.b)
    const numberFirst = kind !== 'dir' && (Boolean(match.groups.nr) || (isYear(second) && !isYear(first)))
    const [year, number] = numberFirst ? [second, first] : [first, second]
    return isYear(year) ? [kind, year, number] : null
  }
  const old = OLD_DIRECTIVE.exec(text)
  return old?.groups ? ['dir', Number(old.groups.a), Number(old.groups.b)] : null
}

/** Fills missing CELEX/ELI/URL of an EU act; existing values stay. */
export function completeEuAct(basis: LegalBasis): LegalBasis {
  const found = basis.act ? euAct(basis.act) : null
  if (!found) return basis
  const [kind, year, number] = found
  const celex = `3${year}${CELEX_TYPE[kind]}${String(number).padStart(4, '0')}`
  return {
    ...basis,
    celex: basis.celex ?? celex,
    eli: basis.eli ?? `http://data.europa.eu/eli/${kind}/${year}/${number}/oj`,
    url: basis.url ?? `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:${celex}`,
  }
}
