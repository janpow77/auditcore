/**
 * Formular des Planers: Eingaben als Text, Umwandlung in die Anfrage des
 * Vertrags. Anteile werden in Prozent erfasst und als Wert zwischen 0 und 1
 * gesendet; gerechnet wird nur im Backend.
 */
import { parseDecimal } from '@auditcore/common'
import type { SampleSizeCatalogue, SampleSizeMethod, SampleSizeRequest, SampleSizeStratumRequest } from './types'

export interface StratumDraft {
  name: string
  populationSize: string
  bookValue: string
  sd: string
  exhaustive: boolean
}

export interface SampleSizeForm {
  methodId: string
  values: Readonly<Record<string, string>>
  finiteCorrection: boolean
  strata: readonly StratumDraft[]
}

/** Feldschlüssel → Fehlerart (`required` oder `invalid`). */
export type SampleSizeIssues = Readonly<Record<string, 'required' | 'invalid'>>

export type StratumColumn = 'name' | 'populationSize' | 'bookValue' | 'sd' | 'exhaustive'

export const EMPTY_FORM: SampleSizeForm = { methodId: '', values: {}, finiteCorrection: false, strata: [] }
export const EMPTY_STRATUM: StratumDraft = { name: '', populationSize: '', bookValue: '', sd: '', exhaustive: false }

/** Felder mit Auswahlliste; alle übrigen skalaren Felder sind Zahlen. */
export const CHOICE_FIELDS: readonly string[] = ['factor_profile', 'confidence_level', 'rule', 'assurance_level']
/** In Prozent erfasste Anteile. */
export const PERCENT_FIELDS: readonly string[] = ['anticipated_error_rate', 'materiality_rate']
/** Felder, die nicht als einzelnes Eingabefeld erscheinen. */
const SPECIAL_FIELDS: readonly string[] = ['strata', 'book_values', 'finite_population_correction']
const OPTIONAL_FIELDS: readonly string[] = ['assurance_level']
const INTEGER_FIELDS: readonly string[] = ['population_size']

export function methodById(catalogue: SampleSizeCatalogue | null, id: string): SampleSizeMethod | null {
  return catalogue?.methods.find((entry) => entry.id === id) ?? null
}

/** Einzelne Eingabefelder der Methode in der Reihenfolge des Katalogs. */
export function scalarFields(method: SampleSizeMethod | null): string[] {
  return method ? method.fields.filter((field) => !SPECIAL_FIELDS.includes(field)) : []
}

export function hasStrata(method: SampleSizeMethod | null): boolean {
  return Boolean(method?.fields.includes('strata'))
}

export function hasFiniteCorrection(method: SampleSizeMethod | null): boolean {
  return Boolean(method?.fields.includes('finite_population_correction'))
}

/** Spalten der Schichttabelle: MUS nach Buchwert, sonst nach Anzahl mit Vollerhebung. */
export function strataColumns(method: SampleSizeMethod | null): StratumColumn[] {
  if (method?.id === 'guidance.mus_stratified') return ['name', 'bookValue', 'sd']
  return ['name', 'populationSize', 'sd', 'exhaustive']
}

/** Anfangswerte bei Methodenwechsel: sichtbar vorbelegt ist nur die Wesentlichkeit von 2 %. */
export function formFor(method: SampleSizeMethod | null, catalogue: SampleSizeCatalogue | null): SampleSizeForm {
  if (!method) return EMPTY_FORM
  const values: Record<string, string> = {}
  if (method.fields.includes('materiality_rate') && catalogue) values.materiality_rate = String(catalogue.materiality_rate * 100)
  const strata = hasStrata(method) ? [EMPTY_STRATUM, EMPTY_STRATUM] : []
  return { methodId: method.id, values, finiteCorrection: false, strata }
}

type Parsed = { value: number } | { issue: 'required' | 'invalid' } | null

