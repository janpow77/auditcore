/**
 * Framework-freie Formularlogik der Hochrechnung: Zeilen als Text (so wie
 * eingegeben), Prüfung je Feld und Aufbau der Anfragen. Nichts wird still
 * ergänzt; leere Fehlerfelder zählen als 0.
 */
import { parseInput } from '../sampling/model'
import type { EvaluationRequest, EvaluationResult, ExtrapolationCatalogue, ExtrapolationMethod, ResidualRequest, StratumInput, UnitInput } from './types'

export interface StratumRow {
  key: string
  name: string
  bookValue: string
  populationSize: string
  systemic: string
}

export interface UnitRow {
  key: string
  id: string
  stratum: string
  bookValue: string
  random: string
  systemic: string
  anomalous: string
  reason: string
  corrected: boolean
  exhaustive: boolean
}

export interface ExtrapolationForm {
  methodId: string
  confidence: number | null
  profileId: string | null
  sampleSize: string
  /** Wesentlichkeitsschwelle in Prozent. */
  materiality: string
  strata: readonly StratumRow[]
  units: readonly UnitRow[]
}

export type ExtrapolationIssue = 'required' | 'invalid' | 'range' | 'reason' | 'stratum' | 'duplicate'
export type ExtrapolationFormError = 'method' | 'confidence' | 'profile' | 'strata' | 'units'
export type ExtrapolationIssues = Readonly<Record<string, ExtrapolationIssue>>

export type EvaluationValidation =
  | { ok: true; request: EvaluationRequest }
  | { ok: false; error: ExtrapolationFormError | null; issues: ExtrapolationIssues }

export interface ResidualForm {
  auditPopulation: string
  /** Gesamtfehlerquote in Prozent. */
  terRate: string
  ongoing: string
  otherNegative: string
  corrections: string
}

export type ResidualValidation = { ok: true; request: ResidualRequest } | { ok: false; issues: ExtrapolationIssues }

export const EMPTY_RESIDUAL: ResidualForm = { auditPopulation: '', terRate: '', ongoing: '', otherNegative: '', corrections: '' }

export function emptyStratum(key: string): StratumRow {
  return { key, name: '', bookValue: '', populationSize: '', systemic: '' }
}

export function emptyUnit(key: string, stratum = ''): UnitRow {
  return { key, id: '', stratum, bookValue: '', random: '', systemic: '', anomalous: '', reason: '', corrected: false, exhaustive: false }
}

type Format = (value: number) => string

const optional = (value: number | undefined, format: Format): string => (value === undefined || value === 0 ? '' : format(value))

export function stratumRows(strata: readonly StratumInput[], format: Format): StratumRow[] {
  return strata.map((stratum, index) => ({
    key: `s${index + 1}`,
    name: stratum.name,
    bookValue: format(stratum.book_value),
    populationSize: stratum.population_size === undefined ? '' : String(stratum.population_size),
    systemic: optional(stratum.systemic_error, format),
  }))
}

export function unitRows(units: readonly UnitInput[], format: Format): UnitRow[] {
  return units.map((unit, index) => ({
    key: `u${index + 1}`,
    id: unit.id,
    stratum: unit.stratum,
    bookValue: format(unit.book_value),
    random: optional(unit.random_error, format),
    systemic: optional(unit.systemic_error, format),
    anomalous: optional(unit.anomalous_error, format),
    reason: unit.anomalous_reason ?? '',
    corrected: unit.anomalous_corrected ?? false,
    exhaustive: unit.exhaustive ?? false,
  }))
}

interface Rule {
  required?: boolean
  positive?: boolean
  integer?: boolean
  max?: number
}

function violates(value: number, rule: Rule): boolean {
  if (rule.integer && !Number.isInteger(value)) return true
  const low = rule.positive ? value <= 0 : value < 0
  return low || (rule.max !== undefined && value > rule.max)
}

/** Zahl eines Textfelds oder der Befund; leere, nicht verlangte Felder ergeben 0. */
export function readExtrapolationAmount(text: string, rule: Rule = {}): number | ExtrapolationIssue {
  const parsed = parseInput(text)
  if (parsed === null) return rule.required ? 'required' : 0
  if (parsed === undefined) return 'invalid'
  if (rule.integer && !Number.isInteger(parsed)) return 'invalid'
  return violates(parsed, rule) ? 'range' : parsed
}

class Collector {
  readonly issues: Record<string, ExtrapolationIssue> = {}

  take(key: string, text: string, rule: Rule = {}): number {
    const value = readExtrapolationAmount(text, rule)
    if (typeof value === 'number') return value
    this.issues[key] = value
    return 0
  }

  flag(key: string, issue: ExtrapolationIssue): void {
    this.issues[key] = issue
  }
}

function readStrata(rows: readonly StratumRow[], method: ExtrapolationMethod, out: Collector): StratumInput[] {
  const seen = new Set<string>()
  return rows.map((row, index) => {
    const name = row.name.trim()
    if (!name) out.flag(`strata.${index}.name`, 'required')
    else if (seen.has(name)) out.flag(`strata.${index}.name`, 'duplicate')
    seen.add(name)
    const stratum: StratumInput = { name, book_value: out.take(`strata.${index}.bookValue`, row.bookValue, { required: true, positive: true }) }
    const systemic = out.take(`strata.${index}.systemic`, row.systemic)
    const size = row.populationSize.trim() || method.needs_population_size
      ? out.take(`strata.${index}.populationSize`, row.populationSize, { required: true, positive: true, integer: true })
      : undefined
    return { ...stratum, ...(size === undefined ? {} : { population_size: size }), ...(systemic ? { systemic_error: systemic } : {}) }
  })
}

