/**
 * Anzeige der Hochrechnung für Vue und React (reine Funktionen): Kennzahlen
 * der TER, Ergebnis-Ton, Herleitungstabelle und Zeilen der RER-Vorlage.
 * Texte ausschließlich aus `extrapolationMessages`.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent, type TableColumn, type TableRow } from '@auditcore/common'
import type { BadgeTone } from '../base/types'
import type { Locale, Translate } from '../i18n'
import type { ExtrapolationMessageKey } from './messages'
import type { ExtrapolationFormError, ExtrapolationIssue } from './model'
import type { Conclusion, EvaluationResult, ExtrapolationCatalogue, ExtrapolationMethod, ResidualErrorRate } from './types'

export type ExtrapolationTranslate = Translate<ExtrapolationMessageKey>

const TONES: Readonly<Record<Conclusion, BadgeTone>> = { material: 'danger', not_material: 'success', inconclusive: 'warning' }

export function conclusionTone(conclusion: Conclusion): BadgeTone {
  return TONES[conclusion]
}

export function conclusionLabel(catalogue: ExtrapolationCatalogue | null, conclusion: Conclusion): string {
  return catalogue?.conclusions.find((entry) => entry.id === conclusion)?.label ?? conclusion
}

export function extrapolationAmount(value: number, locale: Locale): string {
  return `${formatNumber(value, locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`
}

export function extrapolationRate(value: number, locale: Locale): string {
  return formatPercent(value, locale, 2)
}

/** Zahl als Eingabetext (ohne Tausendertrenner). */
export function extrapolationInputNumber(locale: Locale): (value: number) => string {
  return (value) => formatNumber(value, locale, { maximumFractionDigits: 6, useGrouping: false })
}

export function extrapolationIssueKey(issue: ExtrapolationIssue): ExtrapolationMessageKey {
  const keys: Readonly<Record<ExtrapolationIssue, ExtrapolationMessageKey>> = {
    required: 'issueRequired', invalid: 'issueInvalid', range: 'issueRange', reason: 'issueReason', stratum: 'issueStratum', duplicate: 'issueDuplicate',
  }
  return keys[issue]
}

export function extrapolationFormErrorKey(error: ExtrapolationFormError): ExtrapolationMessageKey {
  return `error${error}`
}

export interface ExtrapolationMethodGroup {
  statistical: boolean
  label: string
  methods: readonly ExtrapolationMethod[]
}

export function extrapolationMethodGroups(catalogue: ExtrapolationCatalogue, t: ExtrapolationTranslate): ExtrapolationMethodGroup[] {
  return [true, false].map((statistical) => ({
    statistical,
    label: t(statistical ? 'statistical' : 'nonStatistical'),
    methods: catalogue.methods.filter((method) => method.statistical === statistical),
  }))
}

export function extrapolationConfidenceLabel(level: number, locale: Locale): string {
  return formatPercent(level, locale, 0)
}

export interface ExtrapolationMetric {
  id: string
  label: string
  value: string
  detail?: string
}

function limitMetrics(result: EvaluationResult, t: ExtrapolationTranslate, locale: Locale): ExtrapolationMetric[] {
  const ter = result.total_error_rate
  if (ter.precision === null || ter.upper_limit === null) {
    return [{ id: 'precision', label: t('precision'), value: t('notDeterminable') }, { id: 'upper', label: t('upperLimit'), value: t('notDeterminable') }]
  }
  const metrics: ExtrapolationMetric[] = [
    { id: 'precision', label: t('precision'), value: extrapolationAmount(ter.precision, locale) },
    { id: 'upper', label: t('upperLimit'), value: extrapolationAmount(ter.upper_limit, locale), detail: extrapolationRate(ter.upper_limit_rate ?? 0, locale) },
  ]
  if (ter.difference) {
    metrics.push({ id: 'cbv', label: t('correctedBookValue'), value: extrapolationAmount(ter.difference.corrected_book_value, locale) })
    metrics.push({ id: 'lower', label: t('lowerLimit'), value: extrapolationAmount(ter.difference.lower_limit, locale) })
  }
  return metrics
}

/** Kennzahlen der Gesamtfehlerquote in fester Reihenfolge. */
export function terMetrics(result: EvaluationResult, t: ExtrapolationTranslate, locale: Locale): ExtrapolationMetric[] {
  const ter = result.total_error_rate
  const metrics: ExtrapolationMetric[] = [
    { id: 'projected', label: t('projected'), value: extrapolationAmount(ter.projected_random_error, locale) },
    { id: 'systemic', label: t('systemic'), value: extrapolationAmount(ter.systemic_errors, locale) },
    { id: 'anomalous', label: t('anomalousUncorrected'), value: extrapolationAmount(ter.anomalous_uncorrected, locale) },
  ]
  if (ter.anomalous_corrected_excluded > 0) {
    metrics.push({ id: 'excluded', label: t('anomalousExcluded'), value: extrapolationAmount(ter.anomalous_corrected_excluded, locale) })
  }
  metrics.push(
    { id: 'total', label: t('totalError'), value: extrapolationAmount(ter.total_error, locale) },
    { id: 'ter', label: t('ter'), value: extrapolationRate(ter.rate, locale) },
    { id: 'tolerable', label: t('tolerable'), value: extrapolationAmount(ter.tolerable_error, locale), detail: extrapolationRate(ter.materiality_rate, locale) },
  )
  return [...metrics, ...limitMetrics(result, t, locale)]
}