function parseField(field: string, text: string | undefined): Parsed {
  if (text === undefined || text.trim() === '') return OPTIONAL_FIELDS.includes(field) ? null : { issue: 'required' }
  const value = parseDecimal(text, { allowNegative: false })
  if (value === null || (INTEGER_FIELDS.includes(field) && !Number.isInteger(value))) return { issue: 'invalid' }
  // Prozent → Anteil ohne Gleitkommarest (1,8 % → 0.018, nicht 0.018000000000000002).
  return { value: PERCENT_FIELDS.includes(field) ? Number((value / 100).toPrecision(15)) : value }
}

function scalarValue(field: string, text: string | undefined): Parsed | { text: string } {
  if (field === 'confidence_level') return text ? { value: Number(text) } : { issue: 'required' }
  if (CHOICE_FIELDS.includes(field)) {
    if (text) return { text }
    return OPTIONAL_FIELDS.includes(field) ? null : { issue: 'required' }
  }
  return parseField(field, text)
}

/** Zahl als deutsche Eingabe (Komma, keine Gruppierung), wie sie `parseDecimal` wieder liest. */
function germanText(value: number): string {
  return String(value).replace('.', ',')
}

function optionalNumber(text: string): number | undefined {
  const value = parseDecimal(text, { allowNegative: false })
  return value === null ? undefined : value
}

function stratumRequest(draft: StratumDraft): SampleSizeStratumRequest {
  const size = optionalNumber(draft.populationSize)
  const book = optionalNumber(draft.bookValue)
  const sd = optionalNumber(draft.sd)
  return {
    name: draft.name.trim(),
    exhaustive: draft.exhaustive,
    ...(size === undefined ? {} : { population_size: size }),
    ...(book === undefined ? {} : { book_value: book }),
    ...(sd === undefined ? {} : { sd }),
  }
}

/** Anfrage aus dem Formular oder die Felder mit fehlenden bzw. ungültigen Angaben. */
export function buildRequest(form: SampleSizeForm, method: SampleSizeMethod): { request: SampleSizeRequest } | { issues: SampleSizeIssues } {
  const request: SampleSizeRequest = { method: method.id }
  const issues: Record<string, 'required' | 'invalid'> = {}
  for (const field of scalarFields(method)) {
    const parsed = scalarValue(field, form.values[field])
    if (parsed === null) continue
    if ('issue' in parsed) issues[field] = parsed.issue
    else request[field] = 'text' in parsed ? parsed.text : parsed.value
  }
  if (hasFiniteCorrection(method)) request.finite_population_correction = form.finiteCorrection
  if (hasStrata(method)) request.strata = form.strata.filter((row) => row.name.trim() !== '').map(stratumRequest)
  return Object.keys(issues).length ? { issues } : { request }
}

/** Formular aus einer Anfrage (Vorbelegung über die Eigenschaft `request`). */
export function formFromRequest(request: SampleSizeRequest, catalogue: SampleSizeCatalogue | null): SampleSizeForm {
  const method = methodById(catalogue, request.method)
  const base = formFor(method, catalogue)
  const values: Record<string, string> = { ...base.values }
  for (const field of scalarFields(method)) {
    const raw = request[field]
    if (field === 'confidence_level' && typeof raw === 'number') values[field] = String(raw)
    else if (typeof raw === 'number') values[field] = germanText(PERCENT_FIELDS.includes(field) ? Math.round(raw * 1e10) / 1e8 : raw)
    else if (typeof raw === 'string') values[field] = raw
  }
  const strata = Array.isArray(request.strata)
    ? (request.strata as readonly SampleSizeStratumRequest[]).map((row) => ({
        name: row.name,
        populationSize: row.population_size === undefined ? '' : germanText(row.population_size),
        bookValue: row.book_value === undefined ? '' : germanText(row.book_value),
        sd: row.sd === undefined ? '' : germanText(row.sd),
        exhaustive: row.exhaustive,
      }))
    : base.strata
  return { methodId: base.methodId, values, finiteCorrection: request.finite_population_correction === true, strata }
}