function readUnit(row: UnitRow, index: number, names: ReadonlySet<string>, out: Collector): UnitInput {
  const key = `units.${index}`
  if (!row.id.trim()) out.flag(`${key}.id`, 'required')
  if (!names.has(row.stratum.trim())) out.flag(`${key}.stratum`, 'stratum')
  const anomalous = out.take(`${key}.anomalous`, row.anomalous)
  if (anomalous > 0 && !row.reason.trim()) out.flag(`${key}.reason`, 'reason')
  const unit: UnitInput = {
    id: row.id.trim(),
    stratum: row.stratum.trim(),
    book_value: out.take(`${key}.bookValue`, row.bookValue, { required: true, positive: true }),
    random_error: out.take(`${key}.random`, row.random),
    systemic_error: out.take(`${key}.systemic`, row.systemic),
    anomalous_error: anomalous,
  }
  return { ...unit, ...(anomalous > 0 ? { anomalous_reason: row.reason.trim(), anomalous_corrected: row.corrected } : {}), ...(row.exhaustive ? { exhaustive: true } : {}) }
}

function formError(catalogue: ExtrapolationCatalogue, form: ExtrapolationForm): ExtrapolationFormError | null {
  const method = catalogue.methods.find((entry) => entry.id === form.methodId)
  if (!method) return 'method'
  if (method.statistical && form.confidence === null) return 'confidence'
  if (method.statistical && form.profileId === null) return 'profile'
  if (form.strata.length === 0) return 'strata'
  return form.units.length === 0 ? 'units' : null
}

function settings(method: ExtrapolationMethod, form: ExtrapolationForm, out: Collector): Partial<EvaluationRequest> {
  const materiality = out.take('materiality', form.materiality, { required: true, positive: true, max: 2 })
  const size = method.needs_sample_size ? out.take('sampleSize', form.sampleSize, { required: true, positive: true, integer: true }) : undefined
  return {
    materiality_rate: materiality / 100,
    ...(method.statistical && form.confidence !== null ? { confidence_level: form.confidence } : {}),
    ...(method.statistical && form.profileId !== null ? { factor_profile: form.profileId } : {}),
    ...(size === undefined ? {} : { sample_size: size }),
  }
}

/** Anfrage für `POST /evaluate`; bei Befunden die Feldschlüssel mit ihrem Fehler. */
export function buildEvaluationRequest(catalogue: ExtrapolationCatalogue, form: ExtrapolationForm): EvaluationValidation {
  const error = formError(catalogue, form)
  const method = catalogue.methods.find((entry) => entry.id === form.methodId)
  if (error || !method) return { ok: false, error, issues: {} }
  const out = new Collector()
  const strata = readStrata(form.strata, method, out)
  const names = new Set(strata.map((stratum) => stratum.name).filter(Boolean))
  const units = form.units.map((row, index) => readUnit(row, index, names, out))
  const request = { method: method.id, ...settings(method, form, out), strata, units } as EvaluationRequest
  return Object.keys(out.issues).length ? { ok: false, error: null, issues: out.issues } : { ok: true, request }
}

/** RER-Formular aus einer Auswertung: A = Buchwert, D = Gesamtfehlerquote (in Prozent). */
export function residualFormFrom(result: EvaluationResult, current: ResidualForm, format: (value: number) => string): ResidualForm {
  const ter = result.total_error_rate
  return { ...current, auditPopulation: format(ter.book_value), terRate: format(ter.rate * 100) }
}

/** Anfrage für `POST /residual`; die Gesamtfehlerquote wird in Prozent eingegeben. */
export function buildResidualRequest(form: ResidualForm, materialityRate: number): ResidualValidation {
  const out = new Collector()
  const request: ResidualRequest = {
    audit_population: out.take('auditPopulation', form.auditPopulation, { required: true, positive: true }),
    total_error_rate: out.take('terRate', form.terRate, { required: true, max: 100 }) / 100,
    ongoing_assessment: out.take('ongoing', form.ongoing),
    other_negative_amounts: out.take('otherNegative', form.otherNegative),
    financial_corrections: out.take('corrections', form.corrections),
    materiality_rate: materialityRate,
  }
  return Object.keys(out.issues).length ? { ok: false, issues: out.issues } : { ok: true, request }
}

export function extrapolationMethodById(catalogue: ExtrapolationCatalogue | null, id: string): ExtrapolationMethod | null {
  return catalogue?.methods.find((method) => method.id === id) ?? null
}

/** Konfidenzniveaus, die die gewählte Methode mit Tabellenwerten erlaubt. */
export function confidenceChoices(catalogue: ExtrapolationCatalogue, method: ExtrapolationMethod | null): readonly number[] {
  return method?.id === 'mus.conservative' ? catalogue.confidence_levels['mus.conservative'] : catalogue.confidence_levels.z
}