function stepValue(value: unknown, locale: Locale): string {
  if (typeof value !== 'number') return ''
  const digits = Math.abs(value) < 10 ? 6 : 2
  return formatNumber(value, locale, { maximumFractionDigits: digits })
}

export function extrapolationStepColumns(t: ExtrapolationTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'label', label: t('colStep') },
    { key: 'formula', label: t('colFormula') },
    { key: 'value', label: t('colValue'), align: 'end', format: (value) => stepValue(value, locale) },
    { key: 'source', label: t('colSource') },
  ]
}

export function extrapolationStepRows(result: EvaluationResult): TableRow[] {
  const steps = [...result.projection.steps, ...result.total_error_rate.steps]
  return steps.map((step, index) => ({ id: index + 1, ...step }))
}

export function residualColumns(t: ExtrapolationTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'row', label: t('colRow') },
    { key: 'label', label: t('colLabel') },
    { key: 'value', label: t('colAmount'), align: 'end', format: (value) => (value === null ? t('notApplicable') : stepValue(value, locale)) },
  ]
}

export function residualRows(residual: ResidualErrorRate): TableRow[] {
  return residual.rows.map((row) => ({ id: row.row, row: row.row, label: row.label, value: row.value }))
}

/** Kennzahlen der Restfehlerquote (K, L, M). */
export function residualMetrics(residual: ResidualErrorRate, t: ExtrapolationTranslate, locale: Locale): ExtrapolationMetric[] {
  const verdict = t(residual.exceeds_materiality ? 'rerExceeds' : 'rerWithin')
  const rate = residual.rate === null ? t('notApplicable') : extrapolationRate(residual.rate, locale)
  return [
    { id: 'rer', label: t('rer'), value: rate, detail: verdict },
    { id: 'correction', label: t('extrapolatedCorrection'), value: residual.extrapolated_correction === null ? t('notApplicable') : extrapolationAmount(residual.extrapolated_correction, locale) },
    { id: 'after', label: t('rateAfter'), value: residual.rate_after_correction === null ? t('notApplicable') : extrapolationRate(residual.rate_after_correction, locale) },
  ]
}

export interface ExtrapolationField<K extends string> {
  key: K
  label: ExtrapolationMessageKey
  numeric: boolean
}

export const STRATUM_FIELDS: readonly ExtrapolationField<'name' | 'bookValue' | 'populationSize' | 'systemic'>[] = [
  { key: 'name', label: 'stratumName', numeric: false },
  { key: 'bookValue', label: 'bookValue', numeric: true },
  { key: 'populationSize', label: 'populationSize', numeric: true },
  { key: 'systemic', label: 'systemicDelimited', numeric: true },
]

export const UNIT_FIELDS: readonly ExtrapolationField<'id' | 'bookValue' | 'random' | 'systemic' | 'anomalous' | 'reason'>[] = [
  { key: 'id', label: 'unitId', numeric: false },
  { key: 'bookValue', label: 'bookValue', numeric: true },
  { key: 'random', label: 'randomError', numeric: true },
  { key: 'systemic', label: 'systemicError', numeric: true },
  { key: 'anomalous', label: 'anomalousError', numeric: true },
  { key: 'reason', label: 'anomalousReason', numeric: false },
]

export const UNIT_FLAGS: readonly ExtrapolationField<'corrected' | 'exhaustive'>[] = [
  { key: 'corrected', label: 'anomalousCorrected', numeric: false },
  { key: 'exhaustive', label: 'exhaustive', numeric: false },
]

export const RESIDUAL_FIELDS: readonly ExtrapolationField<'auditPopulation' | 'terRate' | 'ongoing' | 'otherNegative' | 'corrections'>[] = [
  { key: 'auditPopulation', label: 'auditPopulation', numeric: true },
  { key: 'terRate', label: 'terRate', numeric: true },
  { key: 'ongoing', label: 'ongoing', numeric: true },
  { key: 'otherNegative', label: 'otherNegative', numeric: true },
  { key: 'corrections', label: 'corrections', numeric: true },
]

/** Meldung eines Feldes (leer ohne Befund). */
export function extrapolationIssueText(issues: Readonly<Record<string, ExtrapolationIssue>>, key: string, t: ExtrapolationTranslate): string {
  const issue = issues[key]
  return issue ? t(extrapolationIssueKey(issue)) : ''
}

/** Sammelmeldung unter dem Formular: fehlende Auswahl oder markierte Felder. */
export function extrapolationFormMessage(formError: ExtrapolationFormError | null, issues: Readonly<Record<string, ExtrapolationIssue>>, t: ExtrapolationTranslate): string {
  if (formError) return t(extrapolationFormErrorKey(formError))
  return Object.keys(issues).length ? t('formIncomplete') : ''
}

export function extrapolationCellLabel(t: ExtrapolationTranslate, field: ExtrapolationMessageKey, row: number): string {
  return t('cellLabel', { field: t(field), row })
}
